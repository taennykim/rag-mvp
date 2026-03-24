"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";

type UploadedFile = {
  stored_name: string;
  original_name: string;
  size_bytes: number;
};

type DefaultFile = {
  name: string;
  size_bytes: number;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [defaultFiles, setDefaultFiles] = useState<DefaultFile[]>([]);
  const [selectedDefaultFile, setSelectedDefaultFile] = useState("");
  const [message, setMessage] = useState("Select a PDF or DOCX file to upload.");
  const [isLoading, setIsLoading] = useState(false);

  async function loadFiles() {
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedFile) {
      setMessage("Choose a PDF or DOCX file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    setIsLoading(true);
    setMessage("Uploading file...");

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = (await response.json()) as { original_name?: string; detail?: string };

      if (!response.ok) {
        throw new Error(data.detail ?? "Upload failed.");
      }

      setMessage(`Uploaded ${data.original_name ?? selectedFile.name}.`);
      setSelectedFile(null);
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

  async function handleDefaultFileUpload() {
    if (!selectedDefaultFile) {
      setMessage("No default file is available.");
      return;
    }

    setIsLoading(true);
    setMessage("Uploading default file...");

    try {
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
      await loadFiles();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Default file upload failed.");
    } finally {
      setIsLoading(false);
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
            <button
              className="upload-button secondary"
              disabled={isLoading || defaultFiles.length === 0}
              onClick={handleDefaultFileUpload}
              type="button"
            >
              Default file
            </button>
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
        <p className="eyebrow">Files</p>
        <h2>Uploaded file list</h2>
        {files.length === 0 ? (
          <p>No files uploaded yet.</p>
        ) : (
          <ul className="file-list">
            {files.map((file) => (
              <li key={file.stored_name}>
                <strong>{file.original_name}</strong>
                <span>{file.size_bytes} bytes</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
