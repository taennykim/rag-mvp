from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
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
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
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

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
DEFAULT_FILE_DIR = BASE_DIR / "data" / "default-files"
CHUNK_METADATA_DIR = BASE_DIR / "data" / "chunk-metadata"
CHROMA_DIR = BASE_DIR / "data" / "chroma"
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
PREVIEW_LENGTH = 300
QUALITY_WARNING_THRESHOLD = 0.8
WORD_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
CHUNK_TARGET_LENGTH = 800
CHUNK_OVERLAP_LENGTH = 120
CHUNK_PREVIEW_LENGTH = 160
EMBEDDING_DIMENSION = 256
CHROMA_COLLECTION_NAME = "insurance_document_chunks"


def ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def ensure_default_file_dir() -> None:
    DEFAULT_FILE_DIR.mkdir(parents=True, exist_ok=True)


def ensure_chunk_metadata_dir() -> None:
    CHUNK_METADATA_DIR.mkdir(parents=True, exist_ok=True)


def ensure_chroma_dir() -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def tokenize_text(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def build_file_metadata(path: Path) -> dict[str, object]:
    return {
        "stored_name": path.name,
        "original_name": path.name.split("__", 1)[1] if "__" in path.name else path.name,
        "size_bytes": path.stat().st_size,
        "uploaded_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
    }


def list_uploaded_files() -> list[dict[str, object]]:
    ensure_upload_dir()
    files: list[dict[str, object]] = []
    for path in sorted(UPLOAD_DIR.iterdir(), key=lambda item: item.name):
        if not path.is_file():
            continue
        files.append(build_file_metadata(path))
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


def get_uploaded_file_path(stored_name: str) -> Path:
    ensure_upload_dir()
    filename = Path(stored_name).name
    path = UPLOAD_DIR / filename

    if not path.is_file():
        raise HTTPException(status_code=404, detail="Uploaded file not found.")

    extension = get_extension(path.name)
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

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


def extract_text_from_file(path: Path) -> str:
    extension = get_extension(path.name)

    if extension == ".pdf":
        return extract_pdf_text(path)

    if extension == ".docx":
        return extract_docx_text(path)

    raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")


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

    raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")


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


def build_parsing_result(path: Path) -> dict[str, object]:
    text = extract_text_from_file(path)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Extracted text is empty.")

    metadata = build_file_metadata(path)
    metadata.update(
        {
            "status": "parsed",
            "file_type": get_extension(path.name),
            "text_length": len(text),
            "preview": text[:PREVIEW_LENGTH],
            "extracted_text": text,
        }
    )
    return metadata


def build_parsing_quality_result(path: Path) -> dict[str, object]:
    parsed_text = extract_text_from_file(path)
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
        }
    )
    metadata.update(build_quality_metrics(parsed_text, reference_text))
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


def build_chunk_segments(text: str) -> list[str]:
    raw_segments = [line.strip() for line in text.splitlines() if line.strip()]
    segments: list[str] = []

    for raw_segment in raw_segments:
        segments.extend(split_long_segment(raw_segment, CHUNK_TARGET_LENGTH))

    return segments


def build_overlap_text(chunk_text: str, overlap_length: int) -> str:
    if len(chunk_text) <= overlap_length:
        return chunk_text
    return chunk_text[-overlap_length:].strip()


def create_chunks(
    text: str,
    *,
    source: str,
    page_number: int | None = None,
    section_header: str | None = None,
) -> list[dict[str, object]]:
    segments = build_chunk_segments(text)
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
        if current and len(candidate) > CHUNK_TARGET_LENGTH:
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
            overlap = build_overlap_text(current, CHUNK_OVERLAP_LENGTH)
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


def write_chunk_summary(path: Path, chunk_count: int) -> Path:
    ensure_chunk_metadata_dir()
    summary_path = CHUNK_METADATA_DIR / f"{path.name}.json"
    summary = {
        "stored_name": path.name,
        "original_name": path.name.split("__", 1)[1] if "__" in path.name else path.name,
        "chunk_count": chunk_count,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary_path


def build_chunking_result(path: Path) -> dict[str, object]:
    parsed = build_parsing_result(path)
    chunks = create_chunks(parsed["extracted_text"], source=parsed["original_name"])

    if not chunks:
        raise HTTPException(status_code=400, detail="No chunks were created from extracted text.")

    summary_path = write_chunk_summary(path, len(chunks))
    return {
        "status": "chunked",
        "stored_name": parsed["stored_name"],
        "original_name": parsed["original_name"],
        "file_type": parsed["file_type"],
        "text_length": parsed["text_length"],
        "chunk_count": len(chunks),
        "chunk_target_length": CHUNK_TARGET_LENGTH,
        "chunk_overlap_length": CHUNK_OVERLAP_LENGTH,
        "summary_path": str(summary_path),
        "chunks": chunks,
    }


class DefaultFileUploadRequest(BaseModel):
    filename: str


class ParseRequest(BaseModel):
    stored_name: str


def hash_token(token: str) -> int:
    return int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:8], "big")


def build_embedding(text: str, dimension: int = EMBEDDING_DIMENSION) -> list[float]:
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
    return client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)


def index_chunks(path: Path) -> dict[str, object]:
    chunking_result = build_chunking_result(path)
    chunks = chunking_result["chunks"]

    if not isinstance(chunks, list) or not chunks:
        raise HTTPException(status_code=400, detail="No chunks available for indexing.")

    stored_name = str(chunking_result["stored_name"])
    original_name = str(chunking_result["original_name"])
    file_type = str(chunking_result["file_type"])

    documents: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict[str, str | int]] = []
    ids: list[str] = []

    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue

        text = str(chunk["text"])
        documents.append(text)
        embeddings.append(build_embedding(text))
        metadatas.append(
            build_chroma_metadata(
                chunk,
                stored_name=stored_name,
                original_name=original_name,
                file_type=file_type,
            )
        )
        ids.append(f"{stored_name}:{int(chunk['chunk_index'])}")

    collection = get_chroma_collection()
    if ids:
        collection.delete(ids=ids)
        collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    return {
        "status": "indexed",
        "stored_name": stored_name,
        "original_name": original_name,
        "file_type": file_type,
        "chunk_count": chunking_result["chunk_count"],
        "indexed_count": len(ids),
        "collection_name": CHROMA_COLLECTION_NAME,
        "embedding_dimension": EMBEDDING_DIMENSION,
        "chroma_path": str(CHROMA_DIR),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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


@app.delete("/upload/files")
def clear_uploaded_files() -> dict[str, object]:
    ensure_upload_dir()
    removed_count = 0

    for path in UPLOAD_DIR.iterdir():
        if not path.is_file():
            continue
        path.unlink()
        removed_count += 1

    return {"status": "cleared", "removed_count": removed_count}


@app.get("/upload/default-files")
def get_default_files() -> dict[str, object]:
    files = list_default_files()
    return {"files": files, "count": len(files), "directory": str(DEFAULT_FILE_DIR)}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict[str, object]:
    filename = file.filename or ""
    extension = get_extension(filename)

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    return save_content_to_uploads(Path(filename).name, content, file.content_type)


@app.post("/upload/default-file")
def upload_default_file(payload: DefaultFileUploadRequest) -> dict[str, object]:
    ensure_default_file_dir()
    filename = Path(payload.filename).name
    source = DEFAULT_FILE_DIR / filename

    if get_extension(filename) not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    if not source.is_file():
        raise HTTPException(status_code=404, detail="Default file not found.")

    content = source.read_bytes()
    if not content:
        raise HTTPException(status_code=400, detail="Default file is empty.")

    return save_content_to_uploads(filename, content, None)


@app.get("/parse")
def get_parse_status() -> dict[str, object]:
    files = list_uploaded_files()
    return {
        "page": "parse",
        "status": "ready",
        "message": "Parsing API is available for uploaded PDF and DOCX files.",
        "file_count": len(files),
    }


@app.post("/parse")
def parse_uploaded_file(payload: ParseRequest) -> dict[str, object]:
    path = get_uploaded_file_path(payload.stored_name)
    return build_parsing_result(path)


@app.get("/parse/{stored_name}")
def parse_uploaded_file_by_name(stored_name: str) -> dict[str, object]:
    path = get_uploaded_file_path(stored_name)
    return build_parsing_result(path)


@app.post("/parse/quality")
def parse_uploaded_file_quality(payload: ParseRequest) -> dict[str, object]:
    path = get_uploaded_file_path(payload.stored_name)
    return build_parsing_quality_result(path)


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
    return build_chunking_result(path)


@app.get("/chunk/{stored_name}")
def chunk_uploaded_file_by_name(stored_name: str) -> dict[str, object]:
    path = get_uploaded_file_path(stored_name)
    return build_chunking_result(path)


@app.get("/index")
def get_index_status() -> dict[str, object]:
    files = list_uploaded_files()
    return {
        "page": "index",
        "status": "ready",
        "message": "Indexing API is available for chunked uploaded files.",
        "file_count": len(files),
        "collection_name": CHROMA_COLLECTION_NAME,
        "embedding_dimension": EMBEDDING_DIMENSION,
    }


@app.post("/index")
def index_uploaded_file(payload: ParseRequest) -> dict[str, object]:
    path = get_uploaded_file_path(payload.stored_name)
    return index_chunks(path)


@app.get("/index/{stored_name}")
def index_uploaded_file_by_name(stored_name: str) -> dict[str, object]:
    path = get_uploaded_file_path(stored_name)
    return index_chunks(path)


@app.get("/chat")
def get_chat_status() -> dict[str, object]:
    return {
        "page": "chat",
        "status": "not_implemented",
        "message": "Chat API skeleton is ready.",
    }


@app.get("/evaluation")
def get_evaluation_status() -> dict[str, object]:
    return {
        "page": "evaluation",
        "status": "not_implemented",
        "message": "Evaluation API skeleton is ready.",
    }
