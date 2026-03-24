# TODO

---

## Phase 0. Project Initialization (문서 + 구조)

- [x] docs 폴더 생성
- [x] docs/daily 폴더 생성
- [x] docs/plan.md 생성
- [x] docs/retrieval.md 생성
- [x] docs/llm.md 생성
- [x] docs/ui.md 생성
- [x] docs/aws.md 생성

---

## Phase 0.5 AWS Implementation Server

- [x] 기준 EC2 스펙 확인
- [x] Terraform 파일 생성
- [x] terraform init 산출물 확인
- [x] terraform plan 산출물 확인
- [x] terraform plan 재검증
- [x] 사용자 승인 후 terraform apply
- [x] 생성된 EC2 상태 확인

---

## Phase 1. Project Setup

- [x] Create frontend with Next.js skeleton
- [x] Create backend with FastAPI skeleton
- [x] Connect basic routing skeleton
- [x] Add frontend pages for `/upload`, `/chat`, `/evaluation`
- [x] Add frontend root redirect from `/` to `/upload`
- [x] Add shared frontend layout and global styles
- [x] Add backend status routes for `/health`, `/upload`, `/chat`, `/evaluation`
- [x] Add backend dependency manifest
- [x] Add README.md
- [x] Add AGENTS.md
- [x] Add TODO.md

---

## Phase 2. Initial Documentation 작성

- [x] plan.md에 MVP 계획 작성
- [x] retrieval.md에 검색 설계 작성
- [x] llm.md에 RAG 구조 작성
- [x] ui.md에 화면 구조 작성

---

## Phase 3. Upload

- [x] Create PDF upload API
- [x] Create DOCX upload API
- [x] Save uploaded files to backend/data/uploads
- [x] Create uploaded file list API
- [x] Build upload page UI
- [x] Create default file directory for preloaded uploads
- [x] Add default file selection flow in upload page

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

- [x] daily 기록 생성
- [x] 작업 내용 기록
- [x] 이슈 기록
- [x] 다음 작업 정의

---

## Next Session Start Point

- [x] 오늘 작업 내용을 `README.md`, `docs/status.md`, `docs/daily/2026-03-24.md`, `TODO.md`에 반영
- [ ] 내일 시작 시 `docs/status.md`부터 리로드
- [x] frontend 의존성 설치
- [x] backend 의존성 설치
- [ ] frontend 실행 확인
- [x] backend 실행 확인
- [x] upload API 실제 구현 시작
- [x] upload API 최소 구현 완료

---

## Final Check

- [ ] Upload works
- [ ] Parsing works
- [ ] Chunking works
- [ ] Retrieval works
- [ ] Answer generation works
- [ ] Sources are visible
- [ ] RAGAS evaluation works
