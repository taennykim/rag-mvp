"use client";

import { FormEvent, useEffect, useState } from "react";

type UploadedFile = {
  stored_name: string;
  original_name: string;
  size_bytes: number;
  uploaded_at: string;
};

type IndexedFile = {
  stored_name: string;
  original_name: string;
  file_type: string;
  chunk_count: number;
};

type RetrievalHit = {
  id: string;
  text: string;
  distance: number;
  stored_name?: string;
  original_name?: string;
  source?: string;
  chunk_index?: number;
  text_length?: number;
  start_char?: number;
  end_char?: number;
  page_number?: number;
  section_header?: string;
  preview?: string;
};

type RetrievalResponse = {
  status: string;
  query: string;
  top_k: number;
  hit_count: number;
  collection_name: string;
  hits: RetrievalHit[];
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  (typeof window === "undefined" ? "http://localhost:8000" : `${window.location.protocol}//${window.location.hostname}:8000`);

export default function ChatPage() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [indexedFiles, setIndexedFiles] = useState<IndexedFile[]>([]);
  const [selectedStoredName, setSelectedStoredName] = useState("");
  const [query, setQuery] = useState("계약자 변경");
  const [topK, setTopK] = useState(5);
  const [result, setResult] = useState<RetrievalResponse | null>(null);
  const [message, setMessage] = useState("Ask a question to inspect retrieved chunks before answer generation.");
  const [isLoading, setIsLoading] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  async function loadFiles() {
    try {
      const [uploadedResponse, indexedResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/upload/files`, { cache: "no-store" }),
        fetch(`${API_BASE_URL}/index/files`, { cache: "no-store" }),
      ]);
      if (!uploadedResponse.ok) {
        throw new Error("Failed to load uploaded files.");
      }
      if (!indexedResponse.ok) {
        throw new Error("Failed to load indexed files.");
      }

      const uploadedData = (await uploadedResponse.json()) as { files: UploadedFile[] };
      const indexedData = (await indexedResponse.json()) as { files: IndexedFile[] };
      setUploadedFiles(uploadedData.files);
      setIndexedFiles(indexedData.files);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to load uploaded files.");
    }
  }

  useEffect(() => {
    void loadFiles();

    function handleFocus() {
      void loadFiles();
    }

    function handleVisibilityChange() {
      if (document.visibilityState === "visible") {
        void loadFiles();
      }
    }

    window.addEventListener("focus", handleFocus);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      window.removeEventListener("focus", handleFocus);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  function formatDistance(value: number) {
    return value.toFixed(4);
  }

  const unindexedCount = Math.max(uploadedFiles.length - indexedFiles.length, 0);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!query.trim()) {
      setMessage("Enter a search query first.");
      return;
    }

    setIsLoading(true);
    setMessage("Retrieving relevant chunks...");

    try {
      const response = await fetch(`${API_BASE_URL}/retrieve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          top_k: topK,
          stored_name: selectedStoredName || null,
        }),
      });

      const data = (await response.json()) as RetrievalResponse & { detail?: string };
      if (!response.ok) {
        throw new Error(data.detail ?? "Retrieval failed.");
      }

      setResult(data);
      setMessage(`Retrieved ${data.hit_count} chunk(s) from ${data.collection_name}.`);
    } catch (error) {
      setResult(null);
      setMessage(error instanceof Error ? error.message : "Retrieval failed.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleResetIndexedFiles() {
    setIsResetting(true);
    setMessage("Clearing indexed chunks...");

    try {
      const response = await fetch(`${API_BASE_URL}/index/files`, {
        method: "DELETE",
      });
      const data = (await response.json()) as { removed_count?: number; detail?: string };
      if (!response.ok) {
        throw new Error(data.detail ?? "Failed to clear indexed files.");
      }

      setSelectedStoredName("");
      setResult(null);
      await loadFiles();
      setMessage(`Cleared ${data.removed_count ?? 0} indexed chunk(s).`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to clear indexed files.");
    } finally {
      setIsResetting(false);
    }
  }

  return (
    <section className="page">
      <div className="card">
        <p className="eyebrow">Chat</p>
        <h2>Retrieval test</h2>
        <p>질문을 넣고, 어떤 chunk가 근거로 잡히는지 먼저 확인합니다.</p>
        <div className="chat-toolbar">
          <button className="upload-button secondary" onClick={() => void loadFiles()} type="button">
            Refresh indexed files
          </button>
          <button className="upload-button secondary danger" disabled={isResetting} onClick={() => void handleResetIndexedFiles()} type="button">
            {isResetting ? "Resetting..." : "Reset indexed files"}
          </button>
        </div>
        <form className="chat-form" onSubmit={handleSubmit}>
          <label className="upload-label" htmlFor="chat-query">
            Question
          </label>
          <textarea
            className="chat-textarea"
            id="chat-query"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="보험금 지급 기준이나 계약자 변경 같은 질문을 입력하세요."
            rows={4}
            value={query}
          />
          <div className="chat-controls">
            <div className="default-file-row">
              <label className="upload-label" htmlFor="chat-file-select">
                Target file
              </label>
              <select
                className="default-file-select"
                id="chat-file-select"
                onChange={(event) => setSelectedStoredName(event.target.value)}
                value={selectedStoredName}
              >
                <option value="">All indexed files</option>
                {indexedFiles.map((file) => (
                  <option key={file.stored_name} value={file.stored_name}>
                    {file.original_name} ({file.chunk_count})
                  </option>
                ))}
              </select>
            </div>
            <div className="default-file-row chat-topk">
              <label className="upload-label" htmlFor="chat-topk">
                Top K
              </label>
              <select
                className="default-file-select"
                id="chat-topk"
                onChange={(event) => setTopK(Number(event.target.value))}
                value={String(topK)}
              >
                <option value="3">3</option>
                <option value="5">5</option>
                <option value="8">8</option>
              </select>
            </div>
          </div>
          <button className="upload-button" disabled={isLoading} type="submit">
            {isLoading ? "Searching..." : "Search chunks"}
          </button>
        </form>
        {unindexedCount > 0 ? (
          <div className="chat-note">
            {unindexedCount} uploaded file(s) are not indexed yet, so they do not appear in Target file.
          </div>
        ) : null}
        <div className="chat-status">{message}</div>
      </div>

      <div className="card">
        <p className="eyebrow">Results</p>
        <h2>Retrieved chunks</h2>
        {!result || result.hit_count === 0 ? (
          <p>No retrieved chunks yet.</p>
        ) : (
          <div className="retrieval-list">
            <div className="retrieval-summary">
              <span>Query: {result.query}</span>
              <span>Top K: {result.top_k}</span>
              <span>Hits: {result.hit_count}</span>
            </div>
            {result.hits.map((hit) => (
              <article className="retrieval-card" key={hit.id}>
                <div className="retrieval-head">
                  <div className="retrieval-title">
                    <strong>{hit.source ?? hit.original_name ?? "Unknown source"}</strong>
                    <div className="retrieval-meta">
                      <span>chunk #{hit.chunk_index ?? "-"}</span>
                      <span>distance {formatDistance(hit.distance)}</span>
                    </div>
                  </div>
                  <div className="retrieval-tags">
                    {hit.page_number ? <span>page {hit.page_number}</span> : null}
                    {hit.section_header ? <span>{hit.section_header}</span> : null}
                  </div>
                </div>
                <div className="retrieval-preview">{hit.preview ?? hit.text}</div>
                <details className="parse-json">
                  <summary>View full chunk</summary>
                  <pre>{hit.text}</pre>
                </details>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
