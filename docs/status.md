# Current Status

## 1. 목적
- 현재 프로젝트의 실제 구현 상태와 남은 작업을 한 문서에서 확인한다.
- 다음 세션에서 바로 이어서 작업할 수 있도록 우선순위를 명확히 남긴다.

## 2. 현재 목표
- 보험 문서를 업로드하고 문서 근거 기반으로 답변하는 RAG MVP를 완성한다.
- 현재는 `upload -> parse -> chunk -> index -> retrieve`와 `/chat` answer/citation UI까지 연결했고, chat deployment `gpt-4o` 실응답까지 확인했다.
- 현재 `/chat` 우선순위는 외부 RAG contract 미확정 상태에서도 유지 가능한 question / answer / citation shell 정리다.
- 다음 핵심 작업은 외부 RAG contract 정의 전까지 필요한 UI shell 유지와 answer/citation 품질 기록이다.
- 2026-04-08 기준 RAG 서버 frontend/backend를 다시 재기동해 UI 확인 가능한 runtime 상태를 복구했다.
- backend `/chat`은 여전히 Input 정규화 -> structured rewrite -> RAG 검색 API 호출 -> grounded answer 생성 흐름을 유지하지만, frontend는 이에 강하게 결합하지 않도록 단순화했다.
- 2026-04-09 기준 `/chat` Evidence와 `Reference context`의 역할을 분리했고, internal retrieval hit의 `rerank_score` / `matched_queries`를 UI에서 직접 확인할 수 있게 했다.
- 2026-04-09 기준 `docs/chat_plan.md`에 GPT-4o query rewrite 설정과 `rag-mvp` 파일/디렉터리 매핑을 흡수했고, 별도 `docs/chat_plan_addendum.md`는 제거했다.
- 2026-04-09 기준 `/chat` Question 바로 아래에 `LLM Question` (`rewritten_query`)을 표시하도록 반영했다.
- 2026-04-09 기준 GitHub `main`, 현재 서버, RAG 서버 핵심 소스/문서 해시를 다시 일치시켰다.
- 2026-04-10 기준 `docs/chat_plan.md` 순서대로 작업을 다시 시작했고, `Step 1`에 해당하는 대화 입력 정규화와 마지막 고객 발화 추출을 backend `/chat` 흐름에 반영했다.
- 2026-04-10 기준 `Step 2`에 해당하는 Query Rewrite를 seed query 결정, prompt 생성, 응답 파싱, fallback 결과 생성 단계로 정리했다.
- 2026-04-10 기준 frontend가 별도 `conversation_context` 입력 UI를 갖고 있지 않아도, `Question` 멀티라인의 `고객:` / `상담사:` prefix를 backend에서 상담 대화로 파싱하도록 보강했다.
- 2026-04-10 기준 멀티턴 상담 예시를 RAG 서버 `/chat`로 검증했고, Query Rewrite가 마지막 고객 발화를 기준으로 질문형 `rewritten_query`를 생성하는 것을 확인했다.
- 2026-04-10 기준 `Step 3` Standalone Search Query 검증을 backend `/chat`에 연결했고, 길이/질문형/핵심 키워드 규칙과 fallback 순서를 반영했다.
- 2026-04-10 기준 `Step 5` Retrieved Candidate Chunks 표준화를 backend `/retrieve`, `/chat` 응답에 반영했다.
- 2026-04-10 기준 변경된 backend 소스와 문서를 RAG 서버에 다시 동기화했고, backend를 재기동한 뒤 `127.0.0.1:8000/health` 응답 `200`을 확인했다.
- 2026-04-14 기준 `Step 4` Search API 호출 계층을 backend `/chat`에서 분리했고, 내부/외부 검색 경로 공통 trace를 `search_query`, `executed_search_queries` 기준으로 정리했다.
- 2026-04-14 기준 `Step 6` Search Result Evaluation rule-based 1차 구현을 추가했고, `/chat` 응답에 `need_more_context`와 `search_evaluation`을 포함하도록 반영했다.
- 2026-04-14 기준 query rewrite 운영 스펙을 `docs/query-rewrite-spec.md`로 분리했고, backend prompt가 이 문서를 읽어 `rewritten_query` 기준에 반영하도록 연결했다.
- 2026-04-14 기준 `/chat` main UI는 `rewritten_query`만 노출하도록 단순화했고, 내부 Search 후보와 rerank 기준도 `rewritten_query` 우선으로 정리했다.
- 2026-04-15 기준 query rewrite에서 모호한 마지막 고객 발화를 최근 고객 발화 묶음으로 보강하고, `종신보험` 계열 문의의 보장 축 복원 규칙을 추가했다.
- 2026-04-15 기준 개발자 제공 임시 Search API `http://10.160.98.123:8000/api/search`를 `/chat` 외부 검색 endpoint로 사용할 수 있도록 `/api/search` payload와 `results` 응답 normalization을 반영했다.
- 2026-04-15 기준 RAG 서버 `/chat`에서 임시 외부 Search API 호출, `retrieved_chunks` 표준화, Answer 생성까지 end-to-end로 확인했다.
- 2026-04-15 기준 `/chat` 화면의 응답시간을 전체 Response time, Query rewrite time, API response time으로 세분화했다.
- 2026-04-15 기준 `/chat` Question과 LLM Question 사이에 Query Rewrite LLM 선택 UI를 추가했고, backend가 `query_rewrite_model`을 rewrite 호출에 적용하도록 반영했다.
- 2026-04-16 기준 Query Rewrite LLM 기본값을 `gpt-4o-mini`로 변경했다.
- 2026-04-16 기준 RAG 서버에서 `gpt-4.1-mini` deployment 직접 호출 성공을 확인했고 Query Rewrite LLM 선택지에 추가했다.
- 2026-04-16 기준 Query Rewrite LLM UI 기본 선택값 라벨은 `Default (gpt-4o-mini)`로 표시하고, 중복 선택으로 보이지 않도록 별도 `gpt-4o-mini` 옵션은 제거했다.
- 2026-04-16 기준 `/chat` Search API endpoint는 backend 고정값 `http://10.160.98.123:8000/api/search`, Lookup API endpoint는 backend 고정값 `http://10.160.98.123:8000/api/lookup`를 사용하도록 바꿨고, UI는 Search `final_k`와 `Get response`만 노출하며 Lookup 버튼은 hidden 처리했다.
- 2026-04-16 기준 Lookup은 직전 Search 결과 중 최고 `rrf_score` hit의 `document_id`를 사용하도록 연결했다.
- 2026-04-16 기준 Search API 연결 실패 시에도 `/chat`이 `rewritten_query`, 오류 메시지, insufficient-context 상태를 함께 반환하도록 보강했다.
- 2026-04-16 기준 `/chat`은 Query Rewrite LLM과 별도로 Answer LLM도 선택할 수 있고, backend가 `answer_model`을 grounded answer 생성 deployment에 적용하도록 반영했다.
- 2026-04-16 기준 Query Rewrite LLM에 `Custom` 옵션을 추가했고, OpenAI-compatible custom endpoint를 호출할 수 있게 했다.
- 2026-04-16 기준 Answer LLM에도 `Custom` 옵션을 추가했고, OpenAI-compatible custom endpoint로 answer generation을 호출할 수 있게 했다.
- 2026-04-17 기준 RAG 서버 runtime 상태를 재점검했고 backend `127.0.0.1:8000/health`, frontend `127.0.0.1:3000/upload`, `127.0.0.1:3000/chat` 응답 `200`과 `8000/3000` listen 상태를 확인했다.
- 2026-04-17 기준 `/chat` Custom LLM 입력을 `LLM endpoint`, `LLM model name`, `API Key`, `Temperature`, `Top-K`, `Max Tokens` 구조로 정리했다.
- 2026-04-17 기준 answer generation user prompt에 `docs/answer-generation-spec.md` 내용을 포함해 답변 생성 기준을 반영하도록 변경했다.
- 2026-04-17 기준 `/chat`의 `Custom model name` 라벨/문구를 `LLM model name`으로 통일했다.
- 2026-04-17 기준 RAG 서버 반영 경로 오류(루트 `main.py`, `page.tsx` 생성)를 확인했고, 실제 실행 경로(`backend/app/main.py`, `frontend/app/chat/page.tsx`)로 재동기화 후 frontend/backend 재기동 및 `8000/3000` 응답 `200`을 재확인했다.

## 3. 완료된 범위
- 문서 체계:
  - `AGENTS.md`, `README.md`, `TODO.md`, `docs/` 문서 구조 정리 완료
  - `docs/daily/` 기준 일자별 작업 기록 유지 중
- 인프라/환경:
  - Terraform으로 RAG EC2 생성 완료
  - 현재 서버에서 RAG 서버로 `ssh -p 2022` 접속 가능
  - RAG 서버에 frontend/backend 실행 환경 설치 완료
  - 2026-04-06 기준 RAG EC2 `i-09c547c2adaefff77`의 IMDSv2 `HttpTokens=required` 변경 요청 및 Terraform 반영 완료
  - 2026-04-07 기준 현재 서버와 RAG 서버 최신 소스 동기화 및 stale frontend `3000` 프로세스 교체 완료
  - 2026-04-08 기준 PEM 키 `p2an2test001.pem`으로 RAG 서버 접속 후 runtime 상태를 재점검했다
  - 2026-04-08 기준 frontend `next start` 실패 원인이 `.next` production build 부재임을 확인했다
  - 2026-04-08 기준 RAG 서버 frontend를 `next build + next start`로 다시 올리고 `/upload` 응답 `200`을 확인했다
  - 2026-04-08 기준 RAG 서버 backend를 `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`으로 다시 올리고 `/health` 응답 `200`을 확인했다
- frontend:
  - `/upload`, `/chat`, `/evaluation` 페이지 구성 완료
  - `/` -> `/upload` redirect 완료
  - `/upload`에서 파일 업로드, default file 업로드, parsing test, parsing quality check 가능
  - `/upload` 목록에서 파일별 indexing 상태와 chunk 수 표시 가능
  - upload 실패 후에도 `Uploaded file list`가 즉시 refresh되도록 수정 완료
  - `Uploaded file list`는 최신 업로드 순으로 정렬되도록 수정 완료
  - `/upload`에서 `Primary parser`, `Second parser` 선택 가능
  - `/upload`에서 `Docling(md)` 선택 시 second parser 비활성화 및 `markdown_path` 노출 완료
  - upload 실패 시 실패 단계와 backend log 경로를 UI에서 확인 가능
  - `Uploaded file list`에서 `Preview` 버튼으로 parse preview 확인 가능
  - `Uploaded file list`에서 parsing quality 결과를 파일 행 기준으로 확인 가능
  - 업로드 대상 확장자를 `PDF`, `DOC`, `DOCX`, `XLS`, `XLSX`까지 확장 완료
  - `/chat`에 answer panel 및 citation 카드 UI 추가 완료
  - `/chat` main UI를 external RAG-ready shell로 단순화 완료
  - `/chat`에서 question 입력만으로 response shell을 확인할 수 있도록 정리 완료
  - `/chat` debug card에서 현재 backend가 반환하는 raw context를 임시 확인 가능
  - `/chat`에서 `View raw chunk`와 preview block overflow 정리 완료
  - `/chat` question 입력 기본값 제거 완료
  - header / nav / card / form control / result card 기준 UI refresh 완료
  - upload 화면 상단 stat strip 추가 완료
  - header title은 한 줄 기준으로 보이도록 조정 완료
  - `/chat` Evidence는 compact citation pointer 중심으로 축소했고 `Reference context`는 preview/full text + `rerank_score` + `matched_queries` 표시로 역할 분리 완료
  - `/chat` Question 바로 아래에 `LLM Question` 표시 추가 완료
  - `/chat` Question preview에는 `rewritten_query`만 표시하도록 정리 완료
- backend:
  - upload API 구현 완료
  - parse API 및 parse quality API 구현 완료
  - chunk API 구현 완료
  - index API 및 indexed file list API 구현 완료
  - retrieve API 구현 완료
  - `POST /chat` grounded answer API 추가 완료
  - `POST /chat`에서 `conversation_context` / `metadata` 입력을 받아 structured rewrite 후 external/internal RAG endpoint 분기 호출 구현 완료
  - `POST /chat`에서 `conversation_context`의 빈 발화를 제거하고 role alias를 정규화하며 마지막 고객 발화를 추출하도록 보강 완료
  - `POST /chat`에서 `conversation_context`가 비어 있으면 `Question` 멀티라인의 `고객:` / `상담사:` prefix를 파싱해 대화 입력으로 재구성하도록 보강 완료
  - `POST /chat` Query Rewrite는 마지막 고객 발화 우선 seed query, JSON-only prompt, 응답 파싱, fallback 결과 생성 흐름으로 정리 완료
  - `POST /chat` Standalone Search Query 검증은 최소/최대 길이, 질문형 종결, 핵심 키워드 포함 여부를 검사하고 실패 시 `last_customer_message` -> `last_customer_message + metadata` -> LLM retry 1회 순서로 fallback 하도록 반영 완료
  - `/chat` 응답에 `rewrite_source`, `validation_reasons`를 포함해 rewrite 검증 trace를 확인할 수 있도록 정리 완료
  - `/retrieve`, `/chat` 응답에 `retrieved_chunks` 표준 포맷을 추가했고 `document_id`, `chunk_id`, `score`, `section`, `text`, `rank` 기준으로 normalize 하도록 반영 완료
  - `POST /chat` Search API 호출 계층을 `execute_search_for_chat`으로 분리 완료
  - `POST /chat` 임시 외부 Search API `/api/search` 호출 시 `rewritten_query`를 `query`로 보내고 개발자 제공 curl 파라미터를 적용하도록 반영 완료
  - `POST /chat` 외부 Search API의 `results[].content` 응답을 내부 `hits` / `retrieved_chunks` 표준 포맷으로 변환하도록 반영 완료
  - `POST /chat` Search Result Evaluation rule-based 1차 구현 완료
  - `POST /chat` 응답에 `query_rewrite_time_ms`, `search_api_response_time_ms` 추가 완료
  - `POST /chat` 요청/응답에 query rewrite LLM 선택 trace 추가 완료
  - `POST /chat` query rewrite 기본 LLM을 `gpt-4o-mini`로 변경 완료
  - `POST /chat` query rewrite LLM 선택지에 `gpt-4.1-mini` 추가 완료
  - `/chat` Search/Lookup 고정 endpoint와 Search `final_k`, Lookup 버튼 hidden UI 반영 완료
  - Search API 연결 실패 시 `/chat`이 `rewritten_query`와 오류 메시지를 함께 반환하도록 반영 완료
  - `POST /chat` 응답에 `search_query`, `executed_search_queries`, `need_more_context`, `search_evaluation` trace 추가 완료
  - `POST /chat` 내부 검색 후보와 rerank 기준을 `rewritten_query` 우선으로 정리 완료
  - `POST /chat` query rewrite seed를 최근 고객 발화 묶음 기준으로 보강 완료
  - `POST /chat` query rewrite prompt에 보험 도메인 보장 축 복원 규칙과 최소 few-shot 예시 반영 완료
  - upload 직후 자동 indexing 연결 완료
  - parser catalog API `GET /parse/parsers` 추가 완료
  - `Docling(md)` 전용 Docling parse 및 Markdown file output 저장 구현 완료
- parsing:
  - `Docling` 설치 및 primary parser 연결 완료
  - PDF는 `PyMuPDF`, DOCX는 `python-docx` fallback 유지
  - DOC는 `antiword` 기반 fallback parser 구현 완료
  - XLS/XLSX는 `openpyxl`, `xlrd` 기반 fallback parser 구현 완료
  - DOCX table, header/footer 추출 포함
  - parser selection 구조 추가 완료
  - 현재 기본값은 `Legacy auto + Extension default parser`
  - parse 실패 상태와 parser 시도/실패 이유를 metadata 및 system log 기준으로 추적 가능
  - `POST /parse/quality`에 PDF garbled text heuristic 감지 추가 완료
  - quality warning reason과 PDF 세부 지표를 `GET /pipeline/files`로 노출 완료
- chunking/indexing/retrieval:
  - chunk target length `800`, overlap `120`
  - chunk metadata 저장 구현 완료
  - Chroma 기반 vector index 구현 완료
  - Azure OpenAI 기반 실제 embedding 연결 완료
  - embedding provider별 collection 분리 및 전체 재인덱싱 API 추가 완료
  - retrieval candidate 확장 + lexical rerank 보정 추가 완료
  - `/chat` query preprocessing에 `question_type` / `document_hint` 기반 search query expansion 추가 완료
  - query routing 규칙을 `backend/app/query_routing.py`로 분리 완료
  - retrieval context만 사용하는 answer prompt 흐름 추가 완료
  - Azure OpenAI chat deployment `gpt-4o` 사용 가능 확인 완료
  - 조건부 항목을 공통 항목처럼 말하지 않도록 answer prompt 보정 완료
- 검증:
  - RAG 서버 backend `127.0.0.1:8000/health` 응답 확인 완료
  - RAG 서버 frontend `127.0.0.1:3000/upload`, `/chat` 응답 확인 완료
  - 2026-04-08 기준 RAG 서버 frontend `127.0.0.1:3000/upload` 응답 `200` 재확인 완료
  - 2026-04-08 기준 RAG 서버 backend `127.0.0.1:8000/health` 응답 `200` 재확인 완료
  - `GET /parse/parsers`에서 `Docling`, `DOC parser`, `Excel parser` 사용 가능 상태 확인 완료
  - 2026-04-03 기준 RAG 서버 `GET /parse/parsers`에서 `Docling(md)` 노출 확인 완료
  - 2026-04-03 기준 RAG 서버 `Docling(md)` parse 실행 시 `markdown_path` 반환 확인 완료
  - 2026-04-03 기준 RAG 서버 `/chat`에서 blank endpoint 요청 시 `rag_endpoint=internal:/retrieve` 응답 확인 완료
  - 2026-04-03 기준 현재 서버와 RAG 서버의 핵심 소스/문서 해시 일치 확인 완료
  - sample `DOC` 파일은 `doc-parser`로 파싱 검증 완료
  - sample `XLSX` 파일은 `docling` 및 `excel-parser` 둘 다 파싱 검증 완료
  - sample `DOCX` 파일은 `docling` 직접 파싱 검증 완료
  - 2026-03-28 기준 RAG 서버 frontend/backend 재기동 및 `3000/8000` 응답 재확인 완료
  - 2026-03-28 기준 RAG 서버 backend가 `azure_openai / text-embedding-3-small`로 기동됨을 `/health`에서 확인 완료
  - 2026-03-28 기준 RAG 서버 `POST /index/rebuild`로 Azure embedding 전체 재인덱싱 완료
  - 2026-03-28 기준 Azure embedding collection에서 retrieval 응답 확인 완료
  - 2026-03-29 기준 RAG 서버 frontend stale `.next` 제거 후 최신 UI 반영 재확인 완료
  - 2026-03-29 기준 RAG 서버 `GET /pipeline/files`와 `GET /index/files`가 모두 빈 상태가 되도록 테스트 데이터 초기화 완료
  - 2026-03-30 기준 local backend `py_compile`, frontend `npm run build` 검증 완료
  - 2026-03-30 기준 Azure OpenAI chat deployment `gpt-4o` 실제 응답 확인 완료
  - 2026-03-30 기준 `/chat` 실질문 answer/citation 응답 확인 완료
  - 2026-03-30 기준 frontend stale `3000` 프로세스 및 `.next` 캐시 정리 후 최신 chat UI 반영 확인 완료
  - 2026-04-03 기준 local backend에 `Input + Rewrite` 구조화 반영 완료
  - 2026-04-06 기준 RAG 서버 backend `127.0.0.1:8000/health`, frontend `127.0.0.1:3000/upload`, `/chat` 재확인 완료
  - 2026-04-07 기준 RAG 서버 `/chat`에서 `Search API endpoint`, `Lookup API endpoint` 노출 및 `Target file` 비노출 확인 완료
  - 2026-04-07 기준 RAG 서버 `default-files`로 대표 문서 3건을 다시 업로드하고 `chunk_count=103` 상태까지 복구 완료
  - 2026-04-09 기준 GitHub `main`, 현재 서버, RAG 서버 핵심 소스/문서 해시 재일치 확인 완료

## 4. 현재 동작 기준
- frontend 실행 기준:
  - RAG 서버 `127.0.0.1:3000`
- backend 실행 기준:
  - RAG 서버 `127.0.0.1:8000`
- 로그 확인 기준:
  - backend system log: RAG 서버 `/home/ubuntu/rag-mvp/backend/logs/app.log`
  - backend runtime log: RAG 서버 `/home/ubuntu/rag-mvp/run-logs/backend.out`
  - frontend runtime log: RAG 서버 `/home/ubuntu/rag-mvp/run-logs/frontend.out`
- 화면 테스트 기준:
  - 브라우저 확인과 UI 테스트는 RAG 서버에서만 수행한다.
  - 현재 서버에서는 CLI 작업만 수행하고 화면 테스트는 하지 않는다.
- 주의:
  - `127.0.0.1:3001`은 현재 작업 기준 프런트가 아니다.
  - 브라우저에서 화면 확인 시 반드시 `3000` 포트를 기준으로 본다.
  - 현재 frontend는 `next dev`보다 `build + start` 방식이 더 안정적이다.
  - 현재 서버에는 소스만 유지하고 실제 실행과 화면 확인은 RAG 서버에서만 한다.
  - 프로젝트 전체를 `rsync --delete`로 동기화하면 RAG 서버의 `backend/data/uploads`, `parse-metadata` 같은 런타임 데이터도 현재 서버 상태로 덮일 수 있다.
  - 장애 확인 시 먼저 backend system log를 보고, 그다음 frontend/backend runtime log를 확인한다.

## 4.1 2026-04-07 복구 메모
- RAG 서버 `Upload` 화면의 `files/chunks=0`은 UI 버그가 아니라, 현재 서버의 빈 `uploads` 상태가 `rsync --delete`로 서버에도 반영된 결과였다.
- 복구 방식은 `default-files`에서 대표 문서 3건을 다시 업로드하고 `chunk`를 재생성하는 방식으로 진행했다.
- 현재 복구 후 상태:
  - `files = 3`
  - `chunk_count = 103`
  - `parse_status = completed`
  - `chunk_status = completed`
  - `index_status = pending`
  - `indexed chunks = 0`
- 마지막 두 항목은 Azure embedding firewall `403` 영향으로 남아 있으며, 현재 구조상 정상적인 표시다.
- `/chat`은 index가 비어 있어도 내부 lexical fallback 경로로 최소 검색은 가능하도록 보정돼 있다.

## 5. retrieval 현재 상태
- 대표 질문 기준으로:
  - `계약관계자변경.docx` 질문군은 pass
  - 약관 PDF 질문군은 pass
  - 산출방법서 PDF 질문군은 전체 파일 검색에서 fail이 남아 있음
- 판단:
  - 2026-04-06 기준 약관 PDF를 다시 인덱싱 세트에 복구했고 duplicate `300233_test.docx`는 제거했다.
  - 산출방법서는 파일 단독 검색에서는 hit 되므로 indexing 누락 문제는 아니다.
  - 현재 남은 핵심 병목은 산출방법서 질문을 약관/일반 약관 용어와 분리하는 query routing과 retrieval 가중치다.
  - 기존 핵심 병목이었던 `hash embedding` 한계는 제거했다.
  - 2026-03-29 기준 테스트 데이터는 다시 비워 둔 상태다.
  - 이제 남은 검증 포인트는 retrieval 질문 세트 기준 실제 품질 비교와 parser 영향 재확인, answer 품질 기록, 산출방법서 계열 chunk 전략 보정이다.

## 6. parser 현재 상태
- UI에서 선택 가능:
  - primary parser: `Legacy auto`, `Docling`, `Docling(md)`
  - second parser: `Extension default`, `PyMuPDF`, `python-docx`, `DOC parser`, `Excel parser`
- 실제 동작:
  - `Legacy auto`가 현재 기본 primary parser다.
  - `Docling`은 현재 환경에 설치되어 있고 비교 검증용 primary parser로 선택할 수 있다.
  - `Docling(md)`는 fallback 없이 Docling만 사용하고, parse 성공 시 Markdown 파일을 저장한다.
  - `DOCX`와 `XLSX`는 `Docling` 직접 파싱 검증을 끝냈다.
  - `DOC`는 `Docling` 대상이 아니므로 `antiword` fallback parser가 사용된다.
  - `PDF`는 `Docling` 사용 가능 상태지만 문서별 속도/품질 비교는 추가 검증이 필요하다.
  - 같은 파일을 여러 번 업로드하면 `stored_name` 기준으로 별도 행이 누적된다.
  - `Last failure` 표시는 현재 성공 상태와 별개로 과거 parse 실패 이력을 로그 기준으로 함께 노출한다.
  - parse preview와 quality 결과는 `pipeline/files` 메타데이터 기준으로 파일 행에 함께 표시한다.
  - `Docling(md)` 성공 시 `markdown_path`가 `pipeline/files`와 upload list에 함께 노출된다.
  - `Parse test`를 다시 성공시키면 해당 `stored_name`의 최신 parse 결과는 성공 기준으로 덮어써지고, `chunk`를 다시 실행하지 않으면 `chunk_status`는 `pending`으로 남을 수 있다.
- 남은 점검:
  - `PDF`에서 `Docling`과 `PyMuPDF` 결과 비교 보강
  - parser 변경이 chunking/retrieval에 주는 영향 비교
  - `Uploaded file list`에서 latest parse 상태와 success/failure history를 함께 보여주는 최종 UI 검증
  - 산출방법서 계열 표/수식 문서에 맞는 chunk 전략 검토
  - PDF heuristic 경고의 과탐/미탐 여부 실문서 검증

## 6.1 2026-04-01 PDF parser 비교 메모
- 샘플:
  - `약관_(무)신한유니버설종신보험_080312.pdf`
  - `산출방법서_신한큐브종합건강상해보험(무배당, 해약환급금 미지급형)_230404_v2.pdf`
- `PyMuPDF`:
  - 두 샘플 모두 즉시 추출 완료
  - 약관 PDF는 `parsed/reference length ratio = 1.0`, `jaccard = 1.0`, heuristic warning 없음
  - 산출방법서 PDF는 초기 heuristic에서 `suspicious symbol ratio` 때문에 warning이 났지만, `reference suspicious ratio delta` 기준 추가 후 warning이 해소됨
- `Docling`:
  - RAG 서버에서 import와 converter 초기화는 성공
  - 그러나 두 샘플 PDF 모두 `timeout 30` 안에 변환이 끝나지 않았음
- 해석:
  - 현재 운영 관점에서는 PDF 기본 parser를 `PyMuPDF` 쪽으로 두는 편이 안정적이다.
  - 현재 garbled text heuristic은 `reference 대비 기호 비율 차이`까지 봐야 수식형 PDF 과탐을 줄일 수 있다.
  - parser catalog 기본값도 `Legacy auto`로 바꿔 PDF는 `PyMuPDF` 우선 흐름으로 정리했다.
  - 다만 `PyMuPDF`와 reference extractor가 같은 방식으로 깨질 경우 false negative가 날 수 있다.

## 7. 남은 핵심 작업
- 1차 우선순위:
  - 치조골 이식/수술특약/판결 케이스의 query rewrite 규칙 보강
  - RAG 서버 브라우저에서 Query Rewrite LLM 선택 UI, `LLM Question`, 단계별 응답시간, 외부 Search API 결과 표시 육안 확인
  - Query Rewrite LLM 기본값 `gpt-4o-mini` 기준 브라우저 동작 확인
  - `docs/chat_plan.md` Step 7 Need More Context 분기와 Step 8 Lookup API 호출 연결 방식 정리
  - 외부 RAG contract 확정 전까지 `/chat` question / answer / citation shell 유지
  - 정식 외부 Search API contract 확정 시 `/api/search` 임시 adapter request/response mapping 재정리
- retrieval 질문 세트 기준 `/chat` answer generation 품질 및 citation 품질 기록
- internal retrieval 기준 `rerank_score` / `matched_queries`를 활용한 retrieval trace 점검은 가능해졌고, 다음은 실제 answer/citation 품질 기록 보강이다
- parser 후속 우선순위:
  - `Docling` PDF 변환 장시간 실행 원인을 확인
  - garbled detection false negative를 줄이기 위한 문자군 규칙 또는 별도 기준 추가
  - `Uploaded file list` parse success/failure history UI 최종 화면 검증
- 2차 우선순위:
  - parser별 품질 비교 기준 정리
  - `Docling` vs fallback parser 비교 결과를 문서화
- 3차 우선순위:
  - 답변에 표시할 source / chunk reference / section_header / page_number 형식 고정
  - evaluation dataset 초안 작성 및 `/evaluation` 실제 결과 화면 연결

## 8. 이슈 및 메모
- `Docling` 설치 시 모델/torch 의존성 때문에 설치 시간이 길고 용량 사용량이 크다.
- `DOC` 파서는 `antiword` 시스템 패키지에 의존한다.
- Excel 샘플은 `openpyxl` 경고가 한 번 출력됐지만 파싱 결과는 정상적으로 생성됐다.
- GitHub push는 SSH 443 경로로 전환해 정상 동작하는 상태다.
- 2026-04-06 기준 핵심 소스 파일 해시는 현재 서버와 RAG 서버가 일치한다.
- 현재 Git commit 기준으로는 로컬/GitHub와 RAG 서버가 다를 수 있으므로, 서버 동기화 판단은 파일 내용 기준으로 본다.
- backend는 request 시작/종료, upload/parse/chunk/index 시작/완료, parser attempt/failure reason을 system log에 남긴다.
- upload 화면 실패 시 UI에 실패 단계와 backend system log 경로를 함께 표시한다.
- 중복 파일명 문서가 여러 건 있을 때 최신 항목과 과거 항목이 섞여 보여 사용자 혼동이 발생할 수 있다.
- parse 성공/실패 history를 한 행에서 함께 보여주기 위한 backend/frontend 수정은 진행했지만, RAG 서버 화면 기준 최종 검증은 다음 세션에서 다시 확인이 필요하다.
- frontend 반영이 안 보일 때는 stale `3000` 프로세스나 `.next` 캐시가 원인일 수 있다.
- frontend `next start` 실패 시 `.next` production build 부재 여부를 먼저 확인하고, 필요하면 `npm run build` 후 재기동한다.
- 2026-04-03 기준 `backend/app/main.py`, `frontend/app/upload/page.tsx`, `frontend/app/chat/page.tsx`, `frontend/app/globals.css`, `README.md`, `TODO.md`, `docs/*.md` 주요 파일은 현재 서버와 RAG 서버 해시가 일치한다.
- `DELETE /index/files`는 현재 환경에서 sqlite readonly 오류가 날 수 있어, stale backend PID를 함께 점검해야 한다.
- 현재 chat deployment는 `gpt-4o`로 확인됐고, answer 품질 검증이 다음 단계다.
- `계약자 변경을 위한 서류를 알려줘` 질문에서는 grounded answer가 동작했지만, 조건부 서류와 공통 서류를 섞어 말하는 경향이 있어 prompt 보정을 반영했다.
- `(무)종신보험표준형_20210101_산출방법서.doc`는 현재 `chunk_count=7`, `target_length=800`, `overlap=120` 기준으로 잘리고 있고, 표/수식 블록 보존이 약한 편이다.
- upload 단계에서 확장자뿐 아니라 파일 시그니처와 OOXML 내부 구조 기준으로 실제 형식을 검증하도록 강화했다.
- 내일 parser 고도화는 여기서 이어간다:
  - 1단계 완료: 확장자 + 시그니처 + OOXML 내부 구조 기준 타입 판별 강화
  - 2단계 완료: PDF garbled text 감지 기준 추가
  - 3단계 진행중: `Docling` / `PyMuPDF` / reference-style 추출 품질 비교
  - 4단계 완료: parser 품질 경고를 upload 화면 구조에 노출
  - 5단계 완료: 기본 parser 정책을 `Legacy auto / PyMuPDF 우선`으로 조정

## 9. 다음 세션 시작 순서
1. `AGENTS.md` 확인
2. `README.md` 확인
3. `docs/plan.md` 확인
4. `docs/chat_plan.md` 확인
5. `TODO.md` 확인
6. `docs/status.md` 확인
7. 관련 `docs/*.md` 확인
8. 최신 `docs/daily/*` 확인
9. RAG 서버 UI 확인 전 frontend build 유무와 `3000/8000` runtime 상태 확인
10. 치조골 이식/수술특약/판결 테스트 대화로 현재 `rewritten_query`와 검색 결과를 재현
11. `docs/query-rewrite-spec.md`와 backend rewrite prompt/validation 규칙 보강
12. RAG 서버 브라우저에서 Query Rewrite LLM 선택 UI, 단계별 응답시간, 외부 Search API 결과 표시 확인
13. 이후 retrieval 질문 세트 기준 retrieval/answer/citation 품질 확인
