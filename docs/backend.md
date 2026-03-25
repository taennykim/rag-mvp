# Backend

## 1. 목적
- 업로드된 보험 문서를 backend에서 처리해 parsing부터 RAG 파이프라인까지 연결한다.

## 2. 구현 내용
- 현재 구현:
  - `POST /upload`
  - `GET /upload/files`
  - `DELETE /upload/files`
  - `GET /upload/default-files`
  - `POST /upload/default-file`
  - `GET /parse`
  - `POST /parse`
  - `GET /parse/{stored_name}`
  - `POST /parse/quality`
- parsing 방식:
  - PDF: `PyMuPDF`
  - DOCX: `python-docx`
  - DOCX 보강:
    - 문단
    - 표 셀 텍스트
    - header/footer
- parsing 품질 비교:
  - `Parse test`는 텍스트 추출 결과만 반환
  - 품질 점수는 `POST /parse/quality`에서 별도로 계산
  - reference extractor를 같은 원본 파일에서 별도로 실행
  - `Jaccard Similarity`
  - `Levenshtein Distance`
  - `Jaccard Similarity < 0.8` 이면 `파싱 품질주의`
- parsing 응답:
  - `stored_name`
  - `original_name`
  - `size_bytes`
  - `uploaded_at`
  - `file_type`
  - `text_length`
  - `preview`
  - `extracted_text`
- parsing 품질 응답:
  - `stored_name`
  - `original_name`
  - `size_bytes`
  - `uploaded_at`
  - `file_type`
  - `text_length`
  - `reference_text_length`
  - `jaccard_similarity`
  - `levenshtein_distance`
  - `quality_warning`
  - `quality_warning_message`

## 3. 현재 상태
- 진행중
- upload 기능 구현 및 검증 완료
- parsing 기능 최소 구현 및 검증 완료
- parsing 품질 점수 및 UI 검증 완료
- parse와 quality check 분리 완료
- chunking 이후 단계는 미구현

## 4. 이슈 및 문제
- parsing 결과는 아직 메모리 기준 단건 응답만 제공한다.
- `.doc`와 `.xlsx` 기본 파일은 현재 지원 대상이 아니다.
- 추출 텍스트 저장, 캐싱, 후속 chunk 연계는 아직 없다.
- quality score는 별도 reference extractor 기준 비교이며 사람 검수 대체는 아니다.

## 5. 다음 작업
- parsing 결과를 chunking 입력 구조로 넘긴다.
- chunk metadata 구조를 확정한다.
- parsing 실패 케이스별 응답을 더 세분화한다.
