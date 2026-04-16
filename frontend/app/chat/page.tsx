"use client";

import { useState } from "react";

type RetrievalHit = {
  id: string;
  text: string;
  distance?: number;
  rerank_score?: number;
  document_id?: string;
  stored_name?: string;
  matched_queries?: string[];
  source?: string;
  original_name?: string;
  chunk_index?: number;
  page_number?: number;
  section_header?: string;
  preview?: string;
};

type ChatCitation = {
  id?: string;
  rank?: number;
  source?: string;
  original_name?: string;
  chunk_index?: number;
  page_number?: number;
  section_header?: string;
};

type ChatResponse = {
  answer?: string;
  insufficient_context?: boolean;
  citations?: ChatCitation[];
  hits?: RetrievalHit[];
  detail?: string;
  rewritten_query?: string;
  query_rewrite_model?: string | null;
  search_api_endpoint?: string | null;
  lookup_api_endpoint?: string | null;
  action?: string | null;
  query_rewrite_time_ms?: number;
  search_api_response_time_ms?: number;
};

const API_BASE_URL = "/api";
const QUERY_REWRITE_MODEL_OPTIONS = [
  { label: "Default (gpt-4o-mini)", value: "" },
  { label: "GPT-4.1 mini", value: "gpt-4.1-mini" },
  { label: "GPT-4o", value: "gpt-4o" },
];

function formatAnswerState(result: ChatResponse | null) {
  if (!result) {
    return "Waiting";
  }
  if (result.insufficient_context) {
    return "Insufficient context";
  }
  if (!result.answer?.trim()) {
    return "Empty response";
  }
  return "Ready";
}

function buildEvidenceMetaParts(item: {
  chunk_index?: number;
  page_number?: number;
  section_header?: string;
}) {
  const parts: string[] = [];
  if (typeof item.chunk_index === "number") {
    parts.push(`chunk #${item.chunk_index}`);
  }
  if (typeof item.page_number === "number") {
    parts.push(`page ${item.page_number}`);
  }
  if (item.section_header?.trim()) {
    parts.push(item.section_header.trim());
  }
  return parts;
}

function formatMatchedQueries(matchedQueries?: string[]) {
  if (!matchedQueries?.length) {
    return null;
  }
  return matchedQueries.join(" | ");
}

function formatSeconds(milliseconds: number) {
  return `${(milliseconds / 1000).toFixed(2)} s`;
}

function formatResponseTiming(totalMs: number, result: ChatResponse) {
  const detailParts: string[] = [];
  if (typeof result.query_rewrite_time_ms === "number") {
    detailParts.push(`Query rewrite time: ${formatSeconds(result.query_rewrite_time_ms)}`);
  }
  if (typeof result.search_api_response_time_ms === "number") {
    detailParts.push(`API response time: ${formatSeconds(result.search_api_response_time_ms)}`);
  }

  if (!detailParts.length) {
    return `Response time: ${formatSeconds(totalMs)}`;
  }
  return `Response time: ${formatSeconds(totalMs)}, (${detailParts.join(", ")})`;
}

function pickLookupTarget(result: ChatResponse | null): { documentId: string; sectionHint: string | null } | null {
  if (result?.action !== "search" || !result.hits?.length) {
    return null;
  }

  const rankedHits = result.hits.filter((hit) => (hit.document_id || hit.stored_name) && typeof hit.rerank_score === "number");
  const targetHit =
    rankedHits.sort((left, right) => (right.rerank_score ?? Number.NEGATIVE_INFINITY) - (left.rerank_score ?? Number.NEGATIVE_INFINITY))[0]
    ?? result.hits.find((hit) => hit.document_id || hit.stored_name);

  if (!targetHit) {
    return null;
  }

  return {
    documentId: targetHit.document_id ?? targetHit.stored_name ?? "",
    sectionHint: targetHit.section_header?.trim() || null,
  };
}

export default function ChatPage() {
  const [query, setQuery] = useState("");
  const [queryRewriteModel, setQueryRewriteModel] = useState("");
  const [finalK, setFinalK] = useState("5");
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [responseTimeMs, setResponseTimeMs] = useState<number | null>(null);
  const [message, setMessage] = useState(
    "질문 입력과 응답 확인에 집중할 수 있도록 채팅 화면을 단순하게 유지합니다.",
  );
  const [isLoading, setIsLoading] = useState(false);

  async function requestChatResponse(action: "search" | "lookup") {
    if (!query.trim()) {
      setMessage("질문을 먼저 입력하세요.");
      return;
    }

    const lookupTarget = action === "lookup" ? pickLookupTarget(result) : null;
    if (action === "lookup" && !lookupTarget?.documentId) {
      setMessage("먼저 Get response로 Search 결과를 조회한 뒤 Lookup을 실행하세요.");
      return;
    }

    setIsLoading(true);
    setResponseTimeMs(null);
    setMessage(action === "lookup" ? "Lookup 응답을 불러오는 중입니다." : "Search 응답을 불러오는 중입니다.");

    try {
      const startedAt = performance.now();
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          action,
          final_k: Number.parseInt(finalK, 10) || 5,
          document_id: lookupTarget?.documentId ?? null,
          section_hint: lookupTarget?.sectionHint ?? null,
          query_rewrite_model: queryRewriteModel || null,
        }),
      });

      const data = (await response.json()) as ChatResponse;
      if (!response.ok) {
        if (data.rewritten_query?.trim()) {
          setResult(data);
        } else {
          setResult(null);
        }
        throw new Error(data.detail ?? "Chat request failed.");
      }

      setResponseTimeMs(Math.round(performance.now() - startedAt));
      setResult(data);
      setMessage(
        data.answer
          ? "응답을 불러왔습니다."
          : "응답 본문은 비어 있지만 화면 구조는 유지됩니다.",
      );
    } catch (error) {
      setResponseTimeMs(null);
      setMessage(error instanceof Error ? error.message : "Chat request failed.");
    } finally {
      setIsLoading(false);
    }
  }

  function renderCitationLabel(citation: ChatCitation) {
    return citation.source ?? citation.original_name ?? "Unknown source";
  }

  function renderHitLabel(hit: RetrievalHit) {
    return hit.source ?? hit.original_name ?? "Unknown source";
  }

  const answerState = formatAnswerState(result);

  return (
    <section className="page">
      <div className="card">
        <p className="eyebrow">Chat</p>
        <h2>Chat</h2>
        <p>외부 RAG 연동 세부 스키마가 정해지기 전까지는 질문, 응답, 근거 표시 구조를 먼저 고정합니다.</p>
        <div className="chat-form">
          <label className="upload-label" htmlFor="chat-query">
            Question
          </label>
          <textarea
            className="chat-textarea"
            id="chat-query"
            onChange={(event) => setQuery(event.target.value)}
            placeholder={"단일 질문 또는 멀티라인 상담 대화를 입력하세요.\n예:\n고객: 실손보험 청구하려고 하는데요.\n상담사: 어떤 부분이 궁금하신가요?\n고객: 통원 치료도 청구 가능한가요?"}
            rows={6}
            value={query}
          />
          <div className="chat-note">
            `고객:` / `상담사:` 라벨이 있는 멀티라인 입력은 backend에서 `conversation_context`로 해석합니다.
          </div>
          <label className="upload-label" htmlFor="chat-query-rewrite-model">
            Query rewrite LLM
          </label>
          <select
            className="default-file-select"
            id="chat-query-rewrite-model"
            onChange={(event) => setQueryRewriteModel(event.target.value)}
            value={queryRewriteModel}
          >
            {QUERY_REWRITE_MODEL_OPTIONS.map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <div className="chat-query-preview">
            <span className="chat-query-preview-label">LLM Question</span>
            <div className="chat-query-preview-body">
              {result?.rewritten_query?.trim()
                ? result.rewritten_query
                : "응답 후 이 위치에 LLM이 정리한 질문이 표시됩니다."}
            </div>
          </div>
          <label className="upload-label" htmlFor="chat-final-k">
            Search final_k
          </label>
          <input
            className="default-file-select"
            id="chat-final-k"
            inputMode="numeric"
            min="1"
            onChange={(event) => setFinalK(event.target.value)}
            placeholder="5"
            type="number"
            value={finalK}
          />
          <div className="button-row">
            <button className="upload-button" disabled={isLoading} onClick={() => void requestChatResponse("search")} type="button">
              {isLoading ? "Loading..." : "Get response"}
            </button>
          </div>
        </div>
        <div className="chat-note">
          `Get response`는 Search API만 호출합니다.
        </div>
        <div className="chat-status">{message}</div>
      </div>

      <div className="card">
        <p className="eyebrow">Answer</p>
        <h2>Response</h2>
        <p>최종 연결 시 이 영역에 외부 RAG 응답 또는 후속 answer generation 결과가 표시됩니다.</p>
        {!result ? (
          <p>아직 표시할 응답이 없습니다.</p>
        ) : (
          <div className="answer-panel">
            {typeof responseTimeMs === "number" ? (
              <div className="answer-latency">{formatResponseTiming(responseTimeMs, result)}</div>
            ) : null}
            <div className="answer-summary">
              <span>{answerState}</span>
              {result.action ? <span>Mode: {result.action}</span> : null}
              {result.query_rewrite_model ? <span>Rewrite LLM: {result.query_rewrite_model}</span> : null}
              {result.search_api_endpoint ? <span>Search: {result.search_api_endpoint}</span> : null}
              {result.action === "lookup" && result.lookup_api_endpoint ? <span>Lookup: {result.lookup_api_endpoint}</span> : null}
            </div>
            <div className={`answer-body${result.insufficient_context ? " warning" : ""}`}>
              {result.answer ?? "아직 연결된 최종 응답 본문은 없습니다."}
            </div>
          </div>
        )}
      </div>

      <div className="card">
        <p className="eyebrow">Citations</p>
        <h2>Evidence</h2>
        <p>답변 근거로 사용한 chunk 포인터만 간단히 보여주고, 실제 본문은 아래 Reference context에서 확인합니다.</p>
        {!result?.citations?.length ? (
          <p>아직 표시할 근거가 없습니다.</p>
        ) : (
          <div className="citation-list">
            {result.citations.map((citation) => {
              const metaParts = buildEvidenceMetaParts(citation);
              return (
                <article className="citation-card" key={citation.id ?? `${citation.source}-${citation.chunk_index}`}>
                  <div className="citation-card-head">
                    <strong>{renderCitationLabel(citation)}</strong>
                    {typeof citation.rank === "number" ? <span className="citation-rank">#{citation.rank}</span> : null}
                  </div>
                  <div className="retrieval-meta">
                    {metaParts.length > 0 ? metaParts.map((part) => <span key={part}>{part}</span>) : <span>metadata unavailable</span>}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>

      <div className="card">
        <p className="eyebrow">Context</p>
        <h2>Reference context</h2>
        <p>answer generation에 실제로 들어간 retrieval hit를 순서대로 보여주며, rerank score와 matched query도 함께 표시합니다.</p>
        {!result?.hits?.length ? (
          <p>아직 표시할 context가 없습니다.</p>
        ) : (
          <div className="retrieval-list">
            {result.hits.map((hit, index) => {
              const metaParts = buildEvidenceMetaParts(hit);
              const matchedQueries = formatMatchedQueries(hit.matched_queries);
              return (
                <article className="retrieval-card" key={hit.id}>
                  <div className="retrieval-head">
                    <div className="retrieval-title">
                      <div className="retrieval-rank-row">
                        <strong>{renderHitLabel(hit)}</strong>
                        <span className="retrieval-rank">Context #{index + 1}</span>
                      </div>
                      <div className="retrieval-meta">
                        {metaParts.map((part) => (
                          <span key={part}>{part}</span>
                        ))}
                        {typeof hit.distance === "number" ? <span>distance {hit.distance.toFixed(4)}</span> : null}
                        {typeof hit.rerank_score === "number" ? <span>rerank {hit.rerank_score.toFixed(4)}</span> : null}
                      </div>
                    </div>
                  </div>
                  {matchedQueries ? (
                    <div className="retrieval-query-block">
                      <span className="retrieval-query-label">matched queries</span>
                      <div className="retrieval-tags">
                        {hit.matched_queries?.map((matchedQuery) => <span key={matchedQuery}>{matchedQuery}</span>)}
                      </div>
                    </div>
                  ) : null}
                  <div className="retrieval-preview">{hit.preview ?? hit.text}</div>
                  <details className="parse-json retrieval-full">
                    <summary>전체 context 보기</summary>
                    <div className="retrieval-full-body">
                      <pre>{hit.text}</pre>
                    </div>
                  </details>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
