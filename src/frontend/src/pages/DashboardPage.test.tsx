import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { vi } from "vitest";

import {
  createDemoOffers,
  deleteOffer,
  fetchOfferById,
  fetchOfferSchema,
  fetchOffers,
  updateOffer
} from "../services/offersApi";
import { DashboardPage } from "./DashboardPage";

vi.mock("../services/offersApi", () => ({
  fetchOffers: vi.fn(),
  deleteOffer: vi.fn(),
  createDemoOffers: vi.fn(),
  fetchOfferById: vi.fn(),
  fetchOfferSchema: vi.fn(),
  updateOffer: vi.fn()
}));

const mockedFetchOffers = vi.mocked(fetchOffers);
const mockedDeleteOffer = vi.mocked(deleteOffer);
const mockedCreateDemoOffers = vi.mocked(createDemoOffers);
const mockedFetchOfferById = vi.mocked(fetchOfferById);
const mockedFetchOfferSchema = vi.mocked(fetchOfferSchema);
const mockedUpdateOffer = vi.mocked(updateOffer);

const defaultOffers = [
  {
    id: "offer-3",
    company_name: "Zenith Labs",
    role_title: "Engineer III",
    compensation: { annual_base_salary_usd: 175000, signing_bonus_usd: null },
    monetary_benefits: {
      retirement_match_percent: null,
      health_insurance_employer_monthly_usd: null,
      other_monetary_benefits: []
    },
    non_monetary_summary_bullets: ["Strong mentorship", "Remote flexibility"],
    offer_meta: { created_at: "2026-04-10T12:00:00Z" }
  },
  {
    id: "offer-2",
    company_name: "Beacon Cloud",
    role_title: "Platform Engineer",
    compensation: { annual_base_salary_usd: 160000 },
    monetary_benefits: {
      retirement_match_percent: 4,
      other_monetary_benefits: ["Wellness stipend"]
    },
    non_monetary_summary_bullets: ["Mission-driven work"],
    offer_meta: { created_at: "2026-04-09T12:00:00Z" }
  },
  {
    id: "offer-1",
    company_name: "Atlas Systems",
    role_title: "Developer",
    compensation: { annual_base_salary_usd: 140000 },
    monetary_benefits: {},
    non_monetary_benefits: {},
    offer_meta: { created_at: "2026-04-08T12:00:00Z" }
  }
];

const defaultSchema = {
  version: 1,
  identity: { company_name_path: "company_name", role_title_path: "role_title" },
  required: {
    all_of: ["company-name", "role-title", "location"],
    one_of: [["annual-base-salary-usd"], ["hourly-rate-usd", "hours-per-week"]]
  },
  card_sections: [
    { section_id: "salary", title: "Salary" },
    { section_id: "monetary", title: "Monetary benefits" },
    { section_id: "non_monetary", title: "Non-monetary benefits" },
    { section_id: "meta", title: "Date created" }
  ],
  edit_sections: [
    { section_id: "core", title: "Core details" },
    { section_id: "compensation", title: "Compensation" },
    { section_id: "monetary", title: "Monetary benefits" },
    { section_id: "non_monetary", title: "Non-monetary benefits" }
  ],
  fields: [
    {
      id: "company-name",
      label: "Company name",
      storage_path: "company_name",
      data_type: "string",
      group: "core",
      card: { visible: false, section_id: "salary", order: 0, style: "labeled_value" },
      edit: { visible: true, section_id: "core", order: 1, widget: "text" }
    },
    {
      id: "role-title",
      label: "Role title",
      storage_path: "role_title",
      data_type: "string",
      group: "core",
      card: { visible: false, section_id: "salary", order: 0, style: "labeled_value" },
      edit: { visible: true, section_id: "core", order: 2, widget: "text" }
    },
    {
      id: "location",
      label: "Location",
      storage_path: "location",
      data_type: "string",
      group: "core",
      card: { visible: false, section_id: "salary", order: 0, style: "labeled_value" },
      edit: { visible: true, section_id: "core", order: 3, widget: "text" }
    },
    {
      id: "annual-base-salary-usd",
      label: "Annual base salary (USD)",
      storage_path: "compensation.annual_base_salary_usd",
      data_type: "number",
      group: "compensation",
      card: { visible: true, section_id: "salary", order: 1, style: "value" },
      edit: { visible: true, section_id: "compensation", order: 1, widget: "number" }
    },
    {
      id: "signing-bonus-usd",
      label: "Signing bonus (USD)",
      storage_path: "compensation.signing_bonus_usd",
      data_type: "number",
      group: "compensation",
      card: { visible: true, section_id: "monetary", order: 2, style: "labeled_value" },
      edit: { visible: true, section_id: "compensation", order: 2, widget: "number" }
    }
  ]
};

describe("DashboardPage", () => {
  beforeEach(() => {
    mockedFetchOffers.mockReset();
    mockedDeleteOffer.mockReset();
    mockedCreateDemoOffers.mockReset();
    mockedFetchOfferById.mockReset();
    mockedFetchOfferSchema.mockReset();
    mockedUpdateOffer.mockReset();
    mockedFetchOfferSchema.mockResolvedValue(defaultSchema as never);
    vi.restoreAllMocks();
  });

  it("loads with default newest-first sort and renders cards left-to-right", async () => {
    mockedFetchOffers.mockResolvedValueOnce({ offers: defaultOffers });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(mockedFetchOffers).toHaveBeenCalledWith({
        sortBy: "created_at",
        sortDirection: "desc"
      });
    });

    const headings = await screen.findAllByRole("heading", { level: 2 });
    expect(headings.map((heading) => heading.textContent)).toEqual([
      "Zenith Labs",
      "Beacon Cloud",
      "Atlas Systems"
    ]);
  });

  it("requests backend re-sort when Sort by changes", async () => {
    mockedFetchOffers.mockResolvedValue({ offers: defaultOffers });

    render(<DashboardPage />);
    await screen.findByText("Zenith Labs");

    fireEvent.change(screen.getByLabelText("Sort by"), {
      target: { value: "Company (A-Z)" }
    });

    await waitFor(() => {
      expect(mockedFetchOffers).toHaveBeenLastCalledWith({
        sortBy: "company_name",
        sortDirection: "asc"
      });
    });
  });

  it("hides blank optional values instead of rendering placeholders", async () => {
    mockedFetchOffers.mockResolvedValueOnce({ offers: defaultOffers });

    render(<DashboardPage />);
    await screen.findByText("Zenith Labs");

    const zenithCard = screen.getByRole("heading", { name: "Zenith Labs" }).closest("article");
    expect(zenithCard).not.toBeNull();
    const card = within(zenithCard!);
    expect(card.queryByText(/Signing bonus/i)).not.toBeInTheDocument();
    expect(card.queryByText("N/A")).not.toBeInTheDocument();
    expect(card.queryByText("null")).not.toBeInTheDocument();
    expect(card.queryByText("None")).not.toBeInTheDocument();
  });

  it("enforces max-two selected offers and deselects oldest when selecting a third", async () => {
    mockedFetchOffers.mockResolvedValueOnce({ offers: defaultOffers });
    render(<DashboardPage />);
    await screen.findByText("Zenith Labs");

    const first = screen.getByTestId("offer-card-offer-3");
    const second = screen.getByTestId("offer-card-offer-2");
    const third = screen.getByTestId("offer-card-offer-1");

    fireEvent.click(first);
    fireEvent.click(second);
    fireEvent.click(third);

    expect(first).toHaveAttribute("aria-pressed", "false");
    expect(second).toHaveAttribute("aria-pressed", "true");
    expect(third).toHaveAttribute("aria-pressed", "true");
  });

  it("shows compare button for one-or-more selected cards and forwards selected ids", async () => {
    mockedFetchOffers.mockResolvedValueOnce({ offers: defaultOffers });
    const onCompareSelected = vi.fn();

    render(<DashboardPage onCompareSelected={onCompareSelected} />);
    await screen.findByText("Zenith Labs");

    expect(screen.queryByRole("button", { name: "Compare" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("offer-card-offer-3"));
    fireEvent.click(screen.getByRole("button", { name: "Compare" }));
    expect(onCompareSelected).toHaveBeenCalledWith(["offer-3"]);

    fireEvent.click(screen.getByTestId("offer-card-offer-2"));
    fireEvent.click(screen.getByRole("button", { name: "Compare" }));
    expect(onCompareSelected).toHaveBeenLastCalledWith(["offer-3", "offer-2"]);
  });

  it("shows edit/delete buttons only for selected cards", async () => {
    mockedFetchOffers.mockResolvedValueOnce({ offers: defaultOffers });
    render(<DashboardPage />);
    await screen.findByText("Zenith Labs");

    expect(screen.queryByRole("button", { name: "Edit" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("offer-card-offer-3"));

    expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
  });

  it("requires delete confirm click and removes card after confirm", async () => {
    mockedFetchOffers.mockResolvedValueOnce({ offers: defaultOffers });
    mockedDeleteOffer.mockResolvedValueOnce();

    render(<DashboardPage />);
    await screen.findByText("Zenith Labs");

    fireEvent.click(screen.getByTestId("offer-card-offer-3"));
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    expect(mockedDeleteOffer).not.toHaveBeenCalled();
    const confirmButton = screen.getByRole("button", { name: "Confirm" });
    expect(confirmButton).toHaveClass("card-delete-button-confirm");

    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockedDeleteOffer).toHaveBeenCalledWith("offer-3");
      expect(screen.getByTestId("offer-card-offer-3")).toHaveClass("dashboard-card-deleting");
      expect(screen.getByTestId("offer-card-offer-3").parentElement).not.toHaveClass(
        "dashboard-card-shell-collapsing"
      );
    });

    await waitFor(() => {
      expect(screen.getByTestId("offer-card-offer-3").parentElement).toHaveClass(
        "dashboard-card-shell-collapsing"
      );
    });

    await waitFor(() => {
      expect(screen.queryByText("Zenith Labs")).not.toBeInTheDocument();
    });
  });

  it("creates demo offers from debug button and refreshes the dashboard list", async () => {
    mockedFetchOffers.mockResolvedValueOnce({ offers: defaultOffers });
    mockedCreateDemoOffers.mockResolvedValueOnce();
    mockedFetchOffers.mockResolvedValueOnce({ offers: [...defaultOffers, defaultOffers[0]] });

    render(<DashboardPage />);
    await screen.findByText("Zenith Labs");

    fireEvent.click(screen.getByRole("button", { name: "Create Demo Offers" }));

    await waitFor(() => {
      expect(mockedCreateDemoOffers).toHaveBeenCalledTimes(1);
      expect(mockedFetchOffers).toHaveBeenCalledTimes(2);
      expect(mockedFetchOffers).toHaveBeenLastCalledWith({
        sortBy: "created_at",
        sortDirection: "desc"
      });
    });
  });

  it("opens edit panel and pre-fills offer fields", async () => {
    mockedFetchOffers.mockResolvedValueOnce({ offers: defaultOffers });
    mockedFetchOfferById.mockResolvedValueOnce({
      ...defaultOffers[0],
      location: "Denver, CO",
      employment_type: "full_time",
      work_model: "hybrid"
    });

    render(<DashboardPage />);
    await screen.findByText("Zenith Labs");

    fireEvent.click(screen.getByTestId("offer-card-offer-3"));
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));

    await waitFor(() => {
      expect(mockedFetchOfferById).toHaveBeenCalledWith("offer-3");
      expect(screen.getByRole("dialog", { name: "Edit offer" })).toBeInTheDocument();
      expect(screen.getByDisplayValue("Zenith Labs")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Denver, CO")).toBeInTheDocument();
    });
  });

  it("saves edits, closes panel, and updates card content", async () => {
    mockedFetchOffers.mockResolvedValueOnce({ offers: defaultOffers });
    mockedFetchOfferById.mockResolvedValueOnce({
      ...defaultOffers[0],
      location: "Denver, CO"
    });
    mockedUpdateOffer.mockResolvedValueOnce({
      status: "saved",
      errors: [],
      warnings: [],
      missing_field_prompts: [],
      offer: {
        ...defaultOffers[0],
        company_name: "Zenith Labs Updated",
        location: "Boulder, CO"
      }
    });

    render(<DashboardPage />);
    await screen.findByText("Zenith Labs");

    fireEvent.click(screen.getByTestId("offer-card-offer-3"));
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    await screen.findByRole("dialog", { name: "Edit offer" });

    fireEvent.change(screen.getByLabelText("Company name*"), {
      target: { value: "Zenith Labs Updated" }
    });
    fireEvent.change(screen.getByLabelText("Location*"), {
      target: { value: "Boulder, CO" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Save Changes" }));

    await waitFor(() => {
      expect(mockedUpdateOffer).toHaveBeenCalledWith(
        "offer-3",
        expect.objectContaining({
          company_name: "Zenith Labs Updated",
          location: "Boulder, CO"
        })
      );
      expect(screen.queryByRole("dialog", { name: "Edit offer" })).not.toBeInTheDocument();
      expect(screen.getByText("Zenith Labs Updated")).toBeInTheDocument();
    });
  });

  it("prompts before closing dirty edit panel and keeps open if discard is canceled", async () => {
    mockedFetchOffers.mockResolvedValueOnce({ offers: defaultOffers });
    mockedFetchOfferById.mockResolvedValueOnce({
      ...defaultOffers[0],
      location: "Denver, CO"
    });
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValueOnce(false);

    render(<DashboardPage />);
    await screen.findByText("Zenith Labs");

    fireEvent.click(screen.getByTestId("offer-card-offer-3"));
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    await screen.findByRole("dialog", { name: "Edit offer" });

    fireEvent.change(screen.getByLabelText("Location*"), {
      target: { value: "Austin, TX" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(confirmSpy).toHaveBeenCalledWith("Discard unsaved edits?");
    expect(screen.getByRole("dialog", { name: "Edit offer" })).toBeInTheDocument();
  });

  it("shows update errors inline and keeps edit panel open", async () => {
    mockedFetchOffers.mockResolvedValueOnce({ offers: defaultOffers });
    mockedFetchOfferById.mockResolvedValueOnce({
      ...defaultOffers[0],
      location: "Denver, CO"
    });
    mockedUpdateOffer.mockResolvedValueOnce({
      status: "blocked_required_fields",
      errors: ["Provide company_name to save this offer."],
      warnings: [],
      missing_field_prompts: [],
      offer: null
    });

    render(<DashboardPage />);
    await screen.findByText("Zenith Labs");

    fireEvent.click(screen.getByTestId("offer-card-offer-3"));
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    await screen.findByRole("dialog", { name: "Edit offer" });

    fireEvent.change(screen.getByLabelText("Company name*"), {
      target: { value: "" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Save Changes" }));

    await waitFor(() => {
      expect(screen.getAllByText("Provide company_name to save this offer.").length).toBeGreaterThan(0);
      expect(screen.getByRole("dialog", { name: "Edit offer" })).toBeInTheDocument();
    });
  });
});
