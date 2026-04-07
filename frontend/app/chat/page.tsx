"use client";

import { FormEvent, useState } from "react";

type RetrievalHit = {
  id: string;
  text: string;
  distance?: number;
  source?: string;
  original_name?: string;
  chunk_index?: number;
  page_number?: number;
  section_header?: string;
  preview?: string;
};

type ChatCitation = {
  id?: string;
  source?: string;
  original_name?: string;
  chunk_index?: number;
  page_number?: number;
  section_header?: string;
  preview?: string;
};

type ChatResponse = {
  answer?: string;
  insufficient_context?: boolean;
  citations?: ChatCitation[];
  hits?: RetrievalHit[];
  detail?: string;
  search_api_endpoint?: string | null;
  lookup_api_endpoint?: string | null;
};

const API_BASE_URL = "/api";

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

export default function ChatPage() {
  const [query, setQuery] = useState("");
  const [searchApiEndpoint, setSearchApiEndpoint] = useState("");
  const [lookupApiEndpoint, setLookupApiEndpoint] = useState("");
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [message, setMessage] = useState(
    "질문 입력과 응답 확인에 집중할 수 있도록 채팅 화면을 단순하게 유지합니다.",
  );
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!query.trim()) {
      setMessage("질문을 먼저 입력하세요.");
      return;
    }

    setIsLoading(true);
    setMessage("응답을 불러오는 중입니다.");

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          search_api_endpoint: searchApiEndpoint.trim() || null,
          lookup_api_endpoint: lookupApiEndpoint.trim() || null,
        }),
      });

      const data = (await response.json()) as ChatResponse;
      if (!response.ok) {
        throw new Error(data.detail ?? "Chat request failed.");
      }

      setResult(data);
      setMessage(
        data.answer
          ? "응답을 불러왔습니다."
          : "응답 본문은 비어 있지만 화면 구조는 유지됩니다.",
      );
    } catch (error) {
      setResult(null);
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
        <form className="chat-form" onSubmit={handleSubmit}>
          <label className="upload-label" htmlFor="chat-query">
            Question
          </label>
          <textarea
            className="chat-textarea"
            id="chat-query"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="보험 약관, 서류 안내, 보장 조건처럼 사용자가 실제로 물을 질문을 입력하세요."
            rows={4}
            value={query}
          />
          <label className="upload-label" htmlFor="chat-search-api-endpoint">
            Search API endpoint
          </label>
          <input
            className="default-file-select"
            id="chat-search-api-endpoint"
            onChange={(event) => setSearchApiEndpoint(event.target.value)}
            placeholder="선택 입력"
            type="text"
            value={searchApiEndpoint}
          />
          <label className="upload-label" htmlFor="chat-lookup-api-endpoint">
            Lookup API endpoint
          </label>
          <input
            className="default-file-select"
            id="chat-lookup-api-endpoint"
            onChange={(event) => setLookupApiEndpoint(event.target.value)}
            placeholder="선택 입력"
            type="text"
            value={lookupApiEndpoint}
          />
          <button className="upload-button" disabled={isLoading} type="submit">
            {isLoading ? "Loading..." : "Get response"}
          </button>
        </form>
        <div className="chat-note">
          Search API endpoint를 비우면 내부 RAG를 조회하고, 값을 넣으면 해당 외부 search endpoint를 호출합니다.
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
            <div className="answer-summary">
              <span>{answerState}</span>
              {result.search_api_endpoint ? <span>Search: {result.search_api_endpoint}</span> : null}
              {result.lookup_api_endpoint ? <span>Lookup: {result.lookup_api_endpoint}</span> : null}
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
        <p>citation 데이터가 오면 이 영역에 출처, 페이지, 미리보기를 함께 표시합니다.</p>
        {!result?.citations?.length ? (
          <p>아직 표시할 근거가 없습니다.</p>
        ) : (
          <div className="citation-list">
            {result.citations.map((citation) => {
              const metaParts = buildEvidenceMetaParts(citation);
              return (
                <article className="citation-card" key={citation.id ?? `${citation.source}-${citation.chunk_index}`}>
                  <strong>{renderCitationLabel(citation)}</strong>
                  {metaParts.length > 0 ? (
                    <div className="retrieval-meta">
                      {metaParts.map((part) => (
                        <span key={part}>{part}</span>
                      ))}
                    </div>
                  ) : null}
                  {citation.preview ? <div className="citation-preview">{citation.preview}</div> : null}
                </article>
              );
            })}
          </div>
        )}
      </div>

      <div className="card">
        <p className="eyebrow">Context</p>
        <h2>Reference context</h2>
        <p>현재 backend가 `hits`를 주는 동안만 참고용 context를 보여줍니다. 외부 RAG 스키마가 정해지면 이 영역도 그 기준으로 다시 맞춥니다.</p>
        {!result?.hits?.length ? (
          <p>아직 표시할 context가 없습니다.</p>
        ) : (
          <div className="retrieval-list">
            {result.hits.map((hit) => {
              const metaParts = buildEvidenceMetaParts(hit);
              return (
                <article className="retrieval-card" key={hit.id}>
                  <div className="retrieval-head">
                    <div className="retrieval-title">
                      <strong>{renderHitLabel(hit)}</strong>
                      <div className="retrieval-meta">
                        {metaParts.map((part) => (
                          <span key={part}>{part}</span>
                        ))}
                        {typeof hit.distance === "number" ? <span>distance {hit.distance.toFixed(4)}</span> : null}
                      </div>
                    </div>
                  </div>
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
