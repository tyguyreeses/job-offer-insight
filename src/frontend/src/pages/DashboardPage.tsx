import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";

import { deleteOffer, fetchOffers } from "../services/offersApi";
import type { OfferSortBy, OfferSummaryPayload, SortDirection } from "../types/offers";

interface SortOption {
  label: string;
  sortBy: OfferSortBy;
  sortDirection: SortDirection;
}

const SORT_OPTIONS: SortOption[] = [
  { label: "Newest", sortBy: "created_at", sortDirection: "desc" },
  { label: "Oldest", sortBy: "created_at", sortDirection: "asc" },
  { label: "Company (A-Z)", sortBy: "company_name", sortDirection: "asc" },
  { label: "Company (Z-A)", sortBy: "company_name", sortDirection: "desc" },
  { label: "Role (A-Z)", sortBy: "role_title", sortDirection: "asc" },
  { label: "Role (Z-A)", sortBy: "role_title", sortDirection: "desc" }
];

function asNumber(value: unknown): number | null {
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

function asText(value: unknown): string | null {
  return typeof value === "string" && value.trim() !== "" ? value.trim() : null;
}

function asTextList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => (typeof item === "string" ? item.trim() : ""))
    .filter((item) => item.length > 0);
}

function formatUsd(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  }).format(amount);
}

function formatDate(createdAt?: string): string | null {
  if (!createdAt) {
    return null;
  }
  const parsed = new Date(createdAt);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return `${String(parsed.getUTCMonth() + 1).padStart(2, "0")}-${String(parsed.getUTCDate()).padStart(2, "0")}-${parsed.getUTCFullYear()}`;
}

function monetaryItems(offer: OfferSummaryPayload): string[] {
  const compensation = offer.compensation ?? {};
  const monetary = offer.monetary_benefits ?? {};
  const items: string[] = [];

  const signing = asNumber(compensation.signing_bonus_usd);
  if (signing !== null) {
    items.push(`Signing bonus: ${formatUsd(signing)}`);
  }
  const bonusPercent = asNumber(compensation.target_bonus_percent);
  if (bonusPercent !== null) {
    items.push(`Target bonus: ${bonusPercent}%`);
  }
  const equityGrant = asNumber(monetary.equity_grant_usd);
  if (equityGrant !== null) {
    items.push(`Equity grant: ${formatUsd(equityGrant)}`);
  }
  const retirementMatch = asNumber(monetary.retirement_match_percent);
  if (retirementMatch !== null) {
    items.push(`Retirement match: ${retirementMatch}%`);
  }
  const healthMonthly = asNumber(monetary.health_insurance_employer_monthly_usd);
  if (healthMonthly !== null) {
    items.push(`Health insurance (monthly): ${formatUsd(healthMonthly)}`);
  }

  const otherMonetary = asTextList(monetary.other_monetary_benefits);
  return items.concat(otherMonetary);
}

function summaryBullets(offer: OfferSummaryPayload): string[] {
  const directSummary = asTextList(offer.non_monetary_summary_bullets);
  if (directSummary.length > 0) {
    return directSummary;
  }

  const nonMonetary = offer.non_monetary_benefits ?? {};
  const derived = [
    asText(nonMonetary.mission_alignment_notes),
    asText(nonMonetary.culture_notes),
    asText(nonMonetary.growth_notes),
    asText(nonMonetary.wellness_notes),
    asText(nonMonetary.remote_flexibility_notes)
  ].filter((item): item is string => item !== null);
  return derived.concat(asTextList(nonMonetary.other_non_monetary_benefits));
}

function salaryText(offer: OfferSummaryPayload): string | null {
  const compensation = offer.compensation ?? {};
  const annualBase = asNumber(compensation.annual_base_salary_usd);
  if (annualBase !== null) {
    return formatUsd(annualBase);
  }
  const hourlyRate = asNumber(compensation.hourly_rate_usd);
  const hours = asNumber(compensation.hours_per_week);
  if (hourlyRate !== null && hours !== null) {
    return `${formatUsd(hourlyRate)}/hr (${hours} hrs/week)`;
  }
  return null;
}

export function DashboardPage(): JSX.Element {
  const DELETE_ANIMATION_DURATION_MS = 700;

  const [offers, setOffers] = useState<OfferSummaryPayload[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [sortSelection, setSortSelection] = useState(SORT_OPTIONS[0].label);
  const [selectedOfferIds, setSelectedOfferIds] = useState<string[]>([]);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [isDeletingId, setIsDeletingId] = useState<string | null>(null);
  const [deletingOfferIds, setDeletingOfferIds] = useState<string[]>([]);
  const [cardAnimationState, setCardAnimationState] = useState<Record<string, "select" | "deselect">>({});
  const animationTimeoutRef = useRef<Record<string, number>>({});
  const deleteTimeoutRef = useRef<Record<string, number>>({});

  const selectedSort = useMemo(() => {
    return SORT_OPTIONS.find((option) => option.label === sortSelection) ?? SORT_OPTIONS[0];
  }, [sortSelection]);

  const scheduleCardAnimation = (offerId: string, mode: "select" | "deselect"): void => {
    setCardAnimationState((existing) => ({ ...existing, [offerId]: mode }));
    if (animationTimeoutRef.current[offerId] !== undefined) {
      window.clearTimeout(animationTimeoutRef.current[offerId]);
    }
    animationTimeoutRef.current[offerId] = window.setTimeout(() => {
      setCardAnimationState((existing) => {
        const next = { ...existing };
        delete next[offerId];
        return next;
      });
      delete animationTimeoutRef.current[offerId];
    }, 500);
  };

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setErrorText(null);

    void fetchOffers({
      sortBy: selectedSort.sortBy,
      sortDirection: selectedSort.sortDirection
    })
      .then((response) => {
        if (cancelled) {
          return;
        }
        setOffers(response.offers);
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        setErrorText(error instanceof Error ? error.message : "Unable to load offers.");
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedSort.sortBy, selectedSort.sortDirection]);

  const handleToggleSelection = (offerId: string): void => {
    if (deletingOfferIds.includes(offerId)) {
      return;
    }
    setSelectedOfferIds((current) => {
      if (current.includes(offerId)) {
        scheduleCardAnimation(offerId, "deselect");
        if (deleteConfirmId === offerId) {
          setDeleteConfirmId(null);
        }
        return current.filter((id) => id !== offerId);
      }
      scheduleCardAnimation(offerId, "select");
      if (current.length < 2) {
        return [...current, offerId];
      }
      scheduleCardAnimation(current[0], "deselect");
      return [current[1], offerId];
    });
  };

  const handleDeleteClick = async (offerId: string): Promise<void> => {
    if (deleteConfirmId !== offerId) {
      setDeleteConfirmId(offerId);
      return;
    }
    setIsDeletingId(offerId);
    setErrorText(null);
    try {
      await deleteOffer(offerId);
      setDeletingOfferIds((current) => (current.includes(offerId) ? current : [...current, offerId]));
      setSelectedOfferIds((current) => current.filter((id) => id !== offerId));
      setDeleteConfirmId(null);
      if (deleteTimeoutRef.current[offerId] !== undefined) {
        window.clearTimeout(deleteTimeoutRef.current[offerId]);
      }
      deleteTimeoutRef.current[offerId] = window.setTimeout(() => {
        setOffers((current) => current.filter((offer) => offer.id !== offerId));
        setDeletingOfferIds((current) => current.filter((id) => id !== offerId));
        setIsDeletingId(null);
        delete deleteTimeoutRef.current[offerId];
      }, DELETE_ANIMATION_DURATION_MS);
    } catch (error: unknown) {
      setErrorText(error instanceof Error ? error.message : "Unable to delete offer.");
      setIsDeletingId(null);
    }
  };

  useEffect(() => {
    return () => {
      const timeoutIds = Object.values(animationTimeoutRef.current);
      for (const timeoutId of timeoutIds) {
        window.clearTimeout(timeoutId);
      }
      const deleteTimeoutIds = Object.values(deleteTimeoutRef.current);
      for (const timeoutId of deleteTimeoutIds) {
        window.clearTimeout(timeoutId);
      }
    };
  }, []);

  const handleCardKeyDown = (
    event: KeyboardEvent<HTMLElement>,
    offerId: string
  ): void => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handleToggleSelection(offerId);
    }
  };

  return (
    <main className="main-panel dashboard-panel">
      <h1 className="main-title dashboard-title">Dashboard</h1>

      <section className="dashboard-toolbar">
        <label className="input-label dashboard-sort-label" htmlFor="sort-by-control">
          Sort by
        </label>
        <select
          id="sort-by-control"
          className="dashboard-sort-control selectable"
          value={sortSelection}
          onChange={(event) => setSortSelection(event.target.value)}
        >
          {SORT_OPTIONS.map((option) => (
            <option key={option.label} value={option.label}>
              {option.label}
            </option>
          ))}
        </select>
      </section>

      {isLoading ? <p className="dashboard-status">Loading offers...</p> : null}
      {errorText ? <p className="error-text dashboard-status">{errorText}</p> : null}

      {!isLoading && !errorText && offers.length === 0 ? (
        <p className="dashboard-status">No offers yet. Add an entry to populate your dashboard.</p>
      ) : null}

      <section className="dashboard-scroll-row" aria-label="Offer cards">
        {offers.map((offer) => {
          const salary = salaryText(offer);
          const monetary = monetaryItems(offer);
          const summary = summaryBullets(offer);
          const createdDate = formatDate(offer.offer_meta?.created_at);
          const isSelected = selectedOfferIds.includes(offer.id);
          const isDeleteConfirm = deleteConfirmId === offer.id;
          const isDeleting = isDeletingId === offer.id;
          const isPendingRemoval = deletingOfferIds.includes(offer.id);

          return (
            <div
              key={offer.id}
              className={`dashboard-card-shell ${isPendingRemoval ? "dashboard-card-shell-collapsing" : ""}`.trim()}
            >
              <article
                className={
                  isSelected
                    ? `dashboard-card dashboard-card-selected selectable ${
                        cardAnimationState[offer.id] === "select" ? "dashboard-card-flip-select" : ""
                      } ${isPendingRemoval ? "dashboard-card-deleting" : ""}`
                    : `dashboard-card selectable ${
                        cardAnimationState[offer.id] === "deselect" ? "dashboard-card-flip-deselect" : ""
                      } ${isPendingRemoval ? "dashboard-card-deleting" : ""}`
                }
                role="button"
                tabIndex={0}
                aria-pressed={isSelected}
                data-testid={`offer-card-${offer.id}`}
                onClick={() => {
                  if (isPendingRemoval) {
                    return;
                  }
                  handleToggleSelection(offer.id);
                }}
                onKeyDown={(event) => {
                  if (isPendingRemoval) {
                    return;
                  }
                  handleCardKeyDown(event, offer.id);
                }}
              >
                <h2 className="dashboard-card-company">{offer.company_name}</h2>
                <p className="dashboard-card-role">{offer.role_title}</p>

                {salary ? (
                  <section className="dashboard-card-section">
                    <h3>Salary</h3>
                    <p>{salary}</p>
                  </section>
                ) : null}

                {monetary.length > 0 ? (
                  <section className="dashboard-card-section">
                    <h3>Monetary benefits</h3>
                    <ul>
                      {monetary.map((item) => (
                        <li key={`${offer.id}-monetary-${item}`}>{item}</li>
                      ))}
                    </ul>
                  </section>
                ) : null}

                {summary.length > 0 ? (
                  <section className="dashboard-card-section">
                    <h3>Non-monetary benefits</h3>
                    <ul>
                      {summary.map((item) => (
                        <li key={`${offer.id}-non-monetary-${item}`}>{item}</li>
                      ))}
                    </ul>
                  </section>
                ) : null}

                {createdDate ? (
                  <section className="dashboard-card-section">
                    <h3>Date created</h3>
                    <p>{createdDate}</p>
                  </section>
                ) : null}

                {isSelected ? (
                  <div className="dashboard-card-actions">
                    <button
                      type="button"
                      className="secondary-button selectable"
                      onClick={(event) => {
                        event.stopPropagation();
                      }}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className={`secondary-button selectable card-delete-button ${
                        isDeleteConfirm ? "card-delete-button-confirm" : ""
                      }`}
                      disabled={isDeleting || isPendingRemoval}
                      onClick={(event) => {
                        event.stopPropagation();
                        void handleDeleteClick(offer.id);
                      }}
                    >
                      <span className="card-delete-button-label">
                        {isDeleting ? "Deleting..." : isDeleteConfirm ? "Confirm" : "Delete"}
                      </span>
                    </button>
                  </div>
                ) : null}
              </article>
            </div>
          );
        })}
      </section>
    </main>
  );
}
