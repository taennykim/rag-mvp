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


def to_int_percent(value: Any) -> int:
    try:
        percent = int(round(float(value)))
    except Exception:
        return 0

    return max(0, min(100, percent))


def normalize_judgment(value: Any, percent: int) -> str:
    text = str(value or "").strip()

    if text in {"일치", "부분일치", "불일치"}:
        return text

    if percent >= 95:
        return "일치"
    if percent > 0:
        return "부분일치"
    return "불일치"


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
주어진 Question에 대해 실제 Response가 정답과 얼마나 일치하는지 평가하세요.
또한 실제 Context 문서 목록이 기대 문서명과 얼마나 일치하는지 평가하세요.

판정 기준:
1. answer_judgment는 "일치", "부분일치", "불일치" 중 하나입니다.
2. "일치"는 Response가 정답의 핵심 의미, 조건, 필요 서류, 예외사항을 모두 충실히 포함할 때만 사용합니다.
3. "부분일치"는 일부 핵심 내용은 맞지만 중요한 조건, 예외, 서류, 범위가 누락되었거나 일부 부정확할 때 사용합니다.
4. "불일치"는 핵심 답변이 틀렸거나, 정답과 반대이거나, 질문과 무관하거나, 사실상 답을 못 한 경우에만 사용합니다.
5. answer_match_percent는 0~100 정수입니다.
   - 일치: 100
   - 부분일치: 1~99
   - 불일치: 0
6. context_judgment는 "일치", "부분일치", "불일치" 중 하나입니다.
7. context_match_percent는 0~100 정수입니다.
   - Context가 기대 문서명을 명확히 포함하면 100
   - 관련 문서는 있으나 기대 문서명이 일부만 맞거나 유사 문서이면 1~99
   - 기대 문서와 무관하거나 비어 있으면 0
8. final_match_percent는 answer_match_percent 80%, context_match_percent 20% 가중 평균 정수입니다.
9. final_judgment는 다음 기준입니다.
   - final_match_percent가 95 이상이면 "일치"
   - final_match_percent가 1 이상 94 이하이면 "부분일치"
   - final_match_percent가 0이면 "불일치"
10. 반드시 JSON만 출력하세요.

출력 JSON 형식:
{
  "answer_judgment": "부분일치",
  "answer_match_percent": 70,
  "context_judgment": "일치",
  "context_match_percent": 100,
  "final_judgment": "부분일치",
  "final_match_percent": 76,
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
        max_tokens=700,
        timeout=timeout_seconds,
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content or ""
    parsed = parse_json_object(content)

    answer_percent = to_int_percent(parsed.get("answer_match_percent", 0))
    context_percent = to_int_percent(parsed.get("context_match_percent", 0))

    raw_final_percent = parsed.get("final_match_percent")
    if raw_final_percent is None:
        raw_final_percent = round(answer_percent * 0.8 + context_percent * 0.2)

    final_percent = to_int_percent(raw_final_percent)

    answer_judgment = normalize_judgment(parsed.get("answer_judgment"), answer_percent)
    context_judgment = normalize_judgment(parsed.get("context_judgment"), context_percent)
    final_judgment = normalize_judgment(parsed.get("final_judgment"), final_percent)

    return {
        "answer_judgment": answer_judgment,
        "answer_match_percent": answer_percent,
        "context_judgment": context_judgment,
        "context_match_percent": context_percent,
        "final_judgment": final_judgment,
        "final_match_percent": final_percent,
        "reason": str(parsed.get("reason", "")).strip(),
    }


def format_result_label(final_judgment: str, final_percent: int) -> str:
    if final_judgment == "일치":
        return "일치"

    if final_judgment == "부분일치":
        return f"부분일치 {final_percent}%"

    return "불일치"


def write_output_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "No.",
        "Question",
        "Response",
        "Context",
        "정답",
        "문서명",
        "answer_judgment",
        "answer_match_percent",
        "context_judgment",
        "context_match_percent",
        "final_judgment",
        "final_match_percent",
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
            final_percent = to_int_percent(row.get("final_match_percent", 0))
            final_judgment = normalize_judgment(row.get("final_judgment"), final_percent)

            writer.writerow(
                {
                    "No.": clean_tsv_field(row.get("No.", "")),
                    "Question": clean_tsv_field(row.get("Question", "")),
                    "Response": clean_tsv_field(row.get("Response", "")),
                    "Context": clean_tsv_field(row.get("Context", "")),
                    "정답": clean_tsv_field(row.get("정답", "")),
                    "문서명": clean_tsv_field(row.get("문서명", "")),
                    "answer_judgment": clean_tsv_field(row.get("answer_judgment", "")),
                    "answer_match_percent": str(to_int_percent(row.get("answer_match_percent", 0))),
                    "context_judgment": clean_tsv_field(row.get("context_judgment", "")),
                    "context_match_percent": str(to_int_percent(row.get("context_match_percent", 0))),
                    "final_judgment": final_judgment,
                    "final_match_percent": str(final_percent),
                    "Result": format_result_label(final_judgment, final_percent),
                    "reason": clean_tsv_field(row.get("reason", "")),
                }
            )


def build_error_row(
    result: dict[str, str],
    standard: dict[str, str] | None,
    reason: str,
) -> dict[str, Any]:
    return {
        **result,
        "정답": standard.get("정답", "") if standard else "",
        "문서명": standard.get("문서명", "") if standard else "",
        "answer_judgment": "불일치",
        "answer_match_percent": 0,
        "context_judgment": "불일치",
        "context_match_percent": 0,
        "final_judgment": "불일치",
        "final_match_percent": 0,
        "reason": reason,
    }


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
            row = build_error_row(
                result=result,
                standard=None,
                reason="standard_answer.tsv에서 같은 No.를 찾지 못했습니다.",
            )
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
                f"{judge['final_judgment']} {judge['final_match_percent']}% "
                f"(answer={judge['answer_match_percent']}%, context={judge['context_match_percent']}%)"
            )

        except Exception as exc:
            row = build_error_row(
                result=result,
                standard=standard,
                reason=f"ERROR: {type(exc).__name__}: {exc}",
            )

            output_rows.append(row)
            write_output_tsv(output_tsv_path, output_rows)

            print(f"[{index}/{len(result_rows)}, No.={no}] 실패: {row['reason']}")

        time.sleep(sleep_seconds)

    write_output_tsv(output_tsv_path, output_rows)
    print(f"비교 결과 저장 완료: {output_tsv_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="questions_result.tsv와 standard_answer.tsv를 gpt-4o로 비교해 일치/부분일치/불일치를 판정합니다."
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
