"use client";

import { useEffect, useRef, useState } from "react";
import { MessageBubble, StreamingBubble } from "./MessageBubble";
import { SuggestedQuestions } from "./SuggestedQuestions";
import { useChatStream } from "@/lib/hooks/useChatStream";
import { getSession } from "@/lib/api/chat";
import type { DocCategory } from "@/types/document";
import type { ChatMessage } from "@/types/chat";
import { cn } from "@/lib/utils";

interface ChatPanelProps {
  documentId: string;
  sessionId: string;
  category: DocCategory;
}

export function ChatPanel({ documentId, sessionId, category }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const [loadingHistory, setLoadingHistory] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  const {
    messages,
    setMessages,
    streamingContent,
    isStreaming,
    connected,
    error,
    submitMessage,
  } = useChatStream({ documentId, sessionId });

  // Load existing message history
  useEffect(() => {
    getSession(documentId, sessionId)
      .then((session) => setMessages(session.messages))
      .catch(() => {})
      .finally(() => setLoadingHistory(false));
  }, [documentId, sessionId, setMessages]);

  // Auto-scroll on new content
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || isStreaming) return;
    setInput("");
    await submitMessage(text);
  };

  const handleSuggestion = async (q: string) => {
    if (isStreaming) return;
    await submitMessage(q);
  };

  const isEmpty = !loadingHistory && messages.length === 0;

  return (
    <div className="flex h-full flex-col">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {loadingHistory ? (
          <p className="text-center text-sm text-muted-foreground">Loading…</p>
        ) : isEmpty ? (
          <SuggestedQuestions category={category} onSelect={handleSuggestion} />
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}

        {/* Streaming response */}
        {isStreaming && streamingContent !== null && (
          <StreamingBubble content={streamingContent} />
        )}

        {/* Error notice */}
        {error && (
          <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t bg-background px-4 py-3">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={connected ? "Ask a question about this document…" : "Connecting…"}
            disabled={!connected || isStreaming}
            className="flex-1 rounded-lg border border-input bg-background px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || !connected || isStreaming}
            className={cn(
              "rounded-lg px-4 py-2 text-sm font-semibold text-white transition-colors",
              "bg-blue-600 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            )}
          >
            {isStreaming ? "…" : "Send"}
          </button>
        </form>

        {!connected && (
          <p className="mt-1 text-xs text-muted-foreground">Reconnecting to chat server…</p>
        )}
      </div>
    </div>
  );
}
