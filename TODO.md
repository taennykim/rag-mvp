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
- [x] Show indexing status per uploaded file
- [x] Extend upload support to `.doc`, `.xls`, `.xlsx`

---

## Phase 4. Parsing

- [x] Extract text from PDF using PyMuPDF
- [x] Extract text from DOCX using python-docx
- [x] Verify extracted text is not empty
- [x] Return simple parsing result for testing
- [x] Add parsing quality check API
- [x] Add parser selection UI and parser catalog API
- [x] Install and verify Docling as primary parser
- [x] Implement `.doc` auxiliary parser
- [x] Implement Excel auxiliary parser
- [x] Add parser availability exposure in `GET /parse/parsers`
- [x] Verify `DOC`, `DOCX`, `XLSX` parser smoke test on the RAG server
- [x] Add parse failure state tracking and parser/system log tracing
- [ ] Compare `Docling` vs fallback parser quality for PDF
- [ ] Compare parser choice impact on chunking/retrieval

---

## Phase 5. Chunking

- [x] Split extracted text into chunks
- [x] Add metadata to each chunk
- [x] Verify chunk list output
- [x] Store chunk count per file

---

## Phase 6. Indexing

- [x] Generate embeddings for chunks
- [x] Store chunks and embeddings in Chroma
- [x] Create indexing API
- [x] Verify at least one uploaded file is searchable
- [x] Trigger indexing automatically after upload
- [x] Rebuild index after real embedding model integration

---

## Phase 7. Retrieval

- [x] Create question input API
- [x] Implement vector search
- [x] Return top 3 chunks
- [x] Include source metadata in response
- [x] Add retrieval test question set
- [x] Add initial lexical rerank experiment
- [x] Replace hash embedding with real embedding model
- [ ] Re-run retrieval question set after embedding replacement

---

## Phase 8. Answer

- [x] Connect answer generation model on `/chat` with runtime deployment config
- [x] Generate answer from retrieved context only
- [x] Include source file names and chunk references
- [x] Handle insufficient-context case

---

## Phase 9. Chat UI

- [x] Build chat page
- [x] Add question input box
- [x] Show answer output
- [x] Show retrieved chunks and sources
- [x] Connect LLM answer flow to chat screen

---

## Phase 9.5 Upload UX / Operations

- [x] Refresh uploaded file list immediately after upload failure
- [x] Sort uploaded file list by latest upload
- [x] Show file-level indexing status and chunk count
- [x] Show pipeline failure stage and backend log path in UI
- [ ] Final UI verification for parse success/failure history in uploaded file list

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

- [x] 오늘 작업 내용을 `README.md`, `docs/status.md`, `docs/daily/2026-03-31.md`, `TODO.md`에 반영
- [ ] 다음 시작 시 `AGENTS.md` -> `docs/plan.md` -> `TODO.md` -> `docs/status.md` -> 관련 `docs/*.md` -> `docs/daily/2026-03-31.md` 순서로 확인
- [x] frontend 의존성 설치
- [x] backend 의존성 설치
- [x] frontend 실행 확인
- [x] backend 실행 확인
- [x] parser 실제 구현 및 검증
- [ ] retrieval 질문 세트 기준 Azure embedding 재검증
- [ ] embedding 영향과 parser 영향 분리 기준 정리
- [ ] `PDF` 기준 `Docling` vs `PyMuPDF` 비교
- [ ] parser 영향 기반 chunk/retrieval 재검증
- [x] 실제 embedding 모델 교체 방식 결정
- [ ] retrieval 질문 세트 일부 기준 `/chat` answer generation 품질 검증
- [ ] 산출방법서 계열 표/수식 보존형 chunk 전략 검토
- [x] answer 품질 점검표 초안 작성 (`docs/answer-eval.md`)

---

## Final Check

- [x] Upload works
- [x] Parsing works
- [x] Chunking works
- [x] Retrieval works
- [x] Answer generation works with runtime chat deployment
- [x] Sources are visible
- [ ] RAGAS evaluation works
