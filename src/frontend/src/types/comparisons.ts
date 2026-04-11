export type ComparisonMode = "one_to_one" | "one_to_all";

export interface ComparisonPayload {
  id: string;
  comparison_mode: ComparisonMode;
  base_offer_id: string;
  selected_offer_ids: string[];
  summary_text: string;
  note: string | null;
  created_at: string;
  updated_at: string;
}

export interface ComparisonCreateRequest {
  mode: ComparisonMode;
  selected_offer_ids: string[];
  base_offer_id?: string;
  note?: string | null;
}

export interface ComparisonCreateResponse {
  status: string;
  errors: string[];
  comparison: ComparisonPayload | null;
}

export interface ComparisonListResponse {
  comparisons: ComparisonPayload[];
}
