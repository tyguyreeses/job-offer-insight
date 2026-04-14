import type { TextTurnRequest, TextTurnResponse } from "../types/intake";
import type {
  OfferListResponse,
  OfferResponse,
  OfferSchemaPayload,
  OfferSchemaResponse,
  OfferSortBy,
  OfferSummaryPayload,
  OfferUpdateResponse,
  SortDirection
} from "../types/offers";

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

export async function finalizeIntakeSession(sessionId: string): Promise<TextTurnResponse> {
  const response = await fetch("/api/v1/offers/intake/finalize", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ session_id: sessionId })
  });

  if (!response.ok) {
    throw new Error(`Finalize intake request failed with status ${response.status}`);
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

export async function deleteOffer(offerId: string): Promise<void> {
  const response = await fetch(`/api/v1/offers/${offerId}`, {
    method: "DELETE"
  });
  if (!response.ok) {
    throw new Error(`Delete offer request failed with status ${response.status}`);
  }
}

export async function createDemoOffers(): Promise<void> {
  const response = await fetch("/api/v1/offers/debug/demo-seed", {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error(`Demo offer seed request failed with status ${response.status}`);
  }
}

export async function fetchOfferById(offerId: string): Promise<OfferSummaryPayload> {
  const response = await fetch(`/api/v1/offers/${offerId}`, {
    method: "GET"
  });
  if (!response.ok) {
    throw new Error(`Offer detail request failed with status ${response.status}`);
  }
  const payload = (await response.json()) as OfferResponse;
  return payload.offer;
}

export async function fetchOfferSchema(): Promise<OfferSchemaPayload> {
  const response = await fetch("/api/v1/offers/schema", { method: "GET" });
  if (!response.ok) {
    throw new Error(`Offer schema request failed with status ${response.status}`);
  }
  const payload = (await response.json()) as OfferSchemaResponse;
  return payload.offer_schema;
}

export async function updateOffer(
  offerId: string,
  payload: Record<string, unknown>
): Promise<OfferUpdateResponse> {
  const response = await fetch(`/api/v1/offers/${offerId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ payload })
  });
  if (!response.ok) {
    throw new Error(`Update offer request failed with status ${response.status}`);
  }
  return (await response.json()) as OfferUpdateResponse;
}
