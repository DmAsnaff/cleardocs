"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { getDocument } from "@/lib/api/documents";
import { getTranslation, requestTranslation, listTranslations } from "@/lib/api/translations";
import { LanguageSelector } from "@/components/upload/LanguageSelector";
import type { Document } from "@/types/document";
import type { Translation } from "@/types/translation";
import { SEVERITY_COLORS } from "@/types/analysis";
import { cn } from "@/lib/utils";

export default function TranslatePage() {
  const { id: documentId } = useParams<{ id: string }>();
  const router = useRouter();

  const [doc, setDoc] = useState<Document | null>(null);
  const [language, setLanguage] = useState("es");
  const [translation, setTranslation] = useState<Translation | null>(null);
  const [loading, setLoading] = useState(true);
  const [requesting, setRequesting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load document on mount
  useEffect(() => {
    getDocument(documentId)
      .then((d) => {
        setDoc(d);
        setLanguage(d.target_language !== "en" ? d.target_language : "es");
      })
      .catch(() => setError("Failed to load document."))
      .finally(() => setLoading(false));
  }, [documentId]);

  // Fetch translation when language changes
  useEffect(() => {
    if (!doc) return;
    setTranslation(null);
    getTranslation(documentId, language)
      .then(setTranslation)
      .catch(() => {}); // 404 means no translation yet
  }, [documentId, language, doc]);

  const handleRequest = async () => {
    setRequesting(true);
    setError(null);
    try {
      const result = await requestTranslation(documentId, language);
      setTranslation(result);
      // Poll until done
      const poll = setInterval(async () => {
        try {
          const updated = await getTranslation(documentId, language);
          setTranslation(updated);
          if (updated.status === "done" || updated.status === "failed") clearInterval(poll);
        } catch {}
      }, 3000);
    } catch {
      setError("Failed to request translation.");
    } finally {
      setRequesting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-muted-foreground">Loading…</p>
      </div>
    );
  }

  const isDone = translation?.status === "done";
  const isProcessing = translation?.status === "pending" || translation?.status === "processing";
  const noTranslation = !translation;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 space-y-8">
      {/* Header */}
      <div className="flex items-start gap-3">
        <button
          onClick={() => router.back()}
          className="mt-1 text-muted-foreground hover:text-foreground"
        >
          ←
        </button>
        <div>
          <h1 className="text-xl font-bold">{doc?.original_filename}</h1>
          <p className="text-sm text-muted-foreground">Translation</p>
        </div>
      </div>

      {/* Language selector */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Translate to</label>
        <LanguageSelector value={language} onChange={setLanguage} />
      </div>

      {/* Action / status */}
      {noTranslation && (
        <button
          onClick={handleRequest}
          disabled={requesting}
          className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {requesting ? "Requesting…" : "Translate document"}
        </button>
      )}

      {isProcessing && (
        <div className="rounded-lg border bg-muted/40 px-4 py-3 text-sm text-muted-foreground">
          Translation is in progress… This may take a minute.
        </div>
      )}

      {translation?.status === "failed" && (
        <div className="space-y-2">
          <p className="text-sm text-destructive">{translation.error_message ?? "Translation failed."}</p>
          <button
            onClick={handleRequest}
            className="text-sm text-blue-600 underline underline-offset-2"
          >
            Try again
          </button>
        </div>
      )}

      {error && <p className="text-sm text-destructive">{error}</p>}

      {/* Translation content */}
      {isDone && translation && (
        <div className="space-y-8">
          {/* Summary */}
          {translation.summary && (
            <section>
              <h2 className="mb-2 text-base font-semibold">Summary</h2>
              <p className="text-sm leading-relaxed text-muted-foreground">{translation.summary}</p>
            </section>
          )}

          {/* Key points */}
          {translation.key_points?.length > 0 && (
            <section>
              <h2 className="mb-2 text-base font-semibold">Key Points</h2>
              <ul className="space-y-1.5">
                {translation.key_points.map((pt, i) => (
                  <li key={i} className="flex gap-2 text-sm">
                    <span className="mt-0.5 text-blue-500">•</span>
                    <span>{pt}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Simplified text */}
          {translation.simplified_text && (
            <section>
              <h2 className="mb-2 text-base font-semibold">Full Simplified Text</h2>
              <p className="whitespace-pre-wrap rounded-lg border bg-muted/30 p-4 text-sm leading-relaxed">
                {translation.simplified_text}
              </p>
            </section>
          )}

          {/* Clauses */}
          {translation.clauses?.length > 0 && (
            <section>
              <h2 className="mb-3 text-base font-semibold">Clauses</h2>
              <div className="space-y-3">
                {translation.clauses.map((cl, i) => (
                  <div key={i} className="rounded-lg border p-4">
                    <p className="font-medium text-sm">{cl.title}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{cl.simplified}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Risks */}
          {translation.risks?.length > 0 && (
            <section>
              <h2 className="mb-3 text-base font-semibold">Risks</h2>
              <div className="space-y-3">
                {translation.risks.map((risk, i) => (
                  <div key={i} className={cn("rounded-lg border p-4", SEVERITY_COLORS[risk.severity])}>
                    <p className="font-medium text-sm">{risk.title}</p>
                    <p className="mt-1 text-sm">{risk.description}</p>
                    {risk.recommendation && (
                      <p className="mt-1 text-xs opacity-80">→ {risk.recommendation}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
