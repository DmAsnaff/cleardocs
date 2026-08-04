"use client";

import { cn } from "@/lib/utils";
import { STATUS_LABELS, type DocumentStatus } from "@/types/document";

const STAGES: { status: DocumentStatus; label: string }[] = [
  { status: "validating", label: "Scanning" },
  { status: "extracting", label: "Extracting" },
  { status: "chunking", label: "Splitting" },
  { status: "analysing", label: "Analysing" },
  { status: "done", label: "Done" },
];

interface ProgressTrackerProps {
  status: DocumentStatus;
  progress: number;
  message: string;
}

const STAGE_ORDER: Record<DocumentStatus, number> = {
  pending: 0,
  validating: 1,
  extracting: 2,
  chunking: 3,
  analysing: 4,
  translating: 4,
  done: 5,
  failed: -1,
};

export function ProgressTracker({ status, progress, message }: ProgressTrackerProps) {
  const currentOrder = STAGE_ORDER[status] ?? 0;
  const isFailed = status === "failed";

  return (
    <div className="space-y-4">
      {/* Progress bar */}
      <div className="overflow-hidden rounded-full bg-muted h-2">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500 ease-out",
            isFailed ? "bg-destructive" : "bg-blue-500"
          )}
          style={{ width: `${isFailed ? 100 : progress}%` }}
        />
      </div>

      {/* Stage breadcrumbs */}
      <div className="flex items-center gap-1">
        {STAGES.map((stage, idx) => {
          const stageOrder = STAGE_ORDER[stage.status] ?? 0;
          const isDone = !isFailed && currentOrder > stageOrder;
          const isActive = !isFailed && currentOrder === stageOrder;

          return (
            <div key={stage.status} className="flex items-center gap-1">
              <div
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium transition-colors",
                  isDone && "bg-blue-500 text-white",
                  isActive && "bg-blue-100 text-blue-700 ring-2 ring-blue-500 dark:bg-blue-950 dark:text-blue-300",
                  !isDone && !isActive && "bg-muted text-muted-foreground"
                )}
              >
                {isDone ? <CheckIcon className="h-3 w-3" /> : idx + 1}
              </div>
              <span
                className={cn(
                  "text-xs",
                  isActive && "font-medium text-foreground",
                  !isActive && "text-muted-foreground"
                )}
              >
                {stage.label}
              </span>
              {idx < STAGES.length - 1 && (
                <div className={cn("h-px w-4 bg-muted", isDone && "bg-blue-500")} />
              )}
            </div>
          );
        })}
      </div>

      {/* Status message */}
      <p className={cn("text-sm", isFailed ? "text-destructive" : "text-muted-foreground")}>
        {message}
      </p>
    </div>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={3}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}
