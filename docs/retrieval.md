# Retrieval

## 1. 목적
- 질문에 대해 index된 문서 chunk를 검색하고, 근거가 되는 source metadata와 함께 상위 결과를 반환한다.

## 2. 구현 내용
- API:
  - `GET /retrieve`
  - `POST /retrieve`
- 검색 방식:
  - Chroma vector search
  - 현재는 Azure OpenAI `text-embedding-3-small` embedding 사용
  - retrieval 후보를 넓게 조회한 뒤 lexical rerank를 추가로 적용
- 기본 동작:
  - `top_k` 기준 상위 chunk 반환
  - `stored_name`이 있으면 특정 파일로 검색 범위를 제한
- retrieval 응답 필드:
  - `id`
  - `text`
  - `distance`
  - `stored_name`
  - `original_name`
  - `source`
  - `chunk_index`
  - `text_length`
  - `start_char`
  - `end_char`
  - `page_number`
  - `section_header`
  - `preview`
- frontend 연동:
  - `/chat` 페이지에서 retrieval test UI 사용 가능
  - index된 파일만 `Target file` 대상으로 선택 가능
  - `top_k`는 현재 `3`, `5`, `8` 중 선택 가능

## 3. 현재 상태
- 진행중
- retrieval API 구현 완료
- retrieval UI 구현 완료
- retrieval 질문 세트 작성 완료
- 대표 질문 기준 1차 retrieval 품질 점검 완료
- Azure OpenAI embedding 연결 및 재인덱싱 완료
- 계약관계자변경 문서와 약관 문서는 대표 질문 기준 top 1 retrieval이 정상 동작
- 산출방법서 문서는 파일 단독 검색은 가능하지만 전체 파일 대상 검색에서는 ranking 품질 이슈가 남아 있음

## 4. 이슈 및 문제
- 산출방법서처럼 표/수식/짧은 기호형 질의가 많은 문서는 전체 파일 대상 검색에서 오탐이 발생한다.
- lexical rerank를 추가했지만 개선 폭은 제한적이다.
- Azure embedding 적용 후에도 retrieval 질문 세트 기준 정량 재검증이 아직 남아 있다.

## 5. 다음 작업
- parser 변경 시 parse/chunk 품질 변화가 retrieval 결과에 미치는 영향도 같이 확인한다.
- retrieval 질문 세트 기준으로 Azure embedding 적용 후 결과를 다시 비교한다.
- 필요 시 산출방법서 문서군에 맞는 chunk 전략 보정을 추가 검토한다.
