# Answer Evaluation

## 1. 목적
- `/chat`의 answer generation 품질을 retrieval 품질과 분리해서 점검한다.
- 질문별로 `검색은 맞는데 답변이 과하게 요약되었는지`, `답변은 맞지만 citation이 약한지`, `retrieval 자체가 틀린지`를 구분한다.
- retrieval 질문 세트와 같은 질문으로 answer 품질을 반복 비교할 수 있게 한다.

## 2. 구현 내용
- 점검 대상:
  - `docs/retrieval-test-set.md`의 질문 세트 중 대표 질문
- 점검 방법:
  - `/chat`에서 질문 입력
  - 기본은 `Target file = All indexed files`
  - 필요 시 특정 파일로 좁혀서 retrieval 원인과 answer 원인을 분리한다.
- 점검 항목:
  - retrieval 적합성
  - answer 정확성
  - 조건 분기 보존 여부
  - insufficient-context 처리 적절성
  - citation 적절성
- 판정 축:
  - `retrieval_pass / retrieval_fail`
  - `answer_pass / answer_borderline / answer_fail`
  - `citation_pass / citation_borderline / citation_fail`

## 3. 현재 상태
- 진행중
- `/chat` grounded answer flow는 연결 완료
- `gpt-4o` deployment 실응답 확인 완료
- answer 품질 점검표 초안 작성 완료
- 아직 질문 세트 기준 answer 판정 기록은 일부 사례만 확인한 상태다.

## 4. 이슈 및 문제
- retrieval이 맞아도 answer가 여러 조건을 한 문장으로 과하게 합칠 수 있다.
- 표/수식형 문서는 chunk 경계 문제 때문에 answer 품질이 retrieval보다 더 흔들릴 수 있다.
- citation은 retrieval metadata 기반이라 문서 위치 표시는 가능하지만, 답변 문장 내 근거 범위와 1:1 대응은 아직 부족하다.

## 5. 다음 작업
- 아래 템플릿으로 대표 질문 5~10건을 기록한다.
- retrieval fail과 answer fail을 분리해서 원인을 남긴다.
- 산출방법서 계열 질문은 chunk 전략 보정 후보로 따로 표시한다.

## 6. 판정 기준

### 6.1 Retrieval
- `pass`
  - 기대 문서가 top 1 또는 top 3 안에 있고, preview/text에 핵심 근거가 보인다.
- `borderline`
  - 기대 문서는 맞지만 top 1이 아니거나, 근거가 부분적으로만 보인다.
- `fail`
  - 다른 문서가 우선 검색되거나, 답변에 필요한 근거 chunk가 보이지 않는다.

### 6.2 Answer
- `pass`
  - 질문 의도에 맞게 근거 범위 안에서 답한다.
  - 조건부 항목을 공통 항목처럼 섞지 않는다.
  - 문서에 없는 내용을 추가하지 않는다.
- `borderline`
  - 큰 방향은 맞지만 조건 분기, 범위, 표현이 다소 넓거나 모호하다.
- `fail`
  - 문서에 없는 내용을 단정한다.
  - 조건부 항목을 무조건 항목처럼 말한다.
  - retrieval hit와 맞지 않는 답을 한다.

### 6.3 Citation
- `pass`
  - 표시된 citation chunk가 실제 답변 근거와 직접 연결된다.
- `borderline`
  - 같은 문서이긴 하지만 답변 핵심과 직접 연결되는 chunk가 부족하다.
- `fail`
  - citation이 답변 근거와 맞지 않거나 다른 문서를 가리킨다.

## 7. 기록 템플릿
- 질문:
- 기대 source:
- 실제 top 1 source:
- 실제 top 3 source:
- answer:
- citation source/chunk:
- retrieval 판정:
  - `pass`
  - `borderline`
  - `fail`
- answer 판정:
  - `pass`
  - `borderline`
  - `fail`
- citation 판정:
  - `pass`
  - `borderline`
  - `fail`
- 원인 분류:
  - `retrieval`
  - `answer summarization`
  - `conditional mixing`
  - `citation mismatch`
  - `chunking`
- 메모:

## 8. 우선 점검 질문

### 8.1 계약관계자 변경 문서
- `계약자 변경 시 동의가 필요한 대상은 누구인가?`
- `계약자 변경을 위한 서류를 알려줘`
- `대리인 방문 시 추가 구비서류는 무엇인가?`

### 8.2 종신보험 약관 문서
- `청약 철회는 며칠 안에 가능한가?`
- `보험료 납입한도는 어떻게 정해지나?`

### 8.3 산출방법서 문서
- `이 상품의 적용 이율은 얼마인가?`
- `산출방법서에서 m과 t는 무엇을 의미하나?`

## 9. 샘플 기록

### 9.1 2026-03-30
- 질문:
  - `계약자 변경을 위한 서류를 알려줘`
- 기대 source:
  - `300233_계약관계자변경.docx`
- 실제 top 1 source:
  - `300233_계약관계자변경.docx`
- 실제 top 3 source:
  - 모두 `300233_계약관계자변경.docx`
- answer:
  - 공통 서류와 조건부 추가 서류로 분리해 답변하도록 보정 후 재응답 확인
- citation source/chunk:
  - `300233_계약관계자변경.docx` chunk `#10`, `#26` 등
- retrieval 판정:
  - `pass`
- answer 판정:
  - `borderline`
- citation 판정:
  - `pass`
- 원인 분류:
  - `conditional mixing`
- 메모:
  - 초기 답변은 조건부 서류와 공통 서류를 한 목록처럼 합쳤다.
  - prompt 보정 후 공통/조건부 구조는 개선됐지만, 여전히 어떤 경우의 공통 서류인지 세부 분기 점검이 더 필요하다.
