# Insurance Document RAG MVP

## Overview
This project is a simple RAG (Retrieval-Augmented Generation) MVP for insurance documents.

Users can:
- Upload PDF, DOC, DOCX, XLS, or XLSX files
- Choose a primary parser and second parser on the upload screen
- Search indexed chunks based on uploaded documents
- Generate grounded answers from retrieved chunks on `/chat`
- Inspect retrieved source chunks and citations on `/chat`
- View evaluation page skeleton for later RAGAS integration

## Scope
This is an MVP focused on core functionality only.

Included:
- PDF/DOC/DOCX/XLS/XLSX upload
- Parser selection UI
- Text extraction
- Chunking
- Embedding + vector search
- Retrieval + grounded answer UI
- Source citation
- Evaluation page skeleton

Excluded:
- OCR
- Hybrid search
- Production-grade embedding model integration
- Authentication
- Monitoring dashboard

## Main Pages
- `/upload` : upload documents
- `/chat` : run retrieval queries and inspect source chunks
- `/evaluation` : evaluation page skeleton

## Tech Stack
- Frontend: Next.js 15 + React 19 + TypeScript + Tailwind CSS
- Backend: FastAPI + Uvicorn
- Parsing: Docling, PyMuPDF, python-docx, antiword, openpyxl, xlrd
- Vector store: Chroma
- Evaluation: RAGAS

## Core Flow
Upload → Parse → Chunk → Embed → Store → Retrieve

## Goal
Deliver a small, readable, end-to-end MVP before adding advanced features.

## Current Status
- Documentation baseline is in place under `docs/`
- AWS EC2 implementation server was created with Terraform
- The RAG EC2 server is reachable over `ssh -p 2022`
- The RAG EC2 instance type is `t3.xlarge`
- Frontend and backend dependencies are installed on the RAG server
- Upload API and upload UI are implemented
- Backend upload flow has been verified on the RAG server
- Frontend runtime page responds successfully on the RAG server
- `localhost:3001` CORS is allowed for the upload UI flow
- Upload page UI cleanup is complete
- Parsing API for uploaded PDF/DOC/DOCX/XLS/XLSX files is implemented
- Parsing text extraction validation has been verified on the RAG server
- DOCX parser now includes table and header/footer text extraction
- Upload page includes in-browser parse test, full extracted text view, and separate quality-check action
- Upload page includes `Primary parser` / `Second parser` selection UI
- Docling is installed on the RAG server and works as the primary parser
- Upload page now includes `Docling(md)`, which uses Docling only and writes a Markdown output file
- DOC fallback parser uses `antiword`
- Excel fallback parser uses `openpyxl` / `xlrd`
- Parser smoke tests for `DOC`, `DOCX`, and `XLSX` were verified on the RAG server
- Chunking API and chunk metadata output are implemented
- Upload now triggers indexing automatically after the file is stored
- Indexing API stores chunk embeddings in Chroma
- Indexed file list API and retrieval API are implemented
- Chat page is currently organized as an external RAG-ready shell
- Chat page keeps question input, response area, citation slots, and optional debug context visible
- External RAG API request/response schema is not finalized yet, so `/chat` avoids depending on request tuning controls in the main UI
- Current backend can still return retrieval-backed answers and citations while the external contract is pending
- Upload list supports file-level delete of upload + index
- Upload list shows per-file indexing status and chunk count
- Upload list now refreshes immediately even when parse/chunk/index fails after upload
- Upload failure UI now shows the failed pipeline stage and backend log path
- `Default file list` starts from `Select a file`
- Retrieval test question set is documented in `docs/retrieval-test-set.md`
- Retrieval pass/fail has been checked on representative questions
- Azure OpenAI `text-embedding-3-small` embedding replacement and rebuild are complete
- Pricing-method PDF retrieval still remains weak in all-file search, so the next work is parser/chunking/retrieval quality re-check rather than another embedding swap
- Backend exposes `GET /parse/parsers` and supports `Docling -> auxiliary parser fallback`
- Parser catalog now marks `Docling`, `Docling(md)`, `DOC parser`, and `Excel parser` as available on the RAG server
- Parser catalog default primary parser is now `Legacy auto`, so PDF uses `PyMuPDF` first in the normal flow
- Frontend is currently operated more stably with `build + start` than `next dev`
- Backend now writes request and parser system logs on the RAG server
- Upload 화면 UI를 현재 기준으로 리프레시했고, header / stat strip / card 위계를 정리했다
- `Docling(md)` parse 성공 시 upload list에서 `markdown_path`를 함께 확인할 수 있다
- 2026-04-03 기준 현재 서버와 RAG 서버의 핵심 소스/문서 해시가 일치함을 확인했다
- Parse success/failure history UI는 구조상 노출되며, duplicate upload와 과거 실패 이력이 함께 보일 수 있다
- RAG 서버 테스트용 upload/parse/chunk/index 데이터는 2026-03-29 기준 초기화 완료 상태다
- Retrieval-backed answer generation is connected in the current backend
- Retrieval question-set based answer quality review and evaluation execution are deferred behind external RAG contract definition
- Current PDF garbled detection can still miss cases where both the parsed text and the reference extraction are broken in the same way

## Screen Test Rule
- 화면 테스트와 브라우저 확인은 RAG 서버 기준으로만 수행한다.
- 현재 서버에서는 CLI 작업과 코드 수정만 수행한다.
- 화면 확인 기준 주소는 RAG 서버 frontend `127.0.0.1:3000`, backend `127.0.0.1:8000`이다.
- 현재 서버에는 소스만 두고, 실제 frontend/backend 실행은 RAG 서버에서만 유지한다.

## Logs
- Backend system log: `/home/ubuntu/rag-mvp/backend/logs/app.log`
- Backend runtime log: `/home/ubuntu/rag-mvp/run-logs/backend.out`
- Frontend runtime log: `/home/ubuntu/rag-mvp/run-logs/frontend.out`
- 장애 확인은 먼저 backend system log를 보고, 이후 runtime log를 확인한다.

## Upload List Notes
- 같은 원본 파일명을 여러 번 업로드하면 `stored_name` 기준으로 별도 행이 누적된다.
- `Parse test`를 다시 성공시키면 해당 행의 최신 parse 결과는 성공 기준으로 갱신되지만, `chunk`를 다시 실행하지 않으면 `chunk_status`는 `pending`으로 남을 수 있다.
- parse 성공/실패 history를 같은 행에서 함께 보여주는 개선 작업을 진행했고, RAG 서버 화면 기준 최종 검증은 추가 확인이 필요하다.

## Default Files
- Preload files in `backend/data/default-files`
- These files are not committed to git by default
- The `/upload` page can upload one of these files through the `Default file` flow

## Resume Tomorrow
Start from these files first:
- `AGENTS.md`
- `README.md`
- `docs/plan.md`
- `TODO.md`
- `docs/status.md`
- `docs/answer-eval.md`
- `docs/llm.md`
- `docs/daily/2026-03-31.md`

Recommended restart order:
1. Review `AGENTS.md` for the working rules and document order.
2. Review `README.md` for the current runtime and screen-test rules.
3. Review `docs/plan.md` for the current phase and next priority.
4. Review `TODO.md` for unchecked tasks.
5. Review `docs/status.md` for the latest completed scope and blockers.
6. Review related `docs/*.md` such as `docs/answer-eval.md` and `docs/llm.md`.
7. Review `docs/daily/2026-04-01.md` for the latest session log.
8. Start the next task.

## Daily Start Checklist
1. Review `AGENTS.md` for working rules and project operating constraints.
2. Review `README.md` for runtime, deployment, and screen-test rules.
3. Review `docs/plan.md` for the current phase and next work.
4. Review `TODO.md` for unchecked tasks.
5. Review `docs/status.md` for the latest actual progress and blockers.
6. Review related `docs/*.md` and the latest `docs/daily/` file before starting.
