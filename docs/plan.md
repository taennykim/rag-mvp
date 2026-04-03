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
- 현재 단계: retrieval 질문 세트 기준 품질 최적화 진행중 / PDF garbled text 감지와 parser 기본 정책 정리는 반영했고 false negative 보정이 남아 있음
- 현재 단계: retrieval 질문 세트 기준 품질 최적화 진행중 / parser 정책과 `/chat` RAG endpoint 분기 UI는 반영됐고 answer/citation 품질 검증이 남아 있음
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
  - backend `POST /chat` retrieval 기반 answer generation 경로 추가 완료
  - frontend `/chat` answer panel / citation UI 추가 완료
  - frontend `/chat` RAG endpoint 입력 및 internal fallback UI 반영 완료
  - backend `/chat` query interpretation + external/internal RAG endpoint 분기 반영 완료
- 미완료:
  - `Docling` / `PyMuPDF` / reference-style 비교 기록 보강
  - garbled detection false negative 보정
  - retrieval 질문 세트 기준 `/chat` answer/citation 품질 기록
  - retrieval 질문 세트 기준 Azure embedding 재검증
  - parser 영향과 embedding 영향 분리 비교
  - `PDF` 기준 `Docling` vs `PyMuPDF` 품질 비교
  - evaluation dataset / RAGAS / evaluation UI
- 다음 우선 작업:
  - parser 운영 정책은 `Legacy auto` 기본, `Docling` 비교 검증용, `Docling(md)` Markdown 산출물 생성용으로 유지한다
  - `Docling` PDF 변환 장시간 실행 원인을 추가 확인하되, 현재 PDF 기본 parser 정책은 `Legacy auto / PyMuPDF 우선`으로 유지한다
  - `Docling(md)`와 일반 `Docling`이 chunk/retrieval 품질에 주는 차이를 대표 문서 기준으로 점검한다
  - `/chat` 대표 질문 기준으로 internal RAG와 retrieval/answer/citation 품질을 먼저 기록한다
  - 이후 `docs/answer-eval.md` 기준으로 retrieval 질문 세트의 answer/citation 품질을 기록한다
