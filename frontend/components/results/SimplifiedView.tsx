"use client";

import { useState } from "react";
import { ClauseCard } from "./ClauseCard";
import { RiskBadge } from "./RiskBadge";
import { DateTimeline } from "./DateTimeline";
import type { DocumentAnalysis } from "@/types/analysis";
import { cn } from "@/lib/utils";

type Tab = "summary" | "clauses" | "risks" | "dates";

const TABS: { id: Tab; label: string }[] = [
  { id: "summary", label: "Summary" },
  { id: "clauses", label: "Clauses" },
  { id: "risks", label: "Risks" },
  { id: "dates", label: "Dates" },
];

interface SimplifiedViewProps {
  analysis: DocumentAnalysis;
}

export function SimplifiedView({ analysis }: SimplifiedViewProps) {
  const [tab, setTab] = useState<Tab>("summary");

  return (
    <div className="flex h-full flex-col">
      {/* Tab bar */}
      <div className="flex shrink-0 border-b border-border">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={cn(
              "flex-1 border-b-2 px-3 py-2.5 text-sm font-medium transition-colors",
              tab === t.id
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
            {t.id === "risks" && analysis.risks.length > 0 && (
              <span className="ml-1.5 rounded-full bg-red-100 px-1.5 py-0.5 text-xs font-semibold text-red-600">
                {analysis.risks.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto p-4">
        {tab === "summary" && <SummaryTab analysis={analysis} />}
        {tab === "clauses" && <ClausesTab analysis={analysis} />}
        {tab === "risks" && <RisksTab analysis={analysis} />}
        {tab === "dates" && <DatesTab analysis={analysis} />}
      </div>
    </div>
  );
}

function SummaryTab({ analysis }: { analysis: DocumentAnalysis }) {
  return (
    <div className="space-y-6">
      {/* Meta */}
      {(analysis.reading_level || analysis.flesch_kincaid_score != null) && (
        <div className="flex flex-wrap gap-2">
          {analysis.reading_level && (
            <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
              {analysis.reading_level}
            </span>
          )}
          {analysis.flesch_kincaid_score != null && (
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              Readability: {analysis.flesch_kincaid_score.toFixed(0)}/100
            </span>
          )}
          {analysis.word_count != null && (
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              {analysis.word_count.toLocaleString()} words
            </span>
          )}
        </div>
      )}

      {/* Summary */}
      {analysis.summary && (
        <div className="space-y-1.5">
          <h3 className="text-sm font-semibold">Summary</h3>
          <p className="text-sm leading-relaxed text-muted-foreground">{analysis.summary}</p>
        </div>
      )}

      {/* Key points */}
      {analysis.key_points.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold">Key Points</h3>
          <ul className="space-y-1.5">
            {analysis.key_points.map((pt, i) => (
              <li key={i} className="flex gap-2 text-sm">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-500" />
                <span>{pt}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Full simplified text */}
      {analysis.simplified_text && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold">Plain-English Version</h3>
          <div className="rounded-lg border bg-muted/30 p-4">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{analysis.simplified_text}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function ClausesTab({ analysis }: { analysis: DocumentAnalysis }) {
  if (analysis.clauses.length === 0) {
    return <p className="text-sm text-muted-foreground">No clauses extracted.</p>;
  }
  return (
    <div className="space-y-3">
      {analysis.clauses.map((clause, i) => (
        <ClauseCard key={i} clause={clause} index={i} />
      ))}
    </div>
  );
}

function RisksTab({ analysis }: { analysis: DocumentAnalysis }) {
  if (analysis.risks.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-8 text-center">
        <p className="text-2xl">✓</p>
        <p className="text-sm font-medium">No risks flagged</p>
        <p className="text-xs text-muted-foreground">No significant risks were identified in this document.</p>
      </div>
    );
  }

  const sorted = [...analysis.risks].sort((a, b) => {
    const order = { high: 0, medium: 1, low: 2 };
    return (order[a.severity] ?? 3) - (order[b.severity] ?? 3);
  });

  return (
    <div className="space-y-3">
      {sorted.map((risk, i) => (
        <div key={i} className="rounded-xl border border-border p-4 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <p className="font-medium text-sm">{risk.title}</p>
            <RiskBadge severity={risk.severity} />
          </div>
          <p className="text-sm text-muted-foreground">{risk.description}</p>
          {risk.recommendation && (
            <p className="rounded-lg bg-muted/50 px-3 py-2 text-xs">
              <span className="font-medium">Recommendation: </span>
              {risk.recommendation}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

function DatesTab({ analysis }: { analysis: DocumentAnalysis }) {
  return <DateTimeline dates={analysis.key_dates} />;
}
