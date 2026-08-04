export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  sources: string[];
  tokens_used: number;
  created_at: string;
}

export interface ChatSession {
  id: string;
  document_id: string;
  title: string;
  message_count: number;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

export interface ChatSessionSummary {
  id: string;
  document_id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

// WebSocket stream events from the server
export type ChatStreamEvent =
  | { event: "stream_start"; message_id: null }
  | { event: "token"; content: string }
  | { event: "stream_end"; message_id: string; sources: string[] }
  | { event: "error"; message: string };
