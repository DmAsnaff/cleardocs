import apiClient from "./client";
import type { ChatSession, ChatSessionSummary, ChatMessage } from "@/types/chat";

interface ApiEnvelope<T> {
  status: "success" | "error";
  message: string;
  data: T;
}

export async function listSessions(documentId: string): Promise<ChatSessionSummary[]> {
  const { data } = await apiClient.get<ApiEnvelope<ChatSessionSummary[]>>(
    `/documents/${documentId}/chat/sessions/`
  );
  return data.data;
}

export async function createSession(
  documentId: string,
  title?: string
): Promise<ChatSession> {
  const { data } = await apiClient.post<ApiEnvelope<ChatSession>>(
    `/documents/${documentId}/chat/sessions/`,
    title ? { title } : {}
  );
  return data.data;
}

export async function getSession(
  documentId: string,
  sessionId: string
): Promise<ChatSession> {
  const { data } = await apiClient.get<ApiEnvelope<ChatSession>>(
    `/documents/${documentId}/chat/sessions/${sessionId}/`
  );
  return data.data;
}

export async function deleteSession(
  documentId: string,
  sessionId: string
): Promise<void> {
  await apiClient.delete(`/documents/${documentId}/chat/sessions/${sessionId}/`);
}

export async function sendMessage(
  documentId: string,
  sessionId: string,
  content: string
): Promise<ChatMessage> {
  const { data } = await apiClient.post<ApiEnvelope<ChatMessage>>(
    `/documents/${documentId}/chat/sessions/${sessionId}/messages/`,
    { content }
  );
  return data.data;
}
