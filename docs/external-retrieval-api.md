# External Retrieval API

## 1. 목적
- `rag-mvp`가 연동하는 외부 Search API / Lookup API의 최신 계약을 정리한다.
- 이 문서는 [docs/retrieval_api_design.md](/home/ubuntu/rag-mvp/docs/retrieval_api_design.md)를 기준으로 현재 스펙을 다시 정리한 버전이다.

## 2. 구현 내용

### 2.1 API 역할

| API | 역할 | 반환 | 용도 |
|---|---|---|---|
| Search API | 후보 chunk 검색 | 검색 결과 chunk 목록 | 전체/다중 문서 대상 1차 retrieval |
| Lookup API | 문서 한정 정밀 조회 | 매칭 chunk + 앞뒤 context | 특정 문서 내 재검색 및 문맥 보강 |

### 2.2 API 사용 흐름
1. Agent가 질문 분석
2. Search API 호출로 관련 후보 chunk 확보
3. Search 결과만으로 충분하면 답변 생성
4. 특정 문서가 유력하면 Lookup API 호출
5. Lookup API에서 매칭 chunk와 앞뒤 context 확보
6. 근거 기반으로 최종 답변 생성

---

## 3. Search API

### 3.1 목적
- 전체 문서 또는 특정 문서 범위에서 질의와 관련된 후보 chunk를 검색한다.

### 3.2 설계 의도
- 1차 retrieval 용도
- 관련 근거 후보를 넓게 찾는 용도
- 내부적으로 `BM25 + stored vector reuse` hybrid 검색 수행
- 외부에는 검색 방식 자체를 노출하지 않음
- vector 채널은 ingest 시 `header_path + "\n\n" + content` 형식으로 임베딩
- `header_path`가 비어 있으면 `content`만 임베딩

### 3.3 Endpoint
- `POST /api/search`

### 3.4 Request

| 파라미터 | 타입 | 필수 | 예시 | 설명 |
|---|---|---|---|---|
| `query` | string | Y | `"신한유니버설종신보험 월대체공제 기준"` | 사용자 질의 |
| `top_k` | integer | N | `20` | 1차 후보 chunk 개수 |
| `final_k` | integer | N | `5` | 최종 반환 chunk 개수 |
| `use_rerank` | boolean | N | `true` | rerank 적용 여부 |
| `document_ids` | array[string] | N | `["doc_1001"]` | 특정 문서 범위 제한 |
| `filters` | object | N | `{"document_type":["policy"]}` | metadata 필터 |
| `chunk_types` | array[string] | N | `["text","table","mixed"]` | 검색 대상 chunk 유형 제한 |
| `include_source_metadata` | boolean | N | `true` | 출처 metadata 포함 여부 |
| `include_scores` | boolean | N | `true` | BM25, vector, RRF, rerank score 포함 여부 |
| `keyword_vector_weight` | float | N | `0.3` | weighted RRF에서 keyword/BM25 비중 |
| `return_format` | string | N | `"json"` | 반환 형식 (`text`, `markdown`, `json`) |

### 3.5 Request Example

```json
{
  "query": "신한유니버설종신보험 월대체공제 기준",
  "top_k": 20,
  "final_k": 5,
  "use_rerank": true,
  "document_ids": ["doc_1001"],
  "filters": {
    "document_type": ["policy"]
  },
  "chunk_types": ["text", "table", "mixed"],
  "include_source_metadata": true,
  "include_scores": true,
  "keyword_vector_weight": 0.3,
  "return_format": "json"
}
```

### 3.6 Response

| 필드 | 타입 | 설명 |
|---|---|---|
| `query` | string | 입력 질의 |
| `results` | array[object] | 검색 결과 목록 |
| `results[].chunk_id` | string | 검색된 chunk ID |
| `results[].document_id` | string | 문서 ID |
| `results[].document_name` | string | 문서명 |
| `results[].content` | string | chunk 본문 |
| `results[].metadata` | object | 출처 metadata |
| `results[].scores` | object | 검색 점수 |

### 3.7 Response Example

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
        "header_path": "제2관 보험료의 납입 > 제12조 월대체보험료 공제",
        "chunk_type": "text",
        "source_file": "약관_(무)신한유니버설종신보험_080312.md",
        "chunk_index": 12,
        "part": 1,
        "total_parts": 1
      },
      "scores": {
        "bm25_score": 10.42,
        "vector_score": 0.84,
        "rrf_score": 0.73,
        "rerank_score": 0.92
      }
    }
  ]
}
```

### 3.8 Score 운용 원칙
- `bm25_score`는 `header_path_search` BM25와 `content_search` BM25를 가중 합산한 점수다.
- `vector_score`는 Weaviate native vector retrieval 결과의 normalized score다.
- `rrf_score`는 BM25/vector union 범위에서 weighted RRF 결합 이후의 기본 점수다.
- `rerank_score`는 rerank 사용 시 추가되는 최종 우선순위 점수다.
- rerank를 사용하지 않아도 `rrf_score`는 반환 가능해야 한다.

### 3.9 상세 로직
1. `document_ids`, `filters`로 문서 후보 범위를 정한다.
2. `candidate_k = max(20, 2 * request.top_k)`를 계산한다.
3. BM25로 `header_path_search`, `content_search`를 각각 조회하고 가중 합산한다.
4. query를 1회만 임베딩한다.
5. vector 후보를 상위 `candidate_k`까지 조회한다.
6. query와 동일 `embedding_model_id`를 가진 chunk만 유지한다.
7. `chunk_id` 기준 union 후 weighted RRF를 계산한다.
8. `use_rerank=true`면 RRF 상위 `request.top_k`를 rerank하고 `final_k`만 반환한다.

### 3.10 Retrieval 계약
- 검색 시점에 chunk 본문을 다시 임베딩하지 않는다.
- query는 런타임에 1회만 임베딩한다.
- chunk vector는 ingest 시 저장된 vector를 재사용한다.
- chunk vector 생성 기준은 `header_path + "\n\n" + content_raw`다.
- `request.top_k`는 RRF 이후 중간 후보 수다.
- `request.final_k`는 최종 응답 수다.
- legacy chunk처럼 `embedding_model_id`가 없는 데이터는 strict same-model filtering에서 제외한다.

---

## 4. Lookup API

### 4.1 목적
- 특정 문서 안에서 정밀하게 chunk를 다시 조회하고, 필요 시 앞뒤 인접 chunk도 함께 반환한다.

### 4.2 설계 의도
- Search 결과 후속 정밀 조회
- 특정 문서 안에서 좁혀 찾기
- 답변 생성에 필요한 문맥 확보
- 내부적으로 hybrid 검색 수행
- `chunk_index` 기반 순차 context를 일관되게 반환

### 4.3 Endpoint
- `POST /api/lookup`

### 4.4 Request

| 파라미터 | 타입 | 필수 | 예시 | 설명 |
|---|---|---|---|---|
| `query` | string | Y | `"월대체보험료 공제"` | 사용자 질의 |
| `document_id` | string | Y | `"doc_1001"` | 대상 문서 ID |
| `top_k` | integer | N | `3` | 반환할 매칭 chunk 개수 |
| `chunk_types` | array[string] | N | `["text","table","mixed"]` | 조회 대상 chunk 유형 제한 |
| `return_context_window` | boolean | N | `true` | 앞뒤 chunk 포함 여부 |
| `context_window_size` | integer | N | `1` | 앞뒤 몇 개 chunk까지 포함할지 |
| `include_source_metadata` | boolean | N | `true` | 출처 metadata 포함 여부 |
| `return_format` | string | N | `"json"` | 반환 형식 (`text`, `markdown`, `json`) |

### 4.5 Request Example

```json
{
  "query": "월대체보험료 공제",
  "document_id": "doc_1001",
  "top_k": 3,
  "chunk_types": ["text", "table", "mixed"],
  "return_context_window": true,
  "context_window_size": 1,
  "include_source_metadata": true,
  "return_format": "json"
}
```

### 4.6 Response

| 필드 | 타입 | 설명 |
|---|---|---|
| `query` | string | 입력 질의 |
| `matches` | array[object] | 조회 결과 목록 |
| `matches[].chunk_id` | string | 매칭 chunk ID |
| `matches[].document_id` | string | 문서 ID |
| `matches[].document_name` | string | 문서명 |
| `matches[].content` | string | 매칭 chunk 본문 |
| `matches[].metadata` | object | 출처 metadata |
| `matches[].context.previous_chunks` | array[object] | 이전 chunk 목록 |
| `matches[].context.next_chunks` | array[object] | 다음 chunk 목록 |

### 4.7 Response Example

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
        "header_path": "제2관 보험료의 납입 > 제12조 월대체보험료 공제",
        "chunk_type": "text",
        "source_file": "약관_(무)신한유니버설종신보험_080312.md",
        "chunk_index": 12,
        "part": 1,
        "total_parts": 1
      },
      "context": {
        "previous_chunks": [
          {
            "chunk_id": "chk_1001_0011",
            "content": "제11조【제2회 이후 보험료의 납입】...",
            "metadata": {
              "header_path": "제2관 보험료의 납입 > 제11조 제2회 이후 보험료의 납입",
              "chunk_type": "text",
              "source_file": "약관_(무)신한유니버설종신보험_080312.md",
              "chunk_index": 11,
              "part": 1,
              "total_parts": 1
            }
          }
        ],
        "next_chunks": [
          {
            "chunk_id": "chk_1001_0013",
            "content": "제13조【보험료의 납입연체시 납입최고(독촉)와 계약의 해지】...",
            "metadata": {
              "header_path": "제2관 보험료의 납입 > 제13조 보험료의 납입연체시 납입최고(독촉)와 계약의 해지",
              "chunk_type": "text",
              "source_file": "약관_(무)신한유니버설종신보험_080312.md",
              "chunk_index": 13,
              "part": 1,
              "total_parts": 1
            }
          }
        ]
      }
    }
  ]
}
```

### 4.8 Lookup 보강 규칙
- 매칭 chunk를 반환한다.
- 필요 시 `previous_chunks`, `next_chunks`를 반환한다.
- 앞뒤 context는 같은 문서 내 `chunk_index` 기준으로 계산한다.
- 문서 시작/끝 경계에서는 존재하는 범위만 반환한다.
- `include_source_metadata=true`면 Search API와 동일한 6개 metadata 키만 반환한다.

---

## 5. Metadata

### 5.1 Document Metadata

| 필드 | 타입 | 필수 | 예시 | 설명 |
|---|---|---|---|---|
| `document_id` | string | Y | `"doc_1001"` | 문서 식별자 |
| `document_name` | string | Y | `"약관_(무)신한유니버설종신보험_080312.md"` | 문서명 |
| `document_type` | string | Y | `"policy"` | 문서 유형 |
| `embedding_model_id` | string | N | `"bge-m3"` | ingest 시 사용한 embedding model id |

#### document_type 값

| 값 | 설명 |
|---|---|
| `policy` | 약관/규정 문서 |
| `calculation_guide` | 보험료/해약환급금 산출방법서 |
| `business_guide` | 업무처리/가이드 문서 |
| `statistics_table` | 표/통계형 문서 |

#### 운용 원칙
- 외부 API 기준 document metadata는 `document_id`, `document_name`, `document_type`, `embedding_model_id`만 유지한다.
- 주제/별칭/키워드 같은 의미 요약형 필드는 filtering 기준으로 사용하지 않는다.
- `embedding_model_id`는 retrieval consistency 보장을 위한 strict metadata다.

### 5.2 Chunk Metadata

| 필드 | 타입 | 필수 | 예시 | 설명 |
|---|---|---|---|---|
| `header_path` | string | Y | `"제2관 보험료의 납입 > 제12조 월대체보험료 공제"` | breadcrumb 형식 헤더 경로 |
| `chunk_type` | string | Y | `"text"` | 외부 API 청크 유형 |
| `source_file` | string | Y | `"약관_(무)신한유니버설종신보험_080312.md"` | 원본 파일명 |
| `chunk_index` | integer | Y | `12` | 문서 내 1부터 시작하는 전역 순번 |
| `part` | integer | Y | `1` | 분할 청크 순번 |
| `total_parts` | integer | Y | `1` | 같은 청크 그룹의 전체 파트 수 |

#### chunk_type 값

| 값 | 설명 |
|---|---|
| `text` | section/paragraph 기반 일반 텍스트 chunk |
| `table` | Markdown 표 중심 chunk |
| `mixed` | 텍스트와 표가 함께 포함된 chunk |

#### 운용 원칙
- 외부 API chunk metadata는 6개 키만 유지한다.
- `header_path`는 breadcrumb를 `" > "`로 join한 문자열이다.
- `source_file`는 업로드 파일명(`document_name`)을 그대로 사용한다.
- `chunk_index`는 문서 단위 1부터 시작하는 전역 순번이다.
- 분할되지 않은 청크는 `part=1`, `total_parts=1`이다.
- 내부 운영용 필드는 외부 metadata로 노출하지 않는다.

### 5.3 Metadata 노출 규칙
- `include_source_metadata=true`일 때만 metadata를 노출한다.
- Search API의 `results[].metadata`, Lookup API의 `matches[].metadata`, `previous_chunks[].metadata`, `next_chunks[].metadata`는 같은 6개 키를 사용한다.

---

## 6. Filtering

### 6.1 기본 원칙
- 필터링은 exclusion보다 priority adjustment보다 먼저 hard filter 기준을 명확히 적용한다.
- hard filter 대상은 `document_id`, `document_type`다.

| 방식 | 설명 | 적용 metadata 필드 |
|---|---|---|
| hard filter | 조건이 맞지 않으면 제외 | `document_id`, `document_type` |
| metadata narrowing | 문서 metadata 기준 제외는 hard filter만 지원 | `document_id`, `document_type` |

### 6.2 Fallback
- 문서 후보가 충분하면 제한 검색을 수행한다.
- 후보가 없거나 애매하면 전체 검색으로 fallback 한다.

## 3. 현재 상태
- 진행중
- `docs/retrieval_api_design.md` 기준으로 Search API / Lookup API 스펙을 재정리했다.
- 현재 `rag-mvp` backend는 Search API의 `query`, `top_k`, `final_k`, `include_source_metadata`, `include_scores`, `keyword_vector_weight`를 사용하고 있다.
- 현재 `rag-mvp` frontend Lookup 버튼은 직전 Search 결과 중 최고 `rrf_score` hit의 `document_id`를 사용한다.

## 4. 이슈 및 문제
- 현재 `rag-mvp` backend normalize 로직은 Search API/Lookup API 전체 필드를 아직 100% 사용하지 않는다.
- Search API의 `document_ids`, `filters`, `chunk_types`, `return_format`은 현재 UI에서 직접 입력받지 않는다.
- Lookup API는 현재 `document_id`를 필수로 요구하므로, Search 선행 결과가 없으면 바로 호출할 수 없다.

## 5. 다음 작업
- Search API / Lookup API 추가 필드가 실제 운영에서 필요해지면 backend request mapping을 확장한다.
- 외부 API 응답의 metadata와 score 표현을 frontend debug 패널에서 얼마나 노출할지 다시 정리한다.
