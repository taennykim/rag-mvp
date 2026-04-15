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
- backend `POST /chat`은 `conversation_context`가 비어 있어도 `Question` 멀티라인의 `고객:` / `상담사:` prefix를 파싱해 대화 입력으로 재구성할 수 있다.
- backend `POST /chat`은 rewrite 결과에 대해 Standalone Search Query 검증을 수행하고 `rewrite_source`, `validation_reasons`로 fallback trace를 함께 반환한다.
- frontend `/chat`은 `Question`과 `LLM Question` 사이에서 Query Rewrite LLM을 선택할 수 있고, backend는 선택된 `query_rewrite_model`을 rewrite 호출에만 적용한다.
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
