"use client";

import { startTransition, useDeferredValue, useState } from "react";

type RetrievalHit = {
  id: string;
  text: string;
  content?: string;
  distance?: number;
  rrf_score?: number;
  rerank_score?: number;
  score?: number;
  document_id?: string;
  stored_name?: string;
  matched_queries?: string[];
  source?: string;
  original_name?: string;
  document_name?: string;
  chunk_index?: number;
  page_number?: number;
  section_header?: string;
  header_path?: string;
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
  answer_model?: string | null;
  search_api_endpoint?: string | null;
  action?: string | null;
  query_rewrite_time_ms?: number;
  search_api_response_time_ms?: number;
};

const API_BASE_URL = "/api";
const CUSTOM_LLM_MODEL = "custom";
const DEFAULT_LLM_OPTION = "";
const DEFAULT_QUERY_REWRITE_MODEL = "gpt-4o-mini";
const DEFAULT_ANSWER_MODEL = "gpt-4o";
const QUERY_REWRITE_MODEL_OPTIONS = [
  { label: "Default", value: DEFAULT_LLM_OPTION },
  { label: "GPT-5.4", value: "gpt-5.4" },
  { label: "GPT-5.4 mini", value: "gpt-5.4-mini" },
  { label: "GPT-4.1 mini", value: "gpt-4.1-mini" },
  { label: "GPT-4o mini", value: "gpt-4o-mini" },
  { label: "GPT-4o", value: "gpt-4o" },
  { label: "Custom", value: CUSTOM_LLM_MODEL },
];
const CUSTOM_QUERY_REWRITE_MODEL = CUSTOM_LLM_MODEL;
const CUSTOM_ANSWER_MODEL = CUSTOM_LLM_MODEL;
const ANSWER_MODEL_OPTIONS = [
  { label: "Default", value: DEFAULT_LLM_OPTION },
  { label: "GPT-5.4", value: "gpt-5.4" },
  { label: "GPT-5.4 mini", value: "gpt-5.4-mini" },
  { label: "GPT-4.1 mini", value: "gpt-4.1-mini" },
  { label: "GPT-4o mini", value: "gpt-4o-mini" },
  { label: "GPT-4o", value: "gpt-4o" },
  { label: "Custom", value: CUSTOM_LLM_MODEL },
];
const ANSWER_STREAM_FLUSH_INTERVAL_MS = 20;
const REWRITE_STREAM_FLUSH_INTERVAL_MS = 20;

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
  header_path?: string;
}) {
  const parts: string[] = [];
  if (typeof item.chunk_index === "number") {
    parts.push(`chunk #${item.chunk_index}`);
  }
  if (typeof item.page_number === "number") {
    parts.push(`page ${item.page_number}`);
  }
  const sectionLabel = item.header_path?.trim() || item.section_header?.trim();
  if (sectionLabel) {
    parts.push(sectionLabel);
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

export default function ChatPage() {
  const [query, setQuery] = useState("");
  const [queryRewriteModel, setQueryRewriteModel] = useState(DEFAULT_LLM_OPTION);
  const [queryRewriteBaseUrl, setQueryRewriteBaseUrl] = useState("");
  const [queryRewriteCustomModel, setQueryRewriteCustomModel] = useState("");
  const [queryRewriteApiKey, setQueryRewriteApiKey] = useState("");
  const [answerModel, setAnswerModel] = useState(DEFAULT_LLM_OPTION);
  const [answerBaseUrl, setAnswerBaseUrl] = useState("");
  const [answerCustomModel, setAnswerCustomModel] = useState("");
  const [answerApiKey, setAnswerApiKey] = useState("");
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [streamingRewrittenQuery, setStreamingRewrittenQuery] = useState("");
  const [isStreamingRewrite, setIsStreamingRewrite] = useState(false);
  const [streamingAnswer, setStreamingAnswer] = useState("");
  const [isStreamingAnswer, setIsStreamingAnswer] = useState(false);
  const [responseTimeMs, setResponseTimeMs] = useState<number | null>(null);
  const [message, setMessage] = useState(
    "질문 입력과 응답 확인에 집중할 수 있도록 채팅 화면을 단순하게 유지합니다.",
  );
  const [isLoading, setIsLoading] = useState(false);
  const deferredResult = useDeferredValue(result);
  const isCustomQueryRewriteModel = queryRewriteModel === CUSTOM_QUERY_REWRITE_MODEL;
  const isCustomAnswerModel = answerModel === CUSTOM_ANSWER_MODEL;

  async function consumeChatStream(response: Response, startedAt: number) {
    const streamReader = response.body?.getReader();
    if (!streamReader) {
      throw new Error("Chat stream response body is not available.");
    }

    const textDecoder = new TextDecoder();
    let buffer = "";
    let streamedRewrittenQuery = "";
    let streamedAnswer = "";
    let pendingAnswerChunk = "";
    let pendingRewriteChunk = "";
    let answerFlushTimer: number | null = null;
    let rewriteFlushTimer: number | null = null;
    let finalPayload: ChatResponse | null = null;

    const flushPendingAnswerDelta = () => {
      if (!pendingAnswerChunk) {
        return;
      }
      streamedAnswer += pendingAnswerChunk;
      pendingAnswerChunk = "";
      startTransition(() => {
        setStreamingAnswer(streamedAnswer);
      });
    };

    const flushPendingRewriteDelta = () => {
      if (!pendingRewriteChunk) {
        return;
      }
      streamedRewrittenQuery += pendingRewriteChunk;
      pendingRewriteChunk = "";
      startTransition(() => {
        setStreamingRewrittenQuery(streamedRewrittenQuery);
      });
    };

    const scheduleAnswerFlush = () => {
      if (answerFlushTimer !== null) {
        return;
      }
      answerFlushTimer = window.setTimeout(() => {
        answerFlushTimer = null;
        flushPendingAnswerDelta();
      }, ANSWER_STREAM_FLUSH_INTERVAL_MS);
    };

    const scheduleRewriteFlush = () => {
      if (rewriteFlushTimer !== null) {
        return;
      }
      rewriteFlushTimer = window.setTimeout(() => {
        rewriteFlushTimer = null;
        flushPendingRewriteDelta();
      }, REWRITE_STREAM_FLUSH_INTERVAL_MS);
    };

    const applyDelta = (chunkText: string) => {
      if (!chunkText) {
        return;
      }
      pendingAnswerChunk += chunkText;
      if (chunkText.includes("\n")) {
        flushPendingAnswerDelta();
        return;
      }
      scheduleAnswerFlush();
    };

    const applyRewriteDelta = (chunkText: string) => {
      if (!chunkText) {
        return;
      }
      setIsStreamingRewrite(true);
      pendingRewriteChunk += chunkText;
      if (chunkText.includes("\n")) {
        flushPendingRewriteDelta();
        return;
      }
      scheduleRewriteFlush();
    };

    while (true) {
      const { value, done } = await streamReader.read();
      if (done) {
        break;
      }

      buffer += textDecoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");

      while (true) {
        const boundaryIndex = buffer.indexOf("\n\n");
        if (boundaryIndex === -1) {
          break;
        }

        const rawEvent = buffer.slice(0, boundaryIndex).trim();
        buffer = buffer.slice(boundaryIndex + 2);
        if (!rawEvent) {
          continue;
        }

        let eventName = "message";
        const dataLines: string[] = [];
        for (const line of rawEvent.split("\n")) {
          if (line.startsWith("event:")) {
            eventName = line.slice("event:".length).trim();
            continue;
          }
          if (line.startsWith("data:")) {
            dataLines.push(line.slice("data:".length).trimStart());
          }
        }

        const rawData = dataLines.join("\n");
        if (!rawData) {
          continue;
        }

        let parsedData: unknown;
        try {
          parsedData = JSON.parse(rawData);
        } catch {
          if (eventName === "delta") {
            applyDelta(rawData);
          }
          continue;
        }

        if (eventName === "meta" && parsedData && typeof parsedData === "object") {
          const metaPayload = parsedData as ChatResponse;
          if (!streamedRewrittenQuery && typeof metaPayload.rewritten_query === "string" && metaPayload.rewritten_query.trim()) {
            streamedRewrittenQuery = metaPayload.rewritten_query;
            startTransition(() => {
              setStreamingRewrittenQuery(streamedRewrittenQuery);
            });
          }
          startTransition(() => {
            setResult({
              ...metaPayload,
              answer: streamedAnswer || metaPayload.answer || "",
            });
          });
          continue;
        }

        if (eventName === "rewrite_delta" && parsedData && typeof parsedData === "object") {
          const content = (parsedData as { content?: unknown }).content;
          if (typeof content === "string") {
            applyRewriteDelta(content);
          }
          continue;
        }

        if (eventName === "rewrite_done" && parsedData && typeof parsedData === "object") {
          if (rewriteFlushTimer !== null) {
            window.clearTimeout(rewriteFlushTimer);
            rewriteFlushTimer = null;
          }
          flushPendingRewriteDelta();
          const rewrittenQuery = (parsedData as { rewritten_query?: unknown }).rewritten_query;
          if (typeof rewrittenQuery === "string" && rewrittenQuery.trim()) {
            streamedRewrittenQuery = rewrittenQuery;
            startTransition(() => {
              setStreamingRewrittenQuery(rewrittenQuery);
            });
          }
          setIsStreamingRewrite(false);
          continue;
        }

        if (eventName === "delta" && parsedData && typeof parsedData === "object") {
          const content = (parsedData as { content?: unknown }).content;
          if (typeof content === "string") {
            applyDelta(content);
          }
          continue;
        }

        if (eventName === "answer_replace" && parsedData && typeof parsedData === "object") {
          const content = (parsedData as { content?: unknown }).content;
          if (typeof content === "string") {
            if (answerFlushTimer !== null) {
              window.clearTimeout(answerFlushTimer);
              answerFlushTimer = null;
            }
            pendingAnswerChunk = "";
            streamedAnswer = content;
            startTransition(() => {
              setStreamingAnswer(content);
              setResult((previous) => ({
                ...(previous ?? {}),
                answer: content,
                insufficient_context: false,
              }));
            });
          }
          continue;
        }

        if (eventName === "error" && parsedData && typeof parsedData === "object") {
          const detail = (parsedData as { detail?: unknown }).detail;
          throw new Error(typeof detail === "string" && detail ? detail : "Chat stream failed.");
        }

        if (eventName === "done" && parsedData && typeof parsedData === "object") {
          finalPayload = parsedData as ChatResponse;
        }
      }
    }

    if (answerFlushTimer !== null) {
      window.clearTimeout(answerFlushTimer);
      answerFlushTimer = null;
    }
    if (rewriteFlushTimer !== null) {
      window.clearTimeout(rewriteFlushTimer);
      rewriteFlushTimer = null;
    }
    flushPendingAnswerDelta();
    flushPendingRewriteDelta();

    if (finalPayload) {
      startTransition(() => {
        setResult(finalPayload);
      });
      if (typeof finalPayload.rewritten_query === "string" && finalPayload.rewritten_query.trim()) {
        setStreamingRewrittenQuery(finalPayload.rewritten_query);
      }
      setStreamingAnswer(finalPayload.answer ?? streamedAnswer);
      setMessage(
        finalPayload.answer
          ? "응답을 불러왔습니다."
          : "응답 본문은 비어 있지만 화면 구조는 유지됩니다.",
      );
    } else if (streamedAnswer.trim()) {
      startTransition(() => {
        setResult((previous) => ({
          ...(previous ?? {}),
          answer: streamedAnswer,
        }));
      });
      setMessage("응답을 불러왔습니다.");
    } else {
      setMessage("응답 본문은 비어 있지만 화면 구조는 유지됩니다.");
    }

    setIsStreamingRewrite(false);
    setIsStreamingAnswer(false);
    setResponseTimeMs(Math.round(performance.now() - startedAt));
  }

  async function requestChatResponse() {
    if (!query.trim()) {
      setMessage("질문을 먼저 입력하세요.");
      return;
    }
    if (isCustomQueryRewriteModel && !queryRewriteBaseUrl.trim()) {
      setMessage("Custom Query Rewrite LLM의 LLM endpoint를 입력하세요.");
      return;
    }
    if (isCustomQueryRewriteModel && !queryRewriteCustomModel.trim()) {
      setMessage("Custom Query Rewrite LLM의 LLM model name을 입력하세요.");
      return;
    }
    if (isCustomAnswerModel && !answerBaseUrl.trim()) {
      setMessage("Custom Answer LLM의 LLM endpoint를 입력하세요.");
      return;
    }
    if (isCustomAnswerModel && !answerCustomModel.trim()) {
      setMessage("Custom Answer LLM의 LLM model name을 입력하세요.");
      return;
    }

    setIsLoading(true);
    setIsStreamingRewrite(false);
    setStreamingRewrittenQuery("");
    setIsStreamingAnswer(false);
    setStreamingAnswer("");
    setResponseTimeMs(null);
    setMessage("Search 응답을 불러오는 중입니다.");

    try {
      const startedAt = performance.now();
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          action: "search",
          top_k: 30,
          final_k: 10,
          query_rewrite_model: queryRewriteModel || null,
          query_rewrite_base_url: isCustomQueryRewriteModel ? queryRewriteBaseUrl.trim() : null,
          query_rewrite_custom_model: isCustomQueryRewriteModel ? queryRewriteCustomModel.trim() : null,
          query_rewrite_api_key: isCustomQueryRewriteModel ? queryRewriteApiKey : null,
          answer_model: answerModel || null,
          answer_base_url: isCustomAnswerModel ? answerBaseUrl.trim() : null,
          answer_custom_model: isCustomAnswerModel ? answerCustomModel.trim() : null,
          answer_api_key: isCustomAnswerModel ? answerApiKey : null,
          stream: true,
        }),
      });

      const contentType = response.headers.get("content-type") ?? "";
      if (contentType.includes("text/event-stream")) {
        if (!response.ok) {
          throw new Error("Chat stream request failed.");
        }
        setIsStreamingAnswer(true);
        await consumeChatStream(response, startedAt);
        return;
      }

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
      setStreamingRewrittenQuery(data.rewritten_query ?? "");
      setIsStreamingRewrite(false);
      setMessage(
        data.answer
          ? "응답을 불러왔습니다."
          : "응답 본문은 비어 있지만 화면 구조는 유지됩니다.",
      );
    } catch (error) {
      setIsStreamingRewrite(false);
      setIsStreamingAnswer(false);
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
    return hit.document_name ?? hit.source ?? hit.original_name ?? "Unknown source";
  }

  const answerState = isStreamingAnswer ? "Streaming" : formatAnswerState(result);
  const displayedRewrittenQuery = streamingRewrittenQuery.trim()
    ? streamingRewrittenQuery
    : result?.rewritten_query;
  const displayedAnswer = isStreamingAnswer ? streamingAnswer : result?.answer;
  const answer = displayedAnswer ?? "아직 연결된 최종 응답 본문은 없습니다.";
  const showEvidenceSection = false;

  return (
    <section className="page chat-page">
      <div className="chat-layout">
        <div className="chat-left-column">
          <div className="card chat-card">
            <p className="eyebrow">Chat</p>
            <h2>Chat</h2>
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
              {isCustomQueryRewriteModel ? (
                <>
                  <label className="upload-label" htmlFor="chat-query-rewrite-base-url">
                    LLM endpoint
                  </label>
                  <input
                    className="default-file-select"
                    id="chat-query-rewrite-base-url"
                    onChange={(event) => setQueryRewriteBaseUrl(event.target.value)}
                    placeholder="http://10.x.x.x:8000/v1"
                    type="text"
                    value={queryRewriteBaseUrl}
                  />
                  <label className="upload-label" htmlFor="chat-query-rewrite-custom-model">
                    LLM model name
                  </label>
                  <input
                    className="default-file-select"
                    id="chat-query-rewrite-custom-model"
                    onChange={(event) => setQueryRewriteCustomModel(event.target.value)}
                    placeholder="gpt-4o-mini"
                    type="text"
                    value={queryRewriteCustomModel}
                  />
                  <label className="upload-label" htmlFor="chat-query-rewrite-api-key">
                    API Key
                  </label>
                  <input
                    autoComplete="off"
                    className="default-file-select"
                    id="chat-query-rewrite-api-key"
                    onChange={(event) => setQueryRewriteApiKey(event.target.value)}
                    placeholder="필요한 경우만 입력"
                    type="password"
                    value={queryRewriteApiKey}
                  />
                  <div className="chat-note">
                    Custom LLM은 OpenAI-compatible API만 지원하며, 모든 LLM 호출은 `temperature=0`, `top_p=0.9`, `max_tokens=700` 기본값을 사용합니다.
                  </div>
                </>
              ) : null}
              <label className="upload-label" htmlFor="chat-answer-model">
                Answer LLM
              </label>
              <select
                className="default-file-select"
                id="chat-answer-model"
                onChange={(event) => setAnswerModel(event.target.value)}
                value={answerModel}
              >
                {ANSWER_MODEL_OPTIONS.map((option) => (
                  <option key={option.label} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              {isCustomAnswerModel ? (
                <>
                  <label className="upload-label" htmlFor="chat-answer-base-url">
                    LLM endpoint
                  </label>
                  <input
                    className="default-file-select"
                    id="chat-answer-base-url"
                    onChange={(event) => setAnswerBaseUrl(event.target.value)}
                    placeholder="http://10.x.x.x:8000/v1"
                    type="text"
                    value={answerBaseUrl}
                  />
                  <label className="upload-label" htmlFor="chat-answer-custom-model">
                    LLM model name
                  </label>
                  <input
                    className="default-file-select"
                    id="chat-answer-custom-model"
                    onChange={(event) => setAnswerCustomModel(event.target.value)}
                    placeholder="gpt-4o"
                    type="text"
                    value={answerCustomModel}
                  />
                  <label className="upload-label" htmlFor="chat-answer-api-key">
                    API Key
                  </label>
                  <input
                    autoComplete="off"
                    className="default-file-select"
                    id="chat-answer-api-key"
                    onChange={(event) => setAnswerApiKey(event.target.value)}
                    placeholder="필요한 경우만 입력"
                    type="password"
                    value={answerApiKey}
                  />
                  <div className="chat-note">
                    Custom Answer LLM은 OpenAI-compatible API만 지원하며, 모든 LLM 호출은 `temperature=0`, `top_p=0.9`, `max_tokens=700` 기본값을 사용합니다.
                  </div>
                </>
              ) : null}
              <div className="chat-query-preview">
                <span className="chat-query-preview-label">LLM Question</span>
                <div className={`chat-query-preview-body${isStreamingRewrite ? " streaming" : ""}`}>
                  {displayedRewrittenQuery?.trim()
                    ? displayedRewrittenQuery
                    : "응답 후 이 위치에 LLM이 정리한 질문이 표시됩니다."}
                  {isStreamingRewrite ? <span className="stream-cursor" aria-hidden="true">▌</span> : null}
                </div>
              </div>
              <div className="button-row">
                <button className="upload-button" disabled={isLoading} onClick={() => void requestChatResponse()} type="button">
                  {isLoading ? "Loading..." : "Get response"}
                </button>
              </div>
            </div>
            <div className="chat-status">{message}</div>
          </div>
        </div>

        <div className="chat-right-column">
          <div className="card">
            <p className="eyebrow">Answer</p>
            <h2>Response</h2>
            <p>최종 연결 시 이 영역에 외부 RAG 응답 또는 후속 answer generation 결과가 표시됩니다.</p>
            {!result && !isStreamingAnswer ? (
              <p>아직 표시할 응답이 없습니다.</p>
            ) : (
              <div className="answer-panel">
                {result && typeof responseTimeMs === "number" ? (
                  <div className="answer-latency">{formatResponseTiming(responseTimeMs, result)}</div>
                ) : null}
                <div className="answer-summary">
                  <span>{answerState}</span>
                  {result?.action ? <span>Mode: {result.action}</span> : null}
                  {result?.query_rewrite_model ? <span>Rewrite LLM: {result.query_rewrite_model}</span> : null}
                  {result?.answer_model ? <span>Answer LLM: {result.answer_model}</span> : null}
                  {result?.search_api_endpoint ? <span>Search: {result.search_api_endpoint}</span> : null}
                </div>
                <div className={`answer-body${result?.insufficient_context ? " warning" : ""}${isStreamingAnswer ? " streaming" : ""}`}>
                  <div data-testid="answer">{answer}</div>
                  {isStreamingAnswer ? <span className="stream-cursor" aria-hidden="true">▌</span> : null}
                </div>
              </div>
            )}
          </div>

          {showEvidenceSection ? (
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
          ) : null}

          <div className="card">
            <p className="eyebrow">Context</p>
            <h2>Reference context</h2>
            <p>answer generation에 실제로 들어간 retrieval hit를 순서대로 보여주며, rerank score와 matched query도 함께 표시합니다.</p>
            {isStreamingAnswer ? (
              <p>스트리밍 중에는 context 렌더링을 잠시 지연합니다.</p>
            ) : !deferredResult?.hits?.length ? (
              <p>아직 표시할 context가 없습니다.</p>
            ) : (
              <div className="retrieval-list">
                {deferredResult.hits.map((hit, index) => {
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
                            {typeof hit.rrf_score === "number" ? <span>rrf {hit.rrf_score.toFixed(4)}</span> : null}
                            {typeof hit.rerank_score === "number" ? <span>rerank {hit.rerank_score.toFixed(4)}</span> : null}
                            {typeof hit.score === "number" ? <span>score {hit.score.toFixed(4)}</span> : null}
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
        </div>
      </div>
    </section>
  );
}
