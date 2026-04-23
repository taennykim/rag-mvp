# LLM

## 1. 목적
- retrieval 결과만 근거로 grounded answer를 생성한다.

## 2. 구현 내용
- answer generation은 retrieved context 기반으로만 수행한다.
- hallucination 방지를 위해 context 부족 시 부족하다고 답변한다.
- 답변과 함께 source 정보를 보여준다.
- 현재 `/chat` UI는 외부 RAG contract 미확정 상태를 전제로, question / answer / citation 중심 shell로 유지한다.

## 3. 현재 상태
- 진행중
- backend `POST /chat`에 retrieval -> answer generation 흐름을 연결했다.
- backend `POST /chat`에 Input 정규화 + structured rewrite 단계를 추가했다.
- backend query rewrite system prompt는 `docs/query-rewrite-spec.md` 전체가 아니라 `11. LLM System Prompt` 블록만 로딩해 사용한다.
- `docs/query-rewrite-spec.md` 본문과 `11. LLM System Prompt` 블록은 함께 유지하며, 현재 runtime prompt는 그중 `11`번 블록만 사용한다.
- query rewrite / answer generation system prompt에는 `원본 질문이 한국어면 한국어로 응답한다` 규칙을 명시적으로 포함한다.
- backend answer generation user prompt는 `docs/answer-generation-spec.md` 문서를 함께 읽어 답변 기준으로 반영한다.
- backend `POST /chat`은 `conversation_context`가 비어 있어도 `Question` 멀티라인의 `고객:` / `상담사:` prefix를 파싱해 대화 입력으로 재구성할 수 있다.
- backend `POST /chat`은 rewrite 결과에 대해 Standalone Search Query 검증을 수행하고 `rewrite_source`, `validation_reasons`로 fallback trace를 함께 반환한다.
- query rewrite는 긴 상담 대화에서 마지막 고객의 실질 질문을 우선 복원하고, 통계/수치형 질의에서는 연도, 측정 대상, 지표 표현을 유지하도록 보강했다.
- 통계/수치형 질의는 `평균`, `통계`, `기준`, `연도`, `인당`, `비율`, `건수`, `금액`, `진료비`, `수술비` 같은 핵심 표현을 보존하도록 validation을 강화했다.
- 통계형 질의가 보험 보장/약관/청구 가능 여부 질문으로 drift 하면 validation failure 또는 retry 대상으로 처리한다.
- rewrite 결과는 `question_type`, `entities`, `routing_hints`를 더 안정적으로 채우며, 통계형 질의에서는 `year`, `metric`, `procedure`, `target`, `topic`, `statistics_table/statistics_report` 계열 힌트를 우선 붙인다.
- frontend `/chat`은 `Question`과 `LLM Question` 사이에서 Query Rewrite LLM을 선택할 수 있고, backend는 선택된 `query_rewrite_model`을 rewrite 호출에만 적용한다.
- Query Rewrite LLM에서 `Custom`을 선택하면 `LLM endpoint`, `LLM model name`, optional `API Key`를 입력할 수 있고, custom rewrite는 OpenAI-compatible API만 지원한다.
- frontend `/chat`은 `Answer LLM`도 선택할 수 있고, backend는 선택된 `answer_model`을 grounded answer 생성 호출에 적용한다.
- Answer LLM에서도 `Custom`을 선택하면 `LLM endpoint`, `LLM model name`, optional `API Key`를 입력할 수 있고, custom answer는 OpenAI-compatible API만 지원한다.
- Query Rewrite LLM selector 옵션은 `Default`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-4.1-mini`, `gpt-4o-mini`, `gpt-4o`, `Custom`이다.
- Answer LLM selector 옵션은 `Default`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-4.1-mini`, `gpt-4o-mini`, `gpt-4o`, `Custom`이다.
- UI에서 `gpt-5.4`, `gpt-5.4-mini`, `gpt-4.1-mini`, `gpt-4o-mini`, `gpt-4o`를 명시적으로 선택할 수 있다.
- UI에서는 모델 선택과 custom endpoint 정보만 입력받고, 모든 LLM 호출은 `temperature=0.3`, `top_p=0.9`, `max_tokens=700` 기본값을 사용한다.
- `/chat` Custom 입력 라벨은 `Custom model name`에서 `LLM model name`으로 통일했다.
- 두 selector는 서로 독립 동작이며, Query Rewrite 기본 모델은 `gpt-4o-mini`다.
- Answer 기본 모델은 UI 기본값 `gpt-4o`이며, backend에서도 `answer_model`이 비어 있고 `AZURE_OPENAI_ANSWER_DEPLOYMENT`가 없으면 `gpt-4o`를 사용한다.
- RAG 서버에서 `gpt-4.1-mini` Azure OpenAI deployment 직접 호출이 성공했음을 확인했다.
- `/chat` Search API endpoint는 backend 고정값 `http://10.160.98.123:8000/api/search`를 사용하고 화면에서는 입력받지 않는다.
- `/chat` Search API 호출 시 `top_k=30`, `final_k=10` 기준을 사용한다.
- `/chat` answer generation은 외부 Search API 응답의 최종 `results` 리스트를 context 기준으로 사용하므로, `final_k=10`이면 10개 context를 모두 조합해 답변한다.
- `/chat` Search API payload는 현재 `return_format=json`, `keyword_vector_weight=0.3`를 사용하며 `filters.document_type`, `chunk_types`, `filters.year`는 보내지 않는다.
- document type 추론은 query rewrite trace/routing hint로만 유지하고 Search API filter로는 사용하지 않는다.
- `/chat`은 answer 생성 시 `stream=true`로 SSE `delta`를 받아 `Response` 영역에 실시간으로 누적 출력할 수 있다.
- `/chat`은 query rewrite 결과도 SSE `rewrite_delta/rewrite_done`로 받아 `LLM Question` 영역에 실시간으로 표시할 수 있다.
- `/chat` SSE `delta`는 `STATUS/ANSWER` 템플릿 라인을 제외하고 `ANSWER` 본문 증분만 전달한다.
- stream 체감 품질을 위해 frontend는 delta를 배치 렌더링하고 backend는 delta 이벤트를 짧은 간격으로 묶어 전달한다.
- `LLM Question`도 answer와 같은 타이머 배치 렌더링과 커서 표시를 사용하며, frontend/backend flush 간격을 낮춰 더 빠르게 표시되도록 보정했다.
- `/chat`은 현재 Search API만 사용하고 Lookup 경로는 사용하지 않는다.
- backend는 `llm_call`, `search_api_call` 로그를 `app.log`에 남기며, endpoint/model/payload 추적은 가능하지만 API key는 기록하지 않는다.
- answer generation이 `Insufficient context`를 반환하면 Search API를 1회 재호출할 수 있고, stream 모드에서는 `재 시도 중입니다.`를 먼저 표시한다.
- 상품명/보험명 mismatch 필터는 Answer prompt 직전에만 적용되며, 업무/처리 문서의 키워드를 상품명으로 오판하지 않도록 추가 보강이 필요하다.
- backend `POST /chat`은 retrieval hit 원본과 별도로 `retrieved_chunks` 표준 포맷을 함께 반환해 이후 평가/분기 단계에서 재사용할 수 있게 정리했다.
- frontend `/chat`에 answer panel, citation slot, optional debug context 표시를 추가했다.
- `AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o` runtime config를 사용하도록 정리했다.
- RAG 서버 `/chat` 실응답을 확인했고, grounded answer와 citation 반환이 동작한다.
- 조건부 항목을 공통 항목처럼 말하지 않도록 prompt를 보정했다.
- 외부 RAG request/response schema가 정해지기 전까지 `/chat` main UI는 request tuning control 없이 유지한다.

## 4. 이슈 및 문제
- answer 품질은 아직 retrieval 질문 세트 기준으로 전반 점검하지 않았다.
- citation 형식은 현재 retrieval metadata 기반이며, 실제 답변 문장과의 표시 방식은 추가 점검이 필요하다.
- retrieval chunk가 여러 시나리오를 섞고 있으면 answer도 조건을 넓게 요약할 수 있다.
- 외부 RAG API 스키마가 미정이라 adapter 계층 입력/응답 필드는 현재 확정하지 않았다.

## 5. 다음 작업
- 외부 RAG contract 확정 전까지 `/chat` shell을 유지하고 answer/citation 레이아웃만 안정화한다.
- citation 형식과 insufficient-context 응답 톤을 다듬는다.
- 조건 분기가 많은 질문은 answer와 retrieval 원인을 분리해서 기록한다.
- answer 품질 기록은 `docs/answer-eval.md` 템플릿을 기준으로 남긴다.
- 외부 RAG contract가 정해지면 adapter 계층 request/response mapping을 붙인다.
