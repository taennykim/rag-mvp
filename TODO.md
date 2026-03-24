# TODO

## Phase 1. Setup
- [ ] Create frontend with Next.js
- [ ] Create backend with FastAPI
- [ ] Connect basic routing
- [ ] Add README, AGENTS, TODO files

---

## Phase 2. Upload
- [ ] Create PDF upload API
- [ ] Create DOCX upload API
- [ ] Save uploaded files to backend/data/uploads
- [ ] Create uploaded file list API
- [ ] Build upload page UI

---

## Phase 3. Parsing
- [ ] Extract text from PDF using PyMuPDF
- [ ] Extract text from DOCX using python-docx
- [ ] Verify extracted text is not empty
- [ ] Return simple parsing result for testing

---

## Phase 4. Chunking
- [ ] Split extracted text into chunks
- [ ] Add metadata to each chunk
- [ ] Verify chunk list output
- [ ] Store chunk count per file

---

## Phase 5. Indexing
- [ ] Generate embeddings for chunks
- [ ] Store chunks and embeddings in Chroma
- [ ] Create indexing API
- [ ] Verify at least one uploaded file is searchable

---

## Phase 6. Retrieval
- [ ] Create question input API
- [ ] Implement vector search
- [ ] Return top 3 chunks
- [ ] Include source metadata in response

---

## Phase 7. Answer
- [ ] Connect answer generation model
- [ ] Generate answer from retrieved context only
- [ ] Include source file names and chunk references
- [ ] Handle insufficient-context case

---

## Phase 8. Chat UI
- [ ] Build chat page
- [ ] Add question input box
- [ ] Show answer output
- [ ] Show retrieved chunks and sources

---

## Phase 9. Evaluation Data
- [ ] Prepare small evaluation dataset
- [ ] Add sample questions
- [ ] Add reference answers if available

---

## Phase 10. RAGAS
- [ ] Create RAGAS runner
- [ ] Run evaluation on sample dataset
- [ ] Save evaluation results
- [ ] Create evaluation API

---

## Phase 11. Evaluation UI
- [ ] Build evaluation page
- [ ] Show average metrics
- [ ] Show per-question results table
- [ ] Highlight low-scoring cases

---

## Final Check
- [ ] Upload works
- [ ] Parsing works
- [ ] Chunking works
- [ ] Retrieval works
- [ ] Answer generation works
- [ ] Sources are visible
- [ ] RAGAS evaluation works
