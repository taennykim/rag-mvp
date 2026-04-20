# UI

## 1. 목적
- MVP 화면 구조와 현재 UI 구현 범위를 현재 기준으로 정리한다.

## 2. 구현 내용
- `/upload`
  - `PDF`, `DOC`, `DOCX`, `XLS`, `XLSX` 업로드
  - default file 업로드
  - `Primary parser`, `Second parser` 선택
  - `Docling(md)` 선택 시 second parser 비활성화
  - `target_length`, `overlap` chunk 설정 입력
  - 업로드된 파일 목록 표시
  - 파일별 indexing 상태, chunk 수, 업로드 시간 표시
  - 파일별 `Parse test` 실행
  - 파일별 `Preview` 확인
  - parsing quality check 실행 및 결과 표시
  - PDF garbled text 경고와 세부 이유 표시
  - `Docling(md)` 성공 시 Markdown output path 표시
  - upload + index 삭제
  - pipeline 실패 단계와 backend log 경로 표시
- `/chat`
  - 질문 입력
  - `Question` 멀티라인에 `고객:` / `상담사:` prefix를 넣으면 backend에서 상담 대화로 해석
  - `Query Rewrite LLM` 선택
  - `Answer LLM` 선택
  - Query Rewrite LLM 선택 옵션(`Default`, `GPT-5.4`, `GPT-5.4 mini`, `GPT-4.1 mini`, `GPT-4o mini`, `GPT-4o`, `Custom`)
  - Answer LLM 선택 옵션(`Default`, `GPT-5.4`, `GPT-5.4 mini`, `GPT-4.1 mini`, `GPT-4o mini`, `GPT-4o`, `Custom`)
  - 모든 LLM 호출은 `temperature=0`, `top_p=0.9`, `max_tokens=700` 기본값을 사용
  - 화면에서는 LLM 파라미터 입력 필드를 노출하지 않음
  - `LLM Question` 표시
  - `LLM Question` 실시간 stream 출력
  - `LLM Question` stream도 answer와 같은 배치 렌더링/커서 표시 적용
  - `Get response` 버튼으로 Search API 호출
  - response 표시 영역
  - response answer 실시간 stream 출력
  - stream 중 `STATUS/ANSWER` 헤더 없이 answer 본문만 누적 출력
  - stream 중에는 answer를 배치 업데이트하고, `Reference context` 렌더링을 잠시 지연해 버벅임을 줄임
  - stream flush 간격을 줄여 `LLM Question`/answer 표시 속도를 개선함
  - evidence 표시 영역(현재 화면에서는 숨김)
  - reference context 표시 영역
  - internal retrieval 기준 `rerank_score`, `distance`, `matched_queries` 표시
  - `전체 context 보기` 확장 블록 표시
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
- `/chat`은 외부 RAG 연동 스키마가 확정되기 전까지 schema-light shell로 유지한다.
- `/chat` main form은 질문, Query Rewrite LLM 선택, Answer LLM 선택, `Get response` 버튼만 노출하고 endpoint 값은 backend 고정값을 사용한다.
- `/chat` Query Rewrite LLM과 Answer LLM selector는 서로 독립적으로 동작한다.
- Query Rewrite LLM 기본값은 `gpt-4o-mini`다.
- Answer LLM 기본값은 `gpt-4o`다.
- `/chat`은 현재 Search API만 사용하고 Lookup 경로는 사용하지 않는다.
- `/chat` Question은 단일 질문뿐 아니라 `고객:` / `상담사:` 멀티라인 입력도 허용하고, backend가 이를 `conversation_context`로 정규화한다.
- `/chat` Question 바로 아래에는 최종 `rewritten_query`만 `LLM Question`으로 표시한다.
- `/chat` answer card는 최종 응답 영역, citation card는 근거 영역, context card는 참고용 context 확인용으로 나눴다.
- `/chat` Evidence 카드는 source / chunk / page 같은 citation pointer만 compact하게 보여주고, 중복 preview는 제거했다.
- `/chat` Evidence 카드는 데이터는 유지하고 화면 렌더링에서만 임시 숨김 처리했다.
- `/chat` Reference context 카드는 실제 retrieval hit 순서를 유지하며 preview, full text, `distance`, `rerank_score`, `matched_queries`를 함께 보여준다.
- `/chat` preview / citation / raw chunk 블록은 긴 텍스트가 잘리지 않도록 overflow를 정리했다.
- `/evaluation`은 라우트와 기본 페이지만 있고 실제 결과 화면은 아직 없다.
- 실제 화면 확인 기준은 RAG 서버 frontend `127.0.0.1:3000`이다.

## 4. 이슈 및 문제
- `Uploaded file list`의 parse success/failure history, preview, quality 표시 UI는 구현이 진행됐지만 최종 화면 검증이 아직 남아 있다.
- 같은 원본 파일명을 여러 번 업로드하면 서로 다른 `stored_name` 항목이 누적되어 사용자 혼동이 생길 수 있다.
- parser 옵션은 검증에는 유용하지만 실제 사용자 기본 흐름에서는 자동 정책 고정이 더 적합할 수 있다.
- 현재 기본 정책은 `Legacy auto parser`이며, `Docling`은 비교 검증 목적에서만 직접 선택하도록 정리했다.
- `Docling(md)`는 Docling만 사용해서 Markdown 산출물을 만드는 전용 옵션이다.
- 화면 테스트는 현재 서버가 아니라 RAG 서버에서만 수행해야 한다.
- PDF 품질 경고는 현재 heuristic 설명 중심이라, 사용자용 문구 단순화 여부를 추가 검토해야 한다.
- 현재 `PDF garbled text=정상`이어도 실제 preview 문자열이 깨질 수 있어 false negative 보정이 추가로 필요하다.
- 외부 RAG request/response 스키마가 아직 확정되지 않아 `/chat`의 adapter 입력 폼과 응답 매핑은 일부러 보류했다.
- `rerank_score`, `matched_queries`는 현재 internal retrieval 응답에만 안정적으로 존재하므로 외부 RAG endpoint 응답과는 형식을 다시 맞춰야 한다.
- `need_more_context`는 backend 응답에는 남아 있지만 현재 main UI에는 노출하지 않는다.

## 5. 다음 작업
- upload 화면의 parse history / preview / quality 표시를 실제 화면 기준으로 검증하고 필요 시 정리한다.
- parser별 PDF 비교 결과를 어떤 문구로 경고에 매핑할지 다듬는다.
- 외부 RAG contract가 정해지면 `/chat` adapter와 결과 매핑 UI를 그 스키마 기준으로 다시 연결한다.
- evaluation 실행 흐름이 준비되면 `/evaluation` 실제 결과 UI를 구현한다.
