import type { CompareResponse, Offer, OfferInput } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Request failed");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function listOffers() {
  return apiFetch<Offer[]>("/offers");
}

export function createOffer(payload: OfferInput) {
  return apiFetch<Offer>("/offers", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateOffer(offerId: number, payload: Partial<OfferInput>) {
  return apiFetch<Offer>(`/offers/${offerId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteOffer(offerId: number) {
  return apiFetch<void>(`/offers/${offerId}`, {
    method: "DELETE",
  });
}

export function compareOffers(sortBy: string = "total_comp_annual") {
  return apiFetch<CompareResponse>(`/offers/compare?sort_by=${sortBy}&descending=true`);
}

export function seedOffers() {
  return apiFetch<Offer[]>("/dev/seed", {
    method: "POST",
  });
}
