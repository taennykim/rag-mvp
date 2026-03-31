from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from functools import lru_cache
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from urllib import error as urllib_error
from urllib import request as urllib_request
from uuid import uuid4
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import fitz
from docx import Document
from docx.document import Document as DocxDocument
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel


app = FastAPI(title="Insurance Document RAG MVP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://10.160.98.178:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started_at = time.perf_counter()
    logger.info("request_started %s", summarize_request(request))
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.exception("request_failed %s duration_ms=%s", summarize_request(request), duration_ms)
        raise

    duration_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info(
        "request_completed %s status_code=%s duration_ms=%s",
        summarize_request(request),
        response.status_code,
        duration_ms,
    )
    response.headers["X-Backend-Log-Path"] = str(APP_LOG_PATH)
    return response


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    logger.warning(
        "http_error %s status_code=%s detail=%s",
        summarize_request(request),
        exc.status_code,
        exc.detail,
    )
    response = await http_exception_handler(request, exc)
    response.headers["X-Backend-Log-Path"] = str(APP_LOG_PATH)
    return response


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception):
    logger.exception("unexpected_error %s", summarize_request(request))
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Unexpected server error.",
            "log_path": str(APP_LOG_PATH),
        },
        headers={"X-Backend-Log-Path": str(APP_LOG_PATH)},
    )

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
APP_LOG_PATH = LOG_DIR / "app.log"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
DEFAULT_FILE_DIR = BASE_DIR / "data" / "default-files"
PARSE_METADATA_DIR = BASE_DIR / "data" / "parse-metadata"
CHUNK_METADATA_DIR = BASE_DIR / "data" / "chunk-metadata"
CHROMA_DIR = BASE_DIR / "data" / "chroma"
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx"}
PDF_SIGNATURE = b"%PDF-"
ZIP_SIGNATURE = b"PK\x03\x04"
CFBF_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
PREVIEW_LENGTH = 300
QUALITY_WARNING_THRESHOLD = 0.8
WORD_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
CHUNK_TARGET_LENGTH = 800
CHUNK_OVERLAP_LENGTH = 120
CHUNK_PREVIEW_LENGTH = 160
EMBEDDING_DIMENSION = 256
RETRIEVAL_CANDIDATE_MULTIPLIER = 5
RETRIEVAL_MAX_CANDIDATES = 50
PRIMARY_PARSER_DOCLING = "docling"
PRIMARY_PARSER_LEGACY_AUTO = "legacy-auto"
FALLBACK_PARSER_EXTENSION_DEFAULT = "extension-default"
FALLBACK_PARSER_NONE = "none"
FALLBACK_PARSER_PYMUPDF = "pymupdf"
FALLBACK_PARSER_PYTHON_DOCX = "python-docx"
FALLBACK_PARSER_DOC = "doc-parser"
FALLBACK_PARSER_EXCEL = "excel-parser"
EMBEDDING_PROVIDER_HASH = "hash"
EMBEDDING_PROVIDER_AZURE_OPENAI = "azure_openai"
DEFAULT_AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "text-embedding-3-small"
DEFAULT_AZURE_OPENAI_API_VERSION = "2024-02-01"
AZURE_OPENAI_EMBEDDING_BATCH_SIZE = 32
DEFAULT_CHAT_TOP_K = 5
RUNTIME_ENV_FILE = BASE_DIR / ".env.runtime"


def load_runtime_env_file() -> None:
    if not RUNTIME_ENV_FILE.is_file():
        return

    for raw_line in RUNTIME_ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_runtime_env_file()


def configure_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("rag-mvp")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    file_handler = RotatingFileHandler(APP_LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False
    return logger


logger = configure_logging()


def ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def ensure_default_file_dir() -> None:
    DEFAULT_FILE_DIR.mkdir(parents=True, exist_ok=True)


def ensure_parse_metadata_dir() -> None:
    PARSE_METADATA_DIR.mkdir(parents=True, exist_ok=True)


def ensure_chunk_metadata_dir() -> None:
    CHUNK_METADATA_DIR.mkdir(parents=True, exist_ok=True)


def ensure_chroma_dir() -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)


def summarize_request(request: Request) -> str:
    return f"{request.method} {request.url.path}"


def summarize_parser_selection(primary_parser: str, fallback_parser: str) -> str:
    return f"primary={primary_parser}, fallback={fallback_parser}"


def get_parse_history_from_logs() -> dict[str, dict[str, object]]:
    history: dict[str, dict[str, object]] = {}
    open_attempts: list[dict[str, str]] = []
    log_path = APP_LOG_PATH
    if not log_path.is_file():
        return history

    started_pattern = re.compile(r"parse_started stored_name=(\S+) .* primary=(\S+), fallback=(\S+)")
    completed_pattern = re.compile(
        r"parse_completed stored_name=(\S+) parser_used=(\S+) fallback_used=(True|False)"
    )

    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        started_match = started_pattern.search(line)
        if started_match:
            stored_name, primary_parser, fallback_parser = started_match.groups()
            open_attempts.append(
                {
                    "stored_name": stored_name,
                    "primary_parser": primary_parser,
                    "fallback_parser": fallback_parser,
                }
            )
            continue

        completed_match = completed_pattern.search(line)
        if completed_match:
            stored_name, parser_used, fallback_used = completed_match.groups()
            entry = history.setdefault(stored_name, {})
            entry["last_successful_parser_used"] = parser_used
            entry["last_successful_fallback_used"] = fallback_used == "True"
            open_attempts = [attempt for attempt in open_attempts if attempt["stored_name"] != stored_name]
            continue

        if "request_completed POST /parse status_code=400" in line and open_attempts:
            attempt = open_attempts.pop(0)
            entry = history.setdefault(attempt["stored_name"], {})
            entry["last_failed_parser_used"] = f"{attempt['primary_parser']} -> {attempt['fallback_parser']}"
            entry["last_failed_fallback_used"] = attempt["fallback_parser"] != FALLBACK_PARSER_NONE

    return history


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def get_supported_file_types_message() -> str:
    return "PDF, DOC, DOCX, XLS, and XLSX files are supported."


def get_type_validation_message(expected_extension: str, detected_extension: str | None) -> str:
    expected_label = expected_extension.lstrip(".").upper()
    if detected_extension == ".legacy-office":
        detected_label = "legacy Office binary"
    elif detected_extension:
        detected_label = detected_extension.lstrip(".").upper()
    else:
        detected_label = "unknown file type"

    return f"File extension indicates {expected_label}, but the uploaded content looks like {detected_label}."


def detect_ooxml_extension(content: bytes) -> str | None:
    try:
        with ZipFile(BytesIO(content)) as archive:
            names = set(archive.namelist())
    except Exception:
        return None

    if "word/document.xml" in names:
        return ".docx"
    if "xl/workbook.xml" in names:
        return ".xlsx"
    return None


def detect_actual_extension(filename: str, content: bytes) -> str | None:
    extension = get_extension(filename)
    if extension not in ALLOWED_EXTENSIONS:
        return None

    if content.startswith(PDF_SIGNATURE):
        return ".pdf"

    if content.startswith(ZIP_SIGNATURE):
        return detect_ooxml_extension(content)

    if content.startswith(CFBF_SIGNATURE):
        return ".legacy-office"

    return None


def validate_uploaded_file_type(filename: str, content: bytes) -> None:
    extension = get_extension(filename)
    detected_extension = detect_actual_extension(filename, content)

    if extension == ".pdf" and detected_extension != ".pdf":
        raise HTTPException(status_code=400, detail=get_type_validation_message(extension, detected_extension))

    if extension in {".docx", ".xlsx"} and detected_extension != extension:
        raise HTTPException(status_code=400, detail=get_type_validation_message(extension, detected_extension))

    if extension in {".doc", ".xls"} and detected_extension != ".legacy-office":
        raise HTTPException(status_code=400, detail=get_type_validation_message(extension, detected_extension))


def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def tokenize_text(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def get_default_auxiliary_parser(extension: str) -> str:
    if extension == ".pdf":
        return FALLBACK_PARSER_PYMUPDF
    if extension == ".docx":
        return FALLBACK_PARSER_PYTHON_DOCX
    if extension == ".doc":
        return FALLBACK_PARSER_DOC
    if extension in {".xls", ".xlsx"}:
        return FALLBACK_PARSER_EXCEL
    return FALLBACK_PARSER_NONE


def parser_supports_extension(parser_id: str, extension: str) -> bool:
    if parser_id == PRIMARY_PARSER_DOCLING:
        return extension in {".pdf", ".docx", ".xlsx"}
    if parser_id == PRIMARY_PARSER_LEGACY_AUTO:
        return extension in ALLOWED_EXTENSIONS
    if parser_id == FALLBACK_PARSER_PYMUPDF:
        return extension == ".pdf"
    if parser_id == FALLBACK_PARSER_PYTHON_DOCX:
        return extension == ".docx"
    if parser_id == FALLBACK_PARSER_DOC:
        return extension == ".doc"
    if parser_id == FALLBACK_PARSER_EXCEL:
        return extension in {".xls", ".xlsx"}
    return parser_id == FALLBACK_PARSER_NONE


def get_parser_label(parser_id: str) -> str:
    labels = {
        PRIMARY_PARSER_DOCLING: "Docling",
        PRIMARY_PARSER_LEGACY_AUTO: "Legacy auto parser",
        FALLBACK_PARSER_EXTENSION_DEFAULT: "Extension default parser",
        FALLBACK_PARSER_NONE: "No fallback",
        FALLBACK_PARSER_PYMUPDF: "PyMuPDF (PDF)",
        FALLBACK_PARSER_PYTHON_DOCX: "python-docx (DOCX)",
        FALLBACK_PARSER_DOC: "DOC parser",
        FALLBACK_PARSER_EXCEL: "Excel parser",
    }
    return labels.get(parser_id, parser_id)


def is_docling_available() -> bool:
    try:
        import docling  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def is_command_available(command: str) -> bool:
    return shutil.which(command) is not None


def is_excel_parser_available() -> bool:
    try:
        import openpyxl  # noqa: F401
        import xlrd  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


@lru_cache(maxsize=1)
def get_docling_converter():
    try:
        from docling.document_converter import DocumentConverter
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError("Docling is not installed in the current environment.") from exc

    return DocumentConverter()


def get_parser_catalog() -> dict[str, object]:
    docling_available = is_docling_available()
    excel_parser_available = is_excel_parser_available()
    doc_parser_available = is_command_available("antiword")
    return {
        "default_primary_parser": PRIMARY_PARSER_DOCLING,
        "default_fallback_parser": FALLBACK_PARSER_EXTENSION_DEFAULT,
        "primary_parsers": [
            {
                "id": PRIMARY_PARSER_DOCLING,
                "label": "Docling",
                "available": docling_available,
                "description": "기본 파서. PDF, DOCX, XLSX를 우선 Docling으로 변환합니다.",
                "supported_extensions": [".pdf", ".docx", ".xlsx"],
            },
            {
                "id": PRIMARY_PARSER_LEGACY_AUTO,
                "label": "Legacy auto parser",
                "available": True,
                "description": "파일 확장자에 따라 기존 내장 파서를 바로 사용합니다.",
                "supported_extensions": [".pdf", ".doc", ".docx", ".xls", ".xlsx"],
            },
        ],
        "fallback_parsers": [
            {
                "id": FALLBACK_PARSER_EXTENSION_DEFAULT,
                "label": "Extension default parser",
                "available": True,
                "description": "PDF는 PyMuPDF, DOCX는 python-docx, DOC는 antiword, Excel은 openpyxl/xlrd를 자동 선택합니다.",
                "supported_extensions": [".pdf", ".docx", ".doc", ".xls", ".xlsx"],
            },
            {
                "id": FALLBACK_PARSER_PYMUPDF,
                "label": "PyMuPDF (PDF)",
                "available": True,
                "description": "PDF 전용 보조 파서입니다.",
                "supported_extensions": [".pdf"],
            },
            {
                "id": FALLBACK_PARSER_PYTHON_DOCX,
                "label": "python-docx (DOCX)",
                "available": True,
                "description": "DOCX 전용 보조 파서입니다.",
                "supported_extensions": [".docx"],
            },
            {
                "id": FALLBACK_PARSER_DOC,
                "label": "DOC parser",
                "available": doc_parser_available,
                "description": "DOC 전용 보조 파서입니다. antiword를 사용합니다.",
                "supported_extensions": [".doc"],
            },
            {
                "id": FALLBACK_PARSER_EXCEL,
                "label": "Excel parser",
                "available": excel_parser_available,
                "description": "XLS/XLSX 보조 파서입니다. openpyxl과 xlrd를 사용합니다.",
                "supported_extensions": [".xls", ".xlsx"],
            },
            {
                "id": FALLBACK_PARSER_NONE,
                "label": "No fallback",
                "available": True,
                "description": "기본 파서 실패 시 보조 파서를 사용하지 않습니다.",
                "supported_extensions": [],
            },
        ],
    }


def build_token_frequency(tokens: list[str]) -> dict[str, int]:
    frequency: dict[str, int] = {}
    for token in tokens:
        frequency[token] = frequency.get(token, 0) + 1
    return frequency


def normalize_for_ngrams(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def build_character_ngrams(text: str, min_n: int = 2, max_n: int = 4) -> set[str]:
    normalized = normalize_for_ngrams(text)
    ngrams: set[str] = set()

    for size in range(min_n, max_n + 1):
        if len(normalized) < size:
            continue
        for index in range(len(normalized) - size + 1):
            ngrams.add(normalized[index : index + size])

    return ngrams


def build_file_metadata(path: Path) -> dict[str, object]:
    return {
        "stored_name": path.name,
        "original_name": path.name.split("__", 1)[1] if "__" in path.name else path.name,
        "size_bytes": path.stat().st_size,
        "uploaded_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
    }


def get_parse_summary_path(path: Path) -> Path:
    ensure_parse_metadata_dir()
    return PARSE_METADATA_DIR / f"{path.name}.json"


def get_chunk_summary_path(path: Path) -> Path:
    ensure_chunk_metadata_dir()
    return CHUNK_METADATA_DIR / f"{path.name}.json"


def read_json_file(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_parse_summary(
    path: Path,
    *,
    status: str,
    parser_used: str,
    fallback_used: bool,
    text_length: int,
    file_type: str,
    preview: str | None = None,
    error_detail: str | None = None,
) -> Path:
    summary_path = get_parse_summary_path(path)
    summary = {
        "stored_name": path.name,
        "original_name": path.name.split("__", 1)[1] if "__" in path.name else path.name,
        "status": status,
        "file_type": file_type,
        "parser_used": parser_used,
        "fallback_used": fallback_used,
        "text_length": text_length,
        "preview": preview,
        "error_detail": error_detail,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary_path


def write_parse_failure_summary(
    path: Path,
    *,
    file_type: str,
    parser_used: str,
    fallback_used: bool,
    error_detail: str,
) -> Path:
    return write_parse_summary(
        path,
        status="failed",
        parser_used=parser_used,
        fallback_used=fallback_used,
        text_length=0,
        file_type=file_type,
        preview=None,
        error_detail=error_detail,
    )


def update_parse_quality_summary(
    path: Path,
    *,
    parser_used: str,
    fallback_used: bool,
    metrics: dict[str, object],
) -> None:
    summary_path = get_parse_summary_path(path)
    summary = read_json_file(summary_path) or {
        "stored_name": path.name,
        "original_name": path.name.split("__", 1)[1] if "__" in path.name else path.name,
        "status": "completed",
        "file_type": get_extension(path.name),
    }
    summary.update(
        {
            "parser_used": parser_used,
            "fallback_used": fallback_used,
            "quality_checked_at": datetime.now(timezone.utc).isoformat(),
            "jaccard_similarity": metrics.get("jaccard_similarity"),
            "levenshtein_distance": metrics.get("levenshtein_distance"),
            "quality_warning": metrics.get("quality_warning"),
            "quality_warning_message": metrics.get("quality_warning_message"),
        }
    )
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def list_uploaded_files() -> list[dict[str, object]]:
    ensure_upload_dir()
    files: list[dict[str, object]] = []
    for path in sorted(UPLOAD_DIR.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_file():
            continue
        files.append(build_file_metadata(path))
    return files


def list_parsed_files() -> list[dict[str, object]]:
    ensure_parse_metadata_dir()
    files: list[dict[str, object]] = []
    for path in sorted(PARSE_METADATA_DIR.iterdir(), key=lambda item: item.name):
        if not path.is_file() or path.suffix.lower() != ".json":
            continue
        summary = read_json_file(path)
        if summary:
            files.append(summary)
    return files


def list_chunked_files() -> list[dict[str, object]]:
    ensure_chunk_metadata_dir()
    files: list[dict[str, object]] = []
    for path in sorted(CHUNK_METADATA_DIR.iterdir(), key=lambda item: item.name):
        if not path.is_file() or path.suffix.lower() != ".json":
            continue
        summary = read_json_file(path)
        if summary:
            files.append(summary)
    return files


def list_default_files() -> list[dict[str, object]]:
    ensure_default_file_dir()
    files: list[dict[str, object]] = []
    for path in sorted(DEFAULT_FILE_DIR.iterdir(), key=lambda item: item.name):
        if not path.is_file():
            continue
        if get_extension(path.name) not in ALLOWED_EXTENSIONS:
            continue
        files.append(
            {
                "name": path.name,
                "size_bytes": path.stat().st_size,
            }
        )
    return files


def save_content_to_uploads(filename: str, content: bytes, content_type: str | None) -> dict[str, object]:
    ensure_upload_dir()
    stored_name = f"{uuid4().hex}__{Path(filename).name}"
    destination = UPLOAD_DIR / stored_name
    destination.write_bytes(content)
    metadata = build_file_metadata(destination)
    metadata.update(
        {
            "status": "uploaded",
            "content_type": content_type,
        }
    )
    return metadata


def ensure_no_completed_duplicate_upload(filename: str) -> None:
    normalized_name = Path(filename).name
    for file in list_pipeline_files():
        original_name = file.get("original_name")
        index_status = file.get("index_status")
        if original_name == normalized_name and index_status == "completed":
            raise HTTPException(
                status_code=409,
                detail=f"{normalized_name} is already uploaded and indexed. Reset the existing file before uploading it again.",
            )


def get_uploaded_file_path(stored_name: str) -> Path:
    ensure_upload_dir()
    filename = Path(stored_name).name
    path = UPLOAD_DIR / filename

    if not path.is_file():
        raise HTTPException(status_code=404, detail="Uploaded file not found.")

    extension = get_extension(path.name)
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=get_supported_file_types_message())

    return path


def extract_pdf_text(path: Path) -> str:
    document = fitz.open(path)
    try:
        pages = [page.get_text("text") for page in document]
    finally:
        document.close()
    return normalize_text("\n".join(pages))


def extract_docx_text(path: Path) -> str:
    document = Document(path)
    sections: list[str] = []

    sections.extend(extract_docx_container_text(document))

    for section in document.sections:
        sections.extend(extract_docx_container_text(section.header))
        sections.extend(extract_docx_container_text(section.footer))

    return normalize_text("\n".join(section for section in sections if section.strip()))


def extract_doc_text(path: Path) -> str:
    if not is_command_available("antiword"):
        raise RuntimeError("antiword is not installed in the current environment.")

    completed = subprocess.run(
        ["antiword", str(path)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        raise RuntimeError(stderr or "antiword failed to parse the DOC file.")

    return normalize_text(completed.stdout)


def format_excel_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def extract_xlsx_text(path: Path) -> str:
    try:
        from openpyxl import load_workbook
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError("openpyxl is not installed in the current environment.") from exc

    workbook = load_workbook(filename=path, read_only=True, data_only=True)
    sheets: list[str] = []
    try:
        for sheet in workbook.worksheets:
            rows: list[str] = [f"# Sheet: {sheet.title}"]
            for row in sheet.iter_rows(values_only=True):
                values = [format_excel_cell(cell) for cell in row]
                values = [value for value in values if value]
                if values:
                    rows.append(" | ".join(values))
            if len(rows) > 1:
                sheets.append("\n".join(rows))
    finally:
        workbook.close()

    return normalize_text("\n\n".join(sheets))


def extract_xls_text(path: Path) -> str:
    try:
        import xlrd
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError("xlrd is not installed in the current environment.") from exc

    workbook = xlrd.open_workbook(path)
    sheets: list[str] = []
    for sheet in workbook.sheets():
        rows: list[str] = [f"# Sheet: {sheet.name}"]
        for row_index in range(sheet.nrows):
            values = [format_excel_cell(sheet.cell_value(row_index, column_index)) for column_index in range(sheet.ncols)]
            values = [value for value in values if value]
            if values:
                rows.append(" | ".join(values))
        if len(rows) > 1:
            sheets.append("\n".join(rows))

    return normalize_text("\n\n".join(sheets))


def extract_excel_text(path: Path) -> str:
    extension = get_extension(path.name)
    if extension == ".xlsx":
        return extract_xlsx_text(path)
    if extension == ".xls":
        return extract_xls_text(path)
    raise HTTPException(status_code=400, detail="Excel parser is only available for XLS/XLSX files.")


def iter_docx_blocks(parent: DocxDocument | _Cell | object) -> list[Paragraph | Table]:
    if isinstance(parent, DocxDocument):
        parent_element = parent.element.body
    elif hasattr(parent, "_tc"):
        parent_element = parent._tc
    else:
        parent_element = parent._element

    blocks: list[Paragraph | Table] = []
    for child in parent_element.iterchildren():
        if isinstance(child, CT_P):
            blocks.append(Paragraph(child, parent))
            continue
        if isinstance(child, CT_Tbl):
            blocks.append(Table(child, parent))
    return blocks


def extract_docx_table_text(table: Table) -> str:
    rows: list[str] = []

    for row in table.rows:
        cells: list[str] = []
        for cell in row.cells:
            cell_sections = extract_docx_container_text(cell)
            cell_text = " ".join(part for part in cell_sections if part.strip())
            if cell_text:
                cells.append(cell_text)
        if cells:
            rows.append(" | ".join(cells))

    return "\n".join(rows)


def extract_docx_container_text(container: DocxDocument | _Cell | object) -> list[str]:
    parts: list[str] = []

    for block in iter_docx_blocks(container):
        if isinstance(block, Paragraph):
            if block.text.strip():
                parts.append(block.text)
            continue

        table_text = extract_docx_table_text(block)
        if table_text:
            parts.append(table_text)

    return parts


def extract_docling_text(path: Path) -> str:
    converter = get_docling_converter()
    result = converter.convert(path)
    text = result.document.export_to_markdown()
    return normalize_text(text)


def extract_with_parser(path: Path, parser_id: str) -> tuple[str, str]:
    extension = get_extension(path.name)

    if parser_id == PRIMARY_PARSER_DOCLING:
        if not parser_supports_extension(parser_id, extension):
            raise HTTPException(status_code=400, detail=f"Docling does not support {extension} in the current parser policy.")
        return extract_docling_text(path), parser_id

    if parser_id in {PRIMARY_PARSER_LEGACY_AUTO, FALLBACK_PARSER_EXTENSION_DEFAULT}:
        resolved_parser = get_default_auxiliary_parser(extension)
        return extract_with_parser(path, resolved_parser)

    if parser_id == FALLBACK_PARSER_PYMUPDF:
        if extension != ".pdf":
            raise HTTPException(status_code=400, detail="PyMuPDF fallback is only available for PDF files.")
        return extract_pdf_text(path), parser_id

    if parser_id == FALLBACK_PARSER_PYTHON_DOCX:
        if extension != ".docx":
            raise HTTPException(status_code=400, detail="python-docx fallback is only available for DOCX files.")
        return extract_docx_text(path), parser_id

    if parser_id == FALLBACK_PARSER_DOC:
        if extension != ".doc":
            raise HTTPException(status_code=400, detail="DOC fallback parser is only available for DOC files.")
        return extract_doc_text(path), parser_id

    if parser_id == FALLBACK_PARSER_EXCEL:
        if extension not in {".xls", ".xlsx"}:
            raise HTTPException(status_code=400, detail="Excel fallback parser is only available for XLS/XLSX files.")
        return extract_excel_text(path), parser_id

    if parser_id == FALLBACK_PARSER_NONE:
        raise HTTPException(status_code=400, detail="No fallback parser is configured.")

    raise HTTPException(status_code=400, detail=f"Unsupported parser selection: {parser_id}")


def extract_text_from_file(
    path: Path,
    *,
    primary_parser: str = PRIMARY_PARSER_DOCLING,
    fallback_parser: str = FALLBACK_PARSER_EXTENSION_DEFAULT,
) -> tuple[str, str, bool]:
    attempts: list[str] = []
    seen: set[str] = set()

    for parser_id in [primary_parser, fallback_parser]:
        if parser_id in seen:
            continue
        seen.add(parser_id)
        try:
            logger.info("parser_attempt stored_name=%s parser=%s", path.name, parser_id)
            text, parser_used = extract_with_parser(path, parser_id)
            logger.info("parser_success stored_name=%s parser=%s", path.name, parser_used)
            return text, parser_used, parser_used != primary_parser
        except (HTTPException, ModuleNotFoundError, RuntimeError, ValueError) as exc:
            logger.warning("parser_failed stored_name=%s parser=%s reason=%s", path.name, parser_id, str(exc))
            attempts.append(f"{get_parser_label(parser_id)}: {str(exc)}")
            continue

    raise HTTPException(
        status_code=400,
        detail="Parsing failed. " + " | ".join(attempts) if attempts else "Parsing failed.",
    )


def extract_reference_pdf_text(path: Path) -> str:
    document = fitz.open(path)
    try:
        pages: list[str] = []
        for page in document:
            blocks = page.get_text("blocks")
            block_texts = [block[4] for block in blocks if len(block) > 4 and str(block[4]).strip()]
            pages.append("\n".join(block_texts))
    finally:
        document.close()
    return normalize_text("\n".join(pages))


def extract_reference_docx_text(path: Path) -> str:
    parts: list[str] = []
    with ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if not name.startswith("word/"):
                continue
            if not name.endswith(".xml"):
                continue
            if not (name == "word/document.xml" or name.startswith("word/header") or name.startswith("word/footer")):
                continue

            xml_bytes = archive.read(name)
            root = ET.fromstring(xml_bytes)
            texts = [node.text for node in root.findall(".//w:t", WORD_NAMESPACE) if node.text]
            if texts:
                parts.append(" ".join(texts))

    return normalize_text("\n".join(parts))


def extract_reference_text(path: Path) -> str:
    extension = get_extension(path.name)

    if extension == ".pdf":
        return extract_reference_pdf_text(path)

    if extension == ".docx":
        return extract_reference_docx_text(path)

    if extension == ".doc":
        return extract_doc_text(path)

    if extension in {".xls", ".xlsx"}:
        return extract_excel_text(path)

    raise HTTPException(status_code=400, detail=get_supported_file_types_message())


def calculate_jaccard_similarity(left_text: str, right_text: str) -> float:
    left_tokens = set(tokenize_text(left_text))
    right_tokens = set(tokenize_text(right_text))

    if not left_tokens and not right_tokens:
        return 1.0

    union = left_tokens | right_tokens
    if not union:
        return 0.0

    return len(left_tokens & right_tokens) / len(union)


def calculate_levenshtein_distance(left_tokens: list[str], right_tokens: list[str]) -> int:
    if len(left_tokens) < len(right_tokens):
        left_tokens, right_tokens = right_tokens, left_tokens

    previous = list(range(len(right_tokens) + 1))
    for i, left_token in enumerate(left_tokens, start=1):
        current = [i]
        for j, right_token in enumerate(right_tokens, start=1):
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (0 if left_token == right_token else 1)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current

    return previous[-1]


def build_quality_metrics(parsed_text: str, reference_text: str) -> dict[str, object]:
    parsed_tokens = tokenize_text(parsed_text)
    reference_tokens = tokenize_text(reference_text)
    jaccard_similarity = calculate_jaccard_similarity(parsed_text, reference_text)
    levenshtein_distance = calculate_levenshtein_distance(parsed_tokens, reference_tokens)

    return {
        "jaccard_similarity": jaccard_similarity,
        "levenshtein_distance": levenshtein_distance,
        "quality_warning": jaccard_similarity < QUALITY_WARNING_THRESHOLD,
        "quality_warning_message": "파싱 품질주의" if jaccard_similarity < QUALITY_WARNING_THRESHOLD else "",
    }


def build_parsing_result(
    path: Path,
    *,
    primary_parser: str = PRIMARY_PARSER_DOCLING,
    fallback_parser: str = FALLBACK_PARSER_EXTENSION_DEFAULT,
) -> dict[str, object]:
    text, parser_used, fallback_used = extract_text_from_file(
        path,
        primary_parser=primary_parser,
        fallback_parser=fallback_parser,
    )

    if not text.strip():
        raise HTTPException(status_code=400, detail="Extracted text is empty.")

    write_parse_summary(
        path,
        status="completed",
        parser_used=parser_used,
        fallback_used=fallback_used,
        text_length=len(text),
        file_type=get_extension(path.name),
        preview=text[:PREVIEW_LENGTH],
    )

    metadata = build_file_metadata(path)
    metadata.update(
        {
            "status": "parsed",
            "file_type": get_extension(path.name),
            "text_length": len(text),
            "preview": text[:PREVIEW_LENGTH],
            "extracted_text": text,
            "primary_parser": primary_parser,
            "fallback_parser": fallback_parser,
            "parser_used": parser_used,
            "fallback_used": fallback_used,
        }
    )
    return metadata


def build_parsing_quality_result(
    path: Path,
    *,
    primary_parser: str = PRIMARY_PARSER_DOCLING,
    fallback_parser: str = FALLBACK_PARSER_EXTENSION_DEFAULT,
) -> dict[str, object]:
    parsed_text, parser_used, fallback_used = extract_text_from_file(
        path,
        primary_parser=primary_parser,
        fallback_parser=fallback_parser,
    )
    reference_text = extract_reference_text(path)

    if not parsed_text.strip():
        raise HTTPException(status_code=400, detail="Extracted text is empty.")

    metadata = build_file_metadata(path)
    metadata.update(
        {
            "status": "quality_checked",
            "file_type": get_extension(path.name),
            "text_length": len(parsed_text),
            "reference_text_length": len(reference_text),
            "primary_parser": primary_parser,
            "fallback_parser": fallback_parser,
            "parser_used": parser_used,
            "fallback_used": fallback_used,
        }
    )
    quality_metrics = build_quality_metrics(parsed_text, reference_text)
    metadata.update(quality_metrics)
    update_parse_quality_summary(
        path,
        parser_used=parser_used,
        fallback_used=fallback_used,
        metrics=quality_metrics,
    )
    return metadata


def split_long_segment(segment: str, max_length: int) -> list[str]:
    normalized_segment = segment.strip()
    if not normalized_segment:
        return []

    if len(normalized_segment) <= max_length:
        return [normalized_segment]

    sentences = [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+|(?<=[.!?])\n+|\n+", normalized_segment)
        if part.strip()
    ]

    if len(sentences) == 1 and len(sentences[0]) > max_length:
        chunks: list[str] = []
        start = 0
        while start < len(normalized_segment):
            end = min(start + max_length, len(normalized_segment))
            chunks.append(normalized_segment[start:end].strip())
            start = end
        return [chunk for chunk in chunks if chunk]

    segments: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = sentence if not current else f"{current} {sentence}"
        if len(candidate) <= max_length:
            current = candidate
            continue
        if current:
            segments.append(current)
        if len(sentence) > max_length:
            segments.extend(split_long_segment(sentence, max_length))
            current = ""
            continue
        current = sentence

    if current:
        segments.append(current)

    return segments


def normalize_chunk_settings(
    target_length: int | None = None,
    overlap_length: int | None = None,
) -> tuple[int, int]:
    resolved_target_length = target_length if target_length is not None else CHUNK_TARGET_LENGTH
    resolved_overlap_length = overlap_length if overlap_length is not None else CHUNK_OVERLAP_LENGTH

    if resolved_target_length < 100:
        raise HTTPException(status_code=400, detail="chunk target_length must be at least 100.")
    if resolved_overlap_length < 0:
        raise HTTPException(status_code=400, detail="chunk overlap_length must be 0 or greater.")
    if resolved_overlap_length >= resolved_target_length:
        raise HTTPException(status_code=400, detail="chunk overlap_length must be smaller than target_length.")

    return resolved_target_length, resolved_overlap_length


def build_chunk_segments(text: str, target_length: int) -> list[str]:
    raw_segments = [line.strip() for line in text.splitlines() if line.strip()]
    segments: list[str] = []

    for raw_segment in raw_segments:
        segments.extend(split_long_segment(raw_segment, target_length))

    return segments


def build_overlap_text(chunk_text: str, overlap_length: int) -> str:
    if len(chunk_text) <= overlap_length:
        return chunk_text
    return chunk_text[-overlap_length:].strip()


def create_chunks(
    text: str,
    *,
    source: str,
    target_length: int = CHUNK_TARGET_LENGTH,
    overlap_length: int = CHUNK_OVERLAP_LENGTH,
    page_number: int | None = None,
    section_header: str | None = None,
) -> list[dict[str, object]]:
    segments = build_chunk_segments(text, target_length)
    if not segments:
        return []

    chunks: list[dict[str, object]] = []
    current = ""
    current_start = 0
    cursor = 0

    for segment in segments:
        segment_start = cursor
        cursor += len(segment)

        candidate = segment if not current else f"{current}\n{segment}"
        if current and len(candidate) > target_length:
            chunk_end = current_start + len(current)
            chunks.append(
                {
                    "chunk_index": len(chunks),
                    "source": source,
                    "text": current,
                    "text_length": len(current),
                    "start_char": current_start,
                    "end_char": chunk_end,
                    "page_number": page_number,
                    "section_header": section_header,
                    "preview": current[:CHUNK_PREVIEW_LENGTH],
                }
            )
            overlap = build_overlap_text(current, overlap_length)
            current = segment if not overlap else f"{overlap}\n{segment}"
            current_start = max(chunk_end - len(overlap), 0)
            cursor = max(cursor, current_start + len(current))
            continue

        if not current:
            current_start = segment_start
        current = candidate

    if current:
        chunk_end = current_start + len(current)
        chunks.append(
            {
                "chunk_index": len(chunks),
                "source": source,
                "text": current,
                "text_length": len(current),
                "start_char": current_start,
                "end_char": chunk_end,
                "page_number": page_number,
                "section_header": section_header,
                "preview": current[:CHUNK_PREVIEW_LENGTH],
            }
        )

    return chunks


def write_chunk_summary(path: Path, chunk_count: int, *, target_length: int, overlap_length: int) -> Path:
    summary_path = get_chunk_summary_path(path)
    summary = {
        "stored_name": path.name,
        "original_name": path.name.split("__", 1)[1] if "__" in path.name else path.name,
        "chunk_count": chunk_count,
        "chunk_target_length": target_length,
        "chunk_overlap_length": overlap_length,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary_path


def build_chunking_result(
    path: Path,
    *,
    primary_parser: str = PRIMARY_PARSER_DOCLING,
    fallback_parser: str = FALLBACK_PARSER_EXTENSION_DEFAULT,
    chunk_target_length: int | None = None,
    chunk_overlap_length: int | None = None,
) -> dict[str, object]:
    resolved_target_length, resolved_overlap_length = normalize_chunk_settings(
        chunk_target_length,
        chunk_overlap_length,
    )
    parsed = build_parsing_result(
        path,
        primary_parser=primary_parser,
        fallback_parser=fallback_parser,
    )
    chunks = create_chunks(
        parsed["extracted_text"],
        source=parsed["original_name"],
        target_length=resolved_target_length,
        overlap_length=resolved_overlap_length,
    )

    if not chunks:
        raise HTTPException(status_code=400, detail="No chunks were created from extracted text.")

    summary_path = write_chunk_summary(
        path,
        len(chunks),
        target_length=resolved_target_length,
        overlap_length=resolved_overlap_length,
    )
    return {
        "status": "chunked",
        "stored_name": parsed["stored_name"],
        "original_name": parsed["original_name"],
        "file_type": parsed["file_type"],
        "text_length": parsed["text_length"],
        "chunk_count": len(chunks),
        "chunk_target_length": resolved_target_length,
        "chunk_overlap_length": resolved_overlap_length,
        "summary_path": str(summary_path),
        "primary_parser": primary_parser,
        "fallback_parser": fallback_parser,
        "parser_used": parsed["parser_used"],
        "fallback_used": parsed["fallback_used"],
        "chunks": chunks,
    }


class DefaultFileUploadRequest(BaseModel):
    filename: str


class ParseRequest(BaseModel):
    stored_name: str
    primary_parser: str = PRIMARY_PARSER_DOCLING
    fallback_parser: str = FALLBACK_PARSER_EXTENSION_DEFAULT
    chunk_target_length: int | None = None
    chunk_overlap_length: int | None = None


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5
    stored_name: str | None = None


class ChatRequest(BaseModel):
    query: str
    top_k: int = DEFAULT_CHAT_TOP_K
    stored_name: str | None = None


class RebuildIndexRequest(BaseModel):
    primary_parser: str = PRIMARY_PARSER_DOCLING
    fallback_parser: str = FALLBACK_PARSER_EXTENSION_DEFAULT
    chunk_target_length: int | None = None
    chunk_overlap_length: int | None = None


def hash_token(token: str) -> int:
    return int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:8], "big")


def build_hash_embedding(text: str, dimension: int = EMBEDDING_DIMENSION) -> list[float]:
    vector = [0.0] * dimension
    tokens = tokenize_text(text)

    if not tokens:
        return vector

    for token in tokens:
        token_hash = hash_token(token)
        index = token_hash % dimension
        sign = -1.0 if ((token_hash >> 8) & 1) else 1.0
        vector[index] += sign

    norm = sum(value * value for value in vector) ** 0.5
    if norm == 0:
        return vector

    return [value / norm for value in vector]


def get_embedding_provider() -> str:
    provider = os.getenv("EMBEDDING_PROVIDER", EMBEDDING_PROVIDER_HASH).strip().lower()
    if provider not in {EMBEDDING_PROVIDER_HASH, EMBEDDING_PROVIDER_AZURE_OPENAI}:
        raise HTTPException(status_code=500, detail=f"Unsupported embedding provider: {provider}")
    return provider


def get_embedding_model_id() -> str:
    provider = get_embedding_provider()
    if provider == EMBEDDING_PROVIDER_HASH:
        return f"hash-{EMBEDDING_DIMENSION}"

    deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", DEFAULT_AZURE_OPENAI_EMBEDDING_DEPLOYMENT).strip()
    if not deployment:
        raise HTTPException(status_code=500, detail="AZURE_OPENAI_EMBEDDING_DEPLOYMENT is not configured.")
    return deployment


def get_embedding_collection_name() -> str:
    provider = get_embedding_provider()
    model_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", get_embedding_model_id()).strip("-").lower()
    return f"insurance_document_chunks__{provider}__{model_id}"


def get_embedding_dimension() -> int:
    provider = get_embedding_provider()
    if provider == EMBEDDING_PROVIDER_HASH:
        return EMBEDDING_DIMENSION
    return 1536


def get_embedding_config() -> dict[str, object]:
    provider = get_embedding_provider()
    config: dict[str, object] = {
        "provider": provider,
        "model": get_embedding_model_id(),
        "collection_name": get_embedding_collection_name(),
        "embedding_dimension": get_embedding_dimension(),
    }

    if provider == EMBEDDING_PROVIDER_AZURE_OPENAI:
        config["api_version"] = os.getenv("AZURE_OPENAI_API_VERSION", DEFAULT_AZURE_OPENAI_API_VERSION)

    return config


def build_azure_openai_embeddings(texts: list[str]) -> list[list[float]]:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip().rstrip("/")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", DEFAULT_AZURE_OPENAI_EMBEDDING_DEPLOYMENT).strip()
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", DEFAULT_AZURE_OPENAI_API_VERSION).strip()

    if not endpoint:
        raise HTTPException(status_code=500, detail="AZURE_OPENAI_ENDPOINT is not configured.")
    if not api_key:
        raise HTTPException(status_code=500, detail="AZURE_OPENAI_API_KEY is not configured.")
    if not deployment:
        raise HTTPException(status_code=500, detail="AZURE_OPENAI_EMBEDDING_DEPLOYMENT is not configured.")

    embeddings: list[list[float]] = []
    for start in range(0, len(texts), AZURE_OPENAI_EMBEDDING_BATCH_SIZE):
        batch = texts[start : start + AZURE_OPENAI_EMBEDDING_BATCH_SIZE]
        request_url = (
            f"{endpoint}/openai/deployments/{deployment}/embeddings"
            f"?api-version={api_version}"
        )
        payload = json.dumps({"input": batch}).encode("utf-8")
        request = urllib_request.Request(
            request_url,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "api-key": api_key,
            },
        )

        try:
            with urllib_request.urlopen(request, timeout=120) as response:
                raw_body = response.read()
        except urllib_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise HTTPException(status_code=502, detail=f"Azure OpenAI embedding request failed: {detail}") from exc
        except urllib_error.URLError as exc:
            raise HTTPException(status_code=502, detail=f"Azure OpenAI embedding request failed: {exc.reason}") from exc

        try:
            response_payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail="Azure OpenAI embedding response was not valid JSON.") from exc

        data = response_payload.get("data")
        if not isinstance(data, list) or len(data) != len(batch):
            raise HTTPException(status_code=502, detail="Azure OpenAI embedding response shape was invalid.")

        sorted_items = sorted(data, key=lambda item: int(item.get("index", 0)) if isinstance(item, dict) else 0)
        for item in sorted_items:
            if not isinstance(item, dict) or not isinstance(item.get("embedding"), list):
                raise HTTPException(status_code=502, detail="Azure OpenAI embedding response was missing vectors.")
            embeddings.append([float(value) for value in item["embedding"]])

    return embeddings


def get_chat_model_id() -> str:
    candidates = [
        os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "").strip(),
        os.getenv("AZURE_OPENAI_COMPLETION_DEPLOYMENT", "").strip(),
        os.getenv("AZURE_OPENAI_LLM_DEPLOYMENT", "").strip(),
    ]
    for candidate in candidates:
        if candidate:
            return candidate
    raise HTTPException(status_code=500, detail="AZURE_OPENAI_CHAT_DEPLOYMENT is not configured.")


def build_azure_openai_chat_completion(messages: list[dict[str, str]]) -> str:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip().rstrip("/")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    deployment = get_chat_model_id()
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", DEFAULT_AZURE_OPENAI_API_VERSION).strip()

    if not endpoint:
        raise HTTPException(status_code=500, detail="AZURE_OPENAI_ENDPOINT is not configured.")
    if not api_key:
        raise HTTPException(status_code=500, detail="AZURE_OPENAI_API_KEY is not configured.")

    request_url = (
        f"{endpoint}/openai/deployments/{deployment}/chat/completions"
        f"?api-version={api_version}"
    )
    payload = json.dumps(
        {
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 700,
        }
    ).encode("utf-8")
    request = urllib_request.Request(
        request_url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "api-key": api_key,
        },
    )

    try:
        with urllib_request.urlopen(request, timeout=120) as response:
            raw_body = response.read()
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(status_code=502, detail=f"Azure OpenAI chat request failed: {detail}") from exc
    except urllib_error.URLError as exc:
        raise HTTPException(status_code=502, detail=f"Azure OpenAI chat request failed: {exc.reason}") from exc

    try:
        response_payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="Azure OpenAI chat response was not valid JSON.") from exc

    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise HTTPException(status_code=502, detail="Azure OpenAI chat response shape was invalid.")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise HTTPException(status_code=502, detail="Azure OpenAI chat response shape was invalid.")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise HTTPException(status_code=502, detail="Azure OpenAI chat response was missing message data.")

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise HTTPException(status_code=502, detail="Azure OpenAI chat response was empty.")

    return content.strip()


def build_embeddings(texts: list[str]) -> list[list[float]]:
    provider = get_embedding_provider()
    if provider == EMBEDDING_PROVIDER_HASH:
        return [build_hash_embedding(text) for text in texts]
    if provider == EMBEDDING_PROVIDER_AZURE_OPENAI:
        return build_azure_openai_embeddings(texts)
    raise HTTPException(status_code=500, detail=f"Unsupported embedding provider: {provider}")


def build_chroma_metadata(
    chunk: dict[str, object],
    *,
    stored_name: str,
    original_name: str,
    file_type: str,
) -> dict[str, str | int]:
    metadata: dict[str, str | int] = {
        "stored_name": stored_name,
        "original_name": original_name,
        "file_type": file_type,
        "chunk_index": int(chunk["chunk_index"]),
        "source": str(chunk.get("source") or original_name),
        "text_length": int(chunk["text_length"]),
        "start_char": int(chunk["start_char"]),
        "end_char": int(chunk["end_char"]),
        "preview": str(chunk["preview"]),
    }

    page_number = chunk.get("page_number")
    if isinstance(page_number, int):
        metadata["page_number"] = page_number

    section_header = chunk.get("section_header")
    if isinstance(section_header, str) and section_header.strip():
        metadata["section_header"] = section_header.strip()

    return metadata


def get_chroma_collection():
    ensure_chroma_dir()
    try:
        import chromadb
    except ModuleNotFoundError as exc:
        raise HTTPException(status_code=500, detail="chromadb is not installed in the current environment.") from exc

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(name=get_embedding_collection_name())


def index_chunks(
    path: Path,
    *,
    primary_parser: str = PRIMARY_PARSER_DOCLING,
    fallback_parser: str = FALLBACK_PARSER_EXTENSION_DEFAULT,
    chunk_target_length: int | None = None,
    chunk_overlap_length: int | None = None,
) -> dict[str, object]:
    chunking_result = build_chunking_result(
        path,
        primary_parser=primary_parser,
        fallback_parser=fallback_parser,
        chunk_target_length=chunk_target_length,
        chunk_overlap_length=chunk_overlap_length,
    )
    chunks = chunking_result["chunks"]

    if not isinstance(chunks, list) or not chunks:
        raise HTTPException(status_code=400, detail="No chunks available for indexing.")

    stored_name = str(chunking_result["stored_name"])
    original_name = str(chunking_result["original_name"])
    file_type = str(chunking_result["file_type"])

    documents: list[str] = []
    metadatas: list[dict[str, str | int]] = []
    ids: list[str] = []

    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue

        text = str(chunk["text"])
        documents.append(text)
        metadatas.append(
            build_chroma_metadata(
                chunk,
                stored_name=stored_name,
                original_name=original_name,
                file_type=file_type,
            )
        )
        ids.append(f"{stored_name}:{int(chunk['chunk_index'])}")

    embeddings = build_embeddings(documents)
    collection = get_chroma_collection()
    if ids:
        collection.delete(ids=ids)
        collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    embedding_config = get_embedding_config()

    return {
        "status": "indexed",
        "stored_name": stored_name,
        "original_name": original_name,
        "file_type": file_type,
        "chunk_count": chunking_result["chunk_count"],
        "chunk_target_length": chunking_result["chunk_target_length"],
        "chunk_overlap_length": chunking_result["chunk_overlap_length"],
        "indexed_count": len(ids),
        "collection_name": embedding_config["collection_name"],
        "embedding_provider": embedding_config["provider"],
        "embedding_model": embedding_config["model"],
        "embedding_dimension": embedding_config["embedding_dimension"],
        "chroma_path": str(CHROMA_DIR),
        "primary_parser": primary_parser,
        "fallback_parser": fallback_parser,
        "parser_used": chunking_result["parser_used"],
        "fallback_used": chunking_result["fallback_used"],
    }


def build_retrieval_hits(result: dict[str, object]) -> list[dict[str, object]]:
    ids = result.get("ids")
    documents = result.get("documents")
    metadatas = result.get("metadatas")
    distances = result.get("distances")

    if not all(isinstance(item, list) and item for item in [ids, documents, metadatas, distances]):
        return []

    row_ids = ids[0]
    row_documents = documents[0]
    row_metadatas = metadatas[0]
    row_distances = distances[0]

    hits: list[dict[str, object]] = []
    for item_id, document, metadata, distance in zip(row_ids, row_documents, row_metadatas, row_distances):
        if not isinstance(metadata, dict):
            metadata = {}

        hits.append(
            {
                "id": item_id,
                "text": document,
                "distance": distance,
                "stored_name": metadata.get("stored_name"),
                "original_name": metadata.get("original_name"),
                "source": metadata.get("source"),
                "chunk_index": metadata.get("chunk_index"),
                "text_length": metadata.get("text_length"),
                "start_char": metadata.get("start_char"),
                "end_char": metadata.get("end_char"),
                "page_number": metadata.get("page_number"),
                "section_header": metadata.get("section_header"),
                "preview": metadata.get("preview"),
            }
        )

    return hits


def score_hit(query_tokens: list[str], hit: dict[str, object]) -> float:
    if not query_tokens:
        return 0.0

    query_token_set = set(query_tokens)
    text = str(hit.get("text") or "")
    preview = str(hit.get("preview") or "")
    source = str(hit.get("source") or "")
    section_header = str(hit.get("section_header") or "")
    searchable_text = "\n".join([text, preview, source, section_header])
    hit_tokens = tokenize_text(searchable_text)
    if not hit_tokens:
        return 0.0

    hit_frequency = build_token_frequency(hit_tokens)
    overlap_count = sum(hit_frequency.get(token, 0) for token in query_tokens)
    unique_overlap = len(query_token_set & set(hit_tokens))
    query_coverage = unique_overlap / len(query_token_set)
    query_ngram_set = build_character_ngrams(" ".join(query_tokens))
    hit_ngram_set = build_character_ngrams(searchable_text)
    ngram_overlap = len(query_ngram_set & hit_ngram_set)
    ngram_coverage = (ngram_overlap / len(query_ngram_set)) if query_ngram_set else 0.0
    distance = float(hit.get("distance") or 0.0)

    return (query_coverage * 2.5) + (overlap_count * 0.3) + (ngram_coverage * 3.5) - distance


def rerank_hits(query: str, hits: list[dict[str, object]], top_k: int) -> list[dict[str, object]]:
    query_tokens = tokenize_text(query)
    if not query_tokens or not hits:
        return hits[:top_k]

    scored_hits: list[dict[str, object]] = []
    for hit in hits:
        rescored_hit = dict(hit)
        rescored_hit["rerank_score"] = score_hit(query_tokens, hit)
        scored_hits.append(rescored_hit)

    scored_hits.sort(
        key=lambda item: (
            float(item.get("rerank_score") or 0.0),
            -float(item.get("distance") or 0.0),
        ),
        reverse=True,
    )
    return scored_hits[:top_k]


def retrieve_chunks(payload: RetrieveRequest) -> dict[str, object]:
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    top_k = max(1, min(payload.top_k, 20))
    collection = get_chroma_collection()

    where = None
    if payload.stored_name:
        where = {"stored_name": payload.stored_name}

    candidate_count = min(max(top_k * RETRIEVAL_CANDIDATE_MULTIPLIER, top_k), RETRIEVAL_MAX_CANDIDATES)
    query_embedding = build_embeddings([query])[0]
    embedding_config = get_embedding_config()

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=candidate_count,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    hits = rerank_hits(query, build_retrieval_hits(result), top_k)

    return {
        "status": "retrieved",
        "query": query,
        "top_k": top_k,
        "hit_count": len(hits),
        "collection_name": embedding_config["collection_name"],
        "embedding_provider": embedding_config["provider"],
        "embedding_model": embedding_config["model"],
        "hits": hits,
    }


def build_chat_citations(hits: list[dict[str, object]]) -> list[dict[str, object]]:
    citations: list[dict[str, object]] = []
    for hit in hits:
        citations.append(
            {
                "id": hit.get("id"),
                "source": hit.get("source") or hit.get("original_name"),
                "original_name": hit.get("original_name"),
                "stored_name": hit.get("stored_name"),
                "chunk_index": hit.get("chunk_index"),
                "page_number": hit.get("page_number"),
                "section_header": hit.get("section_header"),
                "preview": hit.get("preview"),
            }
        )
    return citations


def format_chat_context(hits: list[dict[str, object]]) -> str:
    sections: list[str] = []
    for index, hit in enumerate(hits, start=1):
        source = str(hit.get("source") or hit.get("original_name") or "Unknown source")
        chunk_index = hit.get("chunk_index")
        page_number = hit.get("page_number")
        section_header = hit.get("section_header")
        text = str(hit.get("text") or "").strip()
        metadata_parts = [f"source={source}"]
        if chunk_index is not None:
            metadata_parts.append(f"chunk={chunk_index}")
        if page_number is not None:
            metadata_parts.append(f"page={page_number}")
        if isinstance(section_header, str) and section_header.strip():
            metadata_parts.append(f"section={section_header.strip()}")

        sections.append(
            f"[Context {index}]\n"
            f"{', '.join(metadata_parts)}\n"
            f"{text}"
        )
    return "\n\n".join(sections)


def parse_chat_completion(content: str) -> tuple[bool, str]:
    status_match = re.search(r"STATUS:\s*(grounded|insufficient)", content, flags=re.IGNORECASE)
    answer_match = re.search(r"ANSWER:\s*(.*)", content, flags=re.IGNORECASE | re.DOTALL)

    if not status_match or not answer_match:
        return False, content.strip()

    status = status_match.group(1).strip().lower()
    answer = answer_match.group(1).strip()
    return status == "insufficient", answer


def generate_grounded_answer(payload: ChatRequest) -> dict[str, object]:
    retrieval = retrieve_chunks(
        RetrieveRequest(
            query=payload.query,
            top_k=payload.top_k,
            stored_name=payload.stored_name,
        )
    )
    hits = retrieval["hits"]
    if not isinstance(hits, list):
        hits = []

    if not hits:
        return {
            "status": "answered",
            "query": retrieval["query"],
            "top_k": retrieval["top_k"],
            "hit_count": 0,
            "collection_name": retrieval["collection_name"],
            "embedding_provider": retrieval["embedding_provider"],
            "embedding_model": retrieval["embedding_model"],
            "answer": "문서에서 충분한 근거를 찾지 못했습니다.",
            "insufficient_context": True,
            "citations": [],
            "hits": [],
            "chat_model": None,
        }

    system_prompt = (
        "You answer questions using only the provided document context.\n"
        "Do not use outside knowledge.\n"
        "If the context is insufficient, say so.\n"
        "Respond in Korean.\n"
        "When the context includes conditional requirements, keep common requirements and conditional requirements separate.\n"
        "Never present conditional requirements as unconditional facts.\n"
        "Use this exact format:\n"
        "STATUS: grounded or insufficient\n"
        "ANSWER: <final answer>"
    )
    user_prompt = (
        f"Question:\n{retrieval['query']}\n\n"
        f"Context:\n{format_chat_context(hits)}\n\n"
        "Rules:\n"
        "- Answer only from the context.\n"
        "- If the context does not support a clear answer, return STATUS: insufficient.\n"
        "- Keep the answer concise and factual.\n"
        "- Do not mention information not present in the context.\n"
        "- If the document lists items that apply only in certain cases, separate them into '공통 서류' and '조건부 추가 서류'.\n"
        "- If the user's question is broad and the required documents vary by condition, explicitly say that additional documents depend on case.\n"
        "- Do not merge multiple scenario-specific document lists into one unconditional checklist."
    )
    response_text = build_azure_openai_chat_completion(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    insufficient_context, answer = parse_chat_completion(response_text)

    return {
        "status": "answered",
        "query": retrieval["query"],
        "top_k": retrieval["top_k"],
        "hit_count": retrieval["hit_count"],
        "collection_name": retrieval["collection_name"],
        "embedding_provider": retrieval["embedding_provider"],
        "embedding_model": retrieval["embedding_model"],
        "answer": answer,
        "insufficient_context": insufficient_context,
        "citations": build_chat_citations(hits),
        "hits": hits,
        "chat_model": get_chat_model_id(),
    }


def delete_indexed_chunks(stored_name: str) -> int:
    collection = get_chroma_collection()
    result = collection.get(where={"stored_name": stored_name}, include=[])
    ids = result.get("ids") if isinstance(result, dict) else None

    if not isinstance(ids, list) or not ids:
        return 0

    collection.delete(ids=ids)
    return len(ids)


def clear_indexed_chunks() -> int:
    collection = get_chroma_collection()
    result = collection.get(include=[])
    ids = result.get("ids") if isinstance(result, dict) else None

    if not isinstance(ids, list) or not ids:
        return 0

    collection.delete(ids=ids)
    return len(ids)


def delete_uploaded_file_and_index(stored_name: str) -> dict[str, object]:
    path = get_uploaded_file_path(stored_name)
    metadata = build_file_metadata(path)
    removed_index_count = delete_indexed_chunks(path.name)

    parse_summary_path = get_parse_summary_path(path)
    parse_summary_removed = parse_summary_path.is_file()
    if parse_summary_removed:
        parse_summary_path.unlink()

    chunk_summary_path = get_chunk_summary_path(path)
    chunk_summary_removed = chunk_summary_path.is_file()
    if chunk_summary_removed:
        chunk_summary_path.unlink()

    path.unlink()

    return {
        "status": "deleted",
        "stored_name": metadata["stored_name"],
        "original_name": metadata["original_name"],
        "removed_index_count": removed_index_count,
        "removed_parse_summary": parse_summary_removed,
        "removed_chunk_summary": chunk_summary_removed,
    }


def list_indexed_files() -> list[dict[str, object]]:
    collection = get_chroma_collection()
    result = collection.get(include=["metadatas"])

    metadatas = result.get("metadatas") if isinstance(result, dict) else None
    if not isinstance(metadatas, list):
        return []

    indexed: dict[str, dict[str, object]] = {}
    for metadata in metadatas:
        if not isinstance(metadata, dict):
            continue

        stored_name = metadata.get("stored_name")
        if not isinstance(stored_name, str) or not stored_name:
            continue

        if stored_name in indexed:
            indexed[stored_name]["chunk_count"] = int(indexed[stored_name]["chunk_count"]) + 1
            continue

        indexed[stored_name] = {
            "stored_name": stored_name,
            "original_name": metadata.get("original_name") or stored_name,
            "file_type": metadata.get("file_type") or "",
            "chunk_count": 1,
        }

    return sorted(indexed.values(), key=lambda item: str(item["original_name"]))


def rebuild_all_indexes(
    *,
    primary_parser: str = PRIMARY_PARSER_DOCLING,
    fallback_parser: str = FALLBACK_PARSER_EXTENSION_DEFAULT,
    chunk_target_length: int | None = None,
    chunk_overlap_length: int | None = None,
) -> dict[str, object]:
    uploaded_files = list_uploaded_files()
    removed_count = clear_indexed_chunks()
    rebuilt: list[dict[str, object]] = []

    for uploaded_file in uploaded_files:
        path = get_uploaded_file_path(str(uploaded_file["stored_name"]))
        rebuilt.append(
            index_chunks(
                path,
                primary_parser=primary_parser,
                fallback_parser=fallback_parser,
                chunk_target_length=chunk_target_length,
                chunk_overlap_length=chunk_overlap_length,
            )
        )

    embedding_config = get_embedding_config()
    return {
        "status": "rebuilt",
        "file_count": len(rebuilt),
        "removed_count": removed_count,
        "collection_name": embedding_config["collection_name"],
        "embedding_provider": embedding_config["provider"],
        "embedding_model": embedding_config["model"],
        "files": [
            {
                "stored_name": item["stored_name"],
                "original_name": item["original_name"],
                "indexed_count": item["indexed_count"],
            }
            for item in rebuilt
        ],
    }


def list_pipeline_files() -> list[dict[str, object]]:
    uploaded_files = list_uploaded_files()
    parse_history = get_parse_history_from_logs()
    parsed_files = {
        str(item.get("stored_name")): item
        for item in list_parsed_files()
        if isinstance(item.get("stored_name"), str)
    }
    chunked_files = {
        str(item.get("stored_name")): item
        for item in list_chunked_files()
        if isinstance(item.get("stored_name"), str)
    }
    indexed_files = {
        str(item.get("stored_name")): item
        for item in list_indexed_files()
        if isinstance(item.get("stored_name"), str)
    }

    pipeline_files: list[dict[str, object]] = []
    for uploaded in uploaded_files:
        stored_name = str(uploaded["stored_name"])
        history = parse_history.get(stored_name, {})
        parsed = parsed_files.get(stored_name)
        chunked = chunked_files.get(stored_name)
        indexed = indexed_files.get(stored_name)

        pipeline_files.append(
            {
                **uploaded,
                "upload_status": "completed",
                "parse_status": (
                    "completed"
                    if chunked or indexed or (parsed and parsed.get("status") != "failed")
                    else "failed"
                    if parsed and parsed.get("status") == "failed"
                    else "pending"
                ),
                "chunk_status": "completed" if chunked else "pending",
                "index_status": "completed" if indexed else "pending",
                "parse_text_length": parsed.get("text_length") if parsed else None,
                "parse_parser_used": parsed.get("parser_used") if parsed and parsed.get("parser_used") else None,
                "parse_fallback_used": parsed.get("fallback_used") if parsed else None,
                "parse_error_detail": parsed.get("error_detail") if parsed else None,
                "parse_preview": parsed.get("preview") if parsed else None,
                "last_successful_parse_parser_used": (
                    parsed.get("parser_used")
                    if parsed and parsed.get("status") == "completed" and parsed.get("parser_used")
                    else history.get("last_successful_parser_used")
                ),
                "last_successful_parse_fallback_used": (
                    parsed.get("fallback_used")
                    if parsed and parsed.get("status") == "completed"
                    else history.get("last_successful_fallback_used")
                ),
                "last_failed_parse_parser_used": (
                    parsed.get("parser_used")
                    if parsed and parsed.get("status") == "failed" and parsed.get("parser_used")
                    else history.get("last_failed_parser_used")
                ),
                "last_failed_parse_fallback_used": (
                    parsed.get("fallback_used")
                    if parsed and parsed.get("status") == "failed"
                    else history.get("last_failed_fallback_used")
                ),
                "chunk_count": chunked.get("chunk_count") if chunked else None,
                "indexed_chunk_count": indexed.get("chunk_count") if indexed else None,
                "quality_checked_at": parsed.get("quality_checked_at") if parsed else None,
                "jaccard_similarity": parsed.get("jaccard_similarity") if parsed else None,
                "levenshtein_distance": parsed.get("levenshtein_distance") if parsed else None,
                "quality_warning": parsed.get("quality_warning") if parsed else None,
                "quality_warning_message": parsed.get("quality_warning_message") if parsed else None,
            }
        )

    return pipeline_files


@app.get("/health")
def health() -> dict[str, str]:
    embedding_config = get_embedding_config()
    return {
        "status": "ok",
        "embedding_provider": str(embedding_config["provider"]),
        "embedding_model": str(embedding_config["model"]),
        "collection_name": str(embedding_config["collection_name"]),
    }


@app.get("/upload")
def get_upload_status() -> dict[str, object]:
    files = list_uploaded_files()
    return {
        "page": "upload",
        "status": "ready",
        "message": "Upload API is available.",
        "file_count": len(files),
    }


@app.get("/upload/files")
def get_uploaded_files() -> dict[str, object]:
    files = list_uploaded_files()
    return {"files": files, "count": len(files)}


@app.get("/pipeline/files")
def get_pipeline_files() -> dict[str, object]:
    files = list_pipeline_files()
    return {"files": files, "count": len(files)}


@app.delete("/upload/files")
def clear_uploaded_files() -> dict[str, object]:
    ensure_upload_dir()
    removed_count = 0

    for path in list(UPLOAD_DIR.iterdir()):
        if not path.is_file():
            continue
        delete_uploaded_file_and_index(path.name)
        removed_count += 1

    return {"status": "cleared", "removed_count": removed_count}


@app.delete("/upload/files/{stored_name}")
def delete_uploaded_file(stored_name: str) -> dict[str, object]:
    return delete_uploaded_file_and_index(stored_name)


@app.get("/upload/default-files")
def get_default_files() -> dict[str, object]:
    files = list_default_files()
    return {"files": files, "count": len(files), "directory": str(DEFAULT_FILE_DIR)}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict[str, object]:
    filename = file.filename or ""
    extension = get_extension(filename)
    logger.info("upload_started filename=%s extension=%s", filename, extension)

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=get_supported_file_types_message())

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    normalized_name = Path(filename).name
    validate_uploaded_file_type(normalized_name, content)
    ensure_no_completed_duplicate_upload(normalized_name)
    saved = save_content_to_uploads(normalized_name, content, file.content_type)
    logger.info(
        "upload_completed stored_name=%s original_name=%s size_bytes=%s",
        saved["stored_name"],
        saved["original_name"],
        saved["size_bytes"],
    )
    return saved


@app.post("/upload/default-file")
def upload_default_file(payload: DefaultFileUploadRequest) -> dict[str, object]:
    logger.info("default_upload_started filename=%s", payload.filename)
    ensure_default_file_dir()
    filename = Path(payload.filename).name
    source = DEFAULT_FILE_DIR / filename

    if get_extension(filename) not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=get_supported_file_types_message())

    if not source.is_file():
        raise HTTPException(status_code=404, detail="Default file not found.")

    content = source.read_bytes()
    if not content:
        raise HTTPException(status_code=400, detail="Default file is empty.")

    validate_uploaded_file_type(filename, content)
    ensure_no_completed_duplicate_upload(filename)
    saved = save_content_to_uploads(filename, content, None)
    logger.info(
        "default_upload_completed stored_name=%s original_name=%s size_bytes=%s",
        saved["stored_name"],
        saved["original_name"],
        saved["size_bytes"],
    )
    return saved


@app.get("/parse")
def get_parse_status() -> dict[str, object]:
    files = list_uploaded_files()
    return {
        "page": "parse",
        "status": "ready",
        "message": "Parsing API is available for uploaded PDF, DOC, DOCX, XLS, and XLSX files.",
        "file_count": len(files),
    }


@app.get("/parse/parsers")
def get_parse_parsers() -> dict[str, object]:
    return get_parser_catalog()


@app.post("/parse")
def parse_uploaded_file(payload: ParseRequest) -> dict[str, object]:
    path = get_uploaded_file_path(payload.stored_name)
    logger.info(
        "parse_started stored_name=%s original_name=%s %s",
        payload.stored_name,
        path.name.split("__", 1)[1] if "__" in path.name else path.name,
        summarize_parser_selection(payload.primary_parser, payload.fallback_parser),
    )
    try:
        result = build_parsing_result(
            path,
            primary_parser=payload.primary_parser,
            fallback_parser=payload.fallback_parser,
        )
    except HTTPException as exc:
        write_parse_failure_summary(
            path,
            file_type=get_extension(path.name),
            parser_used=f"{payload.primary_parser} -> {payload.fallback_parser}",
            fallback_used=payload.fallback_parser != FALLBACK_PARSER_NONE,
            error_detail=str(exc.detail),
        )
        raise
    logger.info(
        "parse_completed stored_name=%s parser_used=%s fallback_used=%s text_length=%s",
        payload.stored_name,
        result["parser_used"],
        result["fallback_used"],
        result["text_length"],
    )
    return result


@app.get("/parse/{stored_name}")
def parse_uploaded_file_by_name(stored_name: str) -> dict[str, object]:
    path = get_uploaded_file_path(stored_name)
    return build_parsing_result(path)


@app.post("/parse/quality")
def parse_uploaded_file_quality(payload: ParseRequest) -> dict[str, object]:
    path = get_uploaded_file_path(payload.stored_name)
    logger.info(
        "parse_quality_started stored_name=%s %s",
        payload.stored_name,
        summarize_parser_selection(payload.primary_parser, payload.fallback_parser),
    )
    result = build_parsing_quality_result(
        path,
        primary_parser=payload.primary_parser,
        fallback_parser=payload.fallback_parser,
    )
    logger.info(
        "parse_quality_completed stored_name=%s parser_used=%s fallback_used=%s jaccard_similarity=%s",
        payload.stored_name,
        result["parser_used"],
        result["fallback_used"],
        result["jaccard_similarity"],
    )
    return result


@app.get("/chunk")
def get_chunk_status() -> dict[str, object]:
    files = list_uploaded_files()
    return {
        "page": "chunk",
        "status": "ready",
        "message": "Chunking API is available for parsed uploaded files.",
        "file_count": len(files),
        "chunk_target_length": CHUNK_TARGET_LENGTH,
        "chunk_overlap_length": CHUNK_OVERLAP_LENGTH,
    }


@app.post("/chunk")
def chunk_uploaded_file(payload: ParseRequest) -> dict[str, object]:
    path = get_uploaded_file_path(payload.stored_name)
    resolved_target_length, resolved_overlap_length = normalize_chunk_settings(
        payload.chunk_target_length,
        payload.chunk_overlap_length,
    )
    logger.info(
        "chunk_started stored_name=%s %s chunk_target_length=%s chunk_overlap_length=%s",
        payload.stored_name,
        summarize_parser_selection(payload.primary_parser, payload.fallback_parser),
        resolved_target_length,
        resolved_overlap_length,
    )
    result = build_chunking_result(
        path,
        primary_parser=payload.primary_parser,
        fallback_parser=payload.fallback_parser,
        chunk_target_length=resolved_target_length,
        chunk_overlap_length=resolved_overlap_length,
    )
    logger.info(
        "chunk_completed stored_name=%s parser_used=%s fallback_used=%s chunk_count=%s chunk_target_length=%s chunk_overlap_length=%s",
        payload.stored_name,
        result["parser_used"],
        result["fallback_used"],
        result["chunk_count"],
        result["chunk_target_length"],
        result["chunk_overlap_length"],
    )
    return result


@app.get("/chunk/{stored_name}")
def chunk_uploaded_file_by_name(stored_name: str) -> dict[str, object]:
    path = get_uploaded_file_path(stored_name)
    return build_chunking_result(path)


@app.get("/index")
def get_index_status() -> dict[str, object]:
    files = list_uploaded_files()
    embedding_config = get_embedding_config()
    return {
        "page": "index",
        "status": "ready",
        "message": "Indexing API is available for chunked uploaded files.",
        "file_count": len(files),
        "collection_name": embedding_config["collection_name"],
        "embedding_provider": embedding_config["provider"],
        "embedding_model": embedding_config["model"],
        "embedding_dimension": embedding_config["embedding_dimension"],
    }


@app.get("/index/files")
def get_indexed_files() -> dict[str, object]:
    files = list_indexed_files()
    embedding_config = get_embedding_config()
    return {
        "files": files,
        "count": len(files),
        "collection_name": embedding_config["collection_name"],
        "embedding_provider": embedding_config["provider"],
        "embedding_model": embedding_config["model"],
    }


@app.delete("/index/files")
def delete_indexed_files() -> dict[str, object]:
    removed_count = clear_indexed_chunks()
    embedding_config = get_embedding_config()
    return {
        "status": "cleared",
        "removed_count": removed_count,
        "collection_name": embedding_config["collection_name"],
        "embedding_provider": embedding_config["provider"],
        "embedding_model": embedding_config["model"],
    }


@app.post("/index")
def index_uploaded_file(payload: ParseRequest) -> dict[str, object]:
    path = get_uploaded_file_path(payload.stored_name)
    resolved_target_length, resolved_overlap_length = normalize_chunk_settings(
        payload.chunk_target_length,
        payload.chunk_overlap_length,
    )
    logger.info(
        "index_started stored_name=%s %s chunk_target_length=%s chunk_overlap_length=%s",
        payload.stored_name,
        summarize_parser_selection(payload.primary_parser, payload.fallback_parser),
        resolved_target_length,
        resolved_overlap_length,
    )
    result = index_chunks(
        path,
        primary_parser=payload.primary_parser,
        fallback_parser=payload.fallback_parser,
        chunk_target_length=resolved_target_length,
        chunk_overlap_length=resolved_overlap_length,
    )
    logger.info(
        "index_completed stored_name=%s parser_used=%s fallback_used=%s indexed_count=%s chunk_target_length=%s chunk_overlap_length=%s",
        payload.stored_name,
        result["parser_used"],
        result["fallback_used"],
        result["indexed_count"],
        result["chunk_target_length"],
        result["chunk_overlap_length"],
    )
    return result


@app.post("/index/rebuild")
def rebuild_indexed_files(payload: RebuildIndexRequest) -> dict[str, object]:
    resolved_target_length, resolved_overlap_length = normalize_chunk_settings(
        payload.chunk_target_length,
        payload.chunk_overlap_length,
    )
    logger.info(
        "index_rebuild_started %s chunk_target_length=%s chunk_overlap_length=%s",
        summarize_parser_selection(payload.primary_parser, payload.fallback_parser),
        resolved_target_length,
        resolved_overlap_length,
    )
    result = rebuild_all_indexes(
        primary_parser=payload.primary_parser,
        fallback_parser=payload.fallback_parser,
        chunk_target_length=resolved_target_length,
        chunk_overlap_length=resolved_overlap_length,
    )
    logger.info(
        "index_rebuild_completed file_count=%s removed_count=%s collection_name=%s embedding_provider=%s embedding_model=%s",
        result["file_count"],
        result["removed_count"],
        result["collection_name"],
        result["embedding_provider"],
        result["embedding_model"],
    )
    return result


@app.get("/index/{stored_name}")
def index_uploaded_file_by_name(stored_name: str) -> dict[str, object]:
    path = get_uploaded_file_path(stored_name)
    return index_chunks(path)


@app.get("/retrieve")
def get_retrieve_status() -> dict[str, object]:
    embedding_config = get_embedding_config()
    return {
        "page": "retrieve",
        "status": "ready",
        "message": "Retrieval API is available for indexed chunks.",
        "collection_name": embedding_config["collection_name"],
        "embedding_provider": embedding_config["provider"],
        "embedding_model": embedding_config["model"],
        "embedding_dimension": embedding_config["embedding_dimension"],
    }


@app.post("/retrieve")
def retrieve_indexed_chunks(payload: RetrieveRequest) -> dict[str, object]:
    return retrieve_chunks(payload)


@app.get("/chat")
def get_chat_status() -> dict[str, object]:
    chat_model = None
    try:
        chat_model = get_chat_model_id()
    except HTTPException:
        chat_model = None

    return {
        "page": "chat",
        "status": "ready",
        "message": "Chat API supports retrieval-based grounded answers.",
        "chat_model": chat_model,
    }


@app.post("/chat")
def answer_with_retrieval(payload: ChatRequest) -> dict[str, object]:
    return generate_grounded_answer(payload)


@app.get("/evaluation")
def get_evaluation_status() -> dict[str, object]:
    return {
        "page": "evaluation",
        "status": "not_implemented",
        "message": "Evaluation API skeleton is ready.",
    }
