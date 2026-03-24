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
