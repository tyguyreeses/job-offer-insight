import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import {
  createComparison,
  fetchComparisonById,
  fetchComparisons,
  generateComparisonAISection,
  generateComparisonDraft
} from "../services/comparisonsApi";
import { fetchOfferSchema, fetchOffers } from "../services/offersApi";
import { ComparePage } from "./ComparePage";

vi.mock("../services/offersApi", () => ({
  fetchOffers: vi.fn(),
  fetchOfferSchema: vi.fn()
}));

vi.mock("../services/comparisonsApi", () => ({
  fetchComparisons: vi.fn(),
  fetchComparisonById: vi.fn(),
  createComparison: vi.fn(),
  generateComparisonDraft: vi.fn(),
  generateComparisonAISection: vi.fn(),
  deleteComparison: vi.fn()
}));

const mockedFetchOffers = vi.mocked(fetchOffers);
const mockedFetchOfferSchema = vi.mocked(fetchOfferSchema);
const mockedFetchComparisons = vi.mocked(fetchComparisons);
const mockedFetchComparisonById = vi.mocked(fetchComparisonById);
const mockedCreateComparison = vi.mocked(createComparison);
const mockedGenerateComparisonDraft = vi.mocked(generateComparisonDraft);
const mockedGenerateComparisonAISection = vi.mocked(generateComparisonAISection);

const offers = [
  { id: "offer-1", company_name: "Atlas", role_title: "Engineer" },
  { id: "offer-2", company_name: "Beacon", role_title: "Architect" }
];

const defaultSchema = {
  version: 1,
  identity: { company_name_path: "company_name", role_title_path: "role_title" },
  required: { all_of: [], one_of: [] },
  card_sections: [
    { section_id: "salary", title: "Salary" },
    { section_id: "monetary", title: "Monetary benefits" }
  ],
  edit_sections: [],
  fields: [
    {
      id: "annual-base-salary-usd",
      label: "Annual base salary (USD)",
      storage_path: "compensation.annual_base_salary_usd",
      data_type: "number",
      group: "compensation",
      card: { visible: true, section_id: "salary", order: 1, style: "value" },
      edit: { visible: false, section_id: "core", order: 1, widget: "text" }
    },
    {
      id: "signing-bonus-usd",
      label: "Signing bonus (USD)",
      storage_path: "compensation.signing_bonus_usd",
      data_type: "number",
      group: "compensation",
      card: { visible: true, section_id: "monetary", order: 2, style: "labeled_value" },
      edit: { visible: false, section_id: "core", order: 2, widget: "text" }
    }
  ]
};

describe("ComparePage", () => {
  beforeEach(() => {
    mockedFetchOffers.mockReset();
    mockedFetchOfferSchema.mockReset();
    mockedFetchComparisons.mockReset();
    mockedFetchComparisonById.mockReset();
    mockedCreateComparison.mockReset();
    mockedGenerateComparisonDraft.mockReset();
    mockedGenerateComparisonAISection.mockReset();
    mockedFetchOffers.mockResolvedValue({ offers } as never);
    mockedFetchOfferSchema.mockResolvedValue(defaultSchema as never);
    mockedFetchComparisons.mockResolvedValue({ comparisons: [] } as never);
    mockedCreateComparison.mockResolvedValue({
      status: "saved",
      errors: [],
      comparison: null
    } as never);
    mockedGenerateComparisonDraft.mockResolvedValue({
      status: "draft_ready",
      errors: [],
      draft_id: "draft-1",
      mode: "one_to_one",
      base_offer_id: "offer-1",
      selected_offer_ids: ["offer-1", "offer-2"],
      code_section: { metrics: [] },
      ai_section_pending: true
    } as never);
    mockedGenerateComparisonAISection.mockResolvedValue({
      status: "completed",
      errors: [],
      draft_id: "draft-1",
      ai_section: "### AI Summary\n- Tradeoff one\n- Tradeoff two"
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
    expect(screen.getByRole("button", { name: "Generate Comparison" })).toBeInTheDocument();
    expect(screen.queryByLabelText("Notes")).not.toBeInTheDocument();
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
          code_section: {
            mode: "one_to_one",
            base_offer_id: "offer-1",
            other_offer_id: "offer-2",
            metrics: [{ metric_label: "Annual base salary", percentage_difference: 10.5 }],
            notes: "Saved deterministic notes"
          },
          ai_section: "### Saved AI\n- Atlas wins on total cash",
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
      code_section: {
        mode: "one_to_one",
        base_offer_id: "offer-1",
        other_offer_id: "offer-2",
        metrics: [{ metric_label: "Annual base salary", percentage_difference: 10.5 }],
        notes: "Saved deterministic notes"
      },
      ai_section: "### Saved AI\n- Atlas wins on total cash",
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

    expect(screen.getByText("Saved detail note")).toBeInTheDocument();
    expect(screen.getByText("Saved AI")).toBeInTheDocument();
    expect(screen.getByText("Atlas wins on total cash")).toBeInTheDocument();
    expect(
      screen.getByText(
        (_, element) => element?.tagName === "LI" && element.textContent === "← Annual base salary: 10.50% lower"
      )
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Available offers")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Saved comparisons")).toBeInTheDocument();
  });

  it("allows deselecting an active saved comparison to return to builder view", async () => {
    mockedFetchComparisons.mockResolvedValue({
      comparisons: [
        {
          id: "comparison-1",
          comparison_mode: "one_to_one",
          base_offer_id: "offer-1",
          selected_offer_ids: ["offer-1", "offer-2"],
          summary_text: "Comparison summary placeholder.",
          code_section: null,
          ai_section: null,
          note: null,
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
      code_section: null,
      ai_section: null,
      note: null,
      created_at: "2026-04-11T00:00:00Z",
      updated_at: "2026-04-11T00:00:00Z"
    } as never);

    render(<ComparePage />);
    const savedButton = await screen.findByRole("button", { name: "Atlas • Beacon" });

    fireEvent.click(savedButton);
    await waitFor(() => {
      expect(mockedFetchComparisonById).toHaveBeenCalledWith("comparison-1");
    });
    expect(screen.queryByLabelText("Available offers")).not.toBeInTheDocument();

    fireEvent.click(savedButton);
    expect(await screen.findByLabelText("Available offers")).toBeInTheDocument();
  });

  it("renders generated AI section as markdown", async () => {
    render(<ComparePage />);
    await screen.findByText("Atlas");

    fireEvent.click(screen.getByRole("button", { name: "Atlas" }));
    fireEvent.click(screen.getByRole("button", { name: "Beacon" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate Comparison" }));

    await waitFor(() => {
      expect(mockedGenerateComparisonDraft).toHaveBeenCalled();
      expect(mockedGenerateComparisonAISection).toHaveBeenCalledWith("draft-1");
    });

    expect(await screen.findByText("AI Summary")).toBeInTheDocument();
    expect(screen.getByText("Tradeoff one")).toBeInTheDocument();
    expect(screen.getByText("Tradeoff two")).toBeInTheDocument();
    expect(screen.getByLabelText("Notes")).toBeInTheDocument();
  });

  it("saves generated code, ai summary, and note together then opens saved view", async () => {
    mockedCreateComparison.mockResolvedValue({
      status: "saved",
      errors: [],
      comparison: {
        id: "comparison-2",
        comparison_mode: "one_to_one",
        base_offer_id: "offer-1",
        selected_offer_ids: ["offer-1", "offer-2"],
        summary_text: "### AI Summary\n- Tradeoff one\n- Tradeoff two",
        code_section: {
          mode: "one_to_one",
          base_offer_id: "offer-1",
          other_offer_id: "offer-2",
          metrics: [{ metric_label: "Annual base salary", percentage_difference: 10.5 }],
          notes: "Saved deterministic notes"
        },
        ai_section: "### AI Summary\n- Tradeoff one\n- Tradeoff two",
        note: "Keep this in final save.",
        created_at: "2026-04-12T00:00:00Z",
        updated_at: "2026-04-12T00:00:00Z"
      }
    } as never);

    render(<ComparePage />);
    await screen.findByText("Atlas");

    fireEvent.click(screen.getByRole("button", { name: "Atlas" }));
    fireEvent.click(screen.getByRole("button", { name: "Beacon" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate Comparison" }));
    await screen.findByText("AI Summary");

    fireEvent.change(screen.getByLabelText("Notes"), {
      target: { value: "Keep this in final save." }
    });
    expect(await screen.findByRole("button", { name: "Save Comparison" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Save Comparison" }));

    await waitFor(() => {
      expect(mockedCreateComparison).toHaveBeenCalledWith(
        expect.objectContaining({
          note: "Keep this in final save.",
          code_section: expect.any(Object),
          ai_section: expect.any(String),
          summary_text: expect.stringContaining("AI Summary")
        })
      );
    });

    expect(await screen.findByText("Saved Comparison")).toBeInTheDocument();
    expect(screen.getByText("Saved Notes")).toBeInTheDocument();
    expect(screen.getByText("Keep this in final save.")).toBeInTheDocument();
    expect(screen.queryByLabelText("Available offers")).not.toBeInTheDocument();
  });
});
