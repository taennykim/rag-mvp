# Chat Task Breakdown

## 목적
`docs/chat_plan.md`에 정의된 보험사 상담용 RAG Chat 흐름을 실제 구현 작업 단위로 분해한다.
이 문서는 Codex CLI 또는 개발자가 바로 작업을 시작할 수 있도록 작업 범위, 책임, 산출물, 완료 기준을 정리한다.

---

## 전체 작업 범위

구현 대상 흐름은 아래와 같다.

```text
[원본 상담 대화]
   ↓
LLM Query Rewrite
   ↓
[Standalone Search Query 생성]
   ↓
Search API (query)
   ↓
[Retrieved Candidate Chunks]
   ↓
Search Result Evaluation
   ↓
[Need More Context?]
   ├─ No  → Answer Generation LLM
   └─ Yes → Lookup API
              ↓
         [Expanded Context]
              ↓
      Answer Generation LLM
   ↓
[최종 상담 답변]
```

---

## Task 1. Conversation Preprocessor

### 목적
원본 상담 대화를 표준 구조로 정리하고 마지막 고객 발화를 추출한다.

### 작업 범위
- conversation message normalize
- empty text 제거
- role 값 표준화 (`customer`, `agent`)
- 마지막 고객 발화 추출
- 이후 단계에서 사용할 conversation helper 제공

### 입력

```json
{
  "conversation": [
    { "role": "customer", "text": "실손보험 청구하려고 하는데요." },
    { "role": "agent", "text": "어떤 부분이 궁금하신가요?" },
    { "role": "customer", "text": "통원 치료받은 것도 청구 가능한가요?" }
  ]
}
```

### 산출물
- `normalized_conversation`
- `last_customer_message`

### 완료 기준
- 대화 순서를 유지한 normalize 가능
- 마지막 고객 발화 정확히 추출 가능
- 비정상 입력에 대한 기본 방어 처리 포함

### 예상 파일
- `backend/.../conversation_preprocessor.py`

---

## Task 2. Query Rewrite Prompt 및 Rewriter 구현

### 목적
상담 대화를 보험 상담지식 검색용 Standalone Search Query로 변환한다.

### 작업 범위
- Query Rewrite prompt 작성
- LLM 호출 래퍼 구현
- 출력 문자열 정리
- 질문 한 문장만 반환하도록 후처리

### 핵심 규칙
- 고객의 마지막 발화를 기준으로 생성
- 고객이 설명한 증상, 문제상황, 사고상황, 처리상황 반영
- 보험 상품명, 보험 종류, 특약명, 서비스명, 업무명 반영
- 반드시 질문형의 완전한 문장
- 개인정보 제거
- 이미 답변 완료된 문의 제외

### 반드시 반영할 Format

> 고객이 설명한 증상이나 문제상황, 고객이 최종적으로 대화의 마지막에서 궁금해했던 내용을 구체적이게 온전한 문장의 검색문의 형태로 만들어주세요. 반드시 질문 형태여야 합니다.

### 산출물
- `standalone_query`

### 완료 기준
- 입력 대화에 대해 검색용 질문 1문장 생성 가능
- 설명 문구, 번호, 따옴표 없이 query만 반환
- 보험 상황 문맥이 query에 반영됨

### 예상 파일
- `backend/.../query_rewriter.py`
- `backend/.../prompts/query_rewrite.txt`

---

## Task 3. Query Validation 및 Fallback 구현

### 목적
Rewrite 결과를 검증하고, 비정상 query일 경우 fallback 처리한다.

### 작업 범위
- 빈 문자열 검사
- 최소/최대 길이 검사
- 질문형 여부 검사
- 핵심 보험 키워드 누락 여부 검사
- fallback 전략 구현

### 권장 규칙
- 최소 길이: 15자 이상
- 최대 길이: 150자 이하
- 질문형 종결 유지
- 대화에 등장한 핵심 보험 키워드 포함 여부 확인

### fallback 우선순위
1. 마지막 고객 발화 사용
2. 마지막 고객 발화 + 상품/서비스명 결합
3. Rewrite 재시도 1회

### 산출물
- `validated_query`

### 완료 기준
- 비정상 query를 안전하게 대체 가능
- query 품질 최소 기준 보장

### 예상 파일
- `backend/.../query_validator.py`

---

## Task 4. Search API Client 구현

### 목적
Validated Query로 Search API를 호출하고 결과를 표준 구조로 반환한다.

### 작업 범위
- Search API request/response client 구현
- timeout 처리
- empty result 처리
- result normalize

### 요청 예시

```json
{
  "query": "실손보험에서 통원 치료비도 보험금 청구가 가능한가요?",
  "top_k": 5
}
```

### 산출물
- `search_results`

### 완료 기준
- Search API를 안정적으로 호출 가능
- 결과를 내부 공통 포맷으로 반환 가능
- 에러 처리 및 로그 포함

### 예상 파일
- `backend/.../retrieval_client.py`

---

## Task 5. Retrieved Chunk 표준화

### 목적
Search 결과를 평가 및 답변 생성에서 재사용 가능한 포맷으로 정리한다.

### 작업 범위
- `document_id`, `chunk_id`, `score`, `section`, `text` normalize
- text trim
- score type normalize
- 중복 chunk 제거
- 동일 문서 grouping 준비

### 산출물
- `retrieved_chunks`

### 완료 기준
- Search 결과가 내부 표준 포맷으로 고정됨
- 이후 evaluator/context builder가 그대로 재사용 가능

### 예상 파일
- `backend/.../retrieval_client.py`
- 또는 `backend/.../retrieval_formatter.py`

---

## Task 6. Search Result Evaluation 구현

### 목적
Search 결과만으로 답변 가능한지, Lookup이 필요한지 판단한다.

### 작업 범위
- rule-based evaluator 구현
- top1 chunk 길이 기준 평가
- 조건/예외/면책/유의사항 키워드 평가
- 동일 문서 집중도 평가

### 1차 규칙 예시
- top1 text 길이 < threshold
- `단,`, `예외`, `면책`, `제외`, `유의`, `조건`, `제출서류` 포함
- top results가 같은 document_id에 집중

### 산출물
- `need_more_context: bool`
- `evaluation_reason`

### 완료 기준
- Search 결과를 기반으로 Lookup 필요 여부를 판단 가능
- rule-based evaluator 단독 테스트 가능

### 예상 파일
- `backend/.../retrieval_evaluator.py`

---

## Task 7. Lookup API Client 구현

### 목적
Search 결과에서 유력한 문서/구간에 대해 Lookup API를 호출하여 주변 문맥을 확장한다.

### 작업 범위
- chunk 기준 Lookup 호출
- section 기준 Lookup 호출 가능 구조 준비
- Search top1 또는 topN 기준 대상 선택
- Lookup 결과 normalize

### 요청 예시

```json
{
  "document_id": "doc_001",
  "chunk_id": "chunk_01",
  "window": 2
}
```

### 산출물
- `lookup_results`

### 완료 기준
- Lookup API 호출 가능
- Search 결과와 결합 가능한 포맷으로 normalize 완료

### 예상 파일
- `backend/.../retrieval_client.py`

---

## Task 8. Context Builder 구현

### 목적
Search 결과와 Lookup 결과를 병합하여 Answer Generation LLM 입력용 context를 만든다.

### 작업 범위
- Search + Lookup 결과 병합
- 중복 제거
- 문서/section/순서 유지
- 관련도 기준 정렬
- 필요 시 문서별 grouping

### 산출물
- `final_context`

### 완료 기준
- Answer LLM에 바로 넣을 수 있는 context 구조 생성 가능
- Search only / Search + Lookup 모두 지원

### 예상 파일
- `backend/.../context_builder.py`

---

## Task 9. Answer Generation LLM 구현

### 목적
검색된 근거만 사용해 최종 상담 답변을 생성한다.

### 작업 범위
- grounded answer prompt 작성
- 원본 상담 대화 + query + context 입력 구성
- 근거 부족 시 insufficient response 처리
- 상담사 응답 스타일 유지

### 답변 원칙
- 검색 근거 내에서만 답변
- 근거 없는 추측 금지
- 부족한 경우 부족함 명시
- 자연스러운 상담 답변 형태 유지

### 산출물
- `final_answer`

### 완료 기준
- Search/Lookup context 기반 답변 생성 가능
- hallucination 억제 규칙 포함

### 예상 파일
- `backend/.../answer_generator.py`
- `backend/.../prompts/answer_generation.txt`

---

## Task 10. 최종 오케스트레이션 구현

### 목적
Conversation → Rewrite → Search → Evaluation → Lookup(optional) → Answer 전체 흐름을 하나의 서비스 로직으로 연결한다.

### 작업 범위
- 전체 pipeline orchestration 함수 구현
- 단계별 예외 처리
- 단계별 로그 연결
- 결과 payload 정의

### 산출물
- `generate_consult_answer(...)`

### 완료 기준
- 단일 진입점에서 전체 플로우 실행 가능
- query, context, answer를 함께 반환 가능

### 예상 파일
- `backend/.../chat_service.py`
- 또는 기존 chat handler/service 파일

---

## Task 11. Logging / Observability 추가

### 목적
각 단계의 품질과 실패 원인을 추적할 수 있도록 로그를 추가한다.

### 작업 범위
- rewritten query 로그
- search 결과 개수 및 top score 로그
- lookup 사용 여부 로그
- final answer 생성 결과 로그
- fallback 발생 여부 로그

### 권장 로그 예시

```json
{
  "conversation": "...",
  "rewritten_query": "...",
  "search_result_count": 5,
  "lookup_used": true,
  "final_answer": "..."
}
```

### 완료 기준
- 각 단계별 디버깅 가능
- 품질 튜닝에 필요한 핵심 로그 확보

---

## Task 12. Tests / Eval 추가

### 목적
회귀를 방지하고 Query Rewrite, Search Evaluation, Grounded Answer 품질을 검증한다.

### 작업 범위
- Query Rewrite 예시 케이스 추가
- Query Validation test 추가
- Search Result Evaluation test 추가
- Context Builder test 추가
- Answer Generation grounding test 추가

### 추천 테스트 유형
- 정상 상담 대화 → 정상 검색문 생성
- 마지막 고객 발화 반영 여부
- 보험 상품/특약명 누락 여부
- Lookup 필요/불필요 분기 테스트
- 근거 부족 답변 테스트

### 완료 기준
- 핵심 플로우 단위 테스트 또는 eval 케이스 확보
- 최소 회귀 방지 장치 마련

### 예상 파일
- `backend/tests/test_query_rewriter.py`
- `backend/tests/test_query_validator.py`
- `backend/tests/test_retrieval_evaluator.py`
- `backend/tests/test_context_builder.py`
- `backend/tests/test_answer_generator.py`

---

## 병렬 작업 추천 단위

### Workstream A. Query Pipeline
- Task 1. Conversation Preprocessor
- Task 2. Query Rewrite Prompt 및 Rewriter
- Task 3. Query Validation 및 Fallback

### Workstream B. Retrieval Pipeline
- Task 4. Search API Client
- Task 5. Retrieved Chunk 표준화
- Task 6. Search Result Evaluation
- Task 7. Lookup API Client
- Task 8. Context Builder

### Workstream C. Answer Pipeline
- Task 9. Answer Generation LLM
- Task 10. 최종 오케스트레이션
- Task 11. Logging / Observability

### Workstream D. Quality
- Task 12. Tests / Eval

---

## 추천 브랜치 예시

- `feat/chat-query-pipeline`
- `feat/chat-retrieval-pipeline`
- `feat/chat-answer-pipeline`
- `test/chat-eval-cases`

---

## Codex CLI에 바로 줄 수 있는 작업 지시 예시

### Query Pipeline
- implement conversation preprocessor for insurance consultation chat
- implement query rewrite prompt and query rewriter
- add validation and fallback for standalone search query

### Retrieval Pipeline
- implement search api client for external retrieval api
- normalize retrieved chunks into internal format
- implement rule-based need_more_context evaluator
- implement lookup api client and context merge logic

### Answer Pipeline
- implement grounded answer generation from retrieved context only
- orchestrate full chat pipeline from conversation to final answer
- add logs for rewrite, retrieval, lookup, and answer stages

### Test / Eval
- add tests for query rewrite, validation, retrieval evaluation, context builder, and grounded answer generation

---

## 최종 정리

권장 구현 순서는 다음과 같다.

1. Query Pipeline 먼저 구현
2. Search API 연동
3. Search Result Evaluation 추가
4. Lookup API 연동
5. Answer Generation 연결
6. Logging / Test 보강

이 문서를 기준으로 작업을 나누면 여러 명이 병렬로 작업하더라도 충돌을 줄이고, 단계별 품질 확인이 쉬워진다.
