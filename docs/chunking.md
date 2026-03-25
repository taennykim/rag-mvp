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
  - `chunk_index`: 파일 내 chunk 순서를 식별한다.
  - `source`: 검색 결과에 원본 파일명 또는 출처를 표시한다.
  - `text`: embedding 생성과 retrieval 대상이 되는 본문이다.
  - `text_length`: chunk 길이 분포 확인과 분할 품질 점검에 사용한다.
  - `start_char`: 원문 내 시작 위치를 추적한다.
  - `end_char`: 원문 내 종료 위치를 추적한다.
  - `page_number`: PDF parsing 등에서 페이지 정보를 추출한 경우 근거 위치를 표시한다.
  - `section_header`: chunk가 속한 상위 조문 번호 또는 제목을 저장해 문맥 이해를 돕는다.
  - `preview`: UI나 로그에서 chunk 내용을 짧게 미리 확인한다.
- 파일별 chunk count 저장:
  - `backend/data/chunk-metadata/{stored_name}.json`

## 3. 현재 상태
- 진행중
- 최소 chunking API 구현 완료
- uploaded file 기준 chunk count 및 chunk list 응답 검증 완료

## 4. 이슈 및 문제
- 현재 chunking은 문자 길이 기준의 단순 규칙 기반이다.
- `page_number`, `section_header`는 parsing 결과에 구조 정보가 있을 때만 채울 수 있다.
- 문서 형식에 따라 일부 metadata는 `null` 또는 빈 값일 수 있다.
- chunk text 자체는 파일에 저장하지 않고 응답으로만 반환한다.

## 5. 다음 작업
- chunk metadata를 indexing 입력 스키마에 맞춘다.
- Chroma 저장 구조를 정한다.
- chunk embedding 생성 및 indexing API를 구현한다.

## 6. 보험 도메인 특화 지침
### 6.1 조문 체계 보존 (Hierarchy Awareness)
지침: 보험 약관의 '장-절-관-조' 체계가 청킹 시 파편화되지 않도록 관리한다.
세부 내용:
가급적 하나의 청크 안에 **'제N조(제목)'**가 온전히 포함되도록 분할한다.
조문이 너무 길어 target length(800)를 초과하여 분할될 경우, 후속 청크의 메타데이터(section_header)에 해당 조문 번호를 복제하여 문맥을 유지한다.
### 6.2 표(Table) 데이터 처리 원칙
지침: 보험금 지급표, 가입대상 제외 업종표 등 표 형태의 데이터가 청킹으로 인해 의미가 유실되지 않게 한다.
세부 내용:
표 내부의 행(Row)이 잘려 숫자의 의미를 알 수 없게 되는 것을 방지하기 위해, 표 시작과 끝을 감지하여 가급적 하나의 청크로 묶는다.
표가 너무 클 경우, 행 단위로 나누되 표의 헤더(컬럼명) 정보를 각 청크에 반복 삽입하는 방식을 검토한다.
### 6.3 고유 용어 및 정의(Definitions) 관리
지침: 약관에서 정의하는 고유 용어(예: '피보험자', '보험수익자')가 포함된 정의 절은 독립적인 청크로 품질을 유지한다.
세부 내용: 용어 정의가 포함된 청크는 검색 시 가중치를 부여하거나, 다른 청크와 결합하여 답변 생성 시 용어 혼동을 방지한다.
### 6.4 면책 및 제한 사항(Exclusions) 강조
지침: '보상하지 않는 손해'와 같은 민감한 정보는 청킹 시 문장이 생략되거나 왜곡되지 않도록 검증한다.
세부 내용: 면책 조항은 질문에 대해 "보장되지 않는다"는 답변의 핵심 근거가 되므로, 텍스트 누락 여부를 엄격히 체크한다.
