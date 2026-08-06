"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { getAccessToken } from "@/lib/api/client";
import { sendMessage } from "@/lib/api/chat";
import type { ChatMessage, ChatStreamEvent } from "@/types/chat";

// Strip a trailing "/ws" so we never build ".../ws/ws/chat/...".
const WS_BASE = (process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000").replace(/\/ws\/?$/, "");
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECTS = 5;

interface UseChatStreamOptions {
  documentId: string;
  sessionId: string;
}

export function useChatStream({ documentId, sessionId }: UseChatStreamOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streamingContent, setStreamingContent] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const disconnect = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  const connect = useCallback(() => {
    const token = getAccessToken();
    const url = `${WS_BASE}/ws/chat/${sessionId}/${token ? `?token=${token}` : ""}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      reconnectCount.current = 0;
    };

    ws.onmessage = (ev) => {
      try {
        const event: ChatStreamEvent = JSON.parse(ev.data);
        handleStreamEvent(event);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = (ev) => {
      setConnected(false);
      if (ev.wasClean || reconnectCount.current >= MAX_RECONNECTS) return;
      reconnectCount.current += 1;
      timeoutRef.current = setTimeout(connect, RECONNECT_DELAY_MS);
    };

    ws.onerror = () => ws.close();
  }, [sessionId]);

  const handleStreamEvent = useCallback((event: ChatStreamEvent) => {
    if (event.event === "stream_start") {
      setStreamingContent("");
      setIsStreaming(true);
      setError(null);
    } else if (event.event === "token") {
      setStreamingContent((prev) => (prev ?? "") + event.content);
    } else if (event.event === "stream_end") {
      setIsStreaming(false);
      setStreamingContent(null);
      // Re-fetch the assistant message via the final content
      if (event.message_id) {
        const assistantMsg: ChatMessage = {
          id: event.message_id,
          role: "assistant",
          // Content will be fetched on next full session load; accumulate from stream for now
          content: "",
          sources: event.sources,
          tokens_used: 0,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      }
    } else if (event.event === "error") {
      setIsStreaming(false);
      setStreamingContent(null);
      setError(event.message);
    }
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  const submitMessage = useCallback(
    async (content: string) => {
      setError(null);
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content,
        sources: [],
        tokens_used: 0,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);

      try {
        await sendMessage(documentId, sessionId, content);
      } catch {
        setError("Failed to send message.");
        setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
      }
    },
    [documentId, sessionId]
  );

  return {
    messages,
    setMessages,
    streamingContent,
    isStreaming,
    connected,
    error,
    submitMessage,
  };
}
