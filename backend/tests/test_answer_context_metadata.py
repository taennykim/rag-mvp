import unittest
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import (
    EMPTY_CONTENT_PLACEHOLDER,
    UNKNOWN_DOCUMENT_NAME,
    UNKNOWN_HEADER_PATH,
    RewriteResult,
    build_answer_generation_messages,
    build_external_search_payload,
    build_standardized_retrieved_chunks,
    filter_hits_for_answer_generation,
    format_chat_context,
    normalize_external_search_hit,
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

    def test_build_external_search_payload_omits_chunk_types(self) -> None:
        payload = build_external_search_payload(
            "http://example.com/api/search",
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

        self.assertEqual(payload["filters"], {"year": ["2024"], "document_type": ["statistics_table"]})
        self.assertNotIn("chunk_types", payload)


if __name__ == "__main__":
    unittest.main()
