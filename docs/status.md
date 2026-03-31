# Current Status

## 1. 목적
- 현재 프로젝트의 실제 구현 상태와 남은 작업을 한 문서에서 확인한다.
- 다음 세션에서 바로 이어서 작업할 수 있도록 우선순위를 명확히 남긴다.

## 2. 현재 목표
- 보험 문서를 업로드하고 문서 근거 기반으로 답변하는 RAG MVP를 완성한다.
- 현재는 `upload -> parse -> chunk -> index -> retrieve`와 `/chat` answer/citation UI까지 연결했고, chat deployment `gpt-4o` 실응답까지 확인했다.
- 다음 핵심 작업은 retrieval 질문 세트 기준 answer/citation 품질 검증과 표/수식형 문서 chunk 전략 보정이다.

## 3. 완료된 범위
- 문서 체계:
  - `AGENTS.md`, `README.md`, `TODO.md`, `docs/` 문서 구조 정리 완료
  - `docs/daily/` 기준 일자별 작업 기록 유지 중
- 인프라/환경:
  - Terraform으로 RAG EC2 생성 완료
  - 현재 서버에서 RAG 서버로 `ssh -p 2022` 접속 가능
  - RAG 서버에 frontend/backend 실행 환경 설치 완료
- frontend:
  - `/upload`, `/chat`, `/evaluation` 페이지 구성 완료
  - `/` -> `/upload` redirect 완료
  - `/upload`에서 파일 업로드, default file 업로드, parsing test, parsing quality check 가능
  - `/upload` 목록에서 파일별 indexing 상태와 chunk 수 표시 가능
  - upload 실패 후에도 `Uploaded file list`가 즉시 refresh되도록 수정 완료
  - `Uploaded file list`는 최신 업로드 순으로 정렬되도록 수정 완료
  - `/upload`에서 `Primary parser`, `Second parser` 선택 가능
  - upload 실패 시 실패 단계와 backend log 경로를 UI에서 확인 가능
  - `Uploaded file list`에서 `Preview` 버튼으로 parse preview 확인 가능
  - `Uploaded file list`에서 parsing quality 결과를 파일 행 기준으로 확인 가능
  - 업로드 대상 확장자를 `PDF`, `DOC`, `DOCX`, `XLS`, `XLSX`까지 확장 완료
  - `/chat`에서 index된 파일 대상 retrieval 테스트 가능
  - `/chat`에 answer panel 및 citation 카드 UI 추가 완료
  - `/chat` question 입력 기본값 제거 완료
  - header / nav / card / form control / result card 기준 UI refresh 완료
  - upload 화면 상단 stat strip 추가 완료
  - header title은 한 줄 기준으로 보이도록 조정 완료
- backend:
  - upload API 구현 완료
  - parse API 및 parse quality API 구현 완료
  - chunk API 구현 완료
  - index API 및 indexed file list API 구현 완료
  - retrieve API 구현 완료
  - `POST /chat` grounded answer API 추가 완료
  - upload 직후 자동 indexing 연결 완료
  - parser catalog API `GET /parse/parsers` 추가 완료
- parsing:
  - `Docling` 설치 및 primary parser 연결 완료
  - PDF는 `PyMuPDF`, DOCX는 `python-docx` fallback 유지
  - DOC는 `antiword` 기반 fallback parser 구현 완료
  - XLS/XLSX는 `openpyxl`, `xlrd` 기반 fallback parser 구현 완료
  - DOCX table, header/footer 추출 포함
  - parser selection 구조 추가 완료
  - 기본값은 `Docling + Extension default parser`
  - parse 실패 상태와 parser 시도/실패 이유를 metadata 및 system log 기준으로 추적 가능
- chunking/indexing/retrieval:
  - chunk target length `800`, overlap `120`
  - chunk metadata 저장 구현 완료
  - Chroma 기반 vector index 구현 완료
  - Azure OpenAI 기반 실제 embedding 연결 완료
  - embedding provider별 collection 분리 및 전체 재인덱싱 API 추가 완료
  - retrieval candidate 확장 + lexical rerank 보정 추가 완료
  - retrieval context만 사용하는 answer prompt 흐름 추가 완료
  - Azure OpenAI chat deployment `gpt-4o` 사용 가능 확인 완료
  - 조건부 항목을 공통 항목처럼 말하지 않도록 answer prompt 보정 완료
- 검증:
  - RAG 서버 backend `127.0.0.1:8000/health` 응답 확인 완료
  - RAG 서버 frontend `127.0.0.1:3000/upload`, `/chat` 응답 확인 완료
  - `GET /parse/parsers`에서 `Docling`, `DOC parser`, `Excel parser` 사용 가능 상태 확인 완료
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
  - 장애 확인 시 먼저 backend system log를 보고, 그다음 frontend/backend runtime log를 확인한다.

## 5. retrieval 현재 상태
- 대표 질문 기준으로:
  - `계약관계자변경.docx` 질문군은 pass
  - 약관 PDF 질문군은 pass
  - 산출방법서 PDF 질문군은 전체 파일 검색에서 fail이 남아 있음
- 판단:
  - 산출방법서는 파일 단독 검색에서는 hit 되므로 indexing 누락 문제는 아니다.
  - 기존 핵심 병목이었던 `hash embedding` 한계는 제거했다.
  - 2026-03-29 기준 테스트 데이터는 다시 비워 둔 상태다.
  - 이제 남은 검증 포인트는 retrieval 질문 세트 기준 실제 품질 비교와 parser 영향 재확인, answer 품질 기록, 산출방법서 계열 chunk 전략 보정이다.

## 6. parser 현재 상태
- UI에서 선택 가능:
  - primary parser: `Docling`
  - second parser: `Extension default`, `PyMuPDF`, `python-docx`, `DOC parser`, `Excel parser`
- 실제 동작:
  - `Docling`은 현재 환경에 설치되어 있고 primary parser로 동작한다.
  - `DOCX`와 `XLSX`는 `Docling` 직접 파싱 검증을 끝냈다.
  - `DOC`는 `Docling` 대상이 아니므로 `antiword` fallback parser가 사용된다.
  - `PDF`는 `Docling` 사용 가능 상태지만 문서별 속도/품질 비교는 추가 검증이 필요하다.
  - 같은 파일을 여러 번 업로드하면 `stored_name` 기준으로 별도 행이 누적된다.
  - `Last failure` 표시는 현재 성공 상태와 별개로 과거 parse 실패 이력을 로그 기준으로 함께 노출한다.
  - parse preview와 quality 결과는 `pipeline/files` 메타데이터 기준으로 파일 행에 함께 표시한다.
  - `Parse test`를 다시 성공시키면 해당 `stored_name`의 최신 parse 결과는 성공 기준으로 덮어써지고, `chunk`를 다시 실행하지 않으면 `chunk_status`는 `pending`으로 남을 수 있다.
- 남은 점검:
  - `PDF`에서 `Docling`과 `PyMuPDF` 결과 비교
  - parser 변경이 chunking/retrieval에 주는 영향 비교
  - `Uploaded file list`에서 latest parse 상태와 success/failure history를 함께 보여주는 최종 UI 검증
  - 산출방법서 계열 표/수식 문서에 맞는 chunk 전략 검토

## 7. 남은 핵심 작업
- 1차 우선순위:
  - retrieval 질문 세트 기준 `/chat` answer generation 품질 및 citation 품질 점검
  - retrieval 질문 세트 기준 Azure embedding 재검증
  - embedding 영향과 parser 영향 분리 비교
  - parser 변경 후 chunk/retrieval 재검증
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
- 현재 기준 실제 작업본은 RAG 서버와 GitHub에 반영되어 있다.
- backend는 request 시작/종료, upload/parse/chunk/index 시작/완료, parser attempt/failure reason을 system log에 남긴다.
- upload 화면 실패 시 UI에 실패 단계와 backend system log 경로를 함께 표시한다.
- 중복 파일명 문서가 여러 건 있을 때 최신 항목과 과거 항목이 섞여 보여 사용자 혼동이 발생할 수 있다.
- parse 성공/실패 history를 한 행에서 함께 보여주기 위한 backend/frontend 수정은 진행했지만, RAG 서버 화면 기준 최종 검증은 다음 세션에서 다시 확인이 필요하다.
- frontend 반영이 안 보일 때는 stale `3000` 프로세스나 `.next` 캐시가 원인일 수 있다.
- `DELETE /index/files`는 현재 환경에서 sqlite readonly 오류가 날 수 있어, stale backend PID를 함께 점검해야 한다.
- 현재 chat deployment는 `gpt-4o`로 확인됐고, answer 품질 검증이 다음 단계다.
- `계약자 변경을 위한 서류를 알려줘` 질문에서는 grounded answer가 동작했지만, 조건부 서류와 공통 서류를 섞어 말하는 경향이 있어 prompt 보정을 반영했다.
- `(무)종신보험표준형_20210101_산출방법서.doc`는 현재 `chunk_count=7`, `target_length=800`, `overlap=120` 기준으로 잘리고 있고, 표/수식 블록 보존이 약한 편이다.

## 9. 다음 세션 시작 순서
1. `AGENTS.md` 확인
2. `docs/plan.md` 확인
3. `TODO.md` 확인
4. `docs/status.md` 확인
5. 관련 `docs/*.md` 확인
6. `docs/daily/2026-03-31.md` 확인
7. retrieval 질문 세트 기준 retrieval/answer/citation 품질 확인
8. 산출방법서 계열 chunk 전략 검토
