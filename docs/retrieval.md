# Retrieval

## 1. 목적
- 질문에 대해 벡터 검색으로 관련 문서 chunk를 찾아 top 3를 반환한다.

## 2. 구현 내용
- 검색 방식: vector search only
- 반환 개수: top 3
- 응답에는 반드시 source metadata를 포함한다.
- source metadata 기본 필드:
  - file_name
  - chunk_index
  - section (optional)

## 3. 현재 상태
- 미구현

## 4. 이슈 및 문제
- Chroma 인덱스가 아직 없음
- embedding 생성 로직이 아직 없음

## 5. 다음 작업
- chunk 저장 구조를 먼저 확정한다.
- retriever 서비스와 `/chat` API 응답 구조를 설계한다.

