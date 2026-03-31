# LLM

## 1. 목적
- retrieval 결과만 근거로 grounded answer를 생성한다.

## 2. 구현 내용
- answer generation은 retrieved context 기반으로만 수행한다.
- hallucination 방지를 위해 context 부족 시 부족하다고 답변한다.
- 답변과 함께 source 정보를 보여준다.

## 3. 현재 상태
- 진행중
- backend `POST /chat`에 retrieval -> answer generation 흐름을 연결했다.
- frontend `/chat`에 answer panel과 citation 표시를 추가했다.
- `AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o` runtime config를 사용하도록 정리했다.
- RAG 서버 `/chat` 실응답을 확인했고, grounded answer와 citation 반환이 동작한다.
- 조건부 항목을 공통 항목처럼 말하지 않도록 prompt를 보정했다.

## 4. 이슈 및 문제
- answer 품질은 아직 retrieval 질문 세트 기준으로 전반 점검하지 않았다.
- citation 형식은 현재 retrieval metadata 기반이며, 실제 답변 문장과의 표시 방식은 추가 점검이 필요하다.
- retrieval chunk가 여러 시나리오를 섞고 있으면 answer도 조건을 넓게 요약할 수 있다.

## 5. 다음 작업
- retrieval 질문 세트 일부를 골라 answer quality를 함께 점검한다.
- citation 형식과 insufficient-context 응답 톤을 다듬는다.
- 조건 분기가 많은 질문은 answer와 retrieval 원인을 분리해서 기록한다.
- answer 품질 기록은 `docs/answer-eval.md` 템플릿을 기준으로 남긴다.
