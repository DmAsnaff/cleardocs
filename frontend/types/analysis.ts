export type RiskSeverity = "high" | "medium" | "low";
export type ClauseType = "obligation" | "right" | "restriction" | "condition" | "definition" | "general";

export interface Clause {
  title: string;
  text: string;
  simplified: string;
  type: ClauseType;
}

export interface Risk {
  title: string;
  description: string;
  severity: RiskSeverity;
  recommendation: string;
}

export interface KeyDate {
  label: string;
  date: string | null;
  relative: string | null;
  description: string;
}

export interface DocumentAnalysis {
  id: string;
  summary: string;
  simplified_text: string;
  reading_level: string;
  flesch_kincaid_score: number | null;
  key_points: string[];
  clauses: Clause[];
  risks: Risk[];
  key_dates: KeyDate[];
  word_count: number | null;
  prompt_version: string;
  model_used: string;
  tokens_used: number;
  estimated_cost_usd: string;
  created_at: string;
  updated_at: string;
}

export const SEVERITY_COLORS: Record<RiskSeverity, string> = {
  high: "text-red-600 bg-red-50 border-red-200",
  medium: "text-amber-600 bg-amber-50 border-amber-200",
  low: "text-green-600 bg-green-50 border-green-200",
};

export const CLAUSE_TYPE_LABELS: Record<ClauseType, string> = {
  obligation: "Obligation",
  right: "Right",
  restriction: "Restriction",
  condition: "Condition",
  definition: "Definition",
  general: "General",
};
