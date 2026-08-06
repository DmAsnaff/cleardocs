"use client";

import { cn } from "@/lib/utils";

interface PDFViewerProps {
  url: string;
  className?: string;
}

/**
 * Renders the original PDF using the browser's built-in PDF viewer via an
 * <iframe>. This intentionally avoids react-pdf / pdfjs-dist, whose ESM build
 * throws "Object.defineProperty called on non-object" under this Next.js setup
 * and takes down the whole results page.
 */
export function PDFViewer({ url, className }: PDFViewerProps) {
  return (
    <div className={cn("flex flex-col bg-neutral-100 dark:bg-neutral-800", className)}>
      <iframe
        src={url}
        title="Original document"
        className="w-full flex-1 border-0"
      />
      <div className="flex shrink-0 items-center justify-between border-t bg-background px-3 py-2 text-sm text-muted-foreground">
        <span>Original document</span>
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          className="text-blue-600 hover:underline"
        >
          Open in new tab ↗
        </a>
      </div>
    </div>
  );
}
