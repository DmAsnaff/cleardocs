"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { createSession, listSessions } from "@/lib/api/chat";
import { getDocument } from "@/lib/api/documents";
import type { Document } from "@/types/document";
import type { ChatSessionSummary } from "@/types/chat";

export default function ChatPage() {
  const { id: documentId } = useParams<{ id: string }>();
  const router = useRouter();

  const [doc, setDoc] = useState<Document | null>(null);
  const [session, setSession] = useState<ChatSessionSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function init() {
      try {
        const [document, sessions] = await Promise.all([
          getDocument(documentId),
          listSessions(documentId),
        ]);
        setDoc(document);

        if (sessions.length > 0) {
          // Resume the most recent session
          setSession(sessions[0]);
        } else {
          // Create a new session
          const newSession = await createSession(documentId);
          setSession(newSession);
        }
      } catch {
        setError("Failed to load document chat.");
      } finally {
        setLoading(false);
      }
    }
    init();
  }, [documentId]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading chat…</p>
      </div>
    );
  }

  if (error || !doc || !session) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4">
        <p className="text-destructive">{error ?? "Something went wrong."}</p>
        <button
          onClick={() => router.back()}
          className="text-sm text-blue-600 underline underline-offset-2"
        >
          Go back
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="flex items-center gap-3 border-b bg-background px-4 py-3">
        <button
          onClick={() => router.back()}
          className="text-muted-foreground hover:text-foreground"
          aria-label="Back"
        >
          ←
        </button>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">{doc.original_filename}</p>
          <p className="text-xs text-muted-foreground capitalize">{doc.doc_category} document</p>
        </div>
      </header>

      {/* Chat panel fills the remaining height */}
      <div className="flex-1 overflow-hidden">
        <ChatPanel
          documentId={documentId}
          sessionId={session.id}
          category={doc.doc_category}
        />
      </div>
    </div>
  );
}
