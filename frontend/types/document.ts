export type DocumentStatus =
  | "pending"
  | "validating"
  | "extracting"
  | "chunking"
  | "analysing"
  | "translating"
  | "done"
  | "failed";

export type DocCategory = "legal" | "medical" | "government" | "financial" | "other";

export interface Document {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  file_size_mb: string;
  page_count: number | null;
  status: DocumentStatus;
  doc_category: DocCategory;
  target_language: string;
  error_message: string | null;
  uploaded_at: string;
  processed_at: string | null;
  expires_at: string;
  signed_url: string | null;
}

export interface DocumentStatus_Payload {
  id: string;
  status: DocumentStatus;
  error_message: string | null;
  processed_at: string | null;
}

export interface ProgressEvent {
  document_id: string;
  status: DocumentStatus;
  progress: number; // 0-100
  message: string;
}

export interface UploadPayload {
  file: File;
  doc_category?: DocCategory;
  target_language?: string;
}

export interface DocumentListResponse {
  next: string | null;
  previous: string | null;
  results: Document[];
}

export const DOC_CATEGORY_LABELS: Record<DocCategory, string> = {
  legal: "Legal",
  medical: "Medical",
  government: "Government",
  financial: "Financial",
  other: "Other",
};

export const STATUS_LABELS: Record<DocumentStatus, string> = {
  pending: "Pending",
  validating: "Scanning",
  extracting: "Extracting",
  chunking: "Splitting",
  analysing: "Analysing",
  translating: "Translating",
  done: "Done",
  failed: "Failed",
};
