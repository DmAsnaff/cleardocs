"use client";

import { cn } from "@/lib/utils";

function Bone({ className }: { className?: string }) {
  return (
    <div className={cn("animate-pulse rounded-md bg-muted", className)} />
  );
}

export function AnalysisSkeleton() {
  return (
    <div className="space-y-6 p-4">
      {/* Summary block */}
      <div className="space-y-2">
        <Bone className="h-4 w-24" />
        <Bone className="h-3 w-full" />
        <Bone className="h-3 w-5/6" />
        <Bone className="h-3 w-4/6" />
      </div>

      {/* Key points */}
      <div className="space-y-2">
        <Bone className="h-4 w-28" />
        {[...Array(3)].map((_, i) => (
          <div key={i} className="flex gap-2">
            <Bone className="mt-1 h-2 w-2 shrink-0 rounded-full" />
            <Bone className="h-3 flex-1" />
          </div>
        ))}
      </div>

      {/* Cards */}
      <div className="space-y-2">
        <Bone className="h-4 w-20" />
        {[...Array(2)].map((_, i) => (
          <div key={i} className="rounded-xl border border-border p-4 space-y-2">
            <Bone className="h-3 w-40" />
            <Bone className="h-3 w-full" />
            <Bone className="h-3 w-3/4" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function PDFViewerSkeleton() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 bg-muted/20 p-6">
      <Bone className="h-full w-full max-w-sm rounded-lg" style={{ minHeight: 400 }} />
      <div className="flex gap-2">
        <Bone className="h-8 w-16 rounded-lg" />
        <Bone className="h-8 w-12 rounded-lg" />
        <Bone className="h-8 w-16 rounded-lg" />
      </div>
    </div>
  );
}
