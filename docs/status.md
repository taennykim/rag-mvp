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
  - 애플리케이션 skeleton 작성 완료
- 완료된 항목:
  - `AGENTS.md`, `TODO.md`, `README.md` 확인
  - `docs/plan.md`, `docs/retrieval.md`, `docs/llm.md`, `docs/ui.md`, `docs/aws.md` 작성
  - `docs/daily/2026-03-24.md` 작성
  - `infra/terraform/` 구조 생성
  - EC2 생성용 Terraform 코드 작성
  - instance name을 `c1an2testadmin001_RAC`로 반영
  - Terraform plan 재검증 완료
  - EC2 `c1an2testadmin001_RAC` 생성 완료
  - `frontend/` Next.js skeleton 생성
  - `backend/` FastAPI skeleton 생성
  - frontend `/upload`, `/chat`, `/evaluation` 페이지 skeleton 추가
  - frontend `/` -> `/upload` redirect 추가
  - frontend 공통 layout 및 global style 추가
  - backend `/health`, `/upload`, `/chat`, `/evaluation` 상태 API 추가
  - backend `requirements.txt` 작성
  - backend Python 소스 문법 확인
  - frontend `package.json` 형식 확인
- 미완료 항목:
  - frontend 의존성 설치와 실행 검증
  - backend 의존성 설치와 실행 검증
  - upload / parsing / chunking / indexing / retrieval / answer / evaluation 기능 전부

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
- frontend/backend 애플리케이션 코드가 아직 없다.
- 문서에 기록된 진행 상태와 실제 파일 상태가 완전히 일치하지 않는다.
- AWS 리소스 생성은 승인 정책상 사용자 승인 이후에만 가능하다.
- Terraform 산출물이 존재하지만 현재 환경에서 plan 내용을 안정적으로 재검증하지 못했다.
- Terraform은 샌드박스가 아닌 권한 상승 환경에서만 정상 동작했다.
- 로컬 환경에는 `pip`가 없어 backend 의존성 설치를 바로 진행할 수 없다.

## 6. 다음 작업
- 1차 우선순위:
  - 내일 시작 시 `docs/status.md`와 `docs/daily/2026-03-24.md`를 먼저 리로드한다.
  - frontend/backend 의존성 설치와 실행 검증을 완료한다.
- 2차 우선순위:
  - SSM 접속 확인을 마무리하고 구현 서버 사용 여부를 확정한다.
  - upload API와 upload UI 최소 기능 구현을 시작한다.
- 3차 우선순위:
  - parsing, chunking, indexing 순서로 backend 기능을 확장한다.
  - chat/evaluation 화면을 실제 API 흐름과 연결한다.

## 7. 추천 실행 순서
1. 문서 상태 정합성부터 맞춘다.
2. frontend/backend 의존성 설치와 실행 검증을 끝낸다.
3. SSM 접속 상태를 마무리 확인한다.
4. upload → parsing → chunking → indexing → retrieval 순서로 백엔드 기능을 붙인다.
5. 마지막에 answer generation과 evaluation UI를 연결한다.
