"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { getAccessToken } from "@/lib/api/client";
import type { ProgressEvent } from "@/types/document";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost";
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECTS = 5;

interface UseDocumentProgressOptions {
  onDone?: (event: ProgressEvent) => void;
  onFailed?: (event: ProgressEvent) => void;
}

export function useDocumentProgress(
  documentId: string | null,
  options: UseDocumentProgressOptions = {}
) {
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [connected, setConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const disconnect = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  const connect = useCallback(() => {
    if (!documentId) return;

    const token = getAccessToken();
    // Pass JWT as query param since WS headers aren't supported from browsers
    const url = `${WS_BASE}/ws/documents/${documentId}/progress/${token ? `?token=${token}` : ""}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      reconnectCount.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data: ProgressEvent = JSON.parse(event.data);
        setProgress(data);

        if (data.status === "done") {
          optionsRef.current.onDone?.(data);
          disconnect();
        } else if (data.status === "failed") {
          optionsRef.current.onFailed?.(data);
          disconnect();
        }
      } catch {
        // malformed message — ignore
      }
    };

    ws.onclose = (event) => {
      setConnected(false);
      // Don't reconnect if we closed intentionally or terminal state reached
      if (event.wasClean || reconnectCount.current >= MAX_RECONNECTS) return;

      reconnectCount.current += 1;
      timeoutRef.current = setTimeout(connect, RECONNECT_DELAY_MS);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [documentId, disconnect]);

  useEffect(() => {
    if (!documentId) return;
    connect();
    return disconnect;
  }, [documentId, connect, disconnect]);

  return { progress, connected };
}
