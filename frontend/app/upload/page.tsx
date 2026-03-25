"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";

type UploadedFile = {
  stored_name: string;
  original_name: string;
  size_bytes: number;
  uploaded_at: string;
};

type DefaultFile = {
  name: string;
  size_bytes: number;
};

type ParseResult = {
  stored_name: string;
  original_name: string;
  file_type: string;
  text_length: number;
  reference_text_length: number;
  preview: string;
  extracted_text: string;
  size_bytes: number;
  uploaded_at: string;
  status: string;
  jaccard_similarity: number;
  levenshtein_distance: number;
  quality_warning: boolean;
  quality_warning_message: string;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [defaultFiles, setDefaultFiles] = useState<DefaultFile[]>([]);
  const [selectedDefaultFile, setSelectedDefaultFile] = useState("");
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [activeParseFile, setActiveParseFile] = useState("");
  const [message, setMessage] = useState("Select a PDF or DOCX file to upload.");
  const [isLoading, setIsLoading] = useState(false);

  async function loadFiles() {
    setFiles([]);
    try {
      const response = await fetch(`${API_BASE_URL}/upload/files`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to load uploaded files.");
      }

      const data = (await response.json()) as { files: UploadedFile[] };
      setFiles(data.files);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to load uploaded files.");
    }
  }

  async function loadDefaultFiles() {
    try {
      const response = await fetch(`${API_BASE_URL}/upload/default-files`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to load default files.");
      }

      const data = (await response.json()) as { files: DefaultFile[] };
      setDefaultFiles(data.files);
      setSelectedDefaultFile((current) => current || data.files[0]?.name || "");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to load default files.");
    }
  }

  useEffect(() => {
    void loadFiles();
    void loadDefaultFiles();
  }, []);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
  }

  function formatFileSize(sizeBytes: number) {
    if (sizeBytes < 1024) {
      return `${sizeBytes} B`;
    }

    if (sizeBytes < 1024 * 1024) {
      return `${(sizeBytes / 1024).toFixed(1)} KB`;
    }

    return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function formatUploadedAt(value: string) {
    return new Intl.DateTimeFormat("ko-KR", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "UTC",
    }).format(new Date(value));
  }

  function formatSimilarity(value: number) {
    return value.toFixed(3);
  }

  async function uploadSelectedDefaultFile() {
    const response = await fetch(`${API_BASE_URL}/upload/default-file`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ filename: selectedDefaultFile }),
    });

    const data = (await response.json()) as { original_name?: string; detail?: string };
    if (!response.ok) {
      throw new Error(data.detail ?? "Default file upload failed.");
    }

    setMessage(`Uploaded default file ${data.original_name ?? selectedDefaultFile}.`);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedFile && !selectedDefaultFile) {
      setMessage("Choose a PDF or DOCX file first, or select a default file.");
      return;
    }

    setIsLoading(true);
    setMessage(selectedFile ? "Uploading file..." : "Uploading default file...");

    try {
      if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);

        const response = await fetch(`${API_BASE_URL}/upload`, {
          method: "POST",
          body: formData,
        });

        const data = (await response.json()) as { original_name?: string; detail?: string };
        if (!response.ok) {
          throw new Error(data.detail ?? "Upload failed.");
        }

        setMessage(`Uploaded ${data.original_name ?? selectedFile.name}.`);
      } else {
        await uploadSelectedDefaultFile();
      }

      setSelectedFile(null);
      setParseResult(null);
      const input = document.getElementById("document-upload") as HTMLInputElement | null;
      if (input) {
        input.value = "";
      }
      await loadFiles();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleClearFiles() {
    setIsLoading(true);
    setMessage("Clearing uploaded file list...");

    try {
      const response = await fetch(`${API_BASE_URL}/upload/files`, {
        method: "DELETE",
      });

      const data = (await response.json()) as { removed_count?: number; detail?: string };
      if (!response.ok) {
        throw new Error(data.detail ?? "Failed to clear uploaded files.");
      }

      setFiles([]);
      setParseResult(null);
      setMessage(`Cleared ${data.removed_count ?? 0} uploaded file(s).`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to clear uploaded files.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleParseTest(file: UploadedFile) {
    setActiveParseFile(file.stored_name);
    setMessage(`Parsing ${file.original_name}...`);

    try {
      const response = await fetch(`${API_BASE_URL}/parse`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ stored_name: file.stored_name }),
      });

      const data = (await response.json()) as ParseResult & { detail?: string };
      if (!response.ok) {
        throw new Error(data.detail ?? "Parsing failed.");
      }

      setParseResult(data);
      setMessage(`Parsed ${data.original_name}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Parsing failed.");
      setParseResult(null);
    } finally {
      setActiveParseFile("");
    }
  }

  return (
    <section className="page">
      <div className="card">
        <p className="eyebrow">Upload</p>
        <h2>Document intake</h2>
        <p>Upload PDF or DOCX files and store them for the next parsing step.</p>
        <form className="upload-form" onSubmit={handleSubmit}>
          <label className="upload-label" htmlFor="document-upload">
            Select document
          </label>
          <div className="upload-row">
            <input
              id="document-upload"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={handleFileChange}
              type="file"
            />
          </div>
          <div className="default-file-row">
            <label className="upload-label" htmlFor="default-file-select">
              Default file list
            </label>
            <select
              className="default-file-select"
              id="default-file-select"
              onChange={(event) => setSelectedDefaultFile(event.target.value)}
              value={selectedDefaultFile}
            >
              {defaultFiles.length === 0 ? (
                <option value="">No default files</option>
              ) : (
                defaultFiles.map((file) => (
                  <option key={file.name} value={file.name}>
                    {file.name} ({file.size_bytes} bytes)
                  </option>
                ))
              )}
            </select>
          </div>
          <button className="upload-button" disabled={isLoading} type="submit">
            {isLoading ? "Uploading..." : "Upload file"}
          </button>
        </form>
        <p>{message}</p>
        <p>
          Put default files in <code>backend/data/default-files</code>.
        </p>
      </div>

      <div className="card upload-list">
        <div className="section-header">
          <div>
            <p className="eyebrow">Files</p>
            <h2>Uploaded file list</h2>
          </div>
          <button
            className="upload-button secondary"
            disabled={isLoading || files.length === 0}
            onClick={handleClearFiles}
            type="button"
          >
            Clear list
          </button>
        </div>
        {files.length === 0 ? (
          <p>No files uploaded yet.</p>
        ) : (
          <ul className="file-list">
            {files.map((file) => (
              <li key={file.stored_name}>
                <div className="file-main">
                  <strong>{file.original_name}</strong>
                  <button
                    className="upload-button secondary"
                    disabled={isLoading || activeParseFile === file.stored_name}
                    onClick={() => void handleParseTest(file)}
                    type="button"
                  >
                    {activeParseFile === file.stored_name ? "Parsing..." : "Parse test"}
                  </button>
                </div>
                <div className="file-meta">
                  <span>{formatFileSize(file.size_bytes)}</span>
                  <span>{formatUploadedAt(file.uploaded_at)}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="card">
        <p className="eyebrow">Parsing</p>
        <h2>Parsing test result</h2>
        {parseResult ? (
          <div className="parse-result">
            <p>
              <strong>{parseResult.original_name}</strong>
            </p>
            <p>Stored name: {parseResult.stored_name}</p>
            <p>Type: {parseResult.file_type}</p>
            <p>Size: {formatFileSize(parseResult.size_bytes)}</p>
            <p>Uploaded at: {formatUploadedAt(parseResult.uploaded_at)}</p>
            <p>Status: {parseResult.status}</p>
            <p>Extracted length: {parseResult.text_length}</p>
            <p>Reference length: {parseResult.reference_text_length}</p>
            <p>Jaccard Similarity: {formatSimilarity(parseResult.jaccard_similarity)}</p>
            <p>Levenshtein Distance: {parseResult.levenshtein_distance}</p>
            {parseResult.quality_warning ? (
              <p className="quality-warning">{parseResult.quality_warning_message}</p>
            ) : null}
            <details className="parse-json" open>
              <summary>Preview</summary>
              <pre>{parseResult.preview}</pre>
            </details>
            <details className="parse-json">
              <summary>View full extracted text</summary>
              <pre>{parseResult.extracted_text}</pre>
            </details>
            <details className="parse-json">
              <summary>View raw JSON</summary>
              <pre>{JSON.stringify(parseResult, null, 2)}</pre>
            </details>
          </div>
        ) : (
          <p>Run Parse test from the uploaded file list to inspect extracted text.</p>
        )}
      </div>
    </section>
  );
}
