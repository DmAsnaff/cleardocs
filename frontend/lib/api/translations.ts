import apiClient from "./client";
import type { Translation } from "@/types/translation";

interface ApiEnvelope<T> {
  status: "success" | "error";
  message: string;
  data: T;
}

export async function listTranslations(documentId: string): Promise<Translation[]> {
  const { data } = await apiClient.get<ApiEnvelope<Translation[]>>(
    `/documents/${documentId}/translations/`
  );
  return data.data;
}

export async function requestTranslation(
  documentId: string,
  language: string
): Promise<Translation> {
  const { data } = await apiClient.post<ApiEnvelope<Translation>>(
    `/documents/${documentId}/translations/`,
    { language }
  );
  return data.data;
}

export async function getTranslation(
  documentId: string,
  language: string
): Promise<Translation> {
  const { data } = await apiClient.get<ApiEnvelope<Translation>>(
    `/documents/${documentId}/translations/${language}/`
  );
  return data.data;
}
