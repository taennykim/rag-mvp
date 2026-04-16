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
- [x] Add PDF garbled text warning heuristics to parsing quality check
- [x] Expose parser quality warning reasons in upload file list
- [x] Add `Docling(md)` parser option for Markdown output generation
- [x] Expose `markdown_path` in upload file list for Markdown parse results

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
- [x] Add optional RAG API endpoint input on `/chat`
- [x] Fall back to internal retrieval when `/chat` RAG endpoint is blank
- [x] Clarify `Generated answer` vs `Retrieved chunks` on `/chat`
- [x] Render `View full chunk` and sample preview blocks without truncation
- [x] Extend `/chat` backend input schema with `conversation_context` and `metadata`
- [x] Replace simple retrieval rewrite with structured rewrite result on `/chat`
- [ ] Show rewrite result and route hints on `/chat`
- [x] Show `RAG question` (`rewritten_query`) under `Question` on `/chat`
- [x] Add Query Rewrite LLM selector between Question and LLM Question on `/chat`
- [x] Set default Query Rewrite LLM to `gpt-4o-mini`
- [x] Test and add `gpt-4.1-mini` to Query Rewrite LLM selector
- [x] Keep Query Rewrite LLM UI default as blank `Default` and expose `gpt-4o-mini` as a selectable option
- [x] Rename default Query Rewrite LLM label to `Default (gpt-4o-mini)` and remove duplicate `gpt-4o-mini` option
- [x] Set `/chat` Search API endpoint default to temporary external Search API
- [x] Mark Lookup API endpoint as Later and disable its input
- [x] Show detailed response timing on `/chat` answer panel
- [x] Separate compact `Evidence` from full `Reference context` on `/chat`
- [x] Show `rerank_score` and `matched_queries` on `/chat` for internal retrieval hits
- [x] Merge `docs/chat_plan_addendum.md` into `docs/chat_plan.md`

---

## Phase 9.1 Chat Plan Steps

- [x] Step 1. 원본 상담 대화 입력 구성
- [x] `Question` 멀티라인의 `고객:` / `상담사:` prefix를 `conversation_context`로 파싱
- [x] Step 2. LLM Query Rewrite
- [x] Step 3. Standalone Search Query 검증
- [x] Step 4. Search API 호출
- [x] 임시 외부 Search API `/api/search` payload와 `results` 응답 normalization 연결
- [x] Step 5. Retrieved Candidate Chunks 표준화
- [x] Step 6. Search Result Evaluation
- [ ] Step 7. Need More Context 분기
- [ ] Step 8. Lookup API 호출
- [ ] Step 9. Expanded Context 병합
- [ ] Step 10. Answer Generation LLM
- [ ] Step 11. 최종 상담 답변 후처리

---

## Phase 9.5 Upload UX / Operations

- [x] Refresh uploaded file list immediately after upload failure
- [x] Sort uploaded file list by latest upload
- [x] Show file-level indexing status and chunk count
- [x] Show pipeline failure stage and backend log path in UI
- [ ] Final UI verification for parse success/failure history in uploaded file list
- [x] Verify `Docling(md)` UI flow on the RAG server and confirm second parser disable behavior in runtime build

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
- [ ] 다음 시작 시 `AGENTS.md` -> `README.md` -> `docs/plan.md` -> `docs/chat_plan.md` -> `TODO.md` -> `docs/status.md` -> 관련 `docs/*.md` -> 최신 `docs/daily/*` 순서로 확인
- [ ] 2026-04-16 시작 시 RAG 서버 backend `8000` / frontend `3000` runtime 상태 확인
- [ ] 치조골 이식/수술특약/판결 케이스 query rewrite 규칙 보강
- [ ] 치조골 이식 케이스 기대 rewrite 기준 반영: `치조골 이식 수술이 보험 수술특약에서 수술비 지급 대상 수술로 인정되는지와 관련 판결 기준은 무엇인가요?`
- [ ] RAG 서버 브라우저에서 Query Rewrite LLM 선택 UI 위치와 선택 모델 표시 확인
- [ ] RAG 서버 브라우저에서 Answer 상단 단계별 응답시간 표시 확인
- [ ] RAG 서버 브라우저에서 외부 Search API 결과가 Evidence / Reference context에 표시되는지 확인
- [ ] Query Rewrite LLM 기본값 `gpt-4o-mini` 기준 브라우저 동작 확인
- [x] frontend 의존성 설치
- [x] backend 의존성 설치
- [x] frontend 실행 확인
- [x] backend 실행 확인
- [x] parser 실제 구현 및 검증
- [ ] retrieval 질문 세트 기준 Azure embedding 재검증
- [ ] embedding 영향과 parser 영향 분리 기준 정리
- [x] upload 단계에서 확장자 + 파일 시그니처 + OOXML 내부 구조 기준 문서 타입 판별 강화
- [x] PDF 파싱 결과에서 garbled text 감지 기준 추가
- [x] PDF 기준 `Docling` / `PyMuPDF` / reference-style 추출 품질 비교 로직 설계
- [x] PDF parser 품질 비교 결과를 upload 화면 경고 구조로 노출
- [ ] `PDF` 기준 `Docling` vs `PyMuPDF` 비교
- [x] 산출방법서 PDF용 garbled text heuristic 과탐 보정
- [ ] `Docling` PDF 변환 장시간 실행 원인 확인
- [x] PDF 기본 parser 정책을 `Legacy auto / PyMuPDF 우선`으로 조정
- [ ] garbled detection false negative 기준 추가
- [x] quality metric 라벨 한글 설명 반영
- [ ] parser 영향 기반 chunk/retrieval 재검증
- [x] parser 운영 정책을 `Legacy auto` / `Docling` / `Docling(md)` 기준으로 정리
- [x] 실제 embedding 모델 교체 방식 결정
- [x] 현재 서버와 RAG 서버의 핵심 소스/문서 동기화 확인
- [x] RAG 서버 EC2 IMDSv2 `HttpTokens=required` 적용
- [x] Terraform EC2 metadata option을 `http_tokens = "required"`로 반영
- [x] 약관 PDF 복구 및 duplicate `300233_test.docx` 제거로 3문서 기준 인덱스 정상화
- [x] `/index/{stored_name}`가 운영 parser 정책 `Legacy auto / Extension default`를 따르도록 수정
- [x] `/chat` query preprocessing에 `question_type` 추가
- [x] `document_hint` / `question_type` 규칙을 `backend/app/query_routing.py`로 분리
- [ ] retrieval 질문 세트 일부 기준 `/chat` answer generation 품질 검증
- [ ] 외부 RAG contract 확정 전 기준 `/chat` answer/citation shell 검증
- [x] 2026-04-08 RAG 서버 frontend `build + start` / backend `uvicorn` 재기동 및 `3000/8000` 응답 확인
- [ ] external RAG adapter request/response mapping은 contract 확정 후 진행
- [ ] 산출방법서 계열 표/수식 보존형 chunk 전략 검토
- [x] answer 품질 점검표 초안 작성 (`docs/answer-eval.md`)
- [x] GitHub `main` / 현재 서버 / RAG 서버 핵심 소스·문서 동기화 재확인

---

## Final Check

- [x] Upload works
- [x] Parsing works
- [x] Chunking works
- [x] Retrieval works
- [x] Answer generation works with runtime chat deployment
- [x] Sources are visible
- [ ] RAGAS evaluation works
