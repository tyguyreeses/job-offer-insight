export type OfferSortBy = "created_at" | "company_name" | "role_title";
export type SortDirection = "asc" | "desc";

export interface OfferMeta {
  created_at?: string;
  updated_at?: string;
}

export interface DerivedMonetaryPayload {
  estimated_total_annual_monetary_benefits_usd?: number;
  estimated_monthly_take_home_usd?: number;
  tax_profile_used?: Record<string, unknown>;
  explanation?: string;
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
  derived_monetary?: DerivedMonetaryPayload;
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

export type OfferSchemaDataType = "string" | "number" | "integer" | "list_string";
export type OfferSchemaFieldGroup = "core" | "compensation" | "monetary" | "non_monetary" | "meta";
export type OfferSchemaCardStyle = "value" | "labeled_value" | "list";
export type OfferSchemaEditWidget = "text" | "number" | "textarea" | "textarea_list";

export interface OfferSchemaCardSection {
  section_id: string;
  title: string;
}

export interface OfferSchemaEditSection {
  section_id: string;
  title: string;
}

export interface OfferSchemaFieldCardConfig {
  visible: boolean;
  section_id: string;
  order: number;
  style: OfferSchemaCardStyle;
}

export interface OfferSchemaFieldEditConfig {
  visible: boolean;
  section_id: string;
  order: number;
  widget: OfferSchemaEditWidget;
}

export interface OfferSchemaField {
  id: string;
  label: string;
  description?: string;
  storage_path: string;
  data_type: OfferSchemaDataType;
  group: OfferSchemaFieldGroup;
  required?: boolean;
  default_when_omitted?: unknown;
  card: OfferSchemaFieldCardConfig;
  edit: OfferSchemaFieldEditConfig;
}

export interface OfferSchemaIdentity {
  company_name_path: string;
  role_title_path: string;
}

export interface OfferSchemaRequired {
  all_of: string[];
  one_of: string[][];
}

export interface OfferSchemaPayload {
  version: number;
  identity: OfferSchemaIdentity;
  required: OfferSchemaRequired;
  card_sections: OfferSchemaCardSection[];
  edit_sections: OfferSchemaEditSection[];
  fields: OfferSchemaField[];
}

export interface OfferSchemaResponse {
  offer_schema: OfferSchemaPayload;
}
