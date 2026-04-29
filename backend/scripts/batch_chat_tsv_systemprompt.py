import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any

import requests


SCRIPT_DIR = Path(__file__).resolve().parent

DEFAULT_INPUT_PATH = SCRIPT_DIR / "questions.tsv"
DEFAULT_OUTPUT_PATH = SCRIPT_DIR / "questions_result.tsv"

DEFAULT_CHAT_API_URL = "http://localhost:8000/chat"
DEFAULT_TIMEOUT_SECONDS = 180
DEFAULT_SLEEP_SECONDS = 0.2
DEFAULT_TOP_K = 30
DEFAULT_FINAL_K = 10
DEFAULT_QUERY_REWRITE_MODEL = "gpt-5.4"
DEFAULT_ANSWER_MODEL = "gpt-5.4"
DEFAULT_ANSWER_SYSTEM_PROMPT = (
    "Use the following pieces of context to answer the question at the end. "
    "If you don't know the answer, just say that you don't know, don't try to make up an answer"
)


REQUIRED_COLUMNS = ["no", "Question"]
OUTPUT_COLUMNS = ["no", "Question", "Response", "Context"]


def normalize_header(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def build_chat_payload(
    question: str,
) -> dict[str, Any]:
    """
    브라우저 /chat 기본 설정과 최대한 동일하게 맞춘다.
    단, 브라우저는 stream=true(SSE)이지만 이 배치 스크립트는 JSON 응답을
    후처리하므로 stream=false로 유지한다.
    """
    return {
        "query": question,
        "action": "search",
        "top_k": DEFAULT_TOP_K,
        "final_k": DEFAULT_FINAL_K,
        "query_rewrite_model": DEFAULT_QUERY_REWRITE_MODEL,
        "answer_model": DEFAULT_ANSWER_MODEL,
        "answer_system_prompt": DEFAULT_ANSWER_SYSTEM_PROMPT,
        "stream": False,
    }


def call_chat_api(
    api_url: str,
    question: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    response = requests.post(
        api_url,
        json=build_chat_payload(question),
        timeout=timeout_seconds,
    )
    response.raise_for_status()

    try:
        return response.json()
    except Exception as exc:
        raise ValueError(
            f"/chat API 응답이 JSON이 아닙니다. "
            f"status={response.status_code}, body={response.text[:500]}"
        ) from exc


def pick_first(data: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


def extract_answer(api_response: dict[str, Any]) -> str:
    answer = pick_first(
        api_response,
        [
            "answer",
            "response",
            "Response",
            "result",
            "message",
            "content",
        ],
    )

    if isinstance(answer, str):
        return answer.strip()

    if isinstance(answer, dict):
        nested = pick_first(
            answer,
            [
                "answer",
                "response",
                "content",
                "message",
                "text",
            ],
        )
        if isinstance(nested, str):
            return nested.strip()

    if answer is None:
        return ""

    return json.dumps(answer, ensure_ascii=False)


def extract_retrieved_chunks(api_response: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[Any] = [
        api_response.get("retrieved_chunks"),
        api_response.get("retrievedChunks"),
    ]

    result = api_response.get("result")
    if isinstance(result, dict):
        candidates.extend(
            [
                result.get("retrieved_chunks"),
                result.get("retrievedChunks"),
            ]
        )

    data = api_response.get("data")
    if isinstance(data, dict):
        candidates.extend(
            [
                data.get("retrieved_chunks"),
                data.get("retrievedChunks"),
            ]
        )

    for candidate in candidates:
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]

    return []


def extract_document_name(chunk: dict[str, Any]) -> str | None:
    document_name = pick_first(
        chunk,
        [
            "document_name",
            "documentName",
        ],
    )

    if isinstance(document_name, str) and document_name.strip():
        return document_name.strip()

    metadata = chunk.get("metadata")
    if isinstance(metadata, dict):
        metadata_document_name = pick_first(
            metadata,
            [
                "document_name",
                "documentName",
            ],
        )
        if isinstance(metadata_document_name, str) and metadata_document_name.strip():
            return metadata_document_name.strip()

    return None


def extract_context(api_response: dict[str, Any]) -> str:
    """
    Context에는 retrieved_chunks[].document_name 리스트를 넣습니다.
    TSV에서 줄바꿈이 불편하지 않도록 ', '로 연결합니다.
    """
    chunks = extract_retrieved_chunks(api_response)

    names: list[str] = []
    seen: set[str] = set()

    for chunk in chunks:
        name = extract_document_name(chunk)
        if not name:
            continue

        if name not in seen:
            seen.add(name)
            names.append(name)

    return ", ".join(names)


def clean_tsv_field(value: Any) -> str:
    """
    TSV 출력이 깨지지 않도록 탭/줄바꿈을 정리합니다.
    """
    if value is None:
        return ""

    text = str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")
    text = text.replace("\n", "\\n")
    return text.strip()


def read_tsv(input_path: Path) -> list[dict[str, str]]:
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("입력 TSV 파일에 header가 없습니다.")

        normalized_headers = {normalize_header(name): name for name in reader.fieldnames}

        if "no" not in normalized_headers:
            raise ValueError("입력 TSV 첫 줄에 'no' 컬럼이 필요합니다.")

        if "question" not in normalized_headers:
            raise ValueError("입력 TSV 첫 줄에 'Question' 컬럼이 필요합니다.")

        no_header = normalized_headers["no"]
        question_header = normalized_headers["question"]

        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append(
                {
                    "no": clean_tsv_field(row.get(no_header, "")),
                    "Question": str(row.get(question_header, "") or "").strip(),
                }
            )

        return rows


def write_tsv(output_path: Path, rows: list[dict[str, str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: clean_tsv_field(row.get(column, "")) for column in OUTPUT_COLUMNS})


def process_rows(
    api_url: str,
    rows: list[dict[str, str]],
    timeout_seconds: int,
    sleep_seconds: float,
) -> list[dict[str, str]]:
    total = len(rows)
    output_rows: list[dict[str, str]] = []

    for index, row in enumerate(rows, start=1):
        no = row.get("no", "")
        question = row.get("Question", "")
        print(f"[{index}/{total}, no={no}] 처리 시작: {question}")

        try:
            api_response = call_chat_api(api_url, question, timeout_seconds)
            answer = extract_answer(api_response)
            context = extract_context(api_response)
            output_rows.append(
                {
                    "no": no,
                    "Question": question,
                    "Response": answer,
                    "Context": context,
                }
            )
            print(f"[{index}/{total}, no={no}] 완료")
        except Exception as exc:
            output_rows.append(
                {
                    "no": no,
                    "Question": question,
                    "Response": f"ERROR: {type(exc).__name__}: {exc}",
                    "Context": "",
                }
            )
            print(f"[{index}/{total}, no={no}] 실패: ERROR: {type(exc).__name__}: {exc}")

        if index < total and sleep_seconds > 0:
            time.sleep(sleep_seconds)

    return output_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="questions.tsv를 읽어 /chat API를 호출하고 결과를 TSV로 저장합니다. 이 버전은 answer system prompt를 별도로 override합니다."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help=f"입력 TSV 경로 (기본값: {DEFAULT_INPUT_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"출력 TSV 경로 (기본값: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_CHAT_API_URL,
        help=f"/chat API URL (기본값: {DEFAULT_CHAT_API_URL})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"요청 타임아웃 초 (기본값: {DEFAULT_TIMEOUT_SECONDS})",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=DEFAULT_SLEEP_SECONDS,
        help=f"요청 사이 대기 초 (기본값: {DEFAULT_SLEEP_SECONDS})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    rows = read_tsv(args.input)
    output_rows = process_rows(
        api_url=args.api_url,
        rows=rows,
        timeout_seconds=args.timeout,
        sleep_seconds=args.sleep,
    )
    write_tsv(args.output, output_rows)

    print(f"완료: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
