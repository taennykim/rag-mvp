# LLM

## 1. 목적
- retrieval 결과만 근거로 grounded answer를 생성한다.

## 2. 구현 내용
- answer generation은 retrieved context 기반으로만 수행한다.
- hallucination 방지를 위해 context 부족 시 부족하다고 답변한다.
- 답변과 함께 source 정보를 보여준다.

## 3. 현재 상태
- 미구현

## 4. 이슈 및 문제
- 사용할 생성 모델이 아직 정해지지 않았다.
- prompt 구조와 insufficient-context 처리 규칙이 아직 없다.

## 5. 다음 작업
- 생성 모델 후보를 정한다.
- answer prompt와 source citation 포맷을 정의한다.

