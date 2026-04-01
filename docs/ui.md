# UI

## 1. 목적
- MVP 화면 구조와 현재 UI 구현 범위를 현재 기준으로 정리한다.

## 2. 구현 내용
- `/upload`
  - `PDF`, `DOC`, `DOCX`, `XLS`, `XLSX` 업로드
  - default file 업로드
  - `Primary parser`, `Second parser` 선택
  - `target_length`, `overlap` chunk 설정 입력
  - 업로드된 파일 목록 표시
  - 파일별 indexing 상태, chunk 수, 업로드 시간 표시
  - 파일별 `Parse test` 실행
  - 파일별 `Preview` 확인
  - parsing quality check 실행 및 결과 표시
  - PDF garbled text 경고와 세부 이유 표시
  - upload + index 삭제
  - pipeline 실패 단계와 backend log 경로 표시
- `/chat`
  - 질문 입력
  - `Target file` 선택
  - `top_k` 선택
  - retrieval 결과 chunk와 source metadata 출력
- `/evaluation`
  - 페이지 skeleton만 존재
  - 실제 평가 결과 UI는 아직 미구현

## 3. 현재 상태
- 진행중
- `/upload`와 `/chat` 기본 UI는 구현되어 있고 RAG 서버 기준 동작 확인이 끝났다.
- `/upload`에서는 parser 선택, chunk 설정, 업로드, parse test, preview 확인, quality check, indexing 상태 확인이 가능하다.
- `/upload`의 기본 primary parser 선택값은 현재 `Legacy auto parser`다.
- `/upload` header / stat strip / card 톤을 2026-03-29 기준으로 다시 정리했다.
- `Uploaded file list`에서 `Preview` 버튼으로 parse preview를 바로 볼 수 있게 정리했다.
- `Check quality` 결과는 각 파일 행에서 바로 확인하도록 정리했다.
- PDF 품질 경고는 `Quality warning`, `PDF garbled text`, suspicious symbol ratio, length ratio 기준으로 파일 행에서 바로 본다.
- quality metric 라벨은 한글 설명 포함 형태로 표시한다.
- 하단 `Parsing test result` 패널은 preview 중심으로 단순화했다.
- `/chat`에서는 indexed file 기준 retrieval 테스트와 source 확인이 가능하다.
- `/evaluation`은 라우트와 기본 페이지만 있고 실제 결과 화면은 아직 없다.
- 실제 화면 확인 기준은 RAG 서버 frontend `127.0.0.1:3000`이다.

## 4. 이슈 및 문제
- `Uploaded file list`의 parse success/failure history, preview, quality 표시 UI는 구현이 진행됐지만 최종 화면 검증이 아직 남아 있다.
- 같은 원본 파일명을 여러 번 업로드하면 서로 다른 `stored_name` 항목이 누적되어 사용자 혼동이 생길 수 있다.
- parser 옵션은 검증에는 유용하지만 실제 사용자 기본 흐름에서는 자동 정책 고정이 더 적합할 수 있다.
- 현재 기본 정책은 `Legacy auto parser`이며, `Docling`은 비교 검증 목적에서만 직접 선택하도록 정리했다.
- 화면 테스트는 현재 서버가 아니라 RAG 서버에서만 수행해야 한다.
- PDF 품질 경고는 현재 heuristic 설명 중심이라, 사용자용 문구 단순화 여부를 추가 검토해야 한다.
- 현재 `PDF garbled text=정상`이어도 실제 preview 문자열이 깨질 수 있어 false negative 보정이 추가로 필요하다.

## 5. 다음 작업
- upload 화면의 parse history / preview / quality 표시를 실제 화면 기준으로 검증하고 필요 시 정리한다.
- parser별 PDF 비교 결과를 어떤 문구로 경고에 매핑할지 다듬는다.
- evaluation 실행 흐름이 준비되면 `/evaluation` 실제 결과 UI를 구현한다.
