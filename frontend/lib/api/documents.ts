import apiClient from "./client";
import type {
  Document,
  DocumentListResponse,
  DocumentStatus_Payload,
  UploadPayload,
} from "@/types/document";

interface ApiEnvelope<T> {
  status: "success" | "error";
  message: string;
  data: T;
}

export async function uploadDocument(payload: UploadPayload): Promise<Document> {
  const form = new FormData();
  form.append("file", payload.file);
  if (payload.doc_category) form.append("doc_category", payload.doc_category);
  if (payload.target_language) form.append("target_language", payload.target_language);

  const { data } = await apiClient.post<ApiEnvelope<Document>>("/documents/", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data.data;
}

export async function listDocuments(params?: {
  cursor?: string;
  category?: string;
  status?: string;
  search?: string;
}): Promise<DocumentListResponse> {
  const { data } = await apiClient.get<DocumentListResponse>("/documents/", { params });
  return data;
}

export async function getDocument(id: string): Promise<Document> {
  const { data } = await apiClient.get<ApiEnvelope<Document>>(`/documents/${id}/`);
  return data.data;
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient.delete(`/documents/${id}/`);
}

export async function getDocumentStatus(id: string): Promise<DocumentStatus_Payload> {
  const { data } = await apiClient.get<ApiEnvelope<DocumentStatus_Payload>>(
    `/documents/${id}/status/`
  );
  return data.data;
}
