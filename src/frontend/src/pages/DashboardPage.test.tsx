import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { vi } from "vitest";

import { fetchOffers } from "../services/offersApi";
import { DashboardPage } from "./DashboardPage";

vi.mock("../services/offersApi", () => ({
  fetchOffers: vi.fn()
}));

const mockedFetchOffers = vi.mocked(fetchOffers);

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

describe("DashboardPage", () => {
  beforeEach(() => {
    mockedFetchOffers.mockReset();
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
    expect(card.queryByText(/Signing bonus:/i)).not.toBeInTheDocument();
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
});
