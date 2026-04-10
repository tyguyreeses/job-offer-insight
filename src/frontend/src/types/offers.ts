export type OfferSortBy = "created_at" | "company_name" | "role_title";
export type SortDirection = "asc" | "desc";

export interface OfferMeta {
  created_at?: string;
  updated_at?: string;
}

export interface OfferSummaryPayload {
  id: string;
  company_name: string;
  role_title: string;
  location?: string;
  compensation?: Record<string, unknown>;
  monetary_benefits?: Record<string, unknown>;
  non_monetary_benefits?: Record<string, unknown>;
  non_monetary_summary_bullets?: string[];
  offer_meta?: OfferMeta;
  [key: string]: unknown;
}

export interface OfferListResponse {
  offers: OfferSummaryPayload[];
}

export interface OfferResponse {
  offer: OfferSummaryPayload;
}

export interface MissingFieldPrompt {
  path: string;
  required: boolean;
  message: string;
}

export interface OfferUpdateResponse {
  status: string;
  errors: string[];
  warnings: string[];
  missing_field_prompts: MissingFieldPrompt[];
  offer: OfferSummaryPayload | null;
}
