export type TranslationStatus = "pending" | "processing" | "done" | "failed";

export interface TranslatedClause {
  title: string;
  simplified: string;
  type: string;
}

export interface TranslatedRisk {
  title: string;
  description: string;
  severity: "high" | "medium" | "low";
  recommendation: string;
}

export interface Translation {
  id: string;
  language: string;
  summary: string;
  simplified_text: string;
  key_points: string[];
  clauses: TranslatedClause[];
  risks: TranslatedRisk[];
  status: TranslationStatus;
  error_message: string | null;
  tokens_used: number;
  created_at: string;
  updated_at: string;
}
