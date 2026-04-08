# External Retrieval API

## 목적
`rag-mvp` Chat이 외부 Retrieval API와 연동하기 위한 API Contract를 정의한다.

---

## API 구성

| API | 목적 | 반환 단위 | 주요 특징 |
|---|---|---|---|
| Search API | 전체/다중 문서 후보 chunk 검색 | 검색 결과 chunk 목록 | 전체/다중 문서 대상 1차 retrieval |
| Lookup API | 특정 문서/섹션 범위 정밀 조회 | 매칭 chunk + 앞뒤 context | 특정 문서 내 재검색 및 문맥 보강 |

---

# Search API

## 목적
전체 문서 또는 특정 문서 범위에서 질의와 관련된 후보 chunk를 검색한다.

## 반환 단위
검색 결과 chunk 목록

## 주요 특징
전체/다중 문서 대상 1차 retrieval

## 설계 의도
- 1차 retrieval 용도
- Agent가 관련 근거 후보를 넓게 찾는 용도
- 내부적으로 hybrid 검색 수행
- 외부에는 검색 방식 노출 안 함

## Endpoint
- **POST** `/api/search`

## Request Body

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| query | string | Y | 사용자 질의 |
| top_k | integer | N | 1차 후보 chunk 개수 |
| final_k | integer | N | 최종 반환 chunk 개수 |
| use_rerank | boolean | N | rerank 적용 여부 |
| document_ids | array[string] | N | 특정 문서 범위 제한 |
| filters | object | N | metadata 필터 |
| chunk_types | array[string] | N | 검색 대상 chunk 유형 제한 |
| include_source_metadata | boolean | N | 출처 metadata 포함 여부 |
| include_scores | boolean | N | 검색 점수 포함 여부 |
| return_format | string | N | 반환 형식 (`text`, `markdown`, `json`) |

## Request Example

```json
{
  "query": "신한유니버설종신보험 월대체공제 기준",
  "top_k": 20,
  "final_k": 5,
  "use_rerank": true,
  "document_ids": ["doc_1001"],
  "filters": {
    "document_type": ["policy"],
    "product_name": ["신한유니버설종신보험"]
  },
  "chunk_types": ["section_chunk", "table_chunk"],
  "include_source_metadata": true,
  "include_scores": true,
  "return_format": "json"
}
```

## Response Body

| 필드 | 타입 | 설명 |
|---|---|---|
| query | string | 입력 질의 |
| results | array[object] | 검색 결과 목록 |
| results[].chunk_id | string | 검색된 chunk ID |
| results[].document_id | string | 문서 ID |
| results[].document_name | string | 문서명 |
| results[].content | string | chunk 본문 |
| results[].metadata | object | 출처 metadata |
| results[].scores | object | 검색 점수 |

## Response Example

```json
{
  "query": "신한유니버설종신보험 월대체공제 기준",
  "results": [
    {
      "chunk_id": "chk_1001_0012",
      "document_id": "doc_1001",
      "document_name": "약관_(무)신한유니버설종신보험_080312.md",
      "content": "제12조【월대체보험료 공제】① 월납계약의 경우 보험료 납입경과기간 2년(24회 납입)까지는 ...",
      "metadata": {
        "document_type": "policy",
        "product_name": "신한유니버설종신보험",
        "chunk_type": "section_chunk",
        "section_title": "제12조 월대체보험료 공제",
        "section_path": [
          "제2관 보험료의 납입",
          "제12조 월대체보험료 공제"
        ],
        "page_start": 9,
        "page_end": 10,
        "has_table": false
      },
      "scores": {
        "retrieval_score": 0.84,
        "rerank_score": 0.92
      }
    }
  ]
}
```

## Rules / Constraints
- `query`는 필수이다.
- `final_k`는 `top_k` 이하여야 한다.
- `use_rerank=false`여도 `final_k`는 적용된다.
- `document_ids`와 `filters`는 함께 사용할 수 있다.
- `include_scores=false`이면 `results[].scores`는 생략될 수 있다.
- `include_source_metadata=false`이면 `results[].metadata`는 생략될 수 있다.

## 상세 로직
1. metadata 기반 문서 후보 선택
2. 후보 문서 대상 제한 검색
3. 실패 시 전체 문서 fallback 검색

---

# Lookup API

## 목적
특정 문서 또는 특정 섹션 범위 안에서 정밀하게 chunk를 재조회하고, 필요 시 앞뒤 인접 chunk를 함께 반환한다.

## 반환 단위
매칭 chunk + 앞뒤 context

## 주요 특징
특정 문서 내 재검색 및 문맥 보강

## 설계 의도
- Search API 결과 후속 정밀 조회
- 특정 문서 안에서 좁혀 찾기
- 답변 생성에 필요한 문맥 확보
- 내부적으로 hybrid 검색 수행

## Endpoint
- **POST** `/api/lookup`

## Request Body

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| query | string | Y | 사용자 질의 |
| document_id | string | Y | 대상 문서 ID |
| section_hint | string | N | 특정 섹션 제목/경로 힌트 |
| top_k | integer | N | 반환할 매칭 chunk 개수 |
| chunk_types | array[string] | N | 조회 대상 chunk 유형 제한 |
| return_context_window | boolean | N | 앞뒤 chunk 포함 여부 |
| context_window_size | integer | N | 앞뒤 몇 개 chunk까지 포함할지 |
| include_source_metadata | boolean | N | 출처 metadata 포함 여부 |
| return_format | string | N | 반환 형식 (`text`, `markdown`, `json`) |

## Request Example

```json
{
  "query": "월대체보험료 공제",
  "document_id": "doc_1001",
  "section_hint": "제12조",
  "top_k": 3,
  "chunk_types": ["section_chunk"],
  "return_context_window": true,
  "context_window_size": 1,
  "include_source_metadata": true,
  "return_format": "json"
}
```

## Response Body

| 필드 | 타입 | 설명 |
|---|---|---|
| query | string | 입력 질의 |
| matches | array[object] | 조회 결과 목록 |
| matches[].chunk_id | string | 매칭 chunk ID |
| matches[].document_id | string | 문서 ID |
| matches[].document_name | string | 문서명 |
| matches[].content | string | 매칭 chunk 본문 |
| matches[].metadata | object | 출처 metadata |
| matches[].context.previous_chunks | array[object] | 이전 chunk 목록 |
| matches[].context.next_chunks | array[object] | 다음 chunk 목록 |

## Response Example

```json
{
  "query": "월대체보험료 공제",
  "matches": [
    {
      "chunk_id": "chk_1001_0012",
      "document_id": "doc_1001",
      "document_name": "약관_(무)신한유니버설종신보험_080312.md",
      "content": "제12조【월대체보험료 공제】① 월납계약의 경우 보험료 납입경과기간 2년(24회 납입)까지는 ...",
      "metadata": {
        "document_type": "policy",
        "product_name": "신한유니버설종신보험",
        "chunk_type": "section_chunk",
        "section_title": "제12조 월대체보험료 공제",
        "section_path": [
          "제2관 보험료의 납입",
          "제12조 월대체보험료 공제"
        ],
        "page_start": 9,
        "page_end": 10
      },
      "context": {
        "previous_chunks": [
          {
            "chunk_id": "chk_1001_0011",
            "content": "직전 조항 내용 ..."
          }
        ],
        "next_chunks": [
          {
            "chunk_id": "chk_1001_0013",
            "content": "다음 조항 내용 ..."
          }
        ]
      }
    }
  ]
}
```

## Rules / Constraints
- `query`와 `document_id`는 필수이다.
- Lookup API는 특정 문서 범위를 전제로 한다.
- `return_context_window=true`일 때만 context가 반환될 수 있다.
- `context_window_size`는 `return_context_window=true`일 때만 의미가 있다.
- `include_source_metadata=false`이면 `matches[].metadata`는 생략될 수 있다.

## 상세 로직
1. `document_id` 기준 검색 범위 제한
2. `section_hint` 존재 시 해당 섹션 우선 검색
3. Hybrid 검색으로 `top_k` 매칭 chunk 선정
4. Context window 활성 시 앞뒤 chunk 추가 조회
5. Context 포함 후 반환

---

# Document Metadata

## Metadata Schema

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| document_id | string | Y | 문서 식별자 |
| document_name | string | Y | 문서명 |
| document_type | string | Y | 문서 유형 |
| document_subject | string | N | 대표 주제 |
| aliases | array[string] | N | 대표 주제 별칭 |
| keywords | array[string] | N | 검색 보조 키워드 |

## document_type

| 값 | 설명 |
|---|---|
| policy | 약관/규정 문서 |
| calculation_guide | 보험료/해약환급금 산출방법서 |
| business_guide | 업무처리/가이드 문서 |
| statistics_table | 표/통계형 문서 |
