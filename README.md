# Insurance Document RAG MVP

## Overview
This project is a simple RAG (Retrieval-Augmented Generation) MVP for insurance documents.

Users can:
- Upload PDF or DOCX files
- Ask questions based on uploaded documents
- Receive answers grounded in retrieved document chunks
- View simple evaluation results using RAGAS

## Scope
This is an MVP focused on core functionality only.

Included:
- PDF/DOCX upload
- Text extraction
- Chunking
- Embedding + vector search
- Question answering
- Source citation
- RAGAS evaluation

Excluded:
- OCR
- Excel ingestion
- Hybrid search
- Reranker
- Authentication
- Monitoring dashboard

## Main Pages
- `/upload` : upload documents
- `/chat` : ask questions and get answers
- `/evaluation` : view RAGAS evaluation results

## Tech Stack
- Frontend: Next.js + Tailwind CSS
- Backend: FastAPI
- Parsing: PyMuPDF, python-docx
- Vector store: Chroma
- Evaluation: RAGAS

## Core Flow
Upload → Parse → Chunk → Embed → Store → Retrieve → Answer → Evaluate

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
- Parsing and later RAG stages are still pending

## Default Files
- Preload files in `backend/data/default-files`
- These files are not committed to git by default
- The `/upload` page can upload one of these files through the `Default file` flow

## Resume Tomorrow
Start from these files first:
- `docs/status.md`
- `docs/daily/2026-03-24.md`
- `TODO.md`

Recommended restart order:
1. Review `docs/status.md` for the latest completed scope and blockers.
2. Review `docs/daily/2026-03-24.md` for today's detailed work log.
3. Continue with parsing implementation from the uploaded files.
4. Implement the next real feature: parsing API and extraction validation.

## Daily Start Checklist
1. Review `AGENTS.md` for working rules and project operating constraints.
2. Review `README.md` for project scope and restart guidance.
3. Review `docs/status.md` for the latest actual progress and blockers.
4. Review the latest file in `docs/daily/` for the previous session context.
5. Review `TODO.md` and choose the first unchecked task for the day.
