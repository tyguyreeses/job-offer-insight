import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { createComparison, fetchComparisonById, fetchComparisons } from "../services/comparisonsApi";
import { fetchOffers } from "../services/offersApi";
import { ComparePage } from "./ComparePage";

vi.mock("../services/offersApi", () => ({
  fetchOffers: vi.fn()
}));

vi.mock("../services/comparisonsApi", () => ({
  fetchComparisons: vi.fn(),
  fetchComparisonById: vi.fn(),
  createComparison: vi.fn()
}));

const mockedFetchOffers = vi.mocked(fetchOffers);
const mockedFetchComparisons = vi.mocked(fetchComparisons);
const mockedFetchComparisonById = vi.mocked(fetchComparisonById);
const mockedCreateComparison = vi.mocked(createComparison);

const offers = [
  { id: "offer-1", company_name: "Atlas", role_title: "Engineer" },
  { id: "offer-2", company_name: "Beacon", role_title: "Architect" }
];

describe("ComparePage", () => {
  beforeEach(() => {
    mockedFetchOffers.mockReset();
    mockedFetchComparisons.mockReset();
    mockedFetchComparisonById.mockReset();
    mockedCreateComparison.mockReset();
    mockedFetchOffers.mockResolvedValue({ offers } as never);
    mockedFetchComparisons.mockResolvedValue({ comparisons: [] } as never);
    mockedCreateComparison.mockResolvedValue({
      status: "saved",
      errors: [],
      comparison: null
    } as never);
  });

  it("renders the empty-state canvas message initially", async () => {
    render(<ComparePage />);

    await screen.findByText("Create new comparison or select previously saved comparison");
    expect(screen.getByTestId("compare-canvas")).toBeInTheDocument();
  });

  it("renders one-to-all draft canvas when one offer is selected", async () => {
    render(<ComparePage />);
    await screen.findByText("Atlas");

    fireEvent.click(screen.getByRole("button", { name: "Atlas" }));

    expect(await screen.findByText("All Other Entries")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save Comparison" })).toBeInTheDocument();
  });

  it("loads saved comparison detail, hides builder row, and keeps saved row visible", async () => {
    mockedFetchComparisons.mockResolvedValue({
      comparisons: [
        {
          id: "comparison-1",
          comparison_mode: "one_to_one",
          base_offer_id: "offer-1",
          selected_offer_ids: ["offer-1", "offer-2"],
          summary_text: "Comparison summary placeholder.",
          note: "Saved detail note",
          created_at: "2026-04-11T00:00:00Z",
          updated_at: "2026-04-11T00:00:00Z"
        }
      ]
    } as never);
    mockedFetchComparisonById.mockResolvedValue({
      id: "comparison-1",
      comparison_mode: "one_to_one",
      base_offer_id: "offer-1",
      selected_offer_ids: ["offer-1", "offer-2"],
      summary_text: "Comparison summary placeholder.",
      note: "Saved detail note",
      created_at: "2026-04-11T00:00:00Z",
      updated_at: "2026-04-11T00:00:00Z"
    } as never);

    render(<ComparePage />);
    await screen.findByRole("button", { name: "Atlas • Beacon" });

    fireEvent.click(screen.getByRole("button", { name: "Atlas • Beacon" }));

    await waitFor(() => {
      expect(mockedFetchComparisonById).toHaveBeenCalledWith("comparison-1");
    });

    expect(await screen.findByText("Saved detail note")).toBeInTheDocument();
    expect(screen.queryByLabelText("Available offers")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Saved comparisons")).toBeInTheDocument();
  });
});
