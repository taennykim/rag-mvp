# Insurance Document RAG MVP

## Overview
This project is a simple RAG (Retrieval-Augmented Generation) MVP for insurance documents.

Users can:
- Upload PDF or DOCX files
- Choose a primary parser and auxiliary parser on the upload screen
- Search indexed chunks based on uploaded documents
- Inspect retrieved source chunks before answer generation
- View evaluation page skeleton for later RAGAS integration

## Scope
This is an MVP focused on core functionality only.

Included:
- PDF/DOCX upload
- Parser selection UI
- Text extraction
- Chunking
- Embedding + vector search
- Retrieval test UI
- Source citation
- Evaluation page skeleton

Excluded:
- OCR
- Real Excel ingestion
- Hybrid search
- Full answer generation
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
- Parsing: PyMuPDF, python-docx, Docling-ready parser routing
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
- Parsing API for uploaded PDF/DOCX files is implemented
- Parsing text extraction validation has been verified on the RAG server
- DOCX parser now includes table and header/footer text extraction
- Upload page includes in-browser parse test, full extracted text view, and separate quality-check action
- Upload page includes `Primary parser` / `Auxiliary parser` selection UI
- Chunking API and chunk metadata output are implemented
- Upload now triggers indexing automatically after the file is stored
- Indexing API stores chunk embeddings in Chroma
- Indexed file list API and retrieval API are implemented
- Chat page can query retrieved chunks and inspect sources
- Upload list supports file-level delete of upload + index
- Upload list shows per-file indexing status and chunk count
- `Default file list` starts from `Select a file`
- Retrieval test question set is documented in `docs/retrieval-test-set.md`
- Retrieval pass/fail has been checked on representative questions
- Pricing-method PDF retrieval remains weak in all-file search and is the main reason to replace the current embedding
- Backend exposes `GET /parse/parsers` and supports `Docling -> auxiliary parser fallback`
- Current environment does not have Docling installed yet, so PDF/DOCX still run through fallback parsers
- Frontend is currently operated more stably with `build + start` than `next dev`
- Answer generation and evaluation execution are still pending

## Default Files
- Preload files in `backend/data/default-files`
- These files are not committed to git by default
- The `/upload` page can upload one of these files through the `Default file` flow

## Resume Tomorrow
Start from these files first:
- `docs/status.md`
- `docs/daily/2026-03-26.md`
- `docs/retrieval-test-set.md`
- `TODO.md`

Recommended restart order:
1. Review `docs/status.md` for the latest completed scope and blockers.
2. Review `docs/daily/2026-03-26.md` for today's detailed work log.
3. Review `docs/retrieval-test-set.md` for retrieval validation criteria and fail cases.
4. Review `TODO.md` for remaining MVP tasks after retrieval stabilization.
5. Continue with Docling installation review or actual embedding model integration.

## Daily Start Checklist
1. Review `AGENTS.md` for working rules and project operating constraints.
2. Review `README.md` for project scope and restart guidance.
3. Review `docs/status.md` for the latest actual progress and blockers.
4. Review the latest file in `docs/daily/` for the previous session context.
5. Review `TODO.md` and choose the first unchecked task for the day.
