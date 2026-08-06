"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { getAccessToken } from "@/lib/api/client";
import { getDocumentStatus } from "@/lib/api/documents";
import type { ProgressEvent, DocumentStatus } from "@/types/document";

// Strip a trailing "/ws" so we never build ".../ws/ws/documents/...".
const WS_BASE = (process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000").replace(/\/ws\/?$/, "");
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECTS = 3;
const POLL_INTERVAL_MS = 2500;

const STATUS_PROGRESS: Record<DocumentStatus, number> = {
  pending: 5,
  validating: 20,
  extracting: 40,
  chunking: 55,
  analysing: 78,
  translating: 85,
  done: 100,
  failed: 0,
};

const STATUS_MESSAGE: Record<DocumentStatus, string> = {
  pending: "Queued…",
  validating: "Scanning the file…",
  extracting: "Extracting text…",
  chunking: "Splitting into sections…",
  analysing: "Analysing with AI…",
  translating: "Translating…",
  done: "Your document is ready.",
  failed: "Processing failed.",
};

function toProgress(
  documentId: string,
  status: DocumentStatus,
  error?: string | null
): ProgressEvent {
  return {
    document_id: documentId,
    status,
    progress: STATUS_PROGRESS[status] ?? 0,
    message: status === "failed" && error ? error : STATUS_MESSAGE[status] ?? "Processing…",
  };
}

interface UseDocumentProgressOptions {
  onDone?: (event: ProgressEvent) => void;
  onFailed?: (event: ProgressEvent) => void;
}

/**
 * Tracks a document's processing progress.
 *
 * Uses a WebSocket for live updates when an ASGI server is available, and
 * ALWAYS polls the status endpoint as a fallback so the UI still advances and
 * completes even when the WebSocket cannot connect (e.g. a WSGI dev server).
 */
export function useDocumentProgress(
  documentId: string | null,
  options: UseDocumentProgressOptions = {}
) {
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [connected, setConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const terminalRef = useRef(false);
  const optionsRef = useRef(options);
  optionsRef.current = options;

  // Fire onDone/onFailed exactly once, whichever source (WS or poll) sees it first.
  const finish = useCallback((event: ProgressEvent) => {
    if (terminalRef.current) return;
    terminalRef.current = true;
    setProgress(event);
    if (event.status === "done") optionsRef.current.onDone?.(event);
    else if (event.status === "failed") optionsRef.current.onFailed?.(event);
  }, []);

  // Reset the terminal guard whenever the tracked document changes.
  useEffect(() => {
    terminalRef.current = false;
  }, [documentId]);

  // --- WebSocket (live updates when the ASGI server is available) ---
  const disconnect = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  const connect = useCallback(() => {
    if (!documentId) return;
    const token = getAccessToken();
    const url = `${WS_BASE}/ws/documents/${documentId}/progress/${token ? `?token=${token}` : ""}`;

    let ws: WebSocket;
    try {
      ws = new WebSocket(url);
    } catch {
      return; // polling fallback will carry the load
    }
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      reconnectCount.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data: ProgressEvent = JSON.parse(event.data);
        if (data.status === "done" || data.status === "failed") {
          finish(data);
          disconnect();
        } else {
          setProgress(data);
        }
      } catch {
        // malformed message — ignore
      }
    };

    ws.onclose = (event) => {
      setConnected(false);
      if (event.wasClean || terminalRef.current || reconnectCount.current >= MAX_RECONNECTS) return;
      reconnectCount.current += 1;
      timeoutRef.current = setTimeout(connect, RECONNECT_DELAY_MS);
    };

    ws.onerror = () => ws.close();
  }, [documentId, disconnect, finish]);

  useEffect(() => {
    if (!documentId) return;
    connect();
    return disconnect;
  }, [documentId, connect, disconnect]);

  // --- Polling fallback (always runs; the reliable path when WS is down) ---
  useEffect(() => {
    if (!documentId) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;

    const poll = async () => {
      try {
        const s = await getDocumentStatus(documentId);
        if (!active) return;
        const event = toProgress(documentId, s.status, s.error_message);
        if (s.status === "done" || s.status === "failed") {
          finish(event);
          return;
        }
        setProgress(event);
      } catch {
        // transient error — keep polling
      }
      if (active) timer = setTimeout(poll, POLL_INTERVAL_MS);
    };

    poll();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [documentId, finish]);

  return { progress, connected };
}
