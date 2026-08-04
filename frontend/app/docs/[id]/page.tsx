"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

import { DocumentLayout } from "@/components/results/DocumentLayout";
import { PDFViewer } from "@/components/results/PDFViewer";
import { SimplifiedView } from "@/components/results/SimplifiedView";
import { ClauseCard } from "@/components/results/ClauseCard";
import { RiskBadge } from "@/components/results/RiskBadge";
import { DateTimeline } from "@/components/results/DateTimeline";
import { AnalysisSkeleton, PDFViewerSkeleton } from "@/components/results/ResultsSkeleton";
import { ProgressTracker } from "@/components/upload/ProgressTracker";
import { ChatPanel } from "@/components/chat/ChatPanel";

import { getDocument } from "@/lib/api/documents";
import { getAnalysis, exportAnalysis } from "@/lib/api/analysis";
import { createSession, listSessions } from "@/lib/api/chat";

import type { Document } from "@/types/document";
import type { DocumentAnalysis } from "@/types/analysis";
import type { ChatSessionSummary } from "@/types/chat";

export default function DocumentResultsPage() {
  const { id: documentId } = useParams<{ id: string }>();
  const router = useRouter();

  const [doc, setDoc] = useState<Document | null>(null);
  const [analysis, setAnalysis] = useState<DocumentAnalysis | null>(null);
  const [chatSession, setChatSession] = useState<ChatSessionSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const document = await getDocument(documentId);
        if (cancelled) return;
        setDoc(document);

        if (document.status === "done") {
          const [analysisData, sessions] = await Promise.all([
            getAnalysis(documentId),
            listSessions(documentId),
          ]);
          if (cancelled) return;
          setAnalysis(analysisData);

          const session =
            sessions.length > 0 ? sessions[0] : await createSession(documentId);
          setChatSession(session);
        }
      } catch {
        if (!cancelled) setError("Failed to load document.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [documentId]);

  const handleExport = async () => {
    if (!doc) return;
    setExporting(true);
    try {
      await exportAnalysis(documentId, `${doc.original_filename}_simplified.pdf`);
    } catch {
      // silent — user will notice no download
    } finally {
      setExporting(false);
    }
  };

  // ── Loading ────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex h-screen flex-col">
        <PageHeader title="Loading…" onBack={() => router.push("/history")} />
        <div className="flex flex-1 overflow-hidden">
          <div className="w-[45%] shrink-0 border-r hidden md:block">
            <PDFViewerSkeleton />
          </div>
          <div className="flex-1">
            <AnalysisSkeleton />
          </div>
        </div>
      </div>
    );
  }

  // ── Error ──────────────────────────────────────────────────────────────
  if (error || !doc) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4">
        <p className="text-destructive">{error ?? "Document not found."}</p>
        <button onClick={() => router.push("/history")} className="text-sm text-blue-600 underline">
          Back to history
        </button>
      </div>
    );
  }

  // ── Still processing ───────────────────────────────────────────────────
  if (doc.status !== "done") {
    return (
      <div className="flex h-screen flex-col">
        <PageHeader title={doc.original_filename} onBack={() => router.push("/history")} />
        <div className="mx-auto mt-16 w-full max-w-md px-4">
          <h2 className="mb-6 text-center text-base font-semibold">Processing your document…</h2>
          <ProgressTracker
            status={doc.status}
            progress={
              doc.status === "failed" ? 100
              : doc.status === "pending" ? 5
              : doc.status === "validating" ? 15
              : doc.status === "extracting" ? 35
              : doc.status === "chunking" ? 55
              : doc.status === "analysing" ? 75
              : 90
            }
            message={
              doc.status === "failed"
                ? "Processing failed. Please try uploading again."
                : "This usually takes less than a minute."
            }
          />
          {doc.status === "failed" && (
            <div className="mt-6 text-center">
              <Link href="/upload" className="text-sm text-blue-600 underline">
                Upload a new document
              </Link>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── Done — full results ────────────────────────────────────────────────
  if (!analysis) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">Analysis data unavailable.</p>
      </div>
    );
  }

  const pdfPanel = doc.signed_url ? (
    <PDFViewer url={doc.signed_url} className="h-full" />
  ) : (
    <div className="flex h-full items-center justify-center bg-muted/20 text-sm text-muted-foreground">
      PDF preview not available
    </div>
  );

  const simplifiedPanel = <SimplifiedView analysis={analysis} />;

  const clausesPanel = (
    <div className="h-full overflow-y-auto p-4 space-y-3">
      {analysis.clauses.length === 0 ? (
        <p className="text-sm text-muted-foreground">No clauses extracted.</p>
      ) : (
        analysis.clauses.map((c, i) => <ClauseCard key={i} clause={c} index={i} />)
      )}
    </div>
  );

  const risksPanel = (
    <div className="h-full overflow-y-auto p-4 space-y-3">
      {analysis.risks.length === 0 ? (
        <p className="text-sm text-muted-foreground">No risks identified.</p>
      ) : (
        [...analysis.risks]
          .sort((a, b) => ({ high: 0, medium: 1, low: 2 }[a.severity] ?? 3) - ({ high: 0, medium: 1, low: 2 }[b.severity] ?? 3))
          .map((risk, i) => (
            <div key={i} className="rounded-xl border p-4 space-y-2">
              <div className="flex items-start justify-between gap-2">
                <p className="font-medium text-sm">{risk.title}</p>
                <RiskBadge severity={risk.severity} />
              </div>
              <p className="text-sm text-muted-foreground">{risk.description}</p>
              {risk.recommendation && (
                <p className="rounded-lg bg-muted/50 px-3 py-2 text-xs">
                  <span className="font-medium">Recommendation: </span>{risk.recommendation}
                </p>
              )}
            </div>
          ))
      )}
    </div>
  );

  const chatPanelNode = chatSession ? (
    <ChatPanel
      documentId={documentId}
      sessionId={chatSession.id}
      category={doc.doc_category}
    />
  ) : (
    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
      Chat unavailable
    </div>
  );

  return (
    <div className="flex h-screen flex-col">
      <PageHeader
        title={doc.original_filename}
        onBack={() => router.push("/history")}
        actions={
          <div className="flex items-center gap-2">
            <Link
              href={`/docs/${documentId}/translate`}
              className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted"
            >
              Translate
            </Link>
            <button
              onClick={handleExport}
              disabled={exporting}
              className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {exporting ? "Exporting…" : "Export PDF"}
            </button>
          </div>
        }
      />

      <div className="flex-1 overflow-hidden">
        <DocumentLayout
          pdfPanel={pdfPanel}
          simplifiedPanel={simplifiedPanel}
          clausesPanel={clausesPanel}
          risksPanel={risksPanel}
          chatPanel={chatPanelNode}
          riskCount={analysis.risks.length}
        />
      </div>
    </div>
  );
}

function PageHeader({
  title,
  onBack,
  actions,
}: {
  title: string;
  onBack: () => void;
  actions?: React.ReactNode;
}) {
  return (
    <header className="flex shrink-0 items-center gap-3 border-b bg-background px-4 py-2.5">
      <button
        onClick={onBack}
        className="text-muted-foreground hover:text-foreground"
        aria-label="Back"
      >
        ←
      </button>
      <p className="min-w-0 flex-1 truncate text-sm font-semibold">{title}</p>
      {actions}
    </header>
  );
}
