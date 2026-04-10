import type { TextTurnRequest, TextTurnResponse } from "../types/intake";

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
