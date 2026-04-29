import unittest
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import (
    ChatRequest,
    EMPTY_CONTENT_PLACEHOLDER,
    UNKNOWN_DOCUMENT_NAME,
    UNKNOWN_HEADER_PATH,
    RewriteResult,
    build_answer_generation_messages,
    build_external_search_payload,
    build_standardized_retrieved_chunks,
    extract_product_name_candidates,
    filter_hits_for_answer_generation,
    format_chat_context,
    normalize_keyword_vector_weight,
    normalize_external_search_hit,
    parse_query_rewrite_response,
    resolve_search_product_name_filter,
    sort_hits_for_output,
)


class AnswerContextMetadataTests(unittest.TestCase):
    def test_normalize_external_search_hit_preserves_metadata_and_contents(self) -> None:
        hit = {
            "id": "chunk-1",
            "document_name": "policy-a.md",
            "content": "  보장 내용입니다.  ",
            "scores": {"rrf_score": 0.83},
            "metadata": {
                "header_path": "제1장 > 보장",
                "source_file": "policy-a.md",
                "chunk_index": 7,
            },
        }

        normalized = normalize_external_search_hit(hit)

        self.assertEqual(normalized["document_name"], "policy-a.md")
        self.assertEqual(normalized["header_path"], "제1장 > 보장")
        self.assertEqual(normalized["section_header"], "제1장 > 보장")
        self.assertEqual(normalized["contents"], "보장 내용입니다.")
        self.assertEqual(normalized["text"], "보장 내용입니다.")
        self.assertEqual(normalized["rrf_score"], 0.83)
        self.assertEqual(normalized["scores"]["rrf_score"], 0.83)

    def test_build_standardized_retrieved_chunks_adds_metadata_fallbacks(self) -> None:
        standardized = build_standardized_retrieved_chunks(
            [
                {
                    "id": "chunk-2",
                    "text": " ",
                }
            ]
        )

        self.assertEqual(len(standardized), 1)
        self.assertEqual(standardized[0]["document_name"], UNKNOWN_DOCUMENT_NAME)
        self.assertEqual(standardized[0]["header_path"], UNKNOWN_HEADER_PATH)
        self.assertEqual(standardized[0]["contents"], EMPTY_CONTENT_PLACEHOLDER)
        self.assertEqual(standardized[0]["text"], EMPTY_CONTENT_PLACEHOLDER)

    def test_sort_hits_for_output_prefers_rrf_score_then_rerank_score(self) -> None:
        sorted_hits = sort_hits_for_output(
            [
                {"id": "third", "score": 0.91},
                {"id": "first", "rrf_score": 0.9, "rerank_score": 0.2},
                {"id": "second", "rerank_score": 0.8},
            ]
        )

        self.assertEqual([hit["id"] for hit in sorted_hits], ["first", "second", "third"])

    def test_filter_hits_for_answer_generation_excludes_clear_product_mismatch(self) -> None:
        filtered_hits = filter_hits_for_answer_generation(
            original_query="신한진심을품은변액유니버설종신에서 중도인출시 언제 지급되나요?",
            rewritten_query="신한진심을품은변액유니버설종신에서 중도인출 시 지급 시점을 알려 주세요?",
            hits=[
                {"id": "keep", "document_name": "약관_신한진심을품은변액유니버설종신.md", "contents": "A"},
                {"id": "drop", "document_name": "약관_신한참좋은치아보험.md", "contents": "B"},
                {"id": "unknown", "document_name": "business_guide_general.md", "contents": "C"},
            ],
        )

        self.assertEqual([hit["id"] for hit in filtered_hits], ["keep", "unknown"])

    def test_answer_generation_messages_include_structured_context_metadata(self) -> None:
        hits = [
            {
                "id": "chunk-1",
                "document_name": "policy-a.md",
                "header_path": "제1장 > 공통",
                "contents": "공통 서류 안내",
            },
            {
                "id": "chunk-2",
                "contents": "추가 서류 안내",
            },
        ]

        context = format_chat_context(hits)
        self.assertIn("[Context 1]", context)
        self.assertIn("document_name=policy-a.md", context)
        self.assertIn("header_path=제1장 > 공통", context)
        self.assertIn("content=공통 서류 안내", context)
        self.assertIn(f"document_name={UNKNOWN_DOCUMENT_NAME}", context)
        self.assertIn(f"header_path={UNKNOWN_HEADER_PATH}", context)

        messages = build_answer_generation_messages(
            original_query="청구 서류가 뭐야?",
            rewritten_query="청구 서류는 무엇인가?",
            hits=hits,
        )
        user_prompt = messages[1]["content"]

        self.assertIn("Review document_name, header_path, and content for every context item before answering.", user_prompt)
        self.assertIn("If different documents or sections disagree", user_prompt)
        self.assertIn("[Context 2]", user_prompt)
        self.assertIn(f"document_name={UNKNOWN_DOCUMENT_NAME}", user_prompt)
        self.assertIn(f"header_path={UNKNOWN_HEADER_PATH}", user_prompt)

    def test_build_external_search_payload_omits_document_type_and_chunk_types(self) -> None:
        payload = build_external_search_payload(
            "http://example.com/api/search",
            payload=ChatRequest(query="2024년 보험 통계 알려줘"),
            question="통계 질의",
            query="2024년 보험 통계 알려줘",
            top_k=30,
            final_k=10,
            stored_name=None,
            rewrite_result=RewriteResult(
                original_query="2024년 보험 통계 알려줘",
                rewritten_query="2024년 보험 통계 알려줘",
                document_type_filters=["statistics_table"],
                entities={"year": "2024"},
                routing_hints={"chunk_types": "table,mixed"},
            ),
        )

        self.assertNotIn("filters", payload)
        self.assertNotIn("chunk_types", payload)
        self.assertNotIn("use_rerank", payload)
        self.assertNotIn("include_source_metadata", payload)
        self.assertNotIn("include_scores", payload)

    def test_build_external_search_payload_includes_product_name_filter_when_available(self) -> None:
        payload = build_external_search_payload(
            "http://example.com/api/search",
            payload=ChatRequest(query="신한유니버설종신보험 해약환급금은 어떻게 계산돼?"),
            question="질문",
            query="신한유니버설종신보험 해약환급금은 어떻게 계산되나요?",
            top_k=30,
            final_k=10,
            stored_name=None,
            rewrite_result=RewriteResult(
                original_query="신한유니버설종신보험 해약환급금은 어떻게 계산돼?",
                rewritten_query="신한유니버설종신보험 해약환급금은 어떻게 계산되나요?",
                entities={"product_name": "신한유니버설종신보험"},
                routing_hints={"keyword_vector_weight": 0.7},
            ),
        )

        self.assertEqual(payload["filters"], {"product_name": ["신한유니버설종신보험"]})
        self.assertEqual(payload["keyword_vector_weight"], 0.7)

    def test_extract_product_name_candidates_prefers_full_product_name_over_truncated_fragment(self) -> None:
        candidates = extract_product_name_candidates(
            "신한진심을품은변액유니버설종신을 연금으로 전환시 연금액은 어떻게 산출이 되나요?"
        )

        self.assertGreaterEqual(len(candidates), 1)
        self.assertEqual(candidates[0], "신한진심을품은변액유니버설종신")

    def test_resolve_search_product_name_filter_uses_full_product_name_when_available(self) -> None:
        query = "신한진심을품은변액유니버설종신을 연금으로 전환시 연금액은 어떻게 산출이 되나요?"
        product_name_filter = resolve_search_product_name_filter(
            ChatRequest(query=query),
            RewriteResult(
                original_query=query,
                rewritten_query=query,
            ),
        )

        self.assertEqual(product_name_filter, ["신한진심을품은변액유니버설종신"])

    def test_build_external_search_payload_omits_empty_filters_when_product_name_missing(self) -> None:
        payload = build_external_search_payload(
            "http://example.com/api/search",
            payload=ChatRequest(query="미성년 계약자가 제지급 요청 시 필요한 서류는 무엇인가?"),
            question="질문",
            query="미성년 계약자가 제지급 요청 시 필요한 서류는 무엇인가?",
            top_k=30,
            final_k=10,
            stored_name=None,
            rewrite_result=RewriteResult(
                original_query="미성년 계약자가 제지급 요청 시 필요한 서류는 무엇인가?",
                rewritten_query="미성년 계약자가 제지급 요청 시 필요한 서류는 무엇인가?",
            ),
        )

        self.assertNotIn("filters", payload)

    def test_parse_query_rewrite_response_promotes_top_level_product_name_and_numeric_weight(self) -> None:
        (
            rewritten_query,
            search_queries,
            _intent,
            _question_type,
            entities,
            routing_hints,
        ) = parse_query_rewrite_response(
            {
                "rewritten_query": "미성년 계약자가 제지급 요청 시 필요한 서류는 무엇인가?",
                "product_name": "신한유니버설종신보험",
                "routing_hints": {"keyword_vector_weight": "0.7"},
            },
            "fallback query",
        )

        self.assertEqual(rewritten_query, "미성년 계약자가 제지급 요청 시 필요한 서류는 무엇인가?")
        self.assertEqual(search_queries[0], rewritten_query)
        self.assertEqual(entities["product_name"], "신한유니버설종신보험")
        self.assertEqual(routing_hints["keyword_vector_weight"], 0.7)

    def test_normalize_keyword_vector_weight_falls_back_to_default_on_invalid_values(self) -> None:
        self.assertEqual(normalize_keyword_vector_weight(None), 0.3)
        self.assertEqual(normalize_keyword_vector_weight("abc"), 0.3)
        self.assertEqual(normalize_keyword_vector_weight("1.2"), 0.3)
        self.assertEqual(normalize_keyword_vector_weight(-0.1), 0.3)
        self.assertEqual(normalize_keyword_vector_weight("0.3"), 0.3)


if __name__ == "__main__":
    unittest.main()
