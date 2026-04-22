# API 설계 문서

## API 역할

같은 chunk 저장소를 보되, 검색 범위와 반환 방식이 다름

| API | 역할 | 반환 | 용도 |
|---|---|---|---|
| Search API | 후보 chunk 검색 | 검색 결과 chunk 목록 | 전체/다중 문서 대상 1차 retrieval |
| Lookup API | 문서 한정 정밀 조회 | 매칭 chunk + 앞뒤 context | 특정 문서 내 재검색 및 문맥 보강 |

---

## API 사용 흐름

1. agent가 질문 분석
2. Search API 호출하여 관련 후보 chunk 확보
3. 2에서 가져온 chunk로 충분히 답변 가능하다면 최종 답변 생성, 아니면 다음 단계를 진행
4. 특정 문서가 유력하면 Lookup API 호출
5. Lookup API에서 매칭 chunk와 앞뒤 chunk 확보
6. agent가 근거 기반으로 최종 답변 생성

---

## 1. Search API

### 목적

전체 문서 또는 특정 문서 범위에서 질의와 관련된 후보 chunk 검색

### 설계 의도

- 1차 retrieval 용도
- agent가 관련 근거 후보를 넓게 찾는 용도
- 내부적으로는 `BM25 + stored vector reuse` hybrid 검색 수행
- 외부에는 검색 방식 노출 안 함
- 요청 스키마는 유지하고 retrieval 내부 계약만 교체
- vector 채널은 ingest 시 각 chunk를 `header_path + "\n\n" + content` 형식으로 임베딩한다.
- `header_path`가 비어 있거나 공백뿐이면 vector 임베딩 입력은 `content`만 사용한다.

### Request

| 파라미터 | 타입 | 필수 | 예시 | 설명 |
|---|---|---|---|---|
| query | string | Y | `"신한유니버설종신보험 월대체공제 기준"` | 사용자 질의 |
| top_k | integer | N | `30` | 1차 후보 chunk 개수 |
| final_k | integer | N | `10` | 최종 반환 chunk 개수, rerank 적용 여부와 무관하게 적용 |
| use_rerank | boolean | N | `true` | rerank 적용 여부 |
| document_ids | array[string] | N | `["doc_1001"]` | 특정 문서 범위 제한, 이전 검색 결과에서 특정 문서가 유력해졌을 때 사용 |
| filters | object | N | `{"document_type":["policy"]}` | metadata 필터 |
| chunk_types | array[string] | N | `["text","table","mixed"]` | 검색 대상 chunk 유형 제한 |
| include_source_metadata | boolean | N | `true` | 출처 metadata 포함 여부 |
| include_scores | boolean | N | `true` | BM25, vector, RRF, rerank score 포함 여부 |
| keyword_vector_weight | float | N | `0.3` | weighted RRF에서 keyword/BM25 비중 |
| return_format | string | N | `"json"` | 반환 형식 (text, markdown, json) |

### Response

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

### Response 예시

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

### score 운용 원칙

- `results[].scores.bm25_score`는 `header_path_search` BM25와 `content_search` BM25를 `bm25_header_weight`, `bm25_content_weight`로 가중 합산한 점수다.
- `results[].scores.vector_score`는 Weaviate native vector retrieval 결과를 API가 사용하는 단일 normalized score다.
- `results[].scores.rrf_score`는 BM25/vector 후보 union 범위에서 weighted RRF 결합 이후 최종 후보 선정을 설명하는 기본 점수다.
- UI 검색 결과 리스트와 상세 패널에는 `bm25_score`, `vector_score`, `rrf_score`, `rerank_score`를 함께 표시할 수 있어야 한다.
- rerank를 사용하지 않는 경우에도 `rrf_score`는 항상 반환 가능해야 한다.

### 상세 로직

| 단계 | 설명 |
|---|---|
| 1. 문서 후보 선택 | `document_ids`, `filters`로 검색 대상 문서 scope를 정한다 |
| 2. candidate size 계산 | `candidate_k = max(20, 2 * request.top_k)`를 계산한다 |
| 3. BM25 후보 수집 | Weaviate BM25로 `header_path_search`, `content_search`를 각각 조회하고 상위 `candidate_k` 후보를 가중 합산해 결합한다 |
| 4. query embedding | default embedding model id를 결정하고 query를 1회만 임베딩한다 |
| 5. vector 후보 수집 | Weaviate native vector query로 상위 `candidate_k` chunk 후보를 수집한다 |
| 6. same-model filtering | BM25/vector 모두 query와 동일 `embedding_model_id`를 가진 chunk만 유지한다 |
| 7. union + RRF | 두 후보군을 `chunk_id` 기준으로 합친 뒤 union 범위에서 weighted RRF를 계산한다 |
| 8. optional rerank | `use_rerank=true`면 RRF 상위 `request.top_k`를 rerank한 뒤 `request.final_k`만 반환한다 |

### retrieval 계약

- 검색 시점에 candidate chunk 본문을 다시 임베딩하지 않는다.
- query는 런타임에 1회만 임베딩하고, chunk vector는 ingest 시 저장된 vector를 재사용한다.
- chunk vector는 ingest 시 `header_path + "\n\n" + content_raw` 기준으로 생성되며, 이 규칙이 바뀌면 기존 적재 데이터는 재ingest 또는 재embedding이 필요하다.
- BM25/vector 각 채널은 동일한 `candidate_k` 규칙을 사용한다.
- `request.top_k`는 RRF 이후 중간 후보 수, `request.final_k`는 최종 응답 수다.
- BM25 계열 점수는 Weaviate BM25 결과만 사용하며, 앱 레이어에서 `header_path_search + content_search` 두 채널 점수를 가중 합산한다.
- `bm25_header_weight`, `bm25_content_weight`는 음수가 될 수 없고, 둘 다 0이면 `1.0 / 1.0` 기본값으로 fallback 한다.
- BM25/vector 채널 모두 동일하게 `document_ids`, `chunk_types`, `embedding_model_id` 필터 계약을 적용한다.
- legacy chunk처럼 `embedding_model_id`가 없는 데이터는 same-model strictness를 위해 BM25/vector 후보군에서 모두 제외한다.
- mixed embedding model 데이터셋에서는 현재 default embedding model id와 일치하는 chunk만 검색 결과에 남는다.

---

## 2. Lookup API

### 목적

특정 문서 안에서 정밀하게 chunk를 다시 조회하고, 필요 시 앞뒤 인접 chunk(context window)도 함께 반환

### 설계 의도

- Search API 결과 후속 정밀 조회
- 특정 문서 안에서 좁혀 찾기
- 답변 생성에 필요한 문맥 확보
- 내부적으로는 hybrid 검색 수행
- `chunk_index` 기반 순차 context를 일관되게 반환

### Request

| 파라미터 | 타입 | 필수 | 예시 | 설명 |
|---|---|---|---|---|
| query | string | Y | `"월대체보험료 공제"` | 사용자 질의 |
| document_id | string | Y | `"doc_1001"` | 대상 문서 ID |
| top_k | integer | N | `3` | 반환할 매칭 chunk 개수 |
| chunk_types | array[string] | N | `["text","table","mixed"]` | 조회 대상 chunk 유형 제한 |
| return_context_window | boolean | N | `true` | 앞뒤 chunk 포함 여부 |
| context_window_size | integer | N | `1` | 앞뒤 몇 개 chunk까지 포함할지 |
| include_source_metadata | boolean | N | `true` | 출처 metadata 포함 여부 |
| return_format | string | N | `"json"` | 반환 형식 (text, markdown, json) |

### Response

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

### Response 예시

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

### Lookup 보강 규칙

- 공통:
  - 매칭 chunk를 반환한다.
  - 필요 시 `previous_chunks`, `next_chunks`를 반환한다.
  - 앞뒤 context는 같은 문서 내 `chunk_index` 기준으로 계산한다.
  - 문서 시작/끝 경계에서는 존재하는 범위만 반환한다.
  - `include_source_metadata=true`면 Search API와 동일한 6개 metadata 키만 반환한다.

---

## Chunk Viewer 표현 규칙

- 청크 상세 조회 화면은 chunk 본문을 plain text가 아니라 Markdown 뷰어로 렌더링한다.
- API는 청크의 원문 Markdown을 손실 없이 반환해야 한다.
- 표, 리스트, heading, 코드성 블록이 Markdown 렌더링에서 보존되도록 한다.
- Kiwi 토큰, `content_search`, metadata는 Markdown 본문과 별도 패널로 분리해 표시한다.

---

## Metadata

### 1. Document Metadata

| 필드 | 타입 | 필수 | 예시 | 설명 |
|---|---|---|---|---|
| document_id | string | Y | `"doc_1001"` | 문서 식별자 |
| document_name | string | Y | `"약관_(무)신한유니버설종신보험_080312.md"` | 문서명 |
| document_type | string | Y | `"policy"` | 문서 유형 |
| embedding_model_id | string | N | `"bge-m3"` | ingest 시 문서/청크에 사용한 embedding model id |

#### document_type 값

| 값 | 설명 |
|---|---|
| policy | 약관/규정 문서 |
| calculation_guide | 보험료/해약환급금 산출방법서 |
| business_guide | 업무처리/가이드 문서 |
| statistics_table | 표/통계형 문서 |
| case_law | 판례 |

#### metadata 운용 원칙

- document metadata는 `document_id`, `document_name`, `document_type`, `embedding_model_id`만 유지한다.
- 문서 주제/별칭/키워드 같은 의미 요약형 필드는 retrieval filtering 기준으로 사용하지 않는다.
- `embedding_model_id`는 문서 검색용 힌트가 아니라 retrieval consistency 보장을 위한 strict metadata로 사용한다.

### 2. Chunk Metadata

| 필드 | 타입 | 필수 | 예시 | 설명 |
|---|---|---|---|---|
| header_path | string | Y | `"제2관 보험료의 납입 > 제12조 월대체보험료 공제"` | breadcrumb 형식의 헤더 경로 |
| chunk_type | string | Y | `"text"` | 외부 API 청크 유형 |
| source_file | string | Y | `"약관_(무)신한유니버설종신보험_080312.md"` | 원본 파일명 |
| chunk_index | integer | Y | `12` | 문서 내 1부터 시작하는 연속 청크 번호 |
| part | integer | Y | `1` | 분할 청크 순번 |
| total_parts | integer | Y | `1` | 같은 청크 그룹의 전체 파트 수 |

#### chunk_type 값

| 값 | 설명 |
|---|---|
| text | section/paragraph 기반 일반 텍스트 chunk |
| table | Markdown 표 중심 chunk |
| mixed | 텍스트와 표가 함께 포함된 chunk |

#### metadata 운용 원칙

- 외부 API에 노출되는 chunk metadata는 6개 키만 유지한다.
- `header_path`는 문서 헤더 breadcrumb를 `" > "`로 join한 문자열이다.
- `source_file`는 업로드 파일명(`document_name`)을 그대로 사용한다.
- `chunk_index`는 문서 단위 1부터 시작하는 전역 순번이며 Lookup context 계산 기준이다.
- 분할되지 않은 청크는 `part=1`, `total_parts=1`이다.
- 외부 API에서는 내부 chunk 세부 타입을 `text | table | mixed`로만 노출한다.
- `max_tokens`, `embedding_model_id` 등 ingest/search 내부 운영 필드는 저장될 수 있으나 외부 API metadata로는 노출하지 않는다.

### Metadata 노출 규칙

- `include_source_metadata=true`일 때 Search API 응답 `results[].metadata`에는 chunk metadata 6개 키만 포함한다.
- Lookup API 응답의 `matches[].metadata`, `previous_chunks[].metadata`, `next_chunks[].metadata`도 같은 6개 키만 포함한다.
- Chunk detail API metadata도 동일한 6개 키만 노출해 검색 결과와 상세 조회 간 일관성을 유지한다.

### Weaviate Reset Strategy

- Document/Chunk 컬렉션 스키마 변경은 기존 컬렉션을 유지한 채 필드만 덧붙이는 방식이 아니라 reset-first 전략으로 운영한다.
- 테스트와 재인제스트 기준선은 항상 `ChunkRecord`를 먼저 drop하고 `DocumentRecord`를 뒤이어 drop한 후, 두 컬렉션을 새 스키마로 다시 생성하는 절차를 따른다.
- 이전 스키마 데이터 호환이나 백필은 이 계약에 포함하지 않으며, 스키마 갱신 후에는 현재 계약으로 전체 재인제스트를 수행한다.

---

## Filtering

"필터링"을 제외(exclusion)가 아니라 **우선순위 조정(priority adjustment)**으로 구현

| 방식 | 설명 | 적용 metadata 필드 |
|---|---|---|
| hard filter | 조건 안 맞으면 아예 제외 | `document_id`, `document_type` |
| metadata narrowing | 문서 metadata 기준 제외는 hard filter만 지원 | `document_id`, `document_type` |

### Fallback 필수

> 문서 후보 선택이 실패해도 검색이 죽으면 안 됩니다.

- 문서 후보가 충분히 있으면 → **제한 검색**
- 후보가 없거나 너무 애매하면 → **전체 검색 fallback**