import type { TextTurnRequest, TextTurnResponse } from "../types/intake";
import type { OfferListResponse, OfferSortBy, SortDirection } from "../types/offers";

export async function sendTextTurn(request: TextTurnRequest): Promise<TextTurnResponse> {
  const response = await fetch("/api/v1/offers/intake/text", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    throw new Error(`Text intake request failed with status ${response.status}`);
  }

  return (await response.json()) as TextTurnResponse;
}

export async function sendAudioTurn(request: FormData): Promise<TextTurnResponse> {
  const response = await fetch("/api/v1/offers/intake/audio", {
    method: "POST",
    body: request
  });

  if (!response.ok) {
    throw new Error(`Audio intake request failed with status ${response.status}`);
  }

  return (await response.json()) as TextTurnResponse;
}

export async function fetchOffers(options?: {
  sortBy?: OfferSortBy;
  sortDirection?: SortDirection;
}): Promise<OfferListResponse> {
  const sortBy = options?.sortBy ?? "created_at";
  const sortDirection = options?.sortDirection ?? "desc";
  const params = new URLSearchParams({
    sort_by: sortBy,
    sort_direction: sortDirection
  });

  const response = await fetch(`/api/v1/offers?${params.toString()}`, {
    method: "GET"
  });

  if (!response.ok) {
    throw new Error(`Offers list request failed with status ${response.status}`);
  }

  return (await response.json()) as OfferListResponse;
}
