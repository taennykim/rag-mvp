"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";

type UploadedFile = {
  stored_name: string;
  original_name: string;
  size_bytes: number;
  uploaded_at: string;
  upload_status: "completed";
  parse_status: "pending" | "completed" | "failed";
  chunk_status: "pending" | "completed";
  index_status: "pending" | "completed";
  parse_text_length?: number | null;
  parse_parser_used?: string | null;
  parse_fallback_used?: boolean | null;
  parse_error_detail?: string | null;
  last_successful_parse_parser_used?: string | null;
  last_successful_parse_fallback_used?: boolean | null;
  last_failed_parse_parser_used?: string | null;
  last_failed_parse_fallback_used?: boolean | null;
  chunk_count?: number | null;
  indexed_chunk_count?: number | null;
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
  preview: string;
  extracted_text: string;
  size_bytes: number;
  uploaded_at: string;
  status: string;
  primary_parser: string;
  fallback_parser: string;
  parser_used: string;
  fallback_used: boolean;
};

type ParseQualityResult = {
  stored_name: string;
  original_name: string;
  file_type: string;
  text_length: number;
  reference_text_length: number;
  size_bytes: number;
  uploaded_at: string;
  status: string;
  jaccard_similarity: number;
  levenshtein_distance: number;
  quality_warning: boolean;
  quality_warning_message: string;
  primary_parser: string;
  fallback_parser: string;
  parser_used: string;
  fallback_used: boolean;
};

type UploadResult = {
  stored_name: string;
  original_name?: string;
  detail?: string;
};

type IndexResult = {
  original_name: string;
  indexed_count: number;
  chunk_target_length?: number;
  chunk_overlap_length?: number;
  parser_used?: string;
  fallback_used?: boolean;
  detail?: string;
};

type ChunkResult = {
  stored_name: string;
  original_name: string;
  chunk_count: number;
  chunk_target_length: number;
  chunk_overlap_length: number;
  parser_used: string;
  fallback_used: boolean;
  detail?: string;
};

type ParserOption = {
  id: string;
  label: string;
  available: boolean;
  description: string;
  supported_extensions: string[];
};

type ParserCatalog = {
  default_primary_parser: string;
  default_fallback_parser: string;
  primary_parsers: ParserOption[];
  fallback_parsers: ParserOption[];
};

type UploadStageId = "upload" | "parse" | "chunk" | "index";

type UploadStage = {
  id: UploadStageId;
  label: string;
  status: "pending" | "active" | "completed" | "failed";
  detail?: string;
};

const API_BASE_URL = "/api";
const BACKEND_LOG_PATH = "/home/ubuntu/rag-mvp/backend/logs/app.log";
const DEFAULT_CHUNK_TARGET_LENGTH = 800;
const DEFAULT_CHUNK_OVERLAP_LENGTH = 120;

function createUploadStages(): UploadStage[] {
  return [
    { id: "upload", label: "Upload", status: "pending" },
    { id: "parse", label: "Parse", status: "pending" },
    { id: "chunk", label: "Chunk", status: "pending" },
    { id: "index", label: "Embedding / Indexing", status: "pending" },
  ];
}

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [defaultFiles, setDefaultFiles] = useState<DefaultFile[]>([]);
  const [selectedDefaultFile, setSelectedDefaultFile] = useState("");
  const [parserCatalog, setParserCatalog] = useState<ParserCatalog | null>(null);
  const [primaryParser, setPrimaryParser] = useState("docling");
  const [fallbackParser, setFallbackParser] = useState("extension-default");
  const [chunkTargetLength, setChunkTargetLength] = useState(String(DEFAULT_CHUNK_TARGET_LENGTH));
  const [chunkOverlapLength, setChunkOverlapLength] = useState(String(DEFAULT_CHUNK_OVERLAP_LENGTH));
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [parseQualityResult, setParseQualityResult] = useState<ParseQualityResult | null>(null);
  const [activeParseFile, setActiveParseFile] = useState("");
  const [activeQualityFile, setActiveQualityFile] = useState("");
  const [activeDeleteFile, setActiveDeleteFile] = useState("");
  const [message, setMessage] = useState("Select a PDF, DOC, DOCX, XLS, or XLSX file to upload.");
  const [errorDetail, setErrorDetail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [uploadStages, setUploadStages] = useState<UploadStage[]>(createUploadStages);

  async function loadFiles() {
    try {
      const response = await fetch(`${API_BASE_URL}/pipeline/files`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to load pipeline files.");
      }

      const data = (await response.json()) as { files: UploadedFile[] };
      setFiles(data.files);
      setErrorDetail("");
    } catch (error) {
      setFiles([]);
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
      setSelectedDefaultFile("");
      setErrorDetail("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to load default files.");
    }
  }

  async function loadParserCatalog() {
    try {
      const response = await fetch(`${API_BASE_URL}/parse/parsers`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to load parser catalog.");
      }

      const data = (await response.json()) as ParserCatalog;
      setParserCatalog(data);
      setPrimaryParser(data.default_primary_parser);
      setFallbackParser(data.default_fallback_parser);
      setErrorDetail("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to load parser catalog.");
    }
  }

  useEffect(() => {
    void loadFiles();
    void loadDefaultFiles();
    void loadParserCatalog();
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

  function getChunkSettings() {
    const parsedTargetLength = Number.parseInt(chunkTargetLength, 10);
    const parsedOverlapLength = Number.parseInt(chunkOverlapLength, 10);

    if (!Number.isFinite(parsedTargetLength) || parsedTargetLength < 100) {
      throw new Error("target_length must be at least 100.");
    }

    if (!Number.isFinite(parsedOverlapLength) || parsedOverlapLength < 0) {
      throw new Error("overlap must be 0 or greater.");
    }

    if (parsedOverlapLength >= parsedTargetLength) {
      throw new Error("overlap must be smaller than target_length.");
    }

    return {
      chunk_target_length: parsedTargetLength,
      chunk_overlap_length: parsedOverlapLength,
    };
  }

  function formatParseStatus(file: UploadedFile) {
    const base = `Parse: ${file.parse_status}`;
    if (!file.parse_parser_used) {
      return base;
    }

    return `${base} (${file.parse_parser_used}${file.parse_fallback_used ? ", fallback" : ""})`;
  }

  function formatParserHistory(label: string, parserUsed?: string | null, fallbackUsed?: boolean | null) {
    if (!parserUsed) {
      return null;
    }

    return `${label}: ${parserUsed}${fallbackUsed ? ", fallback" : ""}`;
  }

  function updateUploadStage(stageId: UploadStageId, status: UploadStage["status"], detail?: string) {
    setUploadStages((current) =>
      current.map((stage) => (stage.id === stageId ? { ...stage, status, detail } : stage)),
    );
  }

  async function parseUploadedFile(storedName: string) {
    const response = await fetch(`${API_BASE_URL}/parse`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        stored_name: storedName,
        primary_parser: primaryParser,
        fallback_parser: fallbackParser,
      }),
    });

    const data = (await response.json()) as ParseResult & { detail?: string };
    if (!response.ok) {
      throw new Error(data.detail ?? "Parsing failed.");
    }

    return data;
  }

  async function chunkUploadedFile(storedName: string) {
    const chunkSettings = getChunkSettings();
    const response = await fetch(`${API_BASE_URL}/chunk`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        stored_name: storedName,
        primary_parser: primaryParser,
        fallback_parser: fallbackParser,
        ...chunkSettings,
      }),
    });

    const data = (await response.json()) as ChunkResult;
    if (!response.ok) {
      throw new Error(data.detail ?? "Chunking failed.");
    }

    return data;
  }

  async function indexUploadedFile(storedName: string) {
    const chunkSettings = getChunkSettings();
    const response = await fetch(`${API_BASE_URL}/index`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        stored_name: storedName,
        primary_parser: primaryParser,
        fallback_parser: fallbackParser,
        ...chunkSettings,
      }),
    });

    const data = (await response.json()) as IndexResult;
    if (!response.ok) {
      throw new Error(data.detail ?? "Indexing failed.");
    }

    return data;
  }

  async function uploadSelectedDefaultFile() {
    const response = await fetch(`${API_BASE_URL}/upload/default-file`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ filename: selectedDefaultFile }),
    });

    const data = (await response.json()) as UploadResult;
    if (!response.ok) {
      throw new Error(data.detail ?? "Default file upload failed.");
    }

    return data;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedFile && !selectedDefaultFile) {
      setMessage("Choose a file first, or select a default file.");
      return;
    }

    try {
      getChunkSettings();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Invalid chunk settings.");
      return;
    }

    setIsLoading(true);
    setUploadStages(createUploadStages());
    setErrorDetail("");
    let currentStage: UploadStageId = "upload";

    try {
      updateUploadStage("upload", "active", "File transfer in progress");
      setMessage(selectedFile ? "Uploading file..." : "Uploading default file...");

      let uploadResult: UploadResult;
      if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);

        const response = await fetch(`${API_BASE_URL}/upload`, {
          method: "POST",
          body: formData,
        });

        const data = (await response.json()) as UploadResult;
        if (!response.ok) {
          throw new Error(data.detail ?? "Upload failed.");
        }
        uploadResult = data;
      } else {
        uploadResult = await uploadSelectedDefaultFile();
      }

      updateUploadStage("upload", "completed", uploadResult.original_name ?? uploadResult.stored_name);

      currentStage = "parse";
      updateUploadStage("parse", "active", "Extracting text");
      setMessage("Parsing uploaded file...");
      const parsedResult = await parseUploadedFile(uploadResult.stored_name);
      setParseResult(parsedResult);
      setParseQualityResult(null);
      updateUploadStage(
        "parse",
        "completed",
        `${parsedResult.text_length} chars via ${parsedResult.parser_used}${parsedResult.fallback_used ? " (fallback)" : ""}`,
      );

      currentStage = "chunk";
      updateUploadStage("chunk", "active", `Building chunks (${chunkTargetLength}/${chunkOverlapLength})`);
      setMessage("Creating chunks...");
      const chunkResult = await chunkUploadedFile(uploadResult.stored_name);
      updateUploadStage(
        "chunk",
        "completed",
        `${chunkResult.chunk_count} chunk(s) (${chunkResult.chunk_target_length}/${chunkResult.chunk_overlap_length})`,
      );

      currentStage = "index";
      updateUploadStage("index", "active", "Generating embeddings and storing index");
      setMessage("Generating embeddings and indexing...");
      const indexResult = await indexUploadedFile(uploadResult.stored_name);
      updateUploadStage(
        "index",
        "completed",
        `${indexResult.indexed_count} chunk(s) indexed (${indexResult.chunk_target_length}/${indexResult.chunk_overlap_length})`,
      );

      setSelectedFile(null);
      const input = document.getElementById("document-upload") as HTMLInputElement | null;
      if (input) {
        input.value = "";
      }
      await loadFiles();
      const parserNote = indexResult.parser_used
        ? ` Parser: ${indexResult.parser_used}${indexResult.fallback_used ? " (fallback)" : ""}.`
        : "";
      setMessage(
        `Uploaded and indexed ${indexResult.original_name}. ${indexResult.indexed_count} chunk(s) stored (${indexResult.chunk_target_length}/${indexResult.chunk_overlap_length}).${parserNote}`,
      );
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Upload or indexing failed.";
      updateUploadStage(currentStage, "failed", detail);
      setMessage(detail);
      setErrorDetail(`${currentStage.toUpperCase()} failed. ${detail} Check backend log: ${BACKEND_LOG_PATH}`);
      await loadFiles();
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
      setParseQualityResult(null);
      setErrorDetail("");
      setMessage(`Cleared ${data.removed_count ?? 0} uploaded file(s).`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to clear uploaded files.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleParseTest(file: UploadedFile) {
    setActiveParseFile(file.stored_name);
    setErrorDetail("");
    setMessage(`Parsing ${file.original_name}...`);

    try {
      const response = await fetch(`${API_BASE_URL}/parse`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          stored_name: file.stored_name,
          primary_parser: primaryParser,
          fallback_parser: fallbackParser,
        }),
      });

      const data = (await response.json()) as ParseResult & { detail?: string };
      if (!response.ok) {
        throw new Error(data.detail ?? "Parsing failed.");
      }

      setParseResult(data);
      setParseQualityResult(null);
      setErrorDetail("");
      await loadFiles();
      setMessage(`Parsed ${data.original_name}.`);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Parsing failed.";
      setMessage(detail);
      setParseResult(null);
      setParseQualityResult(null);
      setErrorDetail(`PARSE failed. ${detail} Check backend log: ${BACKEND_LOG_PATH}`);
    } finally {
      setActiveParseFile("");
    }
  }

  async function handleDeleteFile(file: UploadedFile) {
    setActiveDeleteFile(file.stored_name);
    setMessage(`Deleting ${file.original_name} from uploads and index...`);

    try {
      const response = await fetch(`${API_BASE_URL}/upload/files/${file.stored_name}`, {
        method: "DELETE",
      });

      const data = (await response.json()) as {
        original_name?: string;
        removed_index_count?: number;
        removed_parse_summary?: boolean;
        removed_chunk_summary?: boolean;
        detail?: string;
      };
      if (!response.ok) {
        throw new Error(data.detail ?? "Failed to delete uploaded file.");
      }

      if (parseResult?.stored_name === file.stored_name) {
        setParseResult(null);
        setParseQualityResult(null);
      }

      await loadFiles();
      setErrorDetail("");
      setMessage(
        `Reset ${data.original_name ?? file.original_name}. Removed ${data.removed_index_count ?? 0} indexed chunk(s).`,
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to delete uploaded file.");
    } finally {
      setActiveDeleteFile("");
    }
  }

  async function handleQualityCheck() {
    if (!parseResult) {
      setMessage("Run Parse test first.");
      return;
    }

    setActiveQualityFile(parseResult.stored_name);
    setErrorDetail("");
    setMessage(`Calculating parsing quality for ${parseResult.original_name}...`);

    try {
      const response = await fetch(`${API_BASE_URL}/parse/quality`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          stored_name: parseResult.stored_name,
          primary_parser: primaryParser,
          fallback_parser: fallbackParser,
        }),
      });

      const data = (await response.json()) as ParseQualityResult & { detail?: string };
      if (!response.ok) {
        throw new Error(data.detail ?? "Quality check failed.");
      }

      setParseQualityResult(data);
      setErrorDetail("");
      setMessage(`Calculated parsing quality for ${data.original_name}.`);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Quality check failed.";
      setMessage(detail);
      setParseQualityResult(null);
      setErrorDetail(`QUALITY CHECK failed. ${detail} Check backend log: ${BACKEND_LOG_PATH}`);
    } finally {
      setActiveQualityFile("");
    }
  }

  return (
    <section className="page">
      <div className="card">
        <p className="eyebrow">Upload</p>
        <h2>Document intake</h2>
        <p>Upload PDF, DOC, DOCX, XLS, or XLSX files and process them step by step.</p>
        <form className="upload-form" onSubmit={handleSubmit}>
          <div className="parser-grid">
            <div className="default-file-row">
              <label className="upload-label" htmlFor="primary-parser-select">
                Primary parser
              </label>
              <select
                className="default-file-select"
                id="primary-parser-select"
                onChange={(event) => setPrimaryParser(event.target.value)}
                value={primaryParser}
              >
                {parserCatalog?.primary_parsers.map((parser) => (
                  <option key={parser.id} value={parser.id}>
                    {parser.label}
                    {!parser.available ? " (unavailable)" : ""}
                  </option>
                ))}
              </select>
              <p className="parser-note">
                기본 파서는 Docling을 우선 시도합니다. 현재 환경에 없거나 실패하면 보조 파서로 넘어갑니다.
              </p>
            </div>

            <div className="default-file-row">
              <label className="upload-label" htmlFor="fallback-parser-select">
                Auxiliary parser
              </label>
              <select
                className="default-file-select"
                id="fallback-parser-select"
                onChange={(event) => setFallbackParser(event.target.value)}
                value={fallbackParser}
              >
                {parserCatalog?.fallback_parsers.map((parser) => (
                  <option key={parser.id} value={parser.id}>
                    {parser.label}
                    {!parser.available ? " (coming soon)" : ""}
                  </option>
                ))}
              </select>
              <p className="parser-note">
                PDF, DOC, DOCX, XLS, XLSX용 보조 파서를 선택할 수 있습니다. 환경에 없는 파서는 실행 시 안내됩니다.
              </p>
            </div>
          </div>
          <label className="upload-label" htmlFor="document-upload">
            Select document
          </label>
          <div className="upload-row">
            <input
              id="document-upload"
              accept=".pdf,.doc,.docx,.xls,.xlsx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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
              <option value="">Select a file</option>
              {defaultFiles.length === 0 ? (
                <option value="" disabled>
                  No default files
                </option>
              ) : (
                defaultFiles.map((file) => (
                  <option key={file.name} value={file.name}>
                    {file.name} ({file.size_bytes} bytes)
                  </option>
                ))
              )}
            </select>
          </div>
          <div className="chunk-settings-grid">
            <div className="default-file-row">
              <label className="upload-label" htmlFor="chunk-target-length">
                Chunk target_length
              </label>
              <input
                className="default-file-select"
                id="chunk-target-length"
                inputMode="numeric"
                min={100}
                onChange={(event) => setChunkTargetLength(event.target.value)}
                type="number"
                value={chunkTargetLength}
              />
            </div>
            <div className="default-file-row">
              <label className="upload-label" htmlFor="chunk-overlap-length">
                Chunk overlap
              </label>
              <input
                className="default-file-select"
                id="chunk-overlap-length"
                inputMode="numeric"
                min={0}
                onChange={(event) => setChunkOverlapLength(event.target.value)}
                type="number"
                value={chunkOverlapLength}
              />
            </div>
          </div>
          <p className="parser-note">기본값은 target_length 800, overlap 120입니다.</p>
          <button className="upload-button" disabled={isLoading} type="submit">
            {isLoading ? "Uploading..." : "Upload file"}
          </button>
        </form>
        <p>{message}</p>
        {errorDetail ? <p className="error-banner">{errorDetail}</p> : null}
        <div className="pipeline-status" aria-live="polite">
          {uploadStages.map((stage) => (
            <div key={stage.id} className={`pipeline-stage ${stage.status}`}>
              <div className="pipeline-stage-header">
                <strong>{stage.label}</strong>
                <span className="pipeline-stage-badge">{stage.status}</span>
              </div>
              <p>{stage.detail ?? (stage.status === "pending" ? "Waiting" : "")}</p>
            </div>
          ))}
        </div>
        <p>
          Put default files in <code>backend/data/default-files</code>.
        </p>
      </div>

      <div className="card upload-list">
        <p className="eyebrow">Files</p>
        <h2>Uploaded file list</h2>
        {files.length === 0 ? (
          <p>No files uploaded yet.</p>
        ) : (
          <ul className="file-list">
            {files.map((file) => {
              return (
                <li key={file.stored_name}>
                <div className="file-main">
                  <strong>{file.original_name}</strong>
                  <div className="file-status-row">
                    <span className="file-status-chip indexed">Upload</span>
                    <span className={`file-status-chip ${file.parse_status === "completed" ? "indexed" : "pending"}`}>
                      {formatParseStatus(file)}
                    </span>
                    <span className={`file-status-chip ${file.chunk_status === "completed" ? "indexed" : "pending"}`}>
                      Chunk: {file.chunk_status}
                    </span>
                    <span className={`file-status-chip ${file.index_status === "completed" ? "indexed" : "pending"}`}>
                      Embedding/Indexing: {file.index_status}
                    </span>
                    {file.chunk_count ? <span className="file-status-chip">{file.chunk_count} chunk(s)</span> : null}
                    {formatParserHistory(
                      "Last success",
                      file.last_successful_parse_parser_used,
                      file.last_successful_parse_fallback_used,
                    ) ? (
                      <span className="file-status-chip">
                        {formatParserHistory(
                          "Last success",
                          file.last_successful_parse_parser_used,
                          file.last_successful_parse_fallback_used,
                        )}
                      </span>
                    ) : null}
                    {formatParserHistory(
                      "Last failure",
                      file.last_failed_parse_parser_used,
                      file.last_failed_parse_fallback_used,
                    ) ? (
                      <span className="file-status-chip pending">
                        {formatParserHistory(
                          "Last failure",
                          file.last_failed_parse_parser_used,
                          file.last_failed_parse_fallback_used,
                        )}
                      </span>
                    ) : null}
                  </div>
                  <div className="file-actions">
                    <button
                      className="upload-button secondary"
                      disabled={
                        isLoading ||
                        file.parse_status === "failed" ||
                        activeParseFile === file.stored_name ||
                        activeDeleteFile === file.stored_name
                      }
                      onClick={() => void handleParseTest(file)}
                      type="button"
                    >
                      {activeParseFile === file.stored_name ? "Parsing..." : "Parse test"}
                    </button>
                    <button
                      className="upload-button secondary danger"
                      disabled={isLoading || activeDeleteFile === file.stored_name || activeParseFile === file.stored_name}
                      onClick={() => void handleDeleteFile(file)}
                      type="button"
                    >
                      {activeDeleteFile === file.stored_name ? "Resetting..." : "Reset"}
                    </button>
                  </div>
                </div>
                <div className="file-meta">
                  <span>{formatFileSize(file.size_bytes)}</span>
                  <span>{formatUploadedAt(file.uploaded_at)}</span>
                </div>
                </li>
              );
            })}
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
            <p>Primary parser: {parseResult.primary_parser}</p>
            <p>Auxiliary parser: {parseResult.fallback_parser}</p>
            <p>
              Parser used: {parseResult.parser_used}
              {parseResult.fallback_used ? " (fallback used)" : ""}
            </p>
            <p>Extracted length: {parseResult.text_length}</p>
            <button
              className="upload-button"
              disabled={activeQualityFile === parseResult.stored_name}
              onClick={() => void handleQualityCheck()}
              type="button"
            >
              {activeQualityFile === parseResult.stored_name ? "Calculating..." : "Check parsing quality"}
            </button>
            {parseQualityResult ? (
              <div className="quality-metrics">
                <p>Reference length: {parseQualityResult.reference_text_length}</p>
                <p>Jaccard Similarity: {formatSimilarity(parseQualityResult.jaccard_similarity)}</p>
                <p>Levenshtein Distance: {parseQualityResult.levenshtein_distance}</p>
                <p>
                  Parser used: {parseQualityResult.parser_used}
                  {parseQualityResult.fallback_used ? " (fallback used)" : ""}
                </p>
                {parseQualityResult.quality_warning ? (
                  <p className="quality-warning">{parseQualityResult.quality_warning_message}</p>
                ) : null}
              </div>
            ) : null}
            <details className="parse-json" open>
              <summary>Preview</summary>
              <pre>{parseResult.preview}</pre>
            </details>
          </div>
        ) : (
          <p>Run Parse test from the uploaded file list to inspect extracted text.</p>
        )}
      </div>
    </section>
  );
}
