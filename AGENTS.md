# AGENTS.md

## Project Overview
Build a simple MVP RAG web app for insurance documents.

# 프로젝트 개요
보험사 PDF/Word 문서를 업로드하면 RAG를 생성하고,
사용자가 질문하면 업로드된 문서를 근거로 답변하는 MVP를 만든다.

핵심 흐름:
1. User uploads PDF or DOCX files
2. System extracts text
3. System chunks the text
4. System stores embeddings in a vector store
5. User asks a question
6. System retrieves relevant chunks
7. System generates a grounded answer
8. User can view a simple RAGAS evaluation page

---

## Folder Structure

The project must follow this structure:
rag-mvp/
├─ AGENTS.md
├─ TODO.md
├─ README.md
│
├─ docs/
│ ├─ daily/
│ ├─ upload.md
│ ├─ parsing.md
│ ├─ chunking.md
│ ├─ indexing.md
│ ├─ retrieval.md
│ ├─ answer.md
│ ├─ chat.md
│ └─ evaluation.md
│
├─ frontend/
│ ├─ app/
│ │ ├─ upload/
│ │ │ └─ page.tsx
│ │ ├─ chat/
│ │ │ └─ page.tsx
│ │ ├─ evaluation/
│ │ │ └─ page.tsx
│ │ └─ layout.tsx
│ │
│ ├─ components/
│ ├─ lib/
│ └─ styles/
│
├─ backend/
│ ├─ main.py
│ │
│ ├─ routes/
│ │ ├─ upload.py
│ │ ├─ chat.py
│ │ └─ evaluation.py
│ │
│ ├─ services/
│ │ ├─ pdf_parser.py
│ │ ├─ docx_parser.py
│ │ ├─ chunker.py
│ │ ├─ embedder.py
│ │ ├─ vector_store.py
│ │ ├─ retriever.py
│ │ └─ generator.py
│ │
│ ├─ eval/
│ │ └─ ragas_runner.py
│ │
│ └─ data/
│ ├─ uploads/
│ ├─ chroma/
│ └─ results/
│
└─ .env


# 이 구조를 유지한다. 불필요한 변경 금지.

---

## MVP Scope

### In scope
- PDF upload
- DOCX upload
- Text extraction
- Chunking
- Vector search
- Answer generation
- Source citation
- RAGAS evaluation

### Out of scope
- OCR
- Excel ingestion
- Hybrid search
- Reranker
- Authentication
- Monitoring
- Multi dataset

# MVP는 단순하게 유지한다.

---

## UI Requirements

### Pages
- /upload → 파일 업로드
- /chat → 질문/답변
- /evaluation → RAGAS 결과

---

## Tech Stack

Frontend:
- Next.js
- Tailwind CSS

Backend:
- FastAPI

Parsing:
- PDF: PyMuPDF
- DOCX: python-docx

Vector DB:
- Chroma

Evaluation:
- RAGAS

---

## Architecture Rules

- Keep everything simple
- Avoid unnecessary abstraction
- Build end-to-end quickly

---

## Retrieval Rules

- Use vector search only
- Retrieve top 3 chunks
- Do not hallucinate
- Always show sources

---

## Chunking Rules

- Paragraph-based chunking
- Keep metadata

Metadata:
- file_name
- chunk_index
- section (optional)

---

## Development Order

1. Upload
2. Parsing
3. Chunking
4. Vector store
5. Retrieval
6. Answer
7. UI
8. RAGAS

---

## Project Management Rules

### 1. MVP Plan Tracking
- Maintain overall MVP progress
- Update progress continuously

---

### 2. Daily 기록

- 매일 작업 내용을 기록한다
- 위치: docs/daily/YYYY-MM-DD.md

내용:
- 작업 내용
- 완료된 작업
- 문제점
- 다음 계획

---

### 3. 연속성 유지

- 작업 시작 전 이전 daily 파일을 읽는다
- 이전 작업을 기반으로 이어서 진행한다

---

### 4. MD 파일 인식

작업 시작 전 반드시 확인:
- AGENTS.md
- TODO.md
- docs/*
- daily 기록

---

### 5. 작업별 문서 분리 (파트 기반)

- 기능 단위로 md 파일을 생성한다
- 위치: docs/{파트명}.md

예:
- upload.md
- parsing.md
- chunking.md
- indexing.md
- retrieval.md
- answer.md
- chat.md
- evaluation.md

각 파일에는 다음을 기록:
1. 목적
2. 구현 내용
3. 상태
4. 문제
5. 다음 작업

---

### 6. AWS 환경 규칙

- AWS 환경에서 작업 진행
- 로컬 → AWS 순서

---

### 7. 보안 규칙

- 최소 권한 원칙
- 최소 포트 오픈
- 불필요한 접근 금지

---

### 8. 승인 규칙

다음 작업은 반드시 승인 후 진행:
- EC2 생성
- RDS 생성
- S3 생성
- 네트워크 설정

---

### 9. AWS Tag 규칙

모든 리소스에 적용:
- key: owner
- value: taenny

---

## Working Style

- Small steps
- No over-engineering
- Keep it simple

---

## Definition of Done

- Works end-to-end
- Readable code
- Minimal complexity
