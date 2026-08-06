"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { DropZone } from "@/components/upload/DropZone";
import { CategorySelector } from "@/components/upload/CategorySelector";
import { LanguageSelector } from "@/components/upload/LanguageSelector";
import { ProgressTracker } from "@/components/upload/ProgressTracker";
import { useDocumentProgress } from "@/lib/hooks/useDocumentProgress";
import { uploadDocument } from "@/lib/api/documents";
import type { DocCategory, DocumentStatus, ProgressEvent } from "@/types/document";

type UploadState = "idle" | "uploading" | "processing" | "done" | "error";

export default function UploadPage() {
  const router = useRouter();

  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState<DocCategory>("other");
  const [language, setLanguage] = useState("en");
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [progressData, setProgressData] = useState<ProgressEvent>({
    document_id: "",
    status: "pending",
    progress: 0,
    message: "Starting upload…",
  });

  const handleDone = useCallback(
    (event: ProgressEvent) => {
      setUploadState("done");
      setProgressData(event);
      // Navigate to results after brief delay
      setTimeout(() => router.push(`/docs/${event.document_id}`), 1200);
    },
    [router]
  );

  const handleFailed = useCallback((event: ProgressEvent) => {
    setUploadState("error");
    setErrorMessage(event.message);
    setProgressData(event);
  }, []);

  const { progress } = useDocumentProgress(
    uploadState === "processing" ? documentId : null,
    { onDone: handleDone, onFailed: handleFailed }
  );

  // Keep local progressData in sync with WS events
  const displayProgress = progress ?? progressData;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploadState("uploading");
    setErrorMessage(null);

    try {
      const doc = await uploadDocument({ file, doc_category: category, target_language: language });
      setDocumentId(doc.id);
      setProgressData({
        document_id: doc.id,
        status: "pending",
        progress: 5,
        message: "File uploaded. Processing has started…",
      });
      setUploadState("processing");
    } catch (err: unknown) {
      setUploadState("error");
      const message =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        "Upload failed. Please try again.";
      setErrorMessage(message);
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadState("idle");
    setErrorMessage(null);
    setDocumentId(null);
  };

  const isProcessing = uploadState === "uploading" || uploadState === "processing";
  const isDone = uploadState === "done";

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight">Upload Document</h1>
        <p className="mt-1 text-muted-foreground">
          Upload a PDF, Word document, or image. We'll extract, analyse, and simplify its contents.
        </p>
      </div>

      {isProcessing || isDone ? (
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <h2 className="mb-1 font-semibold">
            {isDone ? "Processing complete!" : "Processing your document…"}
          </h2>
          <p className="mb-4 text-sm text-muted-foreground">{file?.name}</p>
          <ProgressTracker
            status={displayProgress.status as DocumentStatus}
            progress={displayProgress.progress}
            message={displayProgress.message}
          />
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Drop zone */}
          <div>
            <DropZone onFileSelected={setFile} disabled={isProcessing} />
            {file && (
              <p className="mt-2 text-sm text-muted-foreground">
                Selected:{" "}
                <span className="font-medium text-foreground">{file.name}</span>{" "}
                ({(file.size / (1024 * 1024)).toFixed(2)} MB)
              </p>
            )}
          </div>

          {/* Document category */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Document category</label>
            <CategorySelector value={category} onChange={setCategory} disabled={isProcessing} />
          </div>

          {/* Target language */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Simplify & translate to</label>
            <LanguageSelector value={language} onChange={setLanguage} disabled={isProcessing} />
          </div>

          {/* Error */}
          {errorMessage && (
            <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {errorMessage}
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={!file || isProcessing}
            className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Upload & Analyse
          </button>
        </form>
      )}
    </div>
  );
}
