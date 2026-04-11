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
