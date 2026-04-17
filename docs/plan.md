# MVP Plan

## 1. 목적
- 보험 문서를 업로드하고 문서 근거 기반으로 답변하는 RAG MVP를 만든다.
- MVP 범위 안에서 빠르게 end-to-end 흐름을 완성한다.

## 2. 단계별 계획
1. 문서 구조와 작업 기록 체계 정리
2. Terraform으로 AWS 구현 서버 준비
3. Next.js 프론트엔드와 FastAPI 백엔드 초기 구성
4. PDF/DOCX 업로드와 저장
5. 텍스트 파싱과 검증
6. 문단 기반 chunking
7. Chroma 인덱싱
8. top 3 retrieval과 source 반환
9. grounded answer 생성
10. chat UI 연결
11. RAGAS 평가 데이터와 결과 UI 추가

## 3. 현재 진행 상태
- 현재 단계: external RAG contract 확정 전 `/chat` shell 정리 진행중 / PDF garbled text 감지와 parser 기본 정책 정리는 반영했고 false negative 보정이 남아 있음
- 현재 단계: backend retrieval/answer 흐름은 유지하되 frontend는 question / answer / citation 중심 shell로 단순화 완료
- 현재 단계: `/chat` Evidence / Reference context 역할을 분리했고 internal retrieval hit의 rerank trace를 UI에서 바로 확인 가능하게 정리함
- 현재 단계: `docs/chat_plan.md`에 GPT-4o query rewrite 운영 기준과 `rag-mvp` 파일 매핑을 통합했고 addendum 문서는 제거함
- 현재 단계: `docs/chat_plan.md` 순서대로 다시 진행하기로 정리했고 `Step 1` 대화 입력 정규화 / 마지막 고객 발화 추출을 backend `/chat` 흐름에 반영함
- 현재 단계: `/chat` Question 멀티라인 입력의 `고객:` / `상담사:` prefix를 backend에서 `conversation_context`로 파싱하도록 보강함
- 현재 단계: 멀티턴 상담 예시 기준 Query Rewrite가 마지막 고객 발화 중심으로 질문형 검색문을 생성하는지 1차 검증함
- 현재 단계: `Step 3` Standalone Search Query 검증을 backend `/chat` 흐름에 연결했고 질문형/길이/핵심 키워드 규칙과 fallback 순서를 반영함
- 현재 단계: `Step 4` Search API 호출 계층을 backend `/chat`에서 `execute_search_for_chat`으로 분리했고 내부/외부 검색 경로의 공통 trace를 정리함
- 현재 단계: `Step 5` Retrieved Candidate Chunks 표준화를 backend `/retrieve`, `/chat` 응답에 반영함
- 현재 단계: `Step 6` Search Result Evaluation을 rule-based evaluator로 추가했고 `need_more_context`, `evaluation_reasons`, `top_document_id` trace를 `/chat` 응답에 포함함
- 현재 단계: query rewrite 운영 기준을 `docs/query-rewrite-spec.md`로 분리했고 backend prompt가 해당 문서를 참조하도록 정리함
- 현재 단계: `/chat` main UI는 `rewritten_query`만 노출하고, 내부 Search는 `rewritten_query` 우선으로 호출/재정렬하도록 정리함
- 현재 단계: 모호한 마지막 고객 발화는 최근 고객 발화 묶음으로 보강하고, 보험 도메인 보장 축 복원 규칙과 최소 few-shot 예시를 query rewrite에 반영함
- 현재 단계: `Step 2` Query Rewrite 입력 기준, prompt 구성, JSON 파싱, fallback 경로를 backend `/chat` 흐름에서 분리 정리함
- 현재 단계: 개발자 제공 임시 Search API `/api/search`를 `/chat` 외부 검색 endpoint로 사용할 수 있도록 payload와 `results` 응답 normalization을 반영함
- 현재 단계: `/chat` 화면의 응답시간을 전체 Response time, Query rewrite time, API response time으로 세분화함
- 현재 단계: `/chat` Question과 LLM Question 사이에 Query Rewrite LLM 선택 UI를 추가하고 backend 호출 모델 선택값을 연결함
- 현재 단계: Query Rewrite LLM 기본값을 `gpt-4o-mini`로 변경함
- 현재 단계: 사용자 요청으로 특정 케이스(치조골 이식/수술특약/판결) 전용 query rewrite 규칙 보강은 적용하지 않고 원복함
- 현재 단계: `/chat` Answer LLM UI 기본값을 `Default (GPT-4o)`로 고정했고 `DEFAULT_ANSWER_MODEL`도 `gpt-4o`로 정리함
- 현재 단계: RAG 서버에서 호출 검증을 통과한 `gpt-4.1-mini`를 Query Rewrite LLM 선택지에 추가함
- 현재 단계: Query Rewrite LLM과 Answer LLM 선택 옵션을 `Default`, `GPT-4.1 mini`, `GPT-4o`, `Custom` 동일 목록으로 통일했고, 각 selector는 독립 동작으로 유지함
- 현재 단계: Query Rewrite LLM과 Answer LLM 모두 `Custom` 옵션을 지원하고, `LLM endpoint`, `LLM model name`, optional `API Key`, `Temperature`, `Top-K`, `Max Tokens`를 받아 OpenAI-compatible endpoint로 호출할 수 있게 정리함
- 현재 단계: `/chat` Custom 입력 라벨 `Custom model name`을 `LLM model name`으로 통일했고 validation/에러 문구도 동일 용어로 맞춤
- 현재 단계: `/chat` Evidence 섹션은 데이터 유지 상태로 화면에서만 숨기도록 처리함
- 현재 단계: `/chat` answer 출력은 `stream=true` 기반 SSE(`meta/delta/done`)로 실시간 렌더링하도록 반영함
- 현재 단계: `/chat` SSE `delta`는 LLM 원문(`STATUS/ANSWER`)이 아닌 `ANSWER` 본문 증분만 전달하도록 보강함
- 현재 단계: `/chat` stream 체감 개선을 위해 frontend delta 배치 렌더링(약 30fps)과 backend SSE delta 묶음 전송을 반영함
- 현재 단계: `/chat` `LLM Question`도 SSE 기반 `rewrite_delta/rewrite_done` 이벤트로 스트림 표시되도록 반영함
- 현재 단계: `/chat` `LLM Question`도 answer와 동일하게 타이머 기반 배치 렌더링 + 커서 표시로 보강했고, frontend/backend flush 간격을 낮춰 표시 속도를 추가 개선함
- 현재 단계: `/chat` 안내 문구 `Get response는 Search API만 호출합니다.`를 화면에서 제거함
- 현재 단계: answer generation user prompt가 `docs/answer-generation-spec.md`를 함께 읽어 답변 생성 기준을 반영하도록 정리함
- 현재 단계: answer generation 운영 기준을 `docs/answer-generation-spec.md`로 분리하고 backend prompt가 해당 문서를 참조하도록 정리함
- 현재 단계: `/chat` Search/Lookup endpoint는 backend 고정값으로 사용하고, UI는 Search `final_k` 입력과 `Get response`만 노출하며 Lookup 버튼은 hidden 처리함
- 현재 단계: 2026-04-08 기준 RAG 서버 frontend/backend runtime을 다시 복구했고 UI 확인 가능한 상태로 유지 중
- 현재 단계: 2026-04-17 기준 RAG 서버 backend `127.0.0.1:8000/health`, frontend `127.0.0.1:3000/upload`, `127.0.0.1:3000/chat` 응답 `200`과 `8000/3000` listen 상태를 재확인함
- 현재 단계: RAG 서버 반영 시 잘못된 동기화 경로를 수정해 실제 실행 파일 경로(`backend/app/main.py`, `frontend/app/chat/page.tsx`) 기준으로 재반영함
- 현재 단계: 브라우저 client-side exception 보고 후 RAG 서버 backend/frontend를 완전 재기동했고 `8000/3000` listen 및 핵심 endpoint 응답 `200`을 재확인함
- 완료:
  - AGENTS.md, TODO.md 확인
  - 기본 계획 및 파트 문서 작성
  - AWS 구현 서버 기준 확인
  - `infra/terraform/` Terraform 코드 작성
  - Terraform init/plan 재검증 완료
  - EC2 `c1an2testadmin001_RAG` 생성 및 접속 준비 완료
  - frontend Next.js skeleton 생성
  - backend FastAPI skeleton 생성
  - RAG 서버에 프로젝트 동기화 완료
  - RAG 서버에 Node.js 20, npm, pip3, python3.10-venv 설치 완료
  - frontend/backend 의존성 설치 및 import 검증 완료
  - upload API와 upload UI 최소 기능 구현 완료
  - frontend runtime page 응답 및 backend upload API 응답 검증 완료
  - `localhost:3001` 기준 CORS 허용 반영 완료
  - default file 목록 확인 완료
  - upload UI 정리 완료
  - PDF/DOCX parsing API 구현 완료
  - 추출 텍스트 비어 있음 검증 완료
  - parsing API 실제 응답 검증 완료
  - chunking API 구현 완료
  - chunk metadata와 chunk count 저장 구현 완료
  - indexing API 구현 완료
  - 업로드 후 자동 indexing 연결 완료
  - indexed file list 및 retrieval API 구현 완료
  - `/chat` retrieval UI 구현 완료
  - `/upload` 목록의 파일별 indexing 상태 표시 완료
  - `/upload` parser selection UI 구현 완료
  - `/upload` chunk 설정 입력 UI 추가 완료
  - backend parser catalog / fallback routing 구현 완료
  - `Docling` 설치 및 primary parser 검증 완료
  - `DOC` fallback parser 구현 완료
  - `XLS` / `XLSX` fallback parser 구현 완료
  - retrieval 질문 세트 작성 완료
  - representative retrieval 질문 기준 1차 pass/fail 점검 완료
  - retrieval lexical rerank 보정 실험 완료
  - Azure OpenAI `text-embedding-3-small` embedding 연결 완료
  - embedding provider/model 기준 collection 분리 완료
  - `POST /index/rebuild` 전체 재인덱싱 API 추가 완료
  - Azure embedding 기준 전체 재인덱싱 및 retrieval 응답 검증 완료
  - RAG 서버 frontend/backend 재기동 및 `3000/8000` 응답 확인 완료
  - RAG 서버 EC2 IMDSv2 `HttpTokens=required` 적용 및 Terraform 설정 반영 완료
  - backend `POST /chat` retrieval 기반 answer generation 경로 추가 완료
  - frontend `/chat` answer panel / citation UI 추가 완료
  - frontend `/chat`을 external RAG-ready shell 기준으로 단순화 완료
  - 2026-04-08 기준 RAG 서버 frontend `next build + next start` 재기동 및 `/upload` 응답 `200` 재확인 완료
  - 2026-04-08 기준 RAG 서버 backend `uvicorn` 재기동 및 `/health` 응답 `200` 재확인 완료
  - frontend `next start` 실패 원인이 `.next` production build 부재였음을 확인했고, 운영 재기동 절차는 `build + start` 기준으로 다시 맞춤
  - backend `/chat` query interpretation + external/internal RAG endpoint 분기 반영 완료
  - backend `/chat` Input 정규화 + structured rewrite 반영 완료
  - backend `/chat`이 `conversation_context`에서 빈 발화를 제거하고 role/content를 정규화하며 마지막 고객 발화를 추출하도록 보강 완료
  - backend `/chat` Query Rewrite를 seed query 결정, prompt 생성, 응답 파싱, fallback 결과 생성 단계로 분리 완료
  - backend `/chat`이 `conversation_context` 없이도 `Question` 멀티라인의 `고객:` / `상담사:` prefix를 대화 입력으로 파싱하도록 보강 완료
  - backend `/chat` Standalone Search Query 검증 규칙과 fallback(`last_customer_message` -> `last_customer_message + metadata` -> LLM retry 1회) 반영 완료
  - backend `/chat` Step 4 Search API 호출 계층 분리 완료
  - backend `/chat` 임시 외부 Search API `/api/search` 연동 payload와 `results` 응답 표준화 반영 완료
  - backend/frontend `/chat` 단계별 응답시간 표시 반영 완료
  - backend/frontend `/chat` Query Rewrite LLM 선택 UI 및 요청 필드 반영 완료
  - backend/frontend `/chat` Query Rewrite LLM 기본값 `gpt-4o-mini` 반영 완료
  - backend/frontend `/chat` Query Rewrite LLM 선택지 `gpt-4.1-mini` 추가 완료
  - backend/frontend `/chat` Query Rewrite LLM `Custom` 옵션과 OpenAI-compatible custom rewrite 호출 분기 반영 완료
  - backend/frontend `/chat` Answer LLM `Custom` 옵션과 OpenAI-compatible custom answer 호출 분기 반영 완료
  - backend/frontend `/chat` Search/Lookup 고정 endpoint와 Search `final_k` 반영, Lookup 버튼 hidden UI 반영 완료
  - backend `/retrieve`, `/chat`이 `retrieved_chunks` 표준 포맷(`document_id`, `chunk_id`, `score`, `section`, `text`, `rank`)을 함께 반환하도록 반영 완료
  - backend `/chat` Step 6 Search Result Evaluation rule-based 1차 구현 완료
  - frontend `/chat`에서 `LLM Question`에 `rewritten_query`만 표시하도록 정리 완료
- 미완료:
  - `Docling` / `PyMuPDF` / reference-style 비교 기록 보강
  - garbled detection false negative 보정
  - retrieval 질문 세트 기준 `/chat` answer/citation 품질 기록
  - `PDF` 기준 `Docling` vs `PyMuPDF` 품질 비교
  - evaluation dataset / RAGAS / evaluation UI
- 다음 우선 작업:
  - 고객사 custom Query Rewrite / Answer endpoint가 준비되면 실제 `LLM endpoint` / `LLM model name` / `API Key` / `Temperature` / `Top-K` / `Max Tokens` 조합으로 호출 검증을 진행한다
  - RAG 서버 브라우저에서 Query Rewrite LLM 선택 UI, 단계별 응답시간, 외부 Search API 결과 표시를 확인한다
  - RAG 서버 브라우저에서 Query Rewrite LLM / Answer LLM의 `Custom` 선택 시 조건부 입력창 노출과 validation 메시지를 확인한다
  - Query Rewrite LLM 기본값 `gpt-4o-mini` 기준 브라우저 동작을 확인한다
  - `docs/chat_plan.md` 기준 Step 7 Need More Context 분기와 Step 8 Lookup API 호출 연결 방식을 정리한다
  - parser 운영 정책은 `Legacy auto` 기본, `Docling` 비교 검증용, `Docling(md)` Markdown 산출물 생성용으로 유지한다
  - `Docling` PDF 변환 장시간 실행 원인을 추가 확인하되, 현재 PDF 기본 parser 정책은 `Legacy auto / PyMuPDF 우선`으로 유지한다
  - RAG 서버 UI 확인 전에는 먼저 frontend build 유무와 `3000/8000` runtime 상태를 다시 점검한다
  - 외부 RAG contract 확정 전까지 `/chat` answer/citation shell 화면과 문구를 먼저 안정화한다
  - `docs/answer-eval.md` 기준으로 retrieval 질문 세트의 answer/citation 품질을 기록한다
  - 외부 RAG contract가 정해지면 adapter request/response mapping을 별도로 연결한다
