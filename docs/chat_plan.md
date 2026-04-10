# Chat Plan

## 목적
보험사 상담 대화 기반의 RAG 답변 흐름을 정의한다.
이 문서는 상담 대화에서 검색용 질문을 생성하고, Search API와 Lookup API를 사용해 근거를 수집한 뒤, 해당 근거만으로 최종 답변을 생성하는 전체 구현 계획을 설명한다.

---

## 전체 처리 흐름

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

## 기본 원칙

- 외부 검증은 수행하지 않는다.
- Search API와 Lookup API를 사용해 RAG 데이터만 조회한다.
- Answer Generation LLM은 검색된 근거 내에서만 답변한다.
- 근거가 부족하면 추측하지 않고 부족함을 명시한다.
- Query Rewrite는 고객의 마지막 발화를 기준으로 생성한다.
- Query Rewrite 결과는 반드시 질문형의 완전한 문장이어야 한다.
- Query Rewrite 결과는 고객이 설명한 증상, 문제상황, 사고상황, 처리상황, 마지막 궁금증을 구체적으로 반영해야 한다.
- 개인정보는 검색문에 포함하지 않는다.
- 이미 상담사가 답변 완료한 이전 질문은 검색문에 포함하지 않는다.

---

## Step 1. 원본 상담 대화 입력 구성

### 목적
고객과 상담사의 대화 이력을 시스템이 처리할 수 있는 구조로 정리한다.

### 입력 형식

```json
{
  "conversation": [
    { "role": "customer", "text": "실손보험 청구하려고 하는데요." },
    { "role": "agent", "text": "어떤 부분이 궁금하신가요?" },
    { "role": "customer", "text": "통원 치료받은 것도 청구 가능한가요?" }
  ]
}
```

### 구현 포인트
- 대화 순서를 유지한다.
- 각 발화는 최소 `role`, `text` 를 가진다.
- 빈 발화는 제거한다.
- 공백, 줄바꿈, role 값은 normalize 한다.
- 고객의 마지막 발화를 쉽게 추출할 수 있어야 한다.
- `/chat` UI의 단일 `Question` 입력창만 사용하는 경우에도 `고객:` / `상담사:` prefix 멀티라인 입력을 `conversation_context`로 파싱할 수 있어야 한다.

---

## Step 2. LLM Query Rewrite

### 목적
원본 상담 대화를 보험 상담지식 검색에 적합한 Standalone Search Query로 변환한다.

### 채택 모델
- Query Rewrite 전용 LLM은 `GPT-4o` 사용

### 권장 설정
- model: `gpt-4o`
- temperature: `0 ~ 0.1`
- max_tokens: `64 ~ 128`

### 역할
- 고객의 마지막 발화를 기준으로 검색문을 만든다.
- 고객이 설명한 증상, 문제상황, 사고상황, 처리상황을 반영한다.
- 보험 상품명, 보험 종류, 특약명, 서비스명, 업무명을 반영한다.
- 독립적으로 검색 가능한 한 문장을 만든다.
- 반드시 질문형으로 출력한다.

### Prompt 설계 기준
- 마지막 고객 발화 기준
- 고객 의도 변경 금지
- 개인정보 제거
- 이전에 답변 완료된 문의 제외
- 설명 문구 없이 질문 한 문장만 출력
- Answer Generation 모델과 분리 운영
- Validation / Fallback 유지 필수

### Format 반영 기준
검색문은 아래 요구사항을 반드시 만족해야 한다.

> 고객이 설명한 증상이나 문제상황, 고객이 최종적으로 대화의 마지막에서 궁금해했던 내용을 구체적이게 온전한 문장의 검색문의 형태로 만들어주세요. 반드시 질문 형태여야 합니다.

### 예시

원본 대화:

```text
고객: 어제 넘어져서 손목 깁스했는데
고객: 실손보험 청구 가능한가요?
```

검색문:

```text
실손보험에서 넘어져 손목 깁스를 한 경우 치료비 보험금 청구가 가능한가요?
```

---

## Step 3. Standalone Search Query 검증

### 목적
LLM이 생성한 검색문이 Search API 입력으로 적절한지 검증한다.

### 검증 항목
- 빈 문자열이 아닌가
- 질문형 문장인가
- 너무 짧지 않은가
- 너무 길지 않은가
- 핵심 보험 키워드가 누락되지 않았는가

### 권장 규칙
- 최소 길이: 15자 이상
- 최대 길이: 150자 이하
- 질문형 종결 유지
- 대화에 있었던 핵심 보험 키워드 포함 여부 확인

### fallback
검증 실패 시 우선순위:
1. 마지막 고객 발화 사용
2. 마지막 고객 발화 + 상품/서비스명 결합
3. 재생성 1회 시도

### 현재 반영 상태
- backend `/chat` 흐름에서 검증을 수행한다.
- 검증 규칙은 최소 길이 `15`, 최대 길이 `150`, 질문형 종결, 핵심 키워드 포함 여부다.
- 검증 실패 시 `last_customer_message` -> `last_customer_message + metadata` -> LLM retry 1회 순서로 fallback 한다.

---

## Step 4. Search API 호출

### 목적
Standalone Search Query로 전체 보험 상담지식에서 관련 후보 chunk를 검색한다.

### 요청 예시

```json
{
  "query": "실손보험에서 통원 치료비도 보험금 청구가 가능한가요?",
  "top_k": 5
}
```

### 응답 예시

```json
{
  "results": [
    {
      "document_id": "doc_001",
      "chunk_id": "chunk_01",
      "score": 0.92,
      "section": "보험금 청구 가능 항목",
      "text": "실손보험은 통원 치료비에 대해서도 보장 기준 충족 시 청구할 수 있습니다."
    }
  ]
}
```

### 구현 포인트
- Search API는 항상 먼저 호출한다.
- timeout 및 empty result 처리 필요
- score 기준 정렬 확인
- top_k 제한 적용

---

## Step 5. Retrieved Candidate Chunks 표준화

### 목적
Search 결과를 이후 평가 및 답변 생성에서 재사용하기 좋은 내부 포맷으로 정리한다.

### 권장 내부 구조

```json
{
  "retrieved_chunks": [
    {
      "document_id": "doc_001",
      "chunk_id": "chunk_01",
      "score": 0.92,
      "section": "보험금 청구 가능 항목",
      "text": "실손보험은 통원 치료비에 대해서도 보장 기준 충족 시 청구할 수 있습니다."
    }
  ]
}
```

### 구현 포인트
- text trim
- score type normalize
- 중복 chunk 제거
- 동일 문서 grouping 가능하도록 구성

### 현재 반영 상태
- backend `/retrieve`와 `/chat` 응답에 `retrieved_chunks` 표준 포맷을 추가했다.
- 표준 포맷은 `document_id`, `chunk_id`, `score`, `section`, `text`, `rank`를 기본으로 포함한다.
- 내부 `hits` 응답은 유지하고, 이후 Step 6 평가는 `retrieved_chunks`를 기준으로 이어간다.

---

## Step 6. Search Result Evaluation

### 목적
Search 결과만으로 답변 가능한지, 또는 Lookup API를 통해 문맥 보강이 필요한지 판단한다.

### 판단 기준
다음 중 하나라도 해당하면 Lookup 필요 가능성이 높다.

- chunk가 너무 짧다
- 핵심 결론만 있고 조건/예외가 빠져 있다
- 동일 문서의 앞뒤 문맥이 필요하다
- 지급 조건, 면책 조건, 보장 제외, 제출서류, 처리 절차 등이 이어질 가능성이 있다
- top 결과가 같은 문서에 몰려 있다

### 1차 구현 권장 방식
초기 구현은 rule-based 로 시작한다.
이후 필요 시 evaluator LLM 또는 hybrid evaluator로 확장한다.

### 예시 규칙
- top1 text 길이
- 특정 키워드 존재 여부: `단,`, `예외`, `유의`, `조건`, `면책`, `제외`, `제출서류`
- 동일 `document_id` 집중도

---

## Step 7. Need More Context 분기

### 목적
Search 결과 평가 결과에 따라 Answer Generation LLM 또는 Lookup API로 분기한다.

### 분기 규칙
- No: Search 결과만으로 답변 생성
- Yes: Lookup API 호출 후 문맥 보강

---

## Step 8. Lookup API 호출

### 목적
Search에서 찾은 특정 문서 또는 구간의 주변 문맥을 정밀하게 조회한다.

### 사용 시점
- Search 결과는 맞지만 설명이 짧을 때
- 약관, 업무가이드, 처리절차에서 앞뒤 문맥이 필요할 때
- 예외사항, 주의사항, 제출서류, 후속 절차가 이어질 때

### 요청 예시

```json
{
  "document_id": "doc_001",
  "chunk_id": "chunk_01",
  "window": 2
}
```

또는

```json
{
  "document_id": "doc_001",
  "section_id": "claim_coverage"
}
```

### 구현 포인트
- Search top1 또는 topN 기준으로 대상 문서 선택
- Search 결과와 Lookup 결과 중복 제거
- 문서 내 순서를 유지하며 병합

---

## Step 9. Expanded Context 병합

### 목적
Search 결과와 Lookup 결과를 Answer Generation LLM이 사용할 수 있는 형태로 병합한다.

### 병합 원칙
- 중복 제거
- 문서/section/순서 유지
- 가장 관련도 높은 정보가 앞에 오도록 정렬
- 필요 시 문서별 그룹핑

---

## Step 10. Answer Generation LLM

### 목적
검색된 보험 상담지식 근거만 사용하여 최종 상담 답변을 생성한다.

### 입력
- 원본 상담 대화
- Standalone Search Query
- Search 결과
- 필요 시 Lookup 결과

### 답변 원칙
- 검색된 근거 내에서만 답변한다.
- 근거 없는 추측은 하지 않는다.
- 근거가 부족하면 부족함을 명시한다.
- 상담사 응답으로 자연스럽게 작성한다.

### 예시 응답

```text
실손보험에서는 통원 치료비도 보장 기준을 충족하면 보험금 청구가 가능합니다. 다만 보장 제외 항목이나 면책 사유에 해당하는 경우에는 지급이 제한될 수 있으므로, 구체적인 치료 내용과 청구 사유를 함께 확인해야 합니다.
```

---

## Step 11. 최종 상담 답변 후처리

### 목적
LLM 출력값을 실제 상담 화면에 표시 가능한 형태로 정리한다.

### 후처리 항목
- 공백 정리
- 중복 문장 제거
- 문장 단위 정리
- 필요 시 출처 표시용 metadata 연결

---

## 구현 순서 추천

### Phase 1. 최소 동작 버전
1. 원본 상담 대화 입력
2. Query Rewrite
3. Search API 호출
4. Search 결과 기반 Answer Generation

### Phase 2. 평가 로직 추가
1. Search Result Evaluation
2. Need More Context 분기
3. rule-based evaluator

### Phase 3. Lookup 연동
1. Lookup API 호출
2. Search + Lookup 병합
3. 확장 context 기반 답변 생성

### Phase 4. 안정화
1. Query validation / fallback
2. Search 실패 fallback
3. logging / tracing
4. eval dataset 구축
5. 품질 튜닝

---

## 모듈 분리 추천

### conversation_preprocessor
- 대화 normalize
- 마지막 고객 발화 추출

### query_rewriter
- prompt 생성
- LLM 호출
- query validation / fallback

### retrieval_client
- Search API 호출
- Lookup API 호출

### retrieval_evaluator
- Search 결과 평가
- Lookup 필요 여부 판단

### context_builder
- Search/Lookup 결과 병합
- Answer LLM 입력 context 구성

### answer_generator
- grounding prompt 구성
- 최종 답변 생성

---

## rag-mvp 기준 추천 파일/디렉터리 매핑

```text
backend/
  app/
    services/
      chat_service.py
      conversation_preprocessor.py
      query_rewriter.py
      query_validator.py
      retrieval_client.py
      retrieval_evaluator.py
      context_builder.py
      answer_generator.py
    prompts/
      query_rewrite.txt
      answer_generation.txt
    tests/
      test_query_rewriter.py
      test_query_validator.py
      test_retrieval_evaluator.py
      test_context_builder.py
      test_answer_generator.py
```

### 파일별 책임
- `chat_service.py`: 전체 pipeline orchestration
- `conversation_preprocessor.py`: 대화 normalize / 마지막 고객 발화 추출
- `query_rewriter.py`: GPT-4o Query Rewrite 호출
- `query_validator.py`: Query 검증 / fallback
- `retrieval_client.py`: Search / Lookup API 호출
- `retrieval_evaluator.py`: Lookup 필요 여부 판단
- `context_builder.py`: Search/Lookup 병합
- `answer_generator.py`: grounded answer 생성

---

## 의사코드

```python
def generate_consult_answer(conversation):
    normalized_conversation = normalize_conversation(conversation)

    query = rewrite_query(normalized_conversation)
    query = validate_or_fallback_query(query, normalized_conversation)

    search_results = search_api(query=query, top_k=5)

    if need_more_context(search_results):
        lookup_results = lookup_api(
            document_id=search_results[0]["document_id"],
            chunk_id=search_results[0]["chunk_id"],
            window=2,
        )
        context = build_context(search_results, lookup_results)
    else:
        context = build_context(search_results)

    answer = generate_answer(
        conversation=normalized_conversation,
        query=query,
        context=context,
    )

    return {
        "query": query,
        "context": context,
        "answer": answer,
    }
```

---

## 로그 및 관측 포인트

권장 로그 항목:

```json
{
  "conversation": "...",
  "rewritten_query": "...",
  "search_results": ["..."],
  "lookup_used": true,
  "final_answer": "..."
}
```

관측 포인트:
- Query Rewrite 품질
- Search Hit 품질
- Lookup 사용 빈도
- 최종 답변 grounding 여부
- 근거 부족 응답 비율

---

## 최종 정리

이 구조에서 핵심은 다음 세 가지이다.

1. 고객의 마지막 문의와 문제상황을 정확히 반영한 Query Rewrite 품질
2. Search 결과만으로 충분한지 판단하는 Evaluation 품질
3. 검색 근거 밖으로 벗어나지 않도록 제한하는 Answer Generation 품질

이 세 요소를 안정화하면 보험사 상담용 RAG Chat 품질을 단계적으로 높일 수 있다.
