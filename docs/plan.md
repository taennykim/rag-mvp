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
- 현재 단계: Retrieval 품질 점검 완료 / 실제 embedding 교체 준비
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
  - retrieval 질문 세트 작성 완료
  - representative retrieval 질문 기준 1차 pass/fail 점검 완료
  - retrieval lexical rerank 보정 실험 완료
- 미완료:
  - 실제 embedding 모델 교체
  - grounded answer generation
  - evaluation dataset / RAGAS / evaluation UI
- 다음 우선 작업:
  - OpenAI 기반 embedding 교체 준비
  - 기존 Chroma 인덱스 재생성 계획 정리
  - embedding 교체 후 retrieval 질문 세트 재검증
