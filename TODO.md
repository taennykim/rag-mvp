# TODO

---

## Phase 0. Project Initialization (문서 + 구조)

- [ ] docs 폴더 생성
- [ ] docs/daily 폴더 생성
- [ ] docs/plan.md 생성
- [ ] docs/retrieval.md 생성
- [ ] docs/llm.md 생성
- [ ] docs/ui.md 생성

---

## Phase 1. Project Setup

- [ ] Create frontend with Next.js
- [ ] Create backend with FastAPI
- [ ] Connect basic routing
- [ ] Add README.md
- [ ] Add AGENTS.md
- [ ] Add TODO.md

---

## Phase 2. Initial Documentation 작성

- [ ] plan.md에 MVP 계획 작성
- [ ] retrieval.md에 검색 설계 작성
- [ ] llm.md에 RAG 구조 작성
- [ ] ui.md에 화면 구조 작성

---

## Phase 3. Upload

- [ ] Create PDF upload API
- [ ] Create DOCX upload API
- [ ] Save uploaded files to backend/data/uploads
- [ ] Create uploaded file list API
- [ ] Build upload page UI

---

## Phase 4. Parsing

- [ ] Extract text from PDF using PyMuPDF
- [ ] Extract text from DOCX using python-docx
- [ ] Verify extracted text is not empty
- [ ] Return simple parsing result for testing

---

## Phase 5. Chunking

- [ ] Split extracted text into chunks
- [ ] Add metadata to each chunk
- [ ] Verify chunk list output
- [ ] Store chunk count per file

---

## Phase 6. Indexing

- [ ] Generate embeddings for chunks
- [ ] Store chunks and embeddings in Chroma
- [ ] Create indexing API
- [ ] Verify at least one uploaded file is searchable

---

## Phase 7. Retrieval

- [ ] Create question input API
- [ ] Implement vector search
- [ ] Return top 3 chunks
- [ ] Include source metadata in response

---

## Phase 8. Answer

- [ ] Connect answer generation model
- [ ] Generate answer from retrieved context only
- [ ] Include source file names and chunk references
- [ ] Handle insufficient-context case

---

## Phase 9. Chat UI

- [ ] Build chat page
- [ ] Add question input box
- [ ] Show answer output
- [ ] Show retrieved chunks and sources

---

## Phase 10. Evaluation Data

- [ ] Prepare small evaluation dataset
- [ ] Add sample questions
- [ ] Add reference answers if available

---

## Phase 11. RAGAS

- [ ] Create RAGAS runner
- [ ] Run evaluation on sample dataset
- [ ] Save evaluation results
- [ ] Create evaluation API

---

## Phase 12. Evaluation UI

- [ ] Build evaluation page
- [ ] Show average metrics
- [ ] Show per-question results table
- [ ] Highlight low-scoring cases

---

## Phase 13. Daily Management (중요)

- [ ] daily 기록 생성
- [ ] 작업 내용 기록
- [ ] 이슈 기록
- [ ] 다음 작업 정의

---

## Final Check

- [ ] Upload works
- [ ] Parsing works
- [ ] Chunking works
- [ ] Retrieval works
- [ ] Answer generation works
- [ ] Sources are visible
- [ ] RAGAS evaluation works
