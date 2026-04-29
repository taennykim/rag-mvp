import argparse
import csv
import os
import time
from pathlib import Path
from typing import Any

from openai import AzureOpenAI, OpenAI


SCRIPT_DIR = Path(__file__).resolve().parent

DEFAULT_INPUT_TSV_PATH = SCRIPT_DIR / "questions_result.tsv"
DEFAULT_OUTPUT_TSV_PATH = SCRIPT_DIR / "questions_reason.tsv"

DEFAULT_MODEL = "gpt-4o"
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_SLEEP_SECONDS = 0.2

INPUT_REQUIRED_COLUMNS = ["no", "Question", "Response", "Context"]
OUTPUT_COLUMNS = ["no", "Question", "Response", "Context", "Reason"]


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
    return str(value).strip().lower()


def read_questions_result_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("questions_result.tsv에 header가 없습니다.")

        normalized_headers = {normalize_header(name): name for name in reader.fieldnames}

        for column in [name.lower() for name in INPUT_REQUIRED_COLUMNS]:
            if column not in normalized_headers:
                raise ValueError(
                    f"questions_result.tsv에 '{column}' 컬럼이 필요합니다. "
                    f"현재 header={reader.fieldnames}"
                )

        no_col = normalized_headers["no"]
        question_col = normalized_headers["question"]
        response_col = normalized_headers["response"]
        context_col = normalized_headers["context"]

        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append(
                {
                    "no": clean_text(row.get(no_col, "")),
                    "Question": clean_text(row.get(question_col, "")),
                    "Response": clean_text(row.get(response_col, "")),
                    "Context": clean_text(row.get(context_col, "")),
                }
            )

        return rows


def write_questions_reason_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=OUTPUT_COLUMNS,
            delimiter="\t",
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    "no": clean_tsv_field(row.get("no", "")),
                    "Question": clean_tsv_field(row.get("Question", "")),
                    "Response": clean_tsv_field(row.get("Response", "")),
                    "Context": clean_tsv_field(row.get("Context", "")),
                    "Reason": clean_tsv_field(row.get("Reason", "")),
                }
            )


def build_openai_client() -> tuple[Any, str]:
    load_runtime_env_file()

    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

    if azure_endpoint and azure_api_key:
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            api_version=azure_api_version,
        )
        return client, "azure"

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        client = OpenAI(api_key=openai_api_key)
        return client, "openai"

    raise EnvironmentError(
        "OpenAI client 설정이 없습니다. "
        "AZURE_OPENAI_ENDPOINT/AZURE_OPENAI_API_KEY 또는 OPENAI_API_KEY가 필요합니다."
    )


def build_reason_messages(question: str, response: str, context: str) -> list[dict[str, str]]:
    system_prompt = (
        "You analyze why a final answer appears to have been selected.\n"
        "Use only the provided Question, Response, and Context.\n"
        "Write concise Korean.\n"
        "1-3 sentences only.\n"
        "Mention whether the answer was grounded in the listed context documents, "
        "or whether it looks like an insufficient-context fallback.\n"
        "If the response says the answer could not be found, explicitly explain why it appears not to have been found, "
        "such as missing relevant context, wrong document focus, or only generic documents being retrieved.\n"
        "Do not invent hidden pipeline behavior or unseen evidence."
    )

    user_prompt = (
        f"Question:\n{question or '[empty]'}\n\n"
        f"Response:\n{response or '[empty]'}\n\n"
        f"Context:\n{context or '[empty]'}\n\n"
        "위 정보만 보고, 이 답변이 왜 채택된 것으로 보이는지 Reason을 작성하세요.\n"
        "답변을 찾지 못한 경우에는 왜 못 찾은 것으로 보이는지도 분명히 적으세요."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def generate_reason(
    client: Any,
    provider: str,
    *,
    model: str,
    question: str,
    response: str,
    context: str,
    timeout_seconds: int,
) -> str:
    messages = build_reason_messages(question, response, context)

    if provider == "azure":
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            top_p=0.9,
            max_tokens=220,
            timeout=timeout_seconds,
        )
    else:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            top_p=0.9,
            max_tokens=220,
            timeout=timeout_seconds,
        )

    content = completion.choices[0].message.content if completion.choices else ""
    return clean_text(content)


def process_rows(
    input_path: Path,
    output_path: Path,
    *,
    model: str,
    timeout_seconds: int,
    sleep_seconds: float,
) -> None:
    rows = read_questions_result_tsv(input_path)
    client, provider = build_openai_client()

    print(f"입력 파일: {input_path}")
    print(f"출력 파일: {output_path}")
    print(f"모델: {model}")
    print(f"provider: {provider}")
    print(f"처리 대상 row 수: {len(rows)}")

    result_rows: list[dict[str, str]] = []

    for index, row in enumerate(rows, start=1):
        no_value = row.get("no", "")
        question = row.get("Question", "")
        response = row.get("Response", "")
        context = row.get("Context", "")

        print(f"[{index}/{len(rows)}, no={no_value}] Reason 생성 시작")

        try:
            reason = generate_reason(
                client,
                provider,
                model=model,
                question=question,
                response=response,
                context=context,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:
            reason = f"ERROR: {type(exc).__name__}: {exc}"
            print(f"[{index}/{len(rows)}, no={no_value}] 실패: {reason}")
        else:
            print(f"[{index}/{len(rows)}, no={no_value}] 완료")

        result_rows.append(
            {
                "no": no_value,
                "Question": question,
                "Response": response,
                "Context": context,
                "Reason": reason,
            }
        )

        write_questions_reason_tsv(output_path, result_rows)
        time.sleep(sleep_seconds)

    write_questions_reason_tsv(output_path, result_rows)
    print(f"결과 파일 저장 완료: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="questions_result.tsv를 읽어 answer 채택 이유를 생성하고 questions_reason.tsv로 저장합니다."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_TSV_PATH),
        help=f"입력 TSV 파일 경로. 기본값: {DEFAULT_INPUT_TSV_PATH}",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_TSV_PATH),
        help=f"출력 TSV 파일 경로. 기본값: {DEFAULT_OUTPUT_TSV_PATH}",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"LLM 모델명. 기본값: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"row당 timeout 초. 기본값: {DEFAULT_TIMEOUT_SECONDS}",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=DEFAULT_SLEEP_SECONDS,
        help=f"row 사이 대기 초. 기본값: {DEFAULT_SLEEP_SECONDS}",
    )

    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"입력 TSV 파일이 없습니다: {input_path}")

    process_rows(
        input_path=input_path,
        output_path=output_path,
        model=args.model,
        timeout_seconds=args.timeout,
        sleep_seconds=args.sleep,
    )


if __name__ == "__main__":
    main()
