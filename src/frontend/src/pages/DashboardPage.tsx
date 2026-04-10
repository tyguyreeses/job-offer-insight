import { useEffect, useMemo, useRef, useState, type ChangeEvent, type KeyboardEvent } from "react";

import {
  createDemoOffers,
  deleteOffer,
  fetchOfferById,
  fetchOfferSchema,
  fetchOffers,
  updateOffer
} from "../services/offersApi";
import type {
  OfferSchemaField,
  OfferSchemaPayload,
  OfferSortBy,
  OfferSummaryPayload,
  SortDirection
} from "../types/offers";

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

function getPath(payload: Record<string, unknown>, path: string): unknown {
  const parts = path.split(".");
  let cursor: unknown = payload;
  for (const part of parts) {
    if (!cursor || typeof cursor !== "object" || Array.isArray(cursor)) {
      return undefined;
    }
    cursor = (cursor as Record<string, unknown>)[part];
  }
  return cursor;
}

function setPath(payload: Record<string, unknown>, path: string, value: unknown): void {
  const parts = path.split(".");
  let cursor: Record<string, unknown> = payload;
  for (const part of parts.slice(0, -1)) {
    const existing = cursor[part];
    if (!existing || typeof existing !== "object" || Array.isArray(existing)) {
      cursor[part] = {};
    }
    cursor = cursor[part] as Record<string, unknown>;
  }
  cursor[parts[parts.length - 1]] = value;
}

function asText(value: unknown): string {
  return typeof value === "string" ? value : "";
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

function asStringList(value: unknown): string[] {
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

function formatFieldValue(field: OfferSchemaField, value: unknown): string | null {
  if (field.data_type === "list_string") {
    return null;
  }
  if (field.storage_path.endsWith("created_at")) {
    return formatDate(typeof value === "string" ? value : undefined);
  }
  if (field.data_type === "number" || field.data_type === "integer") {
    const parsed = asNumber(value);
    if (parsed === null) {
      return null;
    }
    if (field.storage_path.includes("_usd")) {
      return formatUsd(parsed);
    }
    if (field.storage_path.includes("percent")) {
      return `${parsed}%`;
    }
    return `${parsed}`;
  }
  const text = asText(value).trim();
  return text === "" ? null : text;
}

function listTextForForm(field: OfferSchemaField, value: unknown): string {
  if (field.edit.widget === "textarea_list" || field.data_type === "list_string") {
    return asStringList(value).join("\n");
  }
  if (field.data_type === "number" || field.data_type === "integer") {
    const parsed = asNumber(value);
    return parsed === null ? "" : `${parsed}`;
  }
  return asText(value);
}

function parseFormValue(field: OfferSchemaField, value: string): unknown {
  const trimmed = value.trim();
  if (field.edit.widget === "textarea_list" || field.data_type === "list_string") {
    return value
      .split("\n")
      .map((item) => item.trim())
      .filter((item) => item.length > 0);
  }
  if (field.data_type === "number" || field.data_type === "integer") {
    if (trimmed === "") {
      return null;
    }
    const parsed = Number(trimmed.replace(/,/g, ""));
    if (!Number.isFinite(parsed)) {
      return null;
    }
    if (field.data_type === "integer") {
      return Math.trunc(parsed);
    }
    return parsed;
  }
  return trimmed;
}

function isPresent(value: unknown): boolean {
  if (value === null || value === undefined) {
    return false;
  }
  if (typeof value === "string") {
    return value.trim() !== "";
  }
  if (Array.isArray(value)) {
    return value.length > 0;
  }
  return true;
}

export function DashboardPage(): JSX.Element {
  const DELETE_FADE_DURATION_MS = 280;
  const DELETE_COLLAPSE_DURATION_MS = 460;
  const EDIT_PANEL_TRANSITION_MS = 240;

  const [offerSchema, setOfferSchema] = useState<OfferSchemaPayload | null>(null);
  const [offers, setOffers] = useState<OfferSummaryPayload[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSchemaLoading, setIsSchemaLoading] = useState(true);
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
  const [editForm, setEditForm] = useState<Record<string, string>>({});
  const [initialEditForm, setInitialEditForm] = useState<Record<string, string>>({});
  const [editOfferBasePayload, setEditOfferBasePayload] = useState<OfferSummaryPayload | null>(null);

  const selectedSort = useMemo(() => {
    return SORT_OPTIONS.find((option) => option.label === sortSelection) ?? SORT_OPTIONS[0];
  }, [sortSelection]);

  const editableFields = useMemo(() => {
    if (!offerSchema) {
      return [] as OfferSchemaField[];
    }
    return offerSchema.fields
      .filter((field) => field.edit.visible)
      .sort((left, right) => left.edit.order - right.edit.order);
  }, [offerSchema]);

  const locationPath = useMemo(() => {
    if (!offerSchema) {
      return "location";
    }
    const locationField = offerSchema.fields.find((field) => field.id === "location");
    return locationField?.storage_path ?? "location";
  }, [offerSchema]);

  const requiredAllFieldIds = useMemo(() => {
    return new Set(offerSchema?.required.all_of ?? []);
  }, [offerSchema]);

  const isEditDirty = useMemo(() => {
    return JSON.stringify(editForm) !== JSON.stringify(initialEditForm);
  }, [editForm, initialEditForm]);

  useEffect(() => {
    let cancelled = false;
    setIsSchemaLoading(true);

    void fetchOfferSchema()
      .then((schema) => {
        if (!cancelled) {
          setOfferSchema(schema);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setErrorText(error instanceof Error ? error.message : "Unable to load offer schema.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsSchemaLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

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
        if (!cancelled) {
          setOffers(response.offers);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setErrorText(error instanceof Error ? error.message : "Unable to load offers.");
        }
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
      setEditForm({});
      setInitialEditForm({});
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
    if (!offerSchema) {
      return;
    }
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
        const formState: Record<string, string> = {};
        for (const field of editableFields) {
          formState[field.id] = listTextForForm(field, getPath(offer as Record<string, unknown>, field.storage_path));
        }
        setEditOfferBasePayload(offer);
        setEditForm(formState);
        setInitialEditForm(formState);
      })
      .catch((error: unknown) => {
        setEditErrorText(error instanceof Error ? error.message : "Unable to load offer for editing.");
      })
      .finally(() => {
        setIsEditLoading(false);
      });
  };

  const updateEditField = (fieldId: string, value: string): void => {
    setEditForm((current) => ({ ...current, [fieldId]: value }));
  };

  const handleEditInputChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void => {
    updateEditField(event.target.name, event.target.value);
  };

  const hasFieldError = (field: OfferSchemaField): boolean => {
    const normalized = field.storage_path.toLowerCase();
    return editValidationErrors.some((error) => error.toLowerCase().includes(normalized));
  };

  const handleSaveEdits = async (): Promise<void> => {
    if (editOfferId === null || editOfferBasePayload === null || !offerSchema) {
      return;
    }
    setIsEditSaving(true);
    setEditErrorText(null);
    setEditValidationErrors([]);

    const payload: Record<string, unknown> = { ...editOfferBasePayload };
    for (const field of editableFields) {
      const rawValue = editForm[field.id] ?? "";
      setPath(payload, field.storage_path, parseFormValue(field, rawValue));
    }
    delete payload.id;

    try {
      const result = await updateOffer(editOfferId, payload);
      if (result.status !== "saved" || result.offer === null) {
        setEditValidationErrors(result.errors);
        setEditErrorText(result.errors[0] ?? "Unable to save changes. Check required fields and try again.");
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
      for (const timeoutId of Object.values(animationTimeoutRef.current)) {
        window.clearTimeout(timeoutId);
      }
      for (const timeoutId of Object.values(deleteFadeTimeoutRef.current)) {
        window.clearTimeout(timeoutId);
      }
      for (const timeoutId of Object.values(deleteCollapseTimeoutRef.current)) {
        window.clearTimeout(timeoutId);
      }
      if (editCloseTimeoutRef.current !== null) {
        window.clearTimeout(editCloseTimeoutRef.current);
      }
    };
  }, []);

  const handleCardKeyDown = (event: KeyboardEvent<HTMLElement>, offerId: string): void => {
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

      {isSchemaLoading ? <p className="dashboard-status">Loading schema...</p> : null}
      {isLoading ? <p className="dashboard-status">Loading offers...</p> : null}
      {errorText ? <p className="error-text dashboard-status">{errorText}</p> : null}

      {!isLoading && !isSchemaLoading && !errorText && offers.length === 0 ? (
        <p className="dashboard-status">No offers yet. Add an entry to populate your dashboard.</p>
      ) : null}

      <section className="dashboard-scroll-row" aria-label="Offer cards">
        {offers.map((offer) => {
          const payload = offer as unknown as Record<string, unknown>;
          const companyName = offerSchema ? asText(getPath(payload, offerSchema.identity.company_name_path)) : offer.company_name;
          const roleTitle = offerSchema ? asText(getPath(payload, offerSchema.identity.role_title_path)) : offer.role_title;
          const location = asText(getPath(payload, locationPath)).trim();
          const roleAndLocation = location ? `${roleTitle} • ${location}` : roleTitle;

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
                <h2 className="dashboard-card-company">{companyName}</h2>
                <p className="dashboard-card-role">{roleAndLocation}</p>

                {offerSchema?.card_sections.map((section) => {
                  const fields = offerSchema.fields
                    .filter((field) => field.card.visible && field.card.section_id === section.section_id)
                    .sort((left, right) => left.card.order - right.card.order);

                  const renderedRows = fields
                    .map((field) => {
                      const rawValue = getPath(payload, field.storage_path);
                      if (!isPresent(rawValue)) {
                        return null;
                      }
                      if (field.card.style === "list") {
                        const items = asStringList(rawValue);
                        if (items.length === 0) {
                          return null;
                        }
                        return (
                          <ul key={`${offer.id}-${field.id}`}>
                            {items.map((item) => (
                              <li key={`${offer.id}-${field.id}-${item}`}>{item}</li>
                            ))}
                          </ul>
                        );
                      }

                      const formatted = formatFieldValue(field, rawValue);
                      if (!formatted) {
                        return null;
                      }

                      if (field.card.style === "value") {
                        return <p key={`${offer.id}-${field.id}`}>{formatted}</p>;
                      }

                      return <p key={`${offer.id}-${field.id}`}>{`${field.label}: ${formatted}`}</p>;
                    })
                    .filter((node): node is JSX.Element => node !== null);

                  if (renderedRows.length === 0) {
                    return null;
                  }

                  return (
                    <section key={`${offer.id}-${section.section_id}`} className="dashboard-card-section">
                      <h3>{section.title}</h3>
                      {renderedRows}
                    </section>
                  );
                })}

                {isSelected ? (
                  <div className="dashboard-card-actions">
                    <button
                      type="button"
                      className="secondary-button selectable"
                      onClick={(event) => {
                        event.stopPropagation();
                        handleEditClick(offer.id);
                      }}
                      disabled={!offerSchema}
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

            {!isEditLoading && editOfferId !== null && offerSchema ? (
              <form
                className="edit-offer-form"
                onSubmit={(event) => {
                  event.preventDefault();
                  void handleSaveEdits();
                }}
              >
                {offerSchema.edit_sections.map((section) => {
                  const sectionFields = editableFields.filter((field) => field.edit.section_id === section.section_id);
                  if (sectionFields.length === 0) {
                    return null;
                  }
                  const sectionClassSuffix = section.section_id.replace(/[^a-zA-Z0-9_-]/g, "-");
                  return (
                    <section
                      key={section.section_id}
                      className={`edit-offer-section edit-offer-section-${sectionClassSuffix}`}
                    >
                      <h3>{section.title}</h3>
                      <div className="edit-offer-grid">
                        {sectionFields.map((field) => {
                          const requiredMark = requiredAllFieldIds.has(field.id) ? "*" : "";
                          const labelText = `${field.label}${requiredMark}`;
                          const isFieldError = hasFieldError(field);
                          const className = `${field.edit.widget.includes("textarea") ? "edit-offer-grid-full" : ""} ${
                            isFieldError ? "edit-offer-field-error" : ""
                          }`.trim();

                          if (field.edit.widget === "textarea" || field.edit.widget === "textarea_list") {
                            return (
                              <label key={field.id} className={className}>
                                {labelText}
                                <textarea
                                  name={field.id}
                                  value={editForm[field.id] ?? ""}
                                  onChange={handleEditInputChange}
                                />
                              </label>
                            );
                          }

                          return (
                            <label key={field.id} className={className}>
                              {labelText}
                              <input
                                name={field.id}
                                value={editForm[field.id] ?? ""}
                                onChange={handleEditInputChange}
                                inputMode={field.edit.widget === "number" ? "decimal" : undefined}
                              />
                            </label>
                          );
                        })}
                      </div>
                    </section>
                  );
                })}

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
