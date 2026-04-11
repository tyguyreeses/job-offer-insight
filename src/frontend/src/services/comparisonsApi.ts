import type {
  ComparisonCreateRequest,
  ComparisonCreateResponse,
  ComparisonGenerateAIResponse,
  ComparisonGenerateCodeResponse,
  ComparisonListResponse,
  ComparisonPayload
} from "../types/comparisons";

export async function fetchComparisons(): Promise<ComparisonListResponse> {
  const response = await fetch("/api/v1/comparisons", { method: "GET" });
  if (!response.ok) {
    throw new Error(`Comparisons list request failed with status ${response.status}`);
  }
  return (await response.json()) as ComparisonListResponse;
}

export async function fetchComparisonById(comparisonId: string): Promise<ComparisonPayload> {
  const response = await fetch(`/api/v1/comparisons/${comparisonId}`, { method: "GET" });
  if (!response.ok) {
    throw new Error(`Comparison detail request failed with status ${response.status}`);
  }
  return (await response.json()) as ComparisonPayload;
}

export async function createComparison(
  request: ComparisonCreateRequest
): Promise<ComparisonCreateResponse> {
  const response = await fetch("/api/v1/comparisons", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
  if (!response.ok) {
    throw new Error(`Comparison create request failed with status ${response.status}`);
  }
  return (await response.json()) as ComparisonCreateResponse;
}

export async function generateComparisonDraft(
  request: ComparisonCreateRequest
): Promise<ComparisonGenerateCodeResponse> {
  const response = await fetch("/api/v1/comparisons/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
  if (!response.ok) {
    throw new Error(`Comparison generate request failed with status ${response.status}`);
  }
  return (await response.json()) as ComparisonGenerateCodeResponse;
}

export async function generateComparisonAISection(
  draftId: string
): Promise<ComparisonGenerateAIResponse> {
  const response = await fetch(`/api/v1/comparisons/generate/${draftId}/ai`, {
    method: "POST"
  });
  if (!response.ok) {
    throw new Error(`Comparison AI generate request failed with status ${response.status}`);
  }
  return (await response.json()) as ComparisonGenerateAIResponse;
}

export async function deleteComparison(comparisonId: string): Promise<void> {
  const response = await fetch(`/api/v1/comparisons/${comparisonId}`, {
    method: "DELETE"
  });
  if (!response.ok) {
    throw new Error(`Comparison delete request failed with status ${response.status}`);
  }
}
