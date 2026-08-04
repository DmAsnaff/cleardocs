"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { cn } from "@/lib/utils";

const ACCEPTED_TYPES: Record<string, string[]> = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
};

const MAX_SIZE_MB = 50;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

interface DropZoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export function DropZone({ onFileSelected, disabled = false }: DropZoneProps) {
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: { errors: { message: string }[] }[]) => {
      setError(null);

      if (rejectedFiles.length > 0) {
        const firstError = rejectedFiles[0].errors[0]?.message ?? "Invalid file.";
        setError(firstError);
        return;
      }

      if (acceptedFiles.length > 0) {
        onFileSelected(acceptedFiles[0]);
      }
    },
    [onFileSelected]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_SIZE_BYTES,
    multiple: false,
    disabled,
  });

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={cn(
          "flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-8 py-14 text-center transition-colors cursor-pointer",
          isDragActive && !isDragReject && "border-blue-500 bg-blue-50 dark:bg-blue-950/20",
          isDragReject && "border-red-500 bg-red-50 dark:bg-red-950/20",
          !isDragActive && !isDragReject && "border-muted-foreground/30 hover:border-blue-400 hover:bg-muted/30",
          disabled && "pointer-events-none opacity-50"
        )}
      >
        <input {...getInputProps()} />

        <div className="mb-4 rounded-full bg-muted p-4">
          <UploadIcon className="h-8 w-8 text-muted-foreground" />
        </div>

        {isDragActive ? (
          <p className="text-base font-medium text-blue-600 dark:text-blue-400">
            Drop your file here
          </p>
        ) : (
          <>
            <p className="text-base font-medium">
              Drag & drop a file, or{" "}
              <span className="text-blue-600 dark:text-blue-400 underline underline-offset-2">
                browse
              </span>
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              PDF, DOCX, JPG, PNG — up to {MAX_SIZE_MB} MB
            </p>
          </>
        )}
      </div>

      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
    </div>
  );
}

function UploadIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  );
}
