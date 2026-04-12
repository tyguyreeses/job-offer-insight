export type ComparisonMode = "one_to_one" | "one_to_all";

export interface ComparisonPayload {
  id: string;
  comparison_mode: ComparisonMode;
  base_offer_id: string;
  selected_offer_ids: string[];
  summary_text: string;
  code_section: Record<string, unknown> | null;
  ai_section: unknown | null;
  note: string | null;
  created_at: string;
  updated_at: string;
}

export interface ComparisonCreateRequest {
  mode: ComparisonMode;
  selected_offer_ids: string[];
  base_offer_id?: string;
  summary_text?: string | null;
  code_section?: Record<string, unknown> | null;
  ai_section?: unknown | null;
  note?: string | null;
}

export interface ComparisonCreateResponse {
  status: string;
  errors: string[];
  comparison: ComparisonPayload | null;
}

export interface ComparisonGenerateCodeResponse {
  status: string;
  errors: string[];
  draft_id: string | null;
  mode: ComparisonMode | null;
  base_offer_id: string | null;
  selected_offer_ids: string[];
  code_section: Record<string, unknown> | null;
  ai_section_pending: boolean;
}

export interface ComparisonGenerateAIResponse {
  status: string;
  errors: string[];
  draft_id: string | null;
  ai_section: unknown | null;
}

export interface ComparisonListResponse {
  comparisons: ComparisonPayload[];
}
