import apiClient from "./client";
import type { DocumentAnalysis, Clause, Risk } from "@/types/analysis";

interface ApiEnvelope<T> {
  status: "success" | "error";
  message: string;
  data: T;
}

export async function getAnalysis(documentId: string): Promise<DocumentAnalysis> {
  const { data } = await apiClient.get<ApiEnvelope<DocumentAnalysis>>(
    `/documents/${documentId}/analysis/`
  );
  return data.data;
}

export async function getClauses(documentId: string): Promise<Clause[]> {
  const { data } = await apiClient.get<ApiEnvelope<{ id: string; clauses: Clause[] }>>(
    `/documents/${documentId}/analysis/clauses/`
  );
  return data.data.clauses;
}

export async function getRisks(documentId: string): Promise<Risk[]> {
  const { data } = await apiClient.get<ApiEnvelope<{ id: string; risks: Risk[] }>>(
    `/documents/${documentId}/analysis/risks/`
  );
  return data.data.risks;
}

export async function exportAnalysis(documentId: string, filename: string): Promise<void> {
  const response = await apiClient.post(
    `/documents/${documentId}/analysis/export/`,
    {},
    { responseType: "blob" }
  );
  const url = URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
