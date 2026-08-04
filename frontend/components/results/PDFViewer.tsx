"use client";

import { useState, useCallback } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { cn } from "@/lib/utils";

// Use the bundled worker from pdfjs-dist
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

interface PDFViewerProps {
  url: string;
  className?: string;
}

export function PDFViewer({ url, className }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [error, setError] = useState<string | null>(null);

  const onLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setError(null);
  }, []);

  const onLoadError = useCallback(() => {
    setError("Failed to load PDF.");
  }, []);

  const prev = () => setPageNumber((p) => Math.max(1, p - 1));
  const next = () => setPageNumber((p) => Math.min(numPages, p + 1));
  const zoomIn = () => setScale((s) => Math.min(2.5, +(s + 0.2).toFixed(1)));
  const zoomOut = () => setScale((s) => Math.max(0.5, +(s - 0.2).toFixed(1)));

  if (error) {
    return (
      <div className={cn("flex items-center justify-center bg-muted/20 text-sm text-muted-foreground", className)}>
        {error}
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col", className)}>
      {/* PDF canvas */}
      <div className="flex-1 overflow-auto bg-neutral-200 dark:bg-neutral-800 flex justify-center py-4">
        <Document
          file={url}
          onLoadSuccess={onLoadSuccess}
          onLoadError={onLoadError}
          loading={
            <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
              Loading PDF…
            </div>
          }
        >
          <Page
            pageNumber={pageNumber}
            scale={scale}
            renderAnnotationLayer
            renderTextLayer
            className="shadow-lg"
          />
        </Document>
      </div>

      {/* Controls */}
      <div className="flex shrink-0 items-center justify-between border-t bg-background px-3 py-2 text-sm">
        {/* Pagination */}
        <div className="flex items-center gap-2">
          <button
            onClick={prev}
            disabled={pageNumber <= 1}
            className="rounded px-2 py-1 hover:bg-muted disabled:opacity-40"
            aria-label="Previous page"
          >
            ←
          </button>
          <span className="text-muted-foreground">
            {pageNumber} / {numPages || "—"}
          </span>
          <button
            onClick={next}
            disabled={pageNumber >= numPages}
            className="rounded px-2 py-1 hover:bg-muted disabled:opacity-40"
            aria-label="Next page"
          >
            →
          </button>
        </div>

        {/* Zoom */}
        <div className="flex items-center gap-2">
          <button
            onClick={zoomOut}
            disabled={scale <= 0.5}
            className="rounded px-2 py-1 hover:bg-muted disabled:opacity-40"
            aria-label="Zoom out"
          >
            −
          </button>
          <span className="w-12 text-center text-muted-foreground">{(scale * 100).toFixed(0)}%</span>
          <button
            onClick={zoomIn}
            disabled={scale >= 2.5}
            className="rounded px-2 py-1 hover:bg-muted disabled:opacity-40"
            aria-label="Zoom in"
          >
            +
          </button>
        </div>
      </div>
    </div>
  );
}
