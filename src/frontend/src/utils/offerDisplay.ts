import type { OfferSchemaField } from "../types/offers";

export function getPath(payload: Record<string, unknown>, path: string): unknown {
  const parts = path.split(".");
  let cursor: unknown = payload;
  for (const part of parts) {
    if (!cursor || typeof cursor !== "object" || Array.isArray(cursor)) {
      return undefined;
    }
    cursor = (cursor as Record<string, unknown>)[part];
  }
  return cursor;
}

export function asText(value: unknown): string {
  return typeof value === "string" ? value : "";
}

export function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return null;
}

export function asStringList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => (typeof item === "string" ? item.trim() : ""))
    .filter((item) => item.length > 0);
}

export function formatUsd(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  }).format(amount);
}

export function formatDate(createdAt?: string): string | null {
  if (!createdAt) {
    return null;
  }
  const parsed = new Date(createdAt);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return `${String(parsed.getUTCMonth() + 1).padStart(2, "0")}-${String(parsed.getUTCDate()).padStart(2, "0")}-${parsed.getUTCFullYear()}`;
}

export function formatFieldValue(field: OfferSchemaField, value: unknown): string | null {
  if (field.data_type === "list_string") {
    return null;
  }
  if (field.storage_path.endsWith("created_at")) {
    return formatDate(typeof value === "string" ? value : undefined);
  }
  if (field.data_type === "number" || field.data_type === "integer") {
    const parsed = asNumber(value);
    if (parsed === null) {
      return null;
    }
    if (field.storage_path.includes("_usd")) {
      return formatUsd(parsed);
    }
    if (field.storage_path.includes("percent")) {
      return `${parsed}%`;
    }
    return `${parsed}`;
  }
  const text = asText(value).trim();
  return text === "" ? null : text;
}

export function isPresent(value: unknown): boolean {
  if (value === null || value === undefined) {
    return false;
  }
  if (typeof value === "string") {
    return value.trim() !== "";
  }
  if (Array.isArray(value)) {
    return value.length > 0;
  }
  return true;
}

export function getDerivedMonetary(payload: Record<string, unknown>): {
  annualBenefits: number | null;
  monthlyTakeHome: number | null;
  explanation: string | null;
} {
  const derived = getPath(payload, "derived_monetary");
  if (!derived || typeof derived !== "object" || Array.isArray(derived)) {
    return {
      annualBenefits: null,
      monthlyTakeHome: null,
      explanation: null
    };
  }
  const asRecord = derived as Record<string, unknown>;
  const explanationRaw = asRecord.explanation;
  return {
    annualBenefits: asNumber(asRecord.estimated_total_annual_monetary_benefits_usd),
    monthlyTakeHome: asNumber(asRecord.estimated_monthly_take_home_usd),
    explanation: typeof explanationRaw === "string" && explanationRaw.trim() ? explanationRaw : null
  };
}
