import { useEffect, useMemo, useRef, useState, type ChangeEvent, type KeyboardEvent } from "react";

import { createDemoOffers, deleteOffer, fetchOfferById, fetchOffers, updateOffer } from "../services/offersApi";
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

interface EditOfferFormState {
  company_name: string;
  role_title: string;
  location: string;
  employment_type: string;
  work_model: string;
  annual_base_salary_usd: string;
  hourly_rate_usd: string;
  hours_per_week: string;
  annualized_total_cash_usd: string;
  signing_bonus_usd: string;
  target_bonus_percent: string;
  retirement_match_percent: string;
  retirement_match_cap_usd: string;
  health_insurance_employer_monthly_usd: string;
  hsa_employer_annual_usd: string;
  equity_grant_usd: string;
  equity_vesting_schedule: string;
  other_monetary_benefits_text: string;
  mission_alignment_notes: string;
  culture_notes: string;
  growth_notes: string;
  wellness_notes: string;
  pto_days: string;
  remote_flexibility_notes: string;
  other_non_monetary_benefits_text: string;
  non_monetary_summary_bullets_text: string;
}

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

const EMPTY_EDIT_FORM: EditOfferFormState = {
  company_name: "",
  role_title: "",
  location: "",
  employment_type: "",
  work_model: "",
  annual_base_salary_usd: "",
  hourly_rate_usd: "",
  hours_per_week: "",
  annualized_total_cash_usd: "",
  signing_bonus_usd: "",
  target_bonus_percent: "",
  retirement_match_percent: "",
  retirement_match_cap_usd: "",
  health_insurance_employer_monthly_usd: "",
  hsa_employer_annual_usd: "",
  equity_grant_usd: "",
  equity_vesting_schedule: "",
  other_monetary_benefits_text: "",
  mission_alignment_notes: "",
  culture_notes: "",
  growth_notes: "",
  wellness_notes: "",
  pto_days: "",
  remote_flexibility_notes: "",
  other_non_monetary_benefits_text: "",
  non_monetary_summary_bullets_text: ""
};

function asNumericInputText(value: unknown): string {
  const parsed = asNumber(value);
  return parsed === null ? "" : `${parsed}`;
}

function listTextForTextarea(value: unknown): string {
  return asTextList(value).join("\n");
}

function toOptionalNumber(value: string): number | null {
  const trimmed = value.trim();
  if (trimmed === "") {
    return null;
  }
  const parsed = Number(trimmed.replace(/,/g, ""));
  return Number.isFinite(parsed) ? parsed : null;
}

function parseTextareaList(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function editFormFromOffer(offer: OfferSummaryPayload): EditOfferFormState {
  const compensation = (offer.compensation ?? {}) as Record<string, unknown>;
  const monetary = (offer.monetary_benefits ?? {}) as Record<string, unknown>;
  const nonMonetary = (offer.non_monetary_benefits ?? {}) as Record<string, unknown>;

  return {
    company_name: asText(offer.company_name) ?? "",
    role_title: asText(offer.role_title) ?? "",
    location: asText(offer.location) ?? "",
    employment_type: asText(offer.employment_type) ?? "",
    work_model: asText(offer.work_model) ?? "",
    annual_base_salary_usd: asNumericInputText(compensation.annual_base_salary_usd),
    hourly_rate_usd: asNumericInputText(compensation.hourly_rate_usd),
    hours_per_week: asNumericInputText(compensation.hours_per_week),
    annualized_total_cash_usd: asNumericInputText(compensation.annualized_total_cash_usd),
    signing_bonus_usd: asNumericInputText(compensation.signing_bonus_usd),
    target_bonus_percent: asNumericInputText(compensation.target_bonus_percent),
    retirement_match_percent: asNumericInputText(monetary.retirement_match_percent),
    retirement_match_cap_usd: asNumericInputText(monetary.retirement_match_cap_usd),
    health_insurance_employer_monthly_usd: asNumericInputText(
      monetary.health_insurance_employer_monthly_usd
    ),
    hsa_employer_annual_usd: asNumericInputText(monetary.hsa_employer_annual_usd),
    equity_grant_usd: asNumericInputText(monetary.equity_grant_usd),
    equity_vesting_schedule: asText(monetary.equity_vesting_schedule) ?? "",
    other_monetary_benefits_text: listTextForTextarea(monetary.other_monetary_benefits),
    mission_alignment_notes: asText(nonMonetary.mission_alignment_notes) ?? "",
    culture_notes: asText(nonMonetary.culture_notes) ?? "",
    growth_notes: asText(nonMonetary.growth_notes) ?? "",
    wellness_notes: asText(nonMonetary.wellness_notes) ?? "",
    pto_days: asNumericInputText(nonMonetary.pto_days),
    remote_flexibility_notes: asText(nonMonetary.remote_flexibility_notes) ?? "",
    other_non_monetary_benefits_text: listTextForTextarea(nonMonetary.other_non_monetary_benefits),
    non_monetary_summary_bullets_text: listTextForTextarea(offer.non_monetary_summary_bullets)
  };
}

function offerPayloadFromEditForm(
  form: EditOfferFormState,
  existing: OfferSummaryPayload
): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    ...existing,
    company_name: form.company_name.trim(),
    role_title: form.role_title.trim(),
    location: form.location.trim(),
    employment_type: form.employment_type.trim(),
    work_model: form.work_model.trim(),
    compensation: {
      annual_base_salary_usd: toOptionalNumber(form.annual_base_salary_usd),
      hourly_rate_usd: toOptionalNumber(form.hourly_rate_usd),
      hours_per_week: toOptionalNumber(form.hours_per_week),
      annualized_total_cash_usd: toOptionalNumber(form.annualized_total_cash_usd),
      signing_bonus_usd: toOptionalNumber(form.signing_bonus_usd),
      target_bonus_percent: toOptionalNumber(form.target_bonus_percent)
    },
    monetary_benefits: {
      retirement_match_percent: toOptionalNumber(form.retirement_match_percent),
      retirement_match_cap_usd: toOptionalNumber(form.retirement_match_cap_usd),
      health_insurance_employer_monthly_usd: toOptionalNumber(
        form.health_insurance_employer_monthly_usd
      ),
      hsa_employer_annual_usd: toOptionalNumber(form.hsa_employer_annual_usd),
      equity_grant_usd: toOptionalNumber(form.equity_grant_usd),
      equity_vesting_schedule: form.equity_vesting_schedule.trim(),
      other_monetary_benefits: parseTextareaList(form.other_monetary_benefits_text)
    },
    non_monetary_benefits: {
      mission_alignment_notes: form.mission_alignment_notes.trim(),
      culture_notes: form.culture_notes.trim(),
      growth_notes: form.growth_notes.trim(),
      wellness_notes: form.wellness_notes.trim(),
      pto_days: toOptionalNumber(form.pto_days),
      remote_flexibility_notes: form.remote_flexibility_notes.trim(),
      other_non_monetary_benefits: parseTextareaList(form.other_non_monetary_benefits_text)
    },
    non_monetary_summary_bullets: parseTextareaList(form.non_monetary_summary_bullets_text)
  };
  delete payload.id;
  return payload;
}

export function DashboardPage(): JSX.Element {
  const DELETE_FADE_DURATION_MS = 280;
  const DELETE_COLLAPSE_DURATION_MS = 460;
  const EDIT_PANEL_TRANSITION_MS = 240;

  const [offers, setOffers] = useState<OfferSummaryPayload[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSeedingDemo, setIsSeedingDemo] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [sortSelection, setSortSelection] = useState(SORT_OPTIONS[0].label);
  const [selectedOfferIds, setSelectedOfferIds] = useState<string[]>([]);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [isDeletingId, setIsDeletingId] = useState<string | null>(null);
  const [fadingOfferIds, setFadingOfferIds] = useState<string[]>([]);
  const [collapsingOfferIds, setCollapsingOfferIds] = useState<string[]>([]);
  const [cardAnimationState, setCardAnimationState] = useState<Record<string, "select" | "deselect">>({});
  const animationTimeoutRef = useRef<Record<string, number>>({});
  const deleteFadeTimeoutRef = useRef<Record<string, number>>({});
  const deleteCollapseTimeoutRef = useRef<Record<string, number>>({});
  const editCloseTimeoutRef = useRef<number | null>(null);

  const [editOfferId, setEditOfferId] = useState<string | null>(null);
  const [isEditPanelMounted, setIsEditPanelMounted] = useState(false);
  const [isEditPanelOpen, setIsEditPanelOpen] = useState(false);
  const [isEditLoading, setIsEditLoading] = useState(false);
  const [isEditSaving, setIsEditSaving] = useState(false);
  const [editErrorText, setEditErrorText] = useState<string | null>(null);
  const [editValidationErrors, setEditValidationErrors] = useState<string[]>([]);
  const [editForm, setEditForm] = useState<EditOfferFormState>(EMPTY_EDIT_FORM);
  const [initialEditForm, setInitialEditForm] = useState<EditOfferFormState>(EMPTY_EDIT_FORM);
  const [editOfferBasePayload, setEditOfferBasePayload] = useState<OfferSummaryPayload | null>(null);

  const selectedSort = useMemo(() => {
    return SORT_OPTIONS.find((option) => option.label === sortSelection) ?? SORT_OPTIONS[0];
  }, [sortSelection]);

  const isEditDirty = useMemo(() => {
    return JSON.stringify(editForm) !== JSON.stringify(initialEditForm);
  }, [editForm, initialEditForm]);

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
    if (fadingOfferIds.includes(offerId) || collapsingOfferIds.includes(offerId)) {
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
      setFadingOfferIds((current) => (current.includes(offerId) ? current : [...current, offerId]));
      setSelectedOfferIds((current) => current.filter((id) => id !== offerId));
      setDeleteConfirmId(null);
      if (deleteFadeTimeoutRef.current[offerId] !== undefined) {
        window.clearTimeout(deleteFadeTimeoutRef.current[offerId]);
      }
      if (deleteCollapseTimeoutRef.current[offerId] !== undefined) {
        window.clearTimeout(deleteCollapseTimeoutRef.current[offerId]);
      }
      deleteFadeTimeoutRef.current[offerId] = window.setTimeout(() => {
        setFadingOfferIds((current) => current.filter((id) => id !== offerId));
        setCollapsingOfferIds((current) => (current.includes(offerId) ? current : [...current, offerId]));
        delete deleteFadeTimeoutRef.current[offerId];
      }, DELETE_FADE_DURATION_MS);
      deleteCollapseTimeoutRef.current[offerId] = window.setTimeout(() => {
        setOffers((current) => current.filter((offer) => offer.id !== offerId));
        setCollapsingOfferIds((current) => current.filter((id) => id !== offerId));
        setIsDeletingId(null);
        delete deleteCollapseTimeoutRef.current[offerId];
      }, DELETE_FADE_DURATION_MS + DELETE_COLLAPSE_DURATION_MS);
    } catch (error: unknown) {
      setErrorText(error instanceof Error ? error.message : "Unable to delete offer.");
      setIsDeletingId(null);
    }
  };

  const handleCreateDemoOffers = async (): Promise<void> => {
    setIsSeedingDemo(true);
    setErrorText(null);
    try {
      await createDemoOffers();
      const refreshed = await fetchOffers({
        sortBy: selectedSort.sortBy,
        sortDirection: selectedSort.sortDirection,
      });
      setOffers(refreshed.offers);
    } catch (error: unknown) {
      setErrorText(error instanceof Error ? error.message : "Unable to create demo offers.");
    } finally {
      setIsSeedingDemo(false);
    }
  };

  const closeEditPanel = (): void => {
    setIsEditPanelOpen(false);
    if (editCloseTimeoutRef.current !== null) {
      window.clearTimeout(editCloseTimeoutRef.current);
    }
    editCloseTimeoutRef.current = window.setTimeout(() => {
      setIsEditPanelMounted(false);
      setEditOfferId(null);
      setEditOfferBasePayload(null);
      setEditForm(EMPTY_EDIT_FORM);
      setInitialEditForm(EMPTY_EDIT_FORM);
      setEditErrorText(null);
      setEditValidationErrors([]);
      editCloseTimeoutRef.current = null;
    }, EDIT_PANEL_TRANSITION_MS);
  };

  const requestCloseEditPanel = (): void => {
    if (isEditSaving) {
      return;
    }
    if (isEditDirty) {
      const shouldDiscard = window.confirm("Discard unsaved edits?");
      if (!shouldDiscard) {
        return;
      }
    }
    closeEditPanel();
  };

  const handleEditClick = (offerId: string): void => {
    setIsEditPanelMounted(true);
    window.requestAnimationFrame(() => {
      setIsEditPanelOpen(true);
    });
    setEditOfferId(offerId);
    setIsEditLoading(true);
    setEditErrorText(null);
    setEditValidationErrors([]);
    void fetchOfferById(offerId)
      .then((offer) => {
        const nextForm = editFormFromOffer(offer);
        setEditOfferBasePayload(offer);
        setEditForm(nextForm);
        setInitialEditForm(nextForm);
      })
      .catch((error: unknown) => {
        setEditErrorText(error instanceof Error ? error.message : "Unable to load offer for editing.");
      })
      .finally(() => {
        setIsEditLoading(false);
      });
  };

  const updateEditField = (field: keyof EditOfferFormState, value: string): void => {
    setEditForm((current) => ({ ...current, [field]: value }));
  };

  const handleEditInputChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void => {
    const field = event.target.name as keyof EditOfferFormState;
    updateEditField(field, event.target.value);
  };

  const hasFieldError = (field: string): boolean => {
    const normalized = field.toLowerCase();
    return editValidationErrors.some((error) => error.toLowerCase().includes(normalized));
  };

  const handleSaveEdits = async (): Promise<void> => {
    if (editOfferId === null || editOfferBasePayload === null) {
      return;
    }
    setIsEditSaving(true);
    setEditErrorText(null);
    setEditValidationErrors([]);
    try {
      const payload = offerPayloadFromEditForm(editForm, editOfferBasePayload);
      const result = await updateOffer(editOfferId, payload);
      if (result.status !== "saved" || result.offer === null) {
        setEditValidationErrors(result.errors);
        setEditErrorText(
          result.errors[0] ?? "Unable to save changes. Check required fields and try again."
        );
        return;
      }
      setOffers((current) =>
        current.map((offer) => (offer.id === editOfferId ? result.offer ?? offer : offer))
      );
      closeEditPanel();
    } catch (error: unknown) {
      setEditErrorText(error instanceof Error ? error.message : "Unable to save edits.");
    } finally {
      setIsEditSaving(false);
    }
  };

  useEffect(() => {
    if (!isEditPanelMounted) {
      return;
    }
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isEditPanelMounted]);

  useEffect(() => {
    if (!isEditPanelMounted) {
      return;
    }
    const onEscape = (event: globalThis.KeyboardEvent): void => {
      if (event.key === "Escape") {
        event.preventDefault();
        requestCloseEditPanel();
      }
    };
    window.addEventListener("keydown", onEscape);
    return () => {
      window.removeEventListener("keydown", onEscape);
    };
  }, [isEditPanelMounted, isEditSaving, isEditDirty]);

  useEffect(() => {
    return () => {
      const timeoutIds = Object.values(animationTimeoutRef.current);
      for (const timeoutId of timeoutIds) {
        window.clearTimeout(timeoutId);
      }
      const deleteFadeTimeoutIds = Object.values(deleteFadeTimeoutRef.current);
      for (const timeoutId of deleteFadeTimeoutIds) {
        window.clearTimeout(timeoutId);
      }
      const deleteCollapseTimeoutIds = Object.values(deleteCollapseTimeoutRef.current);
      for (const timeoutId of deleteCollapseTimeoutIds) {
        window.clearTimeout(timeoutId);
      }
      if (editCloseTimeoutRef.current !== null) {
        window.clearTimeout(editCloseTimeoutRef.current);
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
        <button
          type="button"
          className="secondary-button selectable dashboard-debug-button"
          onClick={() => {
            void handleCreateDemoOffers();
          }}
          disabled={isLoading || isSeedingDemo}
        >
          {isSeedingDemo ? "Creating..." : "Create Demo Offers"}
        </button>
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
          const isFading = fadingOfferIds.includes(offer.id);
          const isCollapsing = collapsingOfferIds.includes(offer.id);
          const isPendingRemoval = isFading || isCollapsing;

          return (
            <div
              key={offer.id}
              className={`dashboard-card-shell ${isCollapsing ? "dashboard-card-shell-collapsing" : ""}`.trim()}
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
                        handleEditClick(offer.id);
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

      {isEditPanelMounted ? (
        <div
          className={`edit-offer-overlay ${isEditPanelOpen ? "edit-offer-overlay-open" : ""}`.trim()}
          data-testid="edit-offer-overlay"
          onClick={() => {
            requestCloseEditPanel();
          }}
        >
          <section
            className={`edit-offer-panel ${isEditPanelOpen ? "edit-offer-panel-open" : ""}`.trim()}
            role="dialog"
            aria-modal="true"
            aria-label="Edit offer"
            onClick={(event) => {
              event.stopPropagation();
            }}
          >
            <header className="edit-offer-header">
              <h2>Edit Offer</h2>
              <button
                type="button"
                className="secondary-button selectable"
                onClick={() => {
                  requestCloseEditPanel();
                }}
                disabled={isEditSaving}
              >
                Close
              </button>
            </header>

            {isEditLoading ? <p className="dashboard-status">Loading offer...</p> : null}
            {editErrorText ? <p className="error-text">{editErrorText}</p> : null}

            {!isEditLoading && editOfferId !== null ? (
              <form
                className="edit-offer-form"
                onSubmit={(event) => {
                  event.preventDefault();
                  void handleSaveEdits();
                }}
              >
                <section className="edit-offer-section">
                  <h3>Core details</h3>
                  <div className="edit-offer-grid">
                    <label>
                      Company name*
                      <input name="company_name" value={editForm.company_name} onChange={handleEditInputChange} />
                    </label>
                    <label>
                      Role title*
                      <input name="role_title" value={editForm.role_title} onChange={handleEditInputChange} />
                    </label>
                    <label>
                      Location*
                      <input name="location" value={editForm.location} onChange={handleEditInputChange} />
                    </label>
                    <label>
                      Employment type
                      <input
                        name="employment_type"
                        value={editForm.employment_type}
                        onChange={handleEditInputChange}
                      />
                    </label>
                    <label>
                      Work model
                      <input name="work_model" value={editForm.work_model} onChange={handleEditInputChange} />
                    </label>
                  </div>
                </section>

                <section className="edit-offer-section">
                  <h3>Compensation</h3>
                  <div className="edit-offer-grid">
                    <label className={hasFieldError("annual_base_salary_usd") ? "edit-offer-field-error" : ""}>
                      Annual base salary (USD)*
                      <input
                        name="annual_base_salary_usd"
                        value={editForm.annual_base_salary_usd}
                        onChange={handleEditInputChange}
                        inputMode="decimal"
                      />
                    </label>
                    <label className={hasFieldError("hourly_rate_usd") ? "edit-offer-field-error" : ""}>
                      Hourly rate (USD)
                      <input
                        name="hourly_rate_usd"
                        value={editForm.hourly_rate_usd}
                        onChange={handleEditInputChange}
                        inputMode="decimal"
                      />
                    </label>
                    <label className={hasFieldError("hours_per_week") ? "edit-offer-field-error" : ""}>
                      Hours per week
                      <input
                        name="hours_per_week"
                        value={editForm.hours_per_week}
                        onChange={handleEditInputChange}
                        inputMode="decimal"
                      />
                    </label>
                    <label>
                      Annualized total cash (USD)
                      <input
                        name="annualized_total_cash_usd"
                        value={editForm.annualized_total_cash_usd}
                        onChange={handleEditInputChange}
                        inputMode="decimal"
                      />
                    </label>
                    <label>
                      Signing bonus (USD)
                      <input
                        name="signing_bonus_usd"
                        value={editForm.signing_bonus_usd}
                        onChange={handleEditInputChange}
                        inputMode="decimal"
                      />
                    </label>
                    <label>
                      Target bonus (%)
                      <input
                        name="target_bonus_percent"
                        value={editForm.target_bonus_percent}
                        onChange={handleEditInputChange}
                        inputMode="decimal"
                      />
                    </label>
                  </div>
                </section>

                <section className="edit-offer-section">
                  <h3>Monetary benefits</h3>
                  <div className="edit-offer-grid">
                    <label>
                      Retirement match (%)
                      <input
                        name="retirement_match_percent"
                        value={editForm.retirement_match_percent}
                        onChange={handleEditInputChange}
                        inputMode="decimal"
                      />
                    </label>
                    <label>
                      Retirement match cap (USD)
                      <input
                        name="retirement_match_cap_usd"
                        value={editForm.retirement_match_cap_usd}
                        onChange={handleEditInputChange}
                        inputMode="decimal"
                      />
                    </label>
                    <label>
                      Health insurance employer monthly (USD)
                      <input
                        name="health_insurance_employer_monthly_usd"
                        value={editForm.health_insurance_employer_monthly_usd}
                        onChange={handleEditInputChange}
                        inputMode="decimal"
                      />
                    </label>
                    <label>
                      HSA employer annual (USD)
                      <input
                        name="hsa_employer_annual_usd"
                        value={editForm.hsa_employer_annual_usd}
                        onChange={handleEditInputChange}
                        inputMode="decimal"
                      />
                    </label>
                    <label>
                      Equity grant value (USD)
                      <input
                        name="equity_grant_usd"
                        value={editForm.equity_grant_usd}
                        onChange={handleEditInputChange}
                        inputMode="decimal"
                      />
                    </label>
                    <label>
                      Equity vesting schedule
                      <input
                        name="equity_vesting_schedule"
                        value={editForm.equity_vesting_schedule}
                        onChange={handleEditInputChange}
                      />
                    </label>
                    <label className="edit-offer-grid-full">
                      Other monetary benefits (one per line)
                      <textarea
                        name="other_monetary_benefits_text"
                        value={editForm.other_monetary_benefits_text}
                        onChange={handleEditInputChange}
                      />
                    </label>
                  </div>
                </section>

                <section className="edit-offer-section">
                  <h3>Non-monetary benefits</h3>
                  <div className="edit-offer-grid">
                    <label className="edit-offer-grid-full">
                      Mission alignment notes
                      <textarea
                        name="mission_alignment_notes"
                        value={editForm.mission_alignment_notes}
                        onChange={handleEditInputChange}
                      />
                    </label>
                    <label className="edit-offer-grid-full">
                      Culture notes
                      <textarea name="culture_notes" value={editForm.culture_notes} onChange={handleEditInputChange} />
                    </label>
                    <label className="edit-offer-grid-full">
                      Growth notes
                      <textarea name="growth_notes" value={editForm.growth_notes} onChange={handleEditInputChange} />
                    </label>
                    <label className="edit-offer-grid-full">
                      Wellness notes
                      <textarea
                        name="wellness_notes"
                        value={editForm.wellness_notes}
                        onChange={handleEditInputChange}
                      />
                    </label>
                    <label>
                      PTO days
                      <input name="pto_days" value={editForm.pto_days} onChange={handleEditInputChange} />
                    </label>
                    <label className="edit-offer-grid-full">
                      Remote flexibility notes
                      <textarea
                        name="remote_flexibility_notes"
                        value={editForm.remote_flexibility_notes}
                        onChange={handleEditInputChange}
                      />
                    </label>
                    <label className="edit-offer-grid-full">
                      Other non-monetary benefits (one per line)
                      <textarea
                        name="other_non_monetary_benefits_text"
                        value={editForm.other_non_monetary_benefits_text}
                        onChange={handleEditInputChange}
                      />
                    </label>
                    <label className="edit-offer-grid-full">
                      Non-monetary summary bullets (one per line)
                      <textarea
                        name="non_monetary_summary_bullets_text"
                        value={editForm.non_monetary_summary_bullets_text}
                        onChange={handleEditInputChange}
                      />
                    </label>
                  </div>
                </section>

                {editValidationErrors.length > 0 ? (
                  <ul className="edit-offer-errors">
                    {editValidationErrors.map((error) => (
                      <li key={error}>{error}</li>
                    ))}
                  </ul>
                ) : null}

                <footer className="edit-offer-actions">
                  <button
                    type="button"
                    className="secondary-button selectable"
                    onClick={() => {
                      requestCloseEditPanel();
                    }}
                    disabled={isEditSaving}
                  >
                    Cancel
                  </button>
                  <button type="submit" className="action-button selectable" disabled={isEditSaving}>
                    {isEditSaving ? "Saving..." : "Save Changes"}
                  </button>
                </footer>
              </form>
            ) : null}
          </section>
        </div>
      ) : null}
    </main>
  );
}
