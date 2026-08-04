"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

export type LayoutTab = "original" | "simplified" | "clauses" | "risks" | "chat";

const MOBILE_TABS: { id: LayoutTab; label: string }[] = [
  { id: "original", label: "Original" },
  { id: "simplified", label: "Simplified" },
  { id: "clauses", label: "Clauses" },
  { id: "risks", label: "Risks" },
  { id: "chat", label: "Chat" },
];

interface DocumentLayoutProps {
  /** Left panel — the PDF viewer (desktop only) */
  pdfPanel: React.ReactNode;
  /** Right panel — analysis tabs (desktop) or tab content (mobile) */
  simplifiedPanel: React.ReactNode;
  clausesPanel: React.ReactNode;
  risksPanel: React.ReactNode;
  chatPanel: React.ReactNode;
  riskCount?: number;
}

export function DocumentLayout({
  pdfPanel,
  simplifiedPanel,
  clausesPanel,
  risksPanel,
  chatPanel,
  riskCount = 0,
}: DocumentLayoutProps) {
  const [mobileTab, setMobileTab] = useState<LayoutTab>("simplified");

  return (
    <>
      {/* ── Desktop: two-column split ───────────────────────────────── */}
      <div className="hidden md:flex h-full">
        {/* Left: PDF viewer — 45% width */}
        <div className="w-[45%] shrink-0 border-r border-border overflow-hidden">
          {pdfPanel}
        </div>

        {/* Right: simplified analysis — 55% width */}
        <div className="flex-1 overflow-hidden">
          {simplifiedPanel}
        </div>
      </div>

      {/* ── Mobile: tab layout ──────────────────────────────────────── */}
      <div className="flex md:hidden h-full flex-col">
        {/* Tab bar */}
        <div className="flex shrink-0 overflow-x-auto border-b border-border bg-background">
          {MOBILE_TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setMobileTab(t.id)}
              className={cn(
                "shrink-0 border-b-2 px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors",
                mobileTab === t.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-muted-foreground",
              )}
            >
              {t.label}
              {t.id === "risks" && riskCount > 0 && (
                <span className="ml-1 rounded-full bg-red-100 px-1.5 py-0.5 text-xs font-semibold text-red-600">
                  {riskCount}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-hidden">
          {mobileTab === "original" && pdfPanel}
          {mobileTab === "simplified" && simplifiedPanel}
          {mobileTab === "clauses" && clausesPanel}
          {mobileTab === "risks" && risksPanel}
          {mobileTab === "chat" && chatPanel}
        </div>
      </div>
    </>
  );
}
