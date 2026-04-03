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
  parse_preview?: string | null;
  markdown_path?: string | null;
  quality_checked_at?: string | null;
  jaccard_similarity?: number | null;
  levenshtein_distance?: number | null;
  quality_warning?: boolean | null;
  quality_warning_message?: string | null;
  quality_warning_reasons?: string[] | null;
  pdf_garbled_detected?: boolean | null;
  pdf_suspicious_char_ratio?: number | null;
  pdf_reference_suspicious_char_ratio?: number | null;
  pdf_suspicious_char_ratio_delta?: number | null;
  pdf_replacement_character_count?: number | null;
  pdf_control_character_count?: number | null;
  pdf_text_length_ratio?: number | null;
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
  markdown_path?: string | null;
};

type ParseQualityResult = {
  stored_name: string;
  original_name: string;
  file_type: string;
  text_length: number;
  reference_text_length: number;
  size_bytes: number;
  uploaded_at: string;
  quality_checked_at?: string;
  status: string;
  jaccard_similarity: number;
  levenshtein_distance: number;
  quality_warning: boolean;
  quality_warning_message: string;
  quality_warning_reasons?: string[];
  pdf_garbled_detected?: boolean;
  pdf_suspicious_char_ratio?: number;
  pdf_reference_suspicious_char_ratio?: number;
  pdf_suspicious_char_ratio_delta?: number;
  pdf_replacement_character_count?: number;
  pdf_control_character_count?: number;
  pdf_text_length_ratio?: number;
  primary_parser: string;
  fallback_parser: string;
  parser_used: string;
  fallback_used: boolean;
  markdown_path?: string | null;
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
const PRIMARY_PARSER_ONLY_DOCLING = "docling-markdown";
const FALLBACK_PARSER_NONE = "none";

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
  const [activeParseFile, setActiveParseFile] = useState("");
  const [activeQualityFile, setActiveQualityFile] = useState("");
  const [activeDeleteFile, setActiveDeleteFile] = useState("");
  const [activePreviewFile, setActivePreviewFile] = useState("");
  const [visibleQualityFile, setVisibleQualityFile] = useState("");
  const [message, setMessage] = useState("Select a PDF, DOC, DOCX, XLS, or XLSX file to upload.");
  const [errorDetail, setErrorDetail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [uploadStages, setUploadStages] = useState<UploadStage[]>(createUploadStages);
  const isOnlyDocling = primaryParser === PRIMARY_PARSER_ONLY_DOCLING;

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

  useEffect(() => {
    if (isOnlyDocling && fallbackParser !== FALLBACK_PARSER_NONE) {
      setFallbackParser(FALLBACK_PARSER_NONE);
    }
  }, [fallbackParser, isOnlyDocling]);

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

  function formatRatioAsPercent(value: number) {
    return `${(value * 100).toFixed(1)}%`;
  }

  function formatQualityStatus(file: UploadedFile) {
    if (typeof file.quality_warning !== "boolean") {
      return null;
    }

    return file.quality_warning ? "Quality warning" : "Quality OK";
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

  const indexedFileCount = files.filter((file) => file.index_status === "completed").length;
  const failedParseCount = files.filter((file) => file.parse_status === "failed").length;
  const totalChunkCount = files.reduce((sum, file) => sum + (file.chunk_count ?? 0), 0);

  function updateUploadStage(stageId: UploadStageId, status: UploadStage["status"], detail?: string) {
    setUploadStages((current) =>
      current.map((stage) => (stage.id === stageId ? { ...stage, status, detail } : stage)),
    );
  }

  function getSelectedFallbackParser() {
    return isOnlyDocling ? FALLBACK_PARSER_NONE : fallbackParser;
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
        fallback_parser: getSelectedFallbackParser(),
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
        fallback_parser: getSelectedFallbackParser(),
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
        fallback_parser: getSelectedFallbackParser(),
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
      updateUploadStage(
        "parse",
        "completed",
        parsedResult.markdown_path
          ? `${parsedResult.text_length} chars via ${parsedResult.parser_used} -> Markdown`
          : `${parsedResult.text_length} chars via ${parsedResult.parser_used}${parsedResult.fallback_used ? " (fallback)" : ""}`,
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
      const markdownNote = parsedResult.markdown_path ? ` Markdown: ${parsedResult.markdown_path}.` : "";
      setMessage(
        `Uploaded and indexed ${indexResult.original_name}. ${indexResult.indexed_count} chunk(s) stored (${indexResult.chunk_target_length}/${indexResult.chunk_overlap_length}).${parserNote}${markdownNote}`,
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
      setErrorDetail("");
      setMessage(`Cleared ${data.removed_count ?? 0} uploaded file(s).`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to clear uploaded files.");
    } finally {
      setIsLoading(false);
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

      if (visibleQualityFile === file.stored_name) {
        setVisibleQualityFile("");
      }

      if (activePreviewFile === file.stored_name) {
        setActivePreviewFile("");
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

  async function handleRowQualityCheck(file: UploadedFile) {
    setActiveQualityFile(file.stored_name);
    setErrorDetail("");
    setMessage(`Calculating parsing quality for ${file.original_name}...`);

    try {
      const response = await fetch(`${API_BASE_URL}/parse/quality`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          stored_name: file.stored_name,
          primary_parser: primaryParser,
          fallback_parser: getSelectedFallbackParser(),
        }),
      });

      const data = (await response.json()) as ParseQualityResult & { detail?: string };
      if (!response.ok) {
        throw new Error(data.detail ?? "Quality check failed.");
      }

      setFiles((current) =>
        current.map((item) =>
          item.stored_name === file.stored_name
            ? {
                ...item,
                quality_checked_at: data.quality_checked_at ?? new Date().toISOString(),
                jaccard_similarity: data.jaccard_similarity,
                levenshtein_distance: data.levenshtein_distance,
                quality_warning: data.quality_warning,
                quality_warning_message: data.quality_warning_message,
                quality_warning_reasons: data.quality_warning_reasons,
                pdf_garbled_detected: data.pdf_garbled_detected,
                pdf_suspicious_char_ratio: data.pdf_suspicious_char_ratio,
                pdf_reference_suspicious_char_ratio: data.pdf_reference_suspicious_char_ratio,
                pdf_suspicious_char_ratio_delta: data.pdf_suspicious_char_ratio_delta,
                pdf_replacement_character_count: data.pdf_replacement_character_count,
                pdf_control_character_count: data.pdf_control_character_count,
                pdf_text_length_ratio: data.pdf_text_length_ratio,
              }
            : item,
        ),
      );
      setVisibleQualityFile(file.stored_name);
      setErrorDetail("");
      setMessage(`Calculated parsing quality for ${data.original_name}.`);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Quality check failed.";
      setMessage(detail);
      setErrorDetail(`QUALITY CHECK failed. ${detail} Check backend log: ${BACKEND_LOG_PATH}`);
    } finally {
      setActiveQualityFile("");
    }
  }

  async function handlePreviewToggle(file: UploadedFile) {
    if (activePreviewFile === file.stored_name) {
      setActivePreviewFile("");
      return;
    }

    if (file.parse_preview) {
      setActivePreviewFile(file.stored_name);
      setMessage(`Preview loaded for ${file.original_name}.`);
      return;
    }

    if (file.parse_status !== "completed") {
      setMessage(`Preview is not available until parsing succeeds for ${file.original_name}.`);
      return;
    }

    setActiveParseFile(file.stored_name);
    setMessage(`Loading preview for ${file.original_name}...`);

    try {
      const response = await fetch(`${API_BASE_URL}/parse`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          stored_name: file.stored_name,
          primary_parser: primaryParser,
          fallback_parser: getSelectedFallbackParser(),
        }),
      });

      const data = (await response.json()) as ParseResult & { detail?: string };
      if (!response.ok) {
        throw new Error(data.detail ?? "Preview load failed.");
      }

      setFiles((current) =>
        current.map((item) =>
          item.stored_name === file.stored_name ? { ...item, parse_preview: data.preview } : item,
        ),
      );
      setActivePreviewFile(file.stored_name);
      setMessage(`Preview loaded for ${data.original_name}.`);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Preview load failed.";
      setMessage(detail);
      setErrorDetail(`PREVIEW failed. ${detail} Check backend log: ${BACKEND_LOG_PATH}`);
    } finally {
      setActiveParseFile("");
    }
  }

  return (
    <section className="page">
      <div className="card">
        <p className="eyebrow">Upload</p>
        <h2>Document intake</h2>
        <p>Upload PDF, DOC, DOCX, XLS, or XLSX files and process them step by step.</p>
        <div className="dashboard-strip">
          <div className="dashboard-stat">
            <span className="dashboard-stat-label">Uploaded files</span>
            <strong>{files.length}</strong>
          </div>
          <div className="dashboard-stat">
            <span className="dashboard-stat-label">Indexed files</span>
            <strong>{indexedFileCount}</strong>
          </div>
          <div className="dashboard-stat">
            <span className="dashboard-stat-label">Indexed chunks</span>
            <strong>{totalChunkCount}</strong>
          </div>
          <div className="dashboard-stat warning">
            <span className="dashboard-stat-label">Parse failures</span>
            <strong>{failedParseCount}</strong>
          </div>
        </div>
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
                기본값은 Legacy auto parser입니다. `Docling(md)`를 선택하면 fallback 없이 Docling 결과를 Markdown 파일로 저장합니다.
              </p>
            </div>

            <div className="default-file-row">
              <label className="upload-label" htmlFor="fallback-parser-select">
                Second parser
              </label>
              <select
                className="default-file-select"
                disabled={isOnlyDocling}
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
                {isOnlyDocling
                  ? "Docling(md) 모드에서는 second parser를 사용하지 않습니다."
                  : "PDF, DOC, DOCX, XLS, XLSX용 보조 파서를 선택할 수 있습니다. 환경에 없는 파서는 실행 시 안내됩니다."}
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
                      disabled={isLoading || activeDeleteFile === file.stored_name || activeParseFile === file.stored_name}
                      onClick={() => void handlePreviewToggle(file)}
                      type="button"
                    >
                      {activePreviewFile === file.stored_name
                        ? "Hide preview"
                        : activeParseFile === file.stored_name
                          ? "Loading..."
                          : "Show preview"}
                    </button>
                    <button
                      className="upload-button secondary"
                      disabled={
                        isLoading ||
                        file.parse_status !== "completed" ||
                        activeQualityFile === file.stored_name ||
                        activeDeleteFile === file.stored_name
                      }
                      onClick={() => void handleRowQualityCheck(file)}
                      type="button"
                    >
                      {activeQualityFile === file.stored_name ? "Checking..." : "Check quality"}
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
                  {file.markdown_path ? (
                    <p className="parser-note">
                      Markdown output: <code>{file.markdown_path}</code>
                    </p>
                  ) : null}
                  {visibleQualityFile === file.stored_name && formatQualityStatus(file) ? (
                    <div className="quality-metrics">
                      <p>
                        <strong>{formatQualityStatus(file)}</strong>
                      </p>
                      {typeof file.jaccard_similarity === "number" ? (
                        <p>Jaccard Similarity(집합 유사도): {formatSimilarity(file.jaccard_similarity)}</p>
                      ) : null}
                      {typeof file.levenshtein_distance === "number" ? (
                        <p>Levenshtein Distance(문자열 편집거리): {file.levenshtein_distance}</p>
                      ) : null}
                      {typeof file.pdf_garbled_detected === "boolean" ? (
                        <p>PDF garbled text(깨짐 여부 판단): {file.pdf_garbled_detected ? "깨짐 의심" : "정상"}</p>
                      ) : null}
                      {typeof file.pdf_suspicious_char_ratio === "number" ? (
                        <p>Suspicious symbol ratio(깨진/특수문자 비율): {formatRatioAsPercent(file.pdf_suspicious_char_ratio)}</p>
                      ) : null}
                      {typeof file.pdf_text_length_ratio === "number" ? (
                        <p>Parsed/reference length ratio(길이 비율 비교): {formatRatioAsPercent(file.pdf_text_length_ratio)}</p>
                      ) : null}
                      {typeof file.pdf_replacement_character_count === "number" ? (
                        <p>Replacement chars(깨진 문자 개수): {file.pdf_replacement_character_count}</p>
                      ) : null}
                      {typeof file.pdf_control_character_count === "number" ? (
                        <p>Control chars(제어문자,줄바꿈,탭,커서이동 문자 개수): {file.pdf_control_character_count}</p>
                      ) : null}
                      {file.quality_warning_message ? (
                        <p className="quality-warning">{file.quality_warning_message}</p>
                      ) : null}
                      {file.quality_warning_reasons && file.quality_warning_reasons.length > 0 ? (
                        <div className="quality-reason-list">
                          {file.quality_warning_reasons.map((reason) => (
                            <p key={reason} className="quality-reason-item">
                              {reason}
                            </p>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                  {activePreviewFile === file.stored_name && file.parse_preview ? (
                    <div className="parse-json">
                      <pre>{file.parse_preview}</pre>
                    </div>
                  ) : null}
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

    </section>
  );
}
