# AWS

## 1. 목적
- RAG MVP 구현용 AWS EC2 인스턴스를 Terraform으로 생성한다.
- 실제 앱 개발과 검증은 이 구현 서버에서 수행한다.

## 2. 구현 내용
- 기준 인스턴스: `i-0279082dd48ce62d2` (`c1an2testadmin001`)
- 동일 스펙 기준:
  - instance name: `c1an2testadmin001_RAG`
  - region: `ap-northeast-2`
  - availability zone: `ap-northeast-2a`
  - instance type: `t3.xlarge`
  - AMI: `ami-09e1f7f5fee1f6d4a`
  - subnet: `subnet-0e1132f0332a1c9d7`
  - security groups:
    - `sg-0e3f1efd64bb15288`
    - `sg-071794595b7007c6e`
  - key pair: `p2an2test001`
  - IAM instance profile: `terraform-poc-iac-role`
  - root device name: `/dev/sda1`
  - root volume: `gp2`, `50GiB`
  - tags:
    - `Name`
    - `NAME`
    - `OWNER`
    - `CLASS0`
    - `CLASS1`
    - `owner`
- Terraform 파일 위치:
  - `infra/terraform/`

## 3. 현재 상태
- 기준 EC2 스펙을 바탕으로 Terraform 코드 작성 완료
- `infra/terraform/` 아래에 `main.tf`, `variables.tf`, `outputs.tf`, `providers.tf`, `versions.tf`가 존재함
- `.terraform.lock.hcl`, `tfplan`, `terraform.tfstate`가 존재함
- instance name을 `c1an2testadmin001_RAG`로 정정함
- 샌드박스에서는 provider schema 로드 문제로 `terraform plan`이 실패했지만, 권한 상승 환경에서는 plan/apply가 정상 수행됨
- 생성 결과:
  - instance id: `i-09c547c2adaefff77`
  - private ip: `10.160.98.178`
  - instance type: `t3.xlarge`
  - state: `running`
  - public ip: 없음
  - SSM agent: `Online`
  - SSH daemon: `2022/tcp` listen 확인
  - 현재 서버 `c1an2testadmin001`와의 SSH:
    - source SG와 target SG 기준으로 `2022/tcp` ingress 추가
    - source SG와 target SG 기준으로 `2022/tcp` egress 추가
    - 현재 서버에서 `ssh -p 2022 ubuntu@10.160.98.178` 성공 확인
  - RAG 서버 개발 환경:
    - 프로젝트 경로: `/home/ubuntu/rag-mvp`
    - `Node.js 20.20.1`, `npm 10.8.2` 설치
    - `pip3`, `python3.10-venv` 설치
    - `frontend/node_modules` 설치 완료
    - `backend/.venv` 생성 및 `requirements.txt` 설치 완료

## 4. 이슈 및 문제
- 보안그룹, 서브넷, IAM instance profile은 기존 리소스를 재사용하므로 계정 내 존재해야 한다.
- 태그 정책은 `AGENTS.md`의 `owner=taenny` 기준을 따라야 한다.
- Terraform AWS provider는 현재 샌드박스 실행 환경과 호환되지 않아, 실제 검증/적용은 권한 상승 환경에서 수행해야 한다.
- 퍼블릭 IP가 없으므로 직접 SSH보다 SSM 기반 접속 경로가 우선이다.
- SSM 원격 명령은 발행됐지만 즉시 완료되지는 않아 실제 셸 명령 성공 여부는 추가 확인이 필요하다.
- 인스턴스 간 통신 규칙은 CIDR보다 security group reference 기준으로 여는 것이 맞다.

## 5. 다음 작업
- RAG 서버에서 frontend/backend 실제 실행 검증
- upload 이후 parsing 단계 구현
- 필요 시 앱 실행 스크립트 또는 systemd 운영 방식 정리
