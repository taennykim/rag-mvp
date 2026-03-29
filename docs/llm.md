# LLM

## 1. 목적
- retrieval 결과만 근거로 grounded answer를 생성한다.

## 2. 구현 내용
- answer generation은 retrieved context 기반으로만 수행한다.
- hallucination 방지를 위해 context 부족 시 부족하다고 답변한다.
- 답변과 함께 source 정보를 보여준다.

## 3. 현재 상태
- 진행 전
- retrieval-only answer generation 구조는 아직 연결하지 않았다.
- 다음 작업은 `/chat` 화면에 answer generation 모델을 붙이는 것이다.

## 4. 이슈 및 문제
- 사용할 생성 모델이 아직 정해지지 않았다.
- prompt 구조와 insufficient-context 처리 규칙이 아직 없다.

## 5. 다음 작업
- `/chat`에서 retrieval 결과를 answer generation 입력으로 넘긴다.
- 생성 모델 후보를 정하고 runtime config를 연결한다.
- answer prompt와 source citation 포맷을 정의한다.
- context 부족 시 답변을 보류하는 규칙을 추가한다.
