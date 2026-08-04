"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { Clause } from "@/types/analysis";
import { CLAUSE_TYPE_LABELS } from "@/types/analysis";

interface ClauseCardProps {
  clause: Clause;
  index: number;
}

export function ClauseCard({ clause, index }: ClauseCardProps) {
  const [showOriginal, setShowOriginal] = useState(false);

  return (
    <div className="rounded-xl border border-border bg-card shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 px-4 py-3">
        <div className="min-w-0">
          <p className="font-medium text-sm">{clause.title || `Clause ${index + 1}`}</p>
          <span className="mt-0.5 inline-block rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            {CLAUSE_TYPE_LABELS[clause.type] ?? clause.type}
          </span>
        </div>
        <button
          type="button"
          onClick={() => setShowOriginal((v) => !v)}
          className="shrink-0 text-xs text-blue-600 underline underline-offset-2 hover:text-blue-700"
        >
          {showOriginal ? "Show simplified" : "Show original"}
        </button>
      </div>

      {/* Body */}
      <div className="border-t border-border px-4 py-3">
        {showOriginal ? (
          <p className="text-sm text-muted-foreground leading-relaxed italic">{clause.text}</p>
        ) : (
          <p className="text-sm leading-relaxed">{clause.simplified}</p>
        )}
      </div>
    </div>
  );
}
