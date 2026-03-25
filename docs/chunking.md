# Chunking

## 1. 목적
- parsing으로 추출한 텍스트를 retrieval 가능한 단위의 chunk로 나눈다.

## 2. 구현 내용
- API:
  - `GET /chunk`
  - `POST /chunk`
  - `GET /chunk/{stored_name}`
- chunk 생성 방식:
  - 줄 단위 텍스트를 기본 segment로 사용
  - 긴 segment는 문장 또는 고정 길이로 다시 분할
  - target length: `800`
  - overlap length: `120`
- chunk metadata:
  - `chunk_index`
  - `text`
  - `text_length`
  - `start_char`
  - `end_char`
  - `preview`
- 파일별 chunk count 저장:
  - `backend/data/chunk-metadata/{stored_name}.json`

## 3. 현재 상태
- 진행중
- 최소 chunking API 구현 완료
- uploaded file 기준 chunk count 및 chunk list 응답 검증 완료

## 4. 이슈 및 문제
- 현재 chunking은 문자 길이 기준의 단순 규칙 기반이다.
- section title, heading level 같은 구조 metadata는 아직 없다.
- chunk text 자체는 파일에 저장하지 않고 응답으로만 반환한다.

## 5. 다음 작업
- chunk metadata를 indexing 입력 스키마에 맞춘다.
- Chroma 저장 구조를 정한다.
- chunk embedding 생성 및 indexing API를 구현한다.
