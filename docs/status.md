# Current Status

## 1. 목적
- 현재 프로젝트의 실제 구현 상태와 남은 작업을 한 문서에서 확인한다.
- 다음 세션에서 바로 이어서 작업할 수 있도록 우선순위를 명확히 남긴다.

## 2. 현재 목표
- 보험 문서를 업로드하고 문서 근거 기반으로 답변하는 RAG MVP를 완성한다.
- 현재는 `upload -> parse -> chunk -> index -> retrieve`까지 최소 흐름을 붙였고, 다음 핵심 작업은 retrieval 품질 개선과 answer generation 연결이다.

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
  - `/upload`에서 `Primary parser`, `Auxiliary parser` 선택 가능
  - 업로드 대상 확장자를 `PDF`, `DOC`, `DOCX`, `XLS`, `XLSX`까지 확장 완료
  - `/chat`에서 index된 파일 대상 retrieval 테스트 가능
- backend:
  - upload API 구현 완료
  - parse API 및 parse quality API 구현 완료
  - chunk API 구현 완료
  - index API 및 indexed file list API 구현 완료
  - retrieve API 구현 완료
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
- chunking/indexing/retrieval:
  - chunk target length `800`, overlap `120`
  - chunk metadata 저장 구현 완료
  - Chroma 기반 vector index 구현 완료
  - hash 기반 임시 embedding 구현 완료
  - retrieval candidate 확장 + lexical rerank 보정 추가 완료
- 검증:
  - RAG 서버 backend `127.0.0.1:8000/health` 응답 확인 완료
  - RAG 서버 frontend `127.0.0.1:3000/upload`, `/chat` 응답 확인 완료
  - `GET /parse/parsers`에서 `Docling`, `DOC parser`, `Excel parser` 사용 가능 상태 확인 완료
  - sample `DOC` 파일은 `doc-parser`로 파싱 검증 완료
  - sample `XLSX` 파일은 `docling` 및 `excel-parser` 둘 다 파싱 검증 완료
  - sample `DOCX` 파일은 `docling` 직접 파싱 검증 완료

## 4. 현재 동작 기준
- frontend 실행 기준:
  - RAG 서버 `127.0.0.1:3000`
- backend 실행 기준:
  - RAG 서버 `127.0.0.1:8000`
- 주의:
  - `127.0.0.1:3001`은 현재 작업 기준 프런트가 아니다.
  - 브라우저에서 화면 확인 시 반드시 `3000` 포트를 기준으로 본다.
  - 현재 frontend는 `next dev`보다 `build + start` 방식이 더 안정적이다.

## 5. retrieval 현재 상태
- 대표 질문 기준으로:
  - `계약관계자변경.docx` 질문군은 pass
  - 약관 PDF 질문군은 pass
  - 산출방법서 PDF 질문군은 전체 파일 검색에서 fail이 남아 있음
- 판단:
  - 산출방법서는 파일 단독 검색에서는 hit 되므로 indexing 누락 문제는 아니다.
  - 현재 병목은 `hash embedding` 한계와 전역 ranking 품질이다.
  - lexical rerank는 일부 개선만 가능했고 근본 해결은 아니다.

## 6. parser 현재 상태
- UI에서 선택 가능:
  - primary parser: `Docling`
  - auxiliary parser: `Extension default`, `PyMuPDF`, `python-docx`, `DOC parser`, `Excel parser`
- 실제 동작:
  - `Docling`은 현재 환경에 설치되어 있고 primary parser로 동작한다.
  - `DOCX`와 `XLSX`는 `Docling` 직접 파싱 검증을 끝냈다.
  - `DOC`는 `Docling` 대상이 아니므로 `antiword` fallback parser가 사용된다.
  - `PDF`는 `Docling` 사용 가능 상태지만 문서별 속도/품질 비교는 추가 검증이 필요하다.
- 남은 점검:
  - `PDF`에서 `Docling`과 `PyMuPDF` 결과 비교
  - parser 변경이 chunking/retrieval에 주는 영향 비교

## 7. 남은 핵심 작업
- 1차 우선순위:
  - parser별 품질 비교 기준 정리
  - `Docling` vs fallback parser 비교 결과를 문서화
  - parser 변경 후 chunk/retrieval 재검증
- 2차 우선순위:
  - 실제 embedding 모델 교체 방식 결정 및 적용
  - 기존 Chroma 데이터 재인덱싱 절차 정리
  - retrieval 질문 세트 기준 재검증
- 3차 우선순위:
  - answer generation 연결
  - 답변에 표시할 source / chunk reference / section_header / page_number 형식 고정
  - evaluation dataset 초안 작성 및 `/evaluation` 실제 결과 화면 연결

## 8. 이슈 및 메모
- `Docling` 설치 시 모델/torch 의존성 때문에 설치 시간이 길고 용량 사용량이 크다.
- `DOC` 파서는 `antiword` 시스템 패키지에 의존한다.
- Excel 샘플은 `openpyxl` 경고가 한 번 출력됐지만 파싱 결과는 정상적으로 생성됐다.
- GitHub push는 SSH 443 경로로 전환해 정상 동작하는 상태다.
- 현재 기준 실제 작업본은 RAG 서버와 GitHub에 반영되어 있다.

## 9. 다음 세션 시작 순서
1. `docs/daily/2026-03-27.md` 확인
2. `docs/status.md` 확인
3. parser 품질 비교 범위 확정
4. `PDF` 기준 `Docling` vs `PyMuPDF` 비교 또는 parser 영향 기반 retrieval 재검증 진행
