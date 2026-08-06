"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

export type LayoutTab = "original" | "simplified" | "clauses" | "risks" | "chat";

const TABS: { id: LayoutTab; label: string }[] = [
  { id: "original", label: "Original" },
  { id: "simplified", label: "Simplified" },
  { id: "clauses", label: "Clauses" },
  { id: "risks", label: "Risks" },
  { id: "chat", label: "Chat" },
];

interface DocumentLayoutProps {
  pdfPanel: React.ReactNode;
  simplifiedPanel: React.ReactNode;
  clausesPanel: React.ReactNode;
  risksPanel: React.ReactNode;
  chatPanel: React.ReactNode;
  riskCount?: number;
}

/**
 * Single, always-visible tabbed layout used at every screen size. (An earlier
 * version hid the tab bar on desktop behind a split-panel view, which removed
 * access to Chat on wide screens — this keeps every destination reachable and
 * behaves consistently as the window resizes.)
 */
export function DocumentLayout({
  pdfPanel,
  simplifiedPanel,
  clausesPanel,
  risksPanel,
  chatPanel,
  riskCount = 0,
}: DocumentLayoutProps) {
  const [tab, setTab] = useState<LayoutTab>("simplified");

  return (
    <div className="flex h-full flex-col">
      {/* Tab bar — visible at all screen sizes */}
      <div className="flex shrink-0 overflow-x-auto border-b border-border bg-background">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={cn(
              "shrink-0 border-b-2 px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors",
              tab === t.id
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-muted-foreground hover:text-foreground"
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

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {tab === "original" && pdfPanel}
        {tab === "simplified" && simplifiedPanel}
        {tab === "clauses" && clausesPanel}
        {tab === "risks" && risksPanel}
        {tab === "chat" && chatPanel}
      </div>
    </div>
  );
}
