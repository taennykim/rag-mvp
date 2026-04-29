import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any

import requests


SCRIPT_DIR = Path(__file__).resolve().parent

DEFAULT_INPUT_PATH = SCRIPT_DIR / "questions.tsv"
DEFAULT_OUTPUT_PATH = SCRIPT_DIR / "questions_detail_result.tsv"

DEFAULT_CHAT_API_URL = "http://localhost:8000/chat"
DEFAULT_TIMEOUT_SECONDS = 180
DEFAULT_SLEEP_SECONDS = 0.2
DEFAULT_TOP_K = 30
DEFAULT_FINAL_K = 10
DEFAULT_QUERY_REWRITE_MODEL = "gpt-4o"


OUTPUT_COLUMNS = [
    "no",
    "Question",
    "Response",
    "Context",
    "RewrittenQuery",
    "SearchQueries",
    "Detail",
]


def normalize_header(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def build_chat_payload(question: str) -> dict[str, Any]:
    return {
        "query": question,
        "action": "search",
        "top_k": DEFAULT_TOP_K,
        "final_k": DEFAULT_FINAL_K,
        "query_rewrite_model": DEFAULT_QUERY_REWRITE_MODEL,
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
        ["answer", "response", "Response", "result", "message", "content"],
    )

    if isinstance(answer, str):
        return answer.strip()

    if isinstance(answer, dict):
        nested = pick_first(
            answer,
            ["answer", "response", "content", "message", "text"],
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
    document_name = pick_first(chunk, ["document_name", "documentName"])
    if isinstance(document_name, str) and document_name.strip():
        return document_name.strip()

    metadata = chunk.get("metadata")
    if isinstance(metadata, dict):
        metadata_document_name = pick_first(
            metadata,
            ["document_name", "documentName"],
        )
        if isinstance(metadata_document_name, str) and metadata_document_name.strip():
            return metadata_document_name.strip()

    return None


def extract_context(api_response: dict[str, Any]) -> str:
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
                    "RewrittenQuery": clean_tsv_field(row.get("RewrittenQuery", "")),
                    "SearchQueries": clean_tsv_field(row.get("SearchQueries", "")),
                    "Detail": clean_tsv_field(row.get("Detail", "")),
                }
            )


def process_tsv(
    input_path: Path,
    output_path: Path,
    api_url: str,
    timeout_seconds: int,
    sleep_seconds: float,
) -> None:
    rows = read_tsv(input_path)

    print(f"입력 파일: {input_path}")
    print(f"출력 파일: {output_path}")
    print(f"API URL: {api_url}")
    print(f"처리 대상 row 수: {len(rows)}")

    result_rows: list[dict[str, str]] = []

    for index, row in enumerate(rows, start=1):
        no_value = row.get("no", "")
        question = str(row.get("Question", "") or "").strip()

        if not question:
            result_rows.append(
                {
                    "no": no_value,
                    "Question": question,
                    "Response": "",
                    "Context": "",
                    "RewrittenQuery": "",
                    "SearchQueries": "",
                    "Detail": "",
                }
            )
            continue

        print(f"[{index}/{len(rows)}, no={no_value}] 처리 시작: {question[:100]}")

        try:
            api_response = call_chat_api(
                api_url=api_url,
                question=question,
                timeout_seconds=timeout_seconds,
            )

            answer = extract_answer(api_response)
            context = extract_context(api_response)
            rewritten_query = str(api_response.get("rewritten_query") or "").strip()

            search_queries_value = api_response.get("search_queries")
            if isinstance(search_queries_value, list):
                search_queries = json.dumps(search_queries_value, ensure_ascii=False)
            else:
                search_queries = str(search_queries_value or "").strip()

            detail_value = api_response.get("detail")
            if isinstance(detail_value, (dict, list)):
                detail = json.dumps(detail_value, ensure_ascii=False)
            else:
                detail = str(detail_value or "").strip()

            result_rows.append(
                {
                    "no": no_value,
                    "Question": question,
                    "Response": answer,
                    "Context": context,
                    "RewrittenQuery": rewritten_query,
                    "SearchQueries": search_queries,
                    "Detail": detail,
                }
            )

            print(f"[{index}/{len(rows)}, no={no_value}] 완료")

        except Exception as exc:
            error_message = f"ERROR: {type(exc).__name__}: {exc}"

            result_rows.append(
                {
                    "no": no_value,
                    "Question": question,
                    "Response": error_message,
                    "Context": "",
                    "RewrittenQuery": "",
                    "SearchQueries": "",
                    "Detail": "",
                }
            )

            print(f"[{index}/{len(rows)}, no={no_value}] 실패: {error_message}")

        write_tsv(output_path, result_rows)
        time.sleep(sleep_seconds)

    write_tsv(output_path, result_rows)
    print(f"결과 파일 저장 완료: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TSV의 Question을 rag-mvp /chat API로 배치 실행하고 Response, Context, detail 필드를 함께 저장합니다."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help=f"입력 TSV 파일 경로. 기본값: {DEFAULT_INPUT_PATH}",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help=f"결과 TSV 파일 경로. 기본값: {DEFAULT_OUTPUT_PATH}",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_CHAT_API_URL,
        help=f"/chat API URL. 기본값: {DEFAULT_CHAT_API_URL}",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"질문 1건당 timeout 초. 기본값: {DEFAULT_TIMEOUT_SECONDS}",
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

    process_tsv(
        input_path=input_path,
        output_path=output_path,
        api_url=args.api_url,
        timeout_seconds=args.timeout,
        sleep_seconds=args.sleep,
    )


if __name__ == "__main__":
    main()
