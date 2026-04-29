import argparse
import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import AzureOpenAI, OpenAI


SCRIPT_DIR = Path(__file__).resolve().parent

DEFAULT_RESULT_TSV_PATH = SCRIPT_DIR / "questions_result.tsv"
DEFAULT_STANDARD_ANSWER_TSV_PATH = SCRIPT_DIR / "standard_answer.tsv"
DEFAULT_OUTPUT_TSV_PATH = SCRIPT_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M')}.tsv"

DEFAULT_MODEL = "gpt-4o"
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_SLEEP_SECONDS = 0.2


def load_runtime_env_file() -> None:
    candidate_files = [
        SCRIPT_DIR.parent / ".env.runtime",
        SCRIPT_DIR.parent / ".env",
        SCRIPT_DIR.parent.parent / ".env",
    ]

    for env_file in candidate_files:
        if not env_file.is_file():
            continue

        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value)
    text = text.replace("\\n", "\n")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()


def clean_tsv_field(value: Any) -> str:
    if value is None:
        return ""

    text = str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")
    text = text.replace("\n", "\\n")
    return text.strip()


def normalize_header(value: Any) -> str:
    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "")
        .replace("_", "")
        .replace(".", "")
    )


def normalize_no(value: Any) -> str:
    text = clean_text(value)

    if text.endswith(".0"):
        text = text[:-2]

    return text.strip()


def read_result_tsv(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("questions_result.tsv에 header가 없습니다.")

        normalized_headers = {normalize_header(name): name for name in reader.fieldnames}

        required = ["no", "question", "response", "context"]
        for col in required:
            if col not in normalized_headers:
                raise ValueError(
                    f"questions_result.tsv에 '{col}' 컬럼이 필요합니다. "
                    f"현재 header={reader.fieldnames}"
                )

        no_col = normalized_headers["no"]
        question_col = normalized_headers["question"]
        response_col = normalized_headers["response"]
        context_col = normalized_headers["context"]

        rows: dict[str, dict[str, str]] = {}
        for row in reader:
            no = normalize_no(row.get(no_col, ""))
            if not no:
                continue

            rows[no] = {
                "No.": no,
                "Question": clean_text(row.get(question_col, "")),
                "Response": clean_text(row.get(response_col, "")),
                "Context": clean_text(row.get(context_col, "")),
            }

        return rows


def read_standard_answer_tsv(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("standard_answer.tsv에 header가 없습니다.")

        normalized_headers = {normalize_header(name): name for name in reader.fieldnames}

        print(f"standard_answer.tsv headers: {reader.fieldnames}")

        no_key = None
        for candidate in ["no", "번호"]:
            if candidate in normalized_headers:
                no_key = candidate
                break

        answer_key = None
        for candidate in ["정답", "answer", "standardanswer"]:
            if candidate in normalized_headers:
                answer_key = candidate
                break

        document_key = None
        for candidate in ["문서명", "documentname", "document", "source", "sourcename"]:
            if candidate in normalized_headers:
                document_key = candidate
                break

        if no_key is None:
            raise ValueError(
                "standard_answer.tsv 첫 줄에 'No.' 또는 'No' 컬럼이 필요합니다. "
                f"현재 header={reader.fieldnames}"
            )

        if answer_key is None:
            raise ValueError(
                "standard_answer.tsv 첫 줄에 '정답' 또는 'Answer' 컬럼이 필요합니다. "
                f"현재 header={reader.fieldnames}"
            )

        if document_key is None:
            raise ValueError(
                "standard_answer.tsv 첫 줄에 '문서명' 또는 'DocumentName' 컬럼이 필요합니다. "
                f"현재 header={reader.fieldnames}"
            )

        no_col = normalized_headers[no_key]
        answer_col = normalized_headers[answer_key]
        document_col = normalized_headers[document_key]

        rows: dict[str, dict[str, str]] = {}

        for row in reader:
            no = normalize_no(row.get(no_col, ""))
            if not no:
                continue

            rows[no] = {
                "No.": no,
                "정답": clean_text(row.get(answer_col, "")),
                "문서명": clean_text(row.get(document_col, "")),
            }

        return rows


def build_openai_client() -> tuple[Any, str]:
    load_runtime_env_file()

    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

    deployment = (
        os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
        or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        or os.getenv("ANSWER_MODEL")
        or DEFAULT_MODEL
    )

    if azure_endpoint and azure_api_key:
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            api_version=azure_api_version,
        )
        return client, deployment

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise RuntimeError(
            "LLM 환경변수가 없습니다. "
            "Azure OpenAI를 쓰려면 AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY를 설정하세요. "
            "또는 OPENAI_API_KEY를 설정하세요."
        )

    client = OpenAI(api_key=openai_api_key)
    return client, DEFAULT_MODEL


def build_judge_messages(
    question: str,
    response: str,
    context: str,
    standard_answer: str,
    standard_document_name: str,
) -> list[dict[str, str]]:
    system_prompt = """
당신은 금융/보험 RAG 답변 평가자입니다.
주어진 Question에 대해 실제 Response가 정답과 의미적으로 일치하는지 판단하세요.
또한 실제 Context 문서 목록이 기대 문서명과 일치하는지 판단하세요.

판정 기준:
1. answer_match는 Response가 정답과 핵심 의미, 조건, 필요 서류, 예외사항을 충실히 포함하면 true입니다.
2. 표현이 달라도 의미가 같으면 true입니다.
3. 핵심 조건이 빠졌거나 반대로 답했거나 잘못된 내용을 추가하면 false입니다.
4. context_match는 Context에 문서명이 포함되거나 실질적으로 같은 문서명으로 판단되면 true입니다.
5. 문서명이 여러 개인 경우 하나라도 기대 문서와 명확히 일치하면 true로 볼 수 있습니다.
6. final_match는 answer_match와 context_match가 모두 true일 때 true입니다.
7. 반드시 JSON만 출력하세요.

출력 JSON 형식:
{
  "answer_match": true,
  "context_match": true,
  "final_match": true,
  "reason": "판단 이유를 한국어로 짧게 작성"
}
""".strip()

    user_prompt = f"""
[Question]
{question}

[Actual Response]
{response}

[Actual Context]
{context}

[Standard Answer / 정답]
{standard_answer}

[Standard Document Name / 문서명]
{standard_document_name}
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def parse_json_object(text: str) -> dict[str, Any]:
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError(f"LLM 응답에서 JSON을 찾지 못했습니다: {text[:500]}")


def judge_with_llm(
    client: Any,
    model: str,
    question: str,
    response: str,
    context: str,
    standard_answer: str,
    standard_document_name: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    messages = build_judge_messages(
        question=question,
        response=response,
        context=context,
        standard_answer=standard_answer,
        standard_document_name=standard_document_name,
    )

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        max_tokens=500,
        timeout=timeout_seconds,
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content or ""
    parsed = parse_json_object(content)

    return {
        "answer_match": bool(parsed.get("answer_match", False)),
        "context_match": bool(parsed.get("context_match", False)),
        "final_match": bool(parsed.get("final_match", False)),
        "reason": str(parsed.get("reason", "")).strip(),
    }


def write_output_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "No.",
        "Question",
        "Response",
        "Context",
        "정답",
        "문서명",
        "answer_match",
        "context_match",
        "final_match",
        "Result",
        "reason",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            delimiter="\t",
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()

        for row in rows:
            final_match = bool(row.get("final_match", False))

            writer.writerow(
                {
                    "No.": clean_tsv_field(row.get("No.", "")),
                    "Question": clean_tsv_field(row.get("Question", "")),
                    "Response": clean_tsv_field(row.get("Response", "")),
                    "Context": clean_tsv_field(row.get("Context", "")),
                    "정답": clean_tsv_field(row.get("정답", "")),
                    "문서명": clean_tsv_field(row.get("문서명", "")),
                    "answer_match": str(row.get("answer_match", "")),
                    "context_match": str(row.get("context_match", "")),
                    "final_match": str(row.get("final_match", "")),
                    "Result": "일치" if final_match else "불일치",
                    "reason": clean_tsv_field(row.get("reason", "")),
                }
            )


def compare_files(
    result_tsv_path: Path,
    standard_answer_tsv_path: Path,
    output_tsv_path: Path,
    timeout_seconds: int,
    sleep_seconds: float,
) -> None:
    result_rows = read_result_tsv(result_tsv_path)
    standard_rows = read_standard_answer_tsv(standard_answer_tsv_path)

    client, model = build_openai_client()

    print(f"결과 TSV: {result_tsv_path}")
    print(f"Standard Answer TSV: {standard_answer_tsv_path}")
    print(f"출력 TSV: {output_tsv_path}")
    print(f"LLM model/deployment: {model}")
    print(f"비교 대상 수: {len(result_rows)}")

    output_rows: list[dict[str, Any]] = []

    for index, no in enumerate(result_rows.keys(), start=1):
        result = result_rows[no]
        standard = standard_rows.get(no)

        if standard is None:
            row = {
                **result,
                "정답": "",
                "문서명": "",
                "answer_match": False,
                "context_match": False,
                "final_match": False,
                "reason": "standard_answer.tsv에서 같은 No.를 찾지 못했습니다.",
            }
            output_rows.append(row)
            write_output_tsv(output_tsv_path, output_rows)
            print(f"[{index}/{len(result_rows)}, No.={no}] 불일치: standard No. 없음")
            continue

        try:
            judge = judge_with_llm(
                client=client,
                model=model,
                question=result.get("Question", ""),
                response=result.get("Response", ""),
                context=result.get("Context", ""),
                standard_answer=standard.get("정답", ""),
                standard_document_name=standard.get("문서명", ""),
                timeout_seconds=timeout_seconds,
            )

            row = {
                **result,
                "정답": standard.get("정답", ""),
                "문서명": standard.get("문서명", ""),
                **judge,
            }

            output_rows.append(row)
            write_output_tsv(output_tsv_path, output_rows)

            print(
                f"[{index}/{len(result_rows)}, No.={no}] "
                f"{'일치' if judge['final_match'] else '불일치'} "
                f"(answer={judge['answer_match']}, context={judge['context_match']})"
            )

        except Exception as exc:
            row = {
                **result,
                "정답": standard.get("정답", ""),
                "문서명": standard.get("문서명", ""),
                "answer_match": False,
                "context_match": False,
                "final_match": False,
                "reason": f"ERROR: {type(exc).__name__}: {exc}",
            }

            output_rows.append(row)
            write_output_tsv(output_tsv_path, output_rows)

            print(f"[{index}/{len(result_rows)}, No.={no}] 실패: {row['reason']}")

        time.sleep(sleep_seconds)

    write_output_tsv(output_tsv_path, output_rows)
    print(f"비교 결과 저장 완료: {output_tsv_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="questions_result.tsv와 standard_answer.tsv를 gpt-4o로 비교해 일치/불일치를 판정합니다."
    )

    parser.add_argument(
        "--result-tsv",
        default=str(DEFAULT_RESULT_TSV_PATH),
        help=f"questions_result.tsv 경로. 기본값: {DEFAULT_RESULT_TSV_PATH}",
    )
    parser.add_argument(
        "--standard-answer-tsv",
        default=str(DEFAULT_STANDARD_ANSWER_TSV_PATH),
        help=f"standard_answer.tsv 경로. 기본값: {DEFAULT_STANDARD_ANSWER_TSV_PATH}",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_TSV_PATH),
        help=f"출력 TSV 경로. 기본값: {DEFAULT_OUTPUT_TSV_PATH}",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"LLM 요청 timeout 초. 기본값: {DEFAULT_TIMEOUT_SECONDS}",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=DEFAULT_SLEEP_SECONDS,
        help=f"row 사이 대기 초. 기본값: {DEFAULT_SLEEP_SECONDS}",
    )

    args = parser.parse_args()

    result_tsv_path = Path(args.result_tsv).resolve()
    standard_answer_tsv_path = Path(args.standard_answer_tsv).resolve()
    output_tsv_path = Path(args.output).resolve()

    if not result_tsv_path.exists():
        raise FileNotFoundError(f"questions_result.tsv 파일이 없습니다: {result_tsv_path}")

    if not standard_answer_tsv_path.exists():
        raise FileNotFoundError(f"standard_answer.tsv 파일이 없습니다: {standard_answer_tsv_path}")

    compare_files(
        result_tsv_path=result_tsv_path,
        standard_answer_tsv_path=standard_answer_tsv_path,
        output_tsv_path=output_tsv_path,
        timeout_seconds=args.timeout,
        sleep_seconds=args.sleep,
    )


if __name__ == "__main__":
    main()
