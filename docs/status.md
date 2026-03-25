# Current Status

## 1. 목적
- 현재 프로젝트의 실제 진행 상태를 문서 기준과 파일 기준으로 정리한다.
- 다음 단계에서 바로 수행해야 할 작업 우선순위를 명확히 한다.

## 2. 구현 내용
- 프로젝트 목표:
  - 보험 문서를 업로드하고 문서 근거 기반으로 답변하는 RAG MVP
- 목표 범위:
  - PDF/DOCX 업로드
  - 텍스트 추출
  - chunking
  - embedding + vector search
  - grounded answer
  - source citation
  - RAGAS evaluation

## 3. 현재 상태
- 전체 상태:
  - 문서화 완료
  - 인프라 준비 및 EC2 생성 완료
  - RAG 서버 개발 환경 준비 완료
  - Upload Phase 최소 구현 완료
  - Upload Phase 실행 검증 완료
  - Parsing Phase 최소 구현 완료
  - Parsing 검증 UI 및 품질 지표 추가 완료
- 완료된 항목:
  - `AGENTS.md`, `TODO.md`, `README.md` 확인
  - `docs/plan.md`, `docs/retrieval.md`, `docs/llm.md`, `docs/ui.md`, `docs/aws.md` 작성
  - `docs/daily/2026-03-24.md` 작성
  - `infra/terraform/` 구조 생성
  - EC2 생성용 Terraform 코드 작성
  - instance name을 `c1an2testadmin001_RAG`로 정정
  - Terraform 기본 instance type을 `t3.xlarge`로 정정
  - Terraform plan 재검증 완료
  - EC2 `c1an2testadmin001_RAG` 상태 반영 완료
  - `frontend/` Next.js skeleton 생성
  - `backend/` FastAPI skeleton 생성
  - frontend `/upload`, `/chat`, `/evaluation` 페이지 skeleton 추가
  - frontend `/` -> `/upload` redirect 추가
  - frontend 공통 layout 및 global style 추가
  - backend `/health`, `/upload`, `/chat`, `/evaluation` 상태 API 추가
  - backend `requirements.txt` 작성
  - backend Python 소스 문법 확인
  - frontend `package.json` 형식 확인
  - 현재 서버와 RAG 서버 간 `2022/tcp` SG-to-SG ingress/egress 허용
  - 현재 서버에서 RAG 서버로 `ssh -p 2022` 연결 확인
  - RAG 서버에 프로젝트 동기화 완료
  - RAG 서버에 `Node.js 20`, `npm`, `pip3`, `python3.10-venv` 설치 완료
  - RAG 서버에서 frontend/backend 의존성 설치 완료
  - RAG 서버에서 backend import 검증 완료
  - backend `POST /upload`, `GET /upload/files` 구현
  - backend 기본 업로드 파일 디렉토리 `backend/data/default-files` 생성
  - backend `GET /upload/default-files`, `POST /upload/default-file` 구현
  - backend 업로드 저장 경로 `backend/data/uploads` 구현
  - backend `uvicorn` 실행 및 upload endpoint 실제 호출 검증 완료
  - frontend `/upload` 페이지에 파일 선택, 업로드, 목록 조회 UI 구현
  - frontend `/upload` 페이지에 `Default file` 선택 업로드 UI 구현
  - frontend runtime page `HTTP 200` 검증 완료
  - `localhost:3001`, `127.0.0.1:3001` CORS 허용 반영 완료
  - default file API 응답과 드롭다운 대상 파일 목록 확인 완료
  - frontend `/upload` 페이지에서 default file 전용 버튼 제거
  - frontend `/upload` 페이지에서 uploaded file list 초기화 버튼 추가
  - backend `DELETE /upload/files` 구현
  - backend 업로드 파일 목록에 업로드 시간 필드 추가
  - backend `GET /parse`, `POST /parse`, `GET /parse/{stored_name}` 구현
  - backend PDF text extraction 구현
  - backend DOCX text extraction 구현
  - backend DOCX table 및 header/footer text extraction 구현
  - backend 빈 추출 텍스트 검증 구현
  - backend parse 응답에 full extracted text 추가
  - backend parse 응답에 `Jaccard Similarity`, `Levenshtein Distance` 추가
  - backend parse 응답에 `Jaccard Similarity < 0.8` 경고 플래그 추가
  - frontend `/upload` 페이지에 파일별 `Parse test` 버튼 추가
  - frontend `/upload` 페이지에 parsing test result 카드 추가
  - frontend `/upload` 페이지에서 full extracted text 및 raw JSON 확인 UI 추가
  - frontend `/upload` 페이지에서 품질 경고 문구 `파싱 품질주의` 빨간색 표시 추가
  - RAG 서버에서 PDF/DOCX parsing 함수 실제 호출 검증 완료
  - RAG 서버에서 upload 이후 parsing API 실제 호출 검증 완료
  - RAG 서버에서 DOCX parsing length가 `1087`에서 `22887`로 증가한 것 확인
  - RAG 서버에서 DOCX sample의 `Jaccard Similarity`가 약 `0.994`로 확인됨
- 미완료 항목:
  - chunking / indexing / retrieval / answer / evaluation 기능

## 4. 문서와 실제 상태 차이
- 문서상 AWS 상태:
  - `docs/aws.md`, `docs/plan.md`, `TODO.md`, daily 기준으로는 Terraform이 초안 또는 init/plan 이전 단계처럼 보인다.
- 실제 파일 기준 AWS 상태:
  - `infra/terraform/main.tf`, `variables.tf`, `outputs.tf`, `providers.tf`, `versions.tf`가 존재한다.
  - `.terraform.lock.hcl`, `tfplan`, `terraform.tfstate`, `.terraform.tfstate.lock.info`가 존재한다.
- 해석:
  - Terraform 코드는 이미 작성되었고, `terraform init` 및 `terraform plan`을 적어도 일부 수행한 흔적이 있다.
  - 다만 현재 실행 환경에서는 provider schema 로드 문제로 `terraform show tfplan` 검증은 실패했다.
  - 따라서 현재 프로젝트 상태는 "문서/설계만 완료"가 아니라 "인프라 plan 시도까지 진행"으로 보는 것이 맞다.

## 5. 이슈 및 문제
- 문서에 기록된 진행 상태와 실제 파일 상태가 완전히 일치하지 않는다.
- AWS 리소스 생성은 승인 정책상 사용자 승인 이후에만 가능하다.
- Terraform 산출물이 존재하지만 현재 환경에서 plan 내용을 안정적으로 재검증하지 못했다.
- Terraform은 샌드박스가 아닌 권한 상승 환경에서만 정상 동작했다.
- RAG 서버에는 GitHub private repo 직접 clone 인증이 없어 현재는 `rsync` 기반 동기화를 사용했다.
- frontend `next@15.2.4`는 보안 경고가 있으므로 추후 패치 버전 업그레이드가 필요하다.
- upload 검증 중 생성되는 `backend/data/uploads`와 RAG 서버의 `.venv`는 git 추적 대상이 아니다.
- quality score는 원본 기반 reference extractor와의 자동 비교이므로 최종 품질 판단에는 사람 검수가 여전히 필요하다.

## 6. 다음 작업
- 1차 우선순위:
  - chunking 함수와 metadata 구조를 구현한다.
  - parsing 결과를 chunk list로 변환하는 최소 흐름을 만든다.
- 2차 우선순위:
  - chunk list와 chunk count를 API 응답으로 확인할 수 있게 한다.
  - 파일별 chunk count 저장 방식 초안을 정한다.
- 3차 우선순위:
  - chunking, indexing 순서로 backend 기능을 확장한다.
  - chat/evaluation 화면을 실제 API 흐름과 연결한다.

## 7. 추천 실행 순서
1. 문서 상태 정합성부터 맞춘다.
2. frontend/backend 실행 검증을 끝낸다.
3. parsing → chunking → indexing → retrieval 순서로 백엔드 기능을 붙인다.
4. 마지막에 answer generation과 evaluation UI를 연결한다.
