# Chat Plan Addendum

## 목적
기존 `chat_plan.md` / `chat_task_breakdown.md`에 대한 보완 사항을 정의한다.

추가 범위:
- GPT-4o Query Rewrite 모델 전략 명시
- rag-mvp 기준 추천 파일/디렉터리 매핑 추가

---

## Query Rewrite 모델 전략

### 채택 모델
- Query Rewrite 전용 LLM은 `GPT-4o` 사용

### 권장 설정
- model: `gpt-4o`
- temperature: `0 ~ 0.1`
- max_tokens: `64 ~ 128`

### 운영 원칙
- Query Rewrite는 Answer Generation 모델과 분리 운영
- Validation / Fallback 유지 필수

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

---

## 파일별 책임

- `chat_service.py`: 전체 pipeline orchestration
- `conversation_preprocessor.py`: 대화 normalize / 마지막 고객 발화 추출
- `query_rewriter.py`: GPT-4o Query Rewrite 호출
- `query_validator.py`: Query 검증 / fallback
- `retrieval_client.py`: Search / Lookup API 호출
- `retrieval_evaluator.py`: Lookup 필요 여부 판단
- `context_builder.py`: Search/Lookup 병합
- `answer_generator.py`: grounded answer 생성
