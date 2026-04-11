import { useEffect, useMemo, useRef, useState } from "react";

import { createComparison, fetchComparisonById, fetchComparisons } from "../services/comparisonsApi";
import { fetchOfferSchema, fetchOffers } from "../services/offersApi";
import type { ComparisonPayload } from "../types/comparisons";
import type { OfferSchemaField, OfferSchemaPayload, OfferSummaryPayload } from "../types/offers";

interface ComparePageProps {
  prefillSelectedOfferIds?: string[];
  onPrefillConsumed?: () => void;
}

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

function offerName(offer: OfferSummaryPayload | undefined, fallbackId: string): string {
  return offer?.company_name || `Unknown (${fallbackId.slice(0, 8)})`;
}

function comparisonCardLabel(
  comparison: ComparisonPayload,
  offersById: Map<string, OfferSummaryPayload>
): string {
  if (comparison.comparison_mode === "one_to_all") {
    const baseName = offerName(offersById.get(comparison.base_offer_id), comparison.base_offer_id);
    const otherCount = Math.max(comparison.selected_offer_ids.length - 1, 0);
    return `${baseName} • all ${otherCount} other entries`;
  }
  const firstId = comparison.selected_offer_ids[0];
  const secondId = comparison.selected_offer_ids[1];
  return `${offerName(offersById.get(firstId), firstId)} • ${offerName(offersById.get(secondId), secondId)}`;
}

export function ComparePage({
  prefillSelectedOfferIds = [],
  onPrefillConsumed
}: ComparePageProps): JSX.Element {
  const [offerSchema, setOfferSchema] = useState<OfferSchemaPayload | null>(null);
  const [isSchemaLoading, setIsSchemaLoading] = useState(true);
  const [offers, setOffers] = useState<OfferSummaryPayload[]>([]);
  const [comparisons, setComparisons] = useState<ComparisonPayload[]>([]);
  const [isLoadingOffers, setIsLoadingOffers] = useState(true);
  const [isLoadingComparisons, setIsLoadingComparisons] = useState(true);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [draftSelectedOfferIds, setDraftSelectedOfferIds] = useState<string[]>([]);
  const [activeSavedComparisonId, setActiveSavedComparisonId] = useState<string | null>(null);
  const [activeSavedComparison, setActiveSavedComparison] = useState<ComparisonPayload | null>(null);
  const [draftNote, setDraftNote] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [cardAnimationState, setCardAnimationState] = useState<Record<string, "select" | "deselect">>({});
  const animationTimeoutRef = useRef<Record<string, number>>({});

  const offersById = useMemo(() => {
    return new Map(offers.map((offer) => [offer.id, offer]));
  }, [offers]);

  useEffect(() => {
    let cancelled = false;
    setIsSchemaLoading(true);
    setErrorText(null);
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

  useEffect(() => {
    let cancelled = false;
    setIsLoadingOffers(true);
    setErrorText(null);
    void fetchOffers()
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
          setIsLoadingOffers(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const refreshComparisons = async (): Promise<void> => {
    const response = await fetchComparisons();
    setComparisons(response.comparisons);
  };

  useEffect(() => {
    let cancelled = false;
    setIsLoadingComparisons(true);
    setErrorText(null);
    void fetchComparisons()
      .then((response) => {
        if (!cancelled) {
          setComparisons(response.comparisons);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setErrorText(error instanceof Error ? error.message : "Unable to load comparisons.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoadingComparisons(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (prefillSelectedOfferIds.length === 0) {
      return;
    }
    setActiveSavedComparisonId(null);
    setActiveSavedComparison(null);
    setDraftSelectedOfferIds(prefillSelectedOfferIds.slice(0, 2));
    onPrefillConsumed?.();
  }, [prefillSelectedOfferIds, onPrefillConsumed]);

  const scheduleCardAnimation = (cardId: string, mode: "select" | "deselect"): void => {
    setCardAnimationState((existing) => ({ ...existing, [cardId]: mode }));
    if (animationTimeoutRef.current[cardId] !== undefined) {
      window.clearTimeout(animationTimeoutRef.current[cardId]);
    }
    animationTimeoutRef.current[cardId] = window.setTimeout(() => {
      setCardAnimationState((existing) => {
        const next = { ...existing };
        delete next[cardId];
        return next;
      });
      delete animationTimeoutRef.current[cardId];
    }, 500);
  };

  const toggleDraftOfferSelection = (offerId: string): void => {
    setDraftSelectedOfferIds((current) => {
      if (current.includes(offerId)) {
        scheduleCardAnimation(`offer-${offerId}`, "deselect");
        return current.filter((id) => id !== offerId);
      }
      scheduleCardAnimation(`offer-${offerId}`, "select");
      if (current.length < 2) {
        return [...current, offerId];
      }
      scheduleCardAnimation(`offer-${current[0]}`, "deselect");
      return [current[1], offerId];
    });
  };

  const handleSelectSavedComparison = async (comparisonId: string): Promise<void> => {
    setErrorText(null);
    if (activeSavedComparisonId !== null && activeSavedComparisonId !== comparisonId) {
      scheduleCardAnimation(`saved-${activeSavedComparisonId}`, "deselect");
    }
    scheduleCardAnimation(`saved-${comparisonId}`, "select");
    setActiveSavedComparisonId(comparisonId);
    try {
      const detail = await fetchComparisonById(comparisonId);
      setActiveSavedComparison(detail);
    } catch (error: unknown) {
      setErrorText(error instanceof Error ? error.message : "Unable to load saved comparison detail.");
    }
  };

  const handleSaveDraft = async (): Promise<void> => {
    if (draftSelectedOfferIds.length === 0) {
      return;
    }
    setIsSaving(true);
    setSaveError(null);
    try {
      const mode = draftSelectedOfferIds.length === 1 ? "one_to_all" : "one_to_one";
      const result = await createComparison({
        mode,
        selected_offer_ids: draftSelectedOfferIds,
        base_offer_id: draftSelectedOfferIds[0],
        note: draftNote.trim() === "" ? null : draftNote.trim()
      });
      if (result.status !== "saved") {
        setSaveError(result.errors[0] ?? "Unable to save comparison.");
        return;
      }
      setDraftNote("");
      await refreshComparisons();
    } catch (error: unknown) {
      setSaveError(error instanceof Error ? error.message : "Unable to save comparison.");
    } finally {
      setIsSaving(false);
    }
  };

  const renderOfferPanel = (offerId: string, side: "left" | "right"): JSX.Element => {
    const offer = offersById.get(offerId);
    if (!offer || !offerSchema) {
      return (
        <article className={`compare-canvas-panel compare-canvas-panel-${side}`} data-testid={`compare-panel-${side}`}>
          <h3>Offer unavailable</h3>
          <p>{offerId}</p>
        </article>
      );
    }
    const payload = offer as unknown as Record<string, unknown>;
    const companyName = asText(getPath(payload, offerSchema.identity.company_name_path));
    const roleTitle = asText(getPath(payload, offerSchema.identity.role_title_path));
    const locationField = offerSchema.fields.find((field) => field.id === "location");
    const locationPath = locationField?.storage_path ?? "location";
    const location = asText(getPath(payload, locationPath)).trim();
    const roleAndLocation = location ? `${roleTitle} • ${location}` : roleTitle;

    return (
      <article className={`dashboard-card compare-static-card compare-canvas-panel-${side}`} data-testid={`compare-panel-${side}`}>
        <h2 className="dashboard-card-company">{companyName}</h2>
        <p className="dashboard-card-role">{roleAndLocation}</p>

        {offerSchema.card_sections.map((section) => {
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
      </article>
    );
  };

  const renderCanvas = (): JSX.Element => {
    const activeComparison = activeSavedComparison;
    if (activeComparison !== null) {
      const ids = activeComparison.selected_offer_ids;
      return (
        <>
          <section className="compare-canvas-grid">
            {renderOfferPanel(activeComparison.base_offer_id, "left")}
            <article className="compare-canvas-middle">
              <h3>Comparison Summary</h3>
              <p>{activeComparison.summary_text}</p>
            </article>
            {activeComparison.comparison_mode === "one_to_one" ? (
              renderOfferPanel(ids[1], "right")
            ) : (
              <article className="compare-canvas-right-placeholder">
                <h3>All Other Entries</h3>
                <p>{`Snapshot includes ${Math.max(ids.length - 1, 0)} other offers.`}</p>
              </article>
            )}
          </section>
          {activeComparison.note ? <p className="compare-note">{activeComparison.note}</p> : null}
          <button
            type="button"
            className="secondary-button selectable"
            onClick={() => {
              setActiveSavedComparisonId(null);
              setActiveSavedComparison(null);
            }}
          >
            Create New Comparison
          </button>
        </>
      );
    }

    if (draftSelectedOfferIds.length > 0) {
      const mode = draftSelectedOfferIds.length === 1 ? "one_to_all" : "one_to_one";
      return (
        <>
          <section className="compare-canvas-grid">
            {renderOfferPanel(draftSelectedOfferIds[0], "left")}
            <article className="compare-canvas-middle">
              <h3>Comparison Summary</h3>
              <p>Comparison summary placeholder.</p>
            </article>
            {mode === "one_to_one" ? (
              renderOfferPanel(draftSelectedOfferIds[1], "right")
            ) : (
              <article className="compare-canvas-right-placeholder">
                <h3>All Other Entries</h3>
                <p>This area remains a placeholder in Stage 7.</p>
              </article>
            )}
          </section>
          <label className="compare-note-input">
            Optional note
            <textarea
              value={draftNote}
              onChange={(event) => {
                setDraftNote(event.target.value);
              }}
            />
          </label>
          {saveError ? <p className="error-text">{saveError}</p> : null}
          <button
            type="button"
            className="action-button selectable"
            onClick={() => {
              void handleSaveDraft();
            }}
            disabled={isSaving}
          >
            {isSaving ? "Saving..." : "Save Comparison"}
          </button>
        </>
      );
    }

    return (
      <p className="compare-empty-message">
        Create new comparison or select previously saved comparison
      </p>
    );
  };

  useEffect(() => {
    return () => {
      for (const timeoutId of Object.values(animationTimeoutRef.current)) {
        window.clearTimeout(timeoutId);
      }
    };
  }, []);

  return (
    <main className="main-panel compare-panel">
      <h1 className="main-title">Compare</h1>

      {isSchemaLoading ? <p className="dashboard-status">Loading schema...</p> : null}
      {isLoadingOffers ? <p className="dashboard-status">Loading offers...</p> : null}
      {isLoadingComparisons ? <p className="dashboard-status">Loading comparisons...</p> : null}
      {errorText ? <p className="error-text">{errorText}</p> : null}

      <section className="compare-canvas" data-testid="compare-canvas">
        {renderCanvas()}
      </section>

      {activeSavedComparisonId === null ? (
        <section className="compare-row" aria-label="Available offers">
          {offers.map((offer) => {
            const isSelected = draftSelectedOfferIds.includes(offer.id);
            const animationClass =
              cardAnimationState[`offer-${offer.id}`] === "select"
                ? "dashboard-card-flip-select"
                : cardAnimationState[`offer-${offer.id}`] === "deselect"
                  ? "dashboard-card-flip-deselect"
                  : "";
            return (
              <div key={offer.id} className="dashboard-card-shell">
                <button
                  type="button"
                  className={`compare-offer-card dashboard-card selectable ${
                    isSelected ? "dashboard-card-selected" : ""
                  } ${animationClass}`.trim()}
                  aria-pressed={isSelected}
                  onClick={() => {
                    toggleDraftOfferSelection(offer.id);
                  }}
                >
                  <h2 className="dashboard-card-company">{offer.company_name}</h2>
                </button>
              </div>
            );
          })}
        </section>
      ) : null}

      <section className="compare-row compare-saved-row" aria-label="Saved comparisons">
        {comparisons.map((comparison) => {
          const isSelected = comparison.id === activeSavedComparisonId;
          const animationClass =
            cardAnimationState[`saved-${comparison.id}`] === "select"
              ? "dashboard-card-flip-select"
              : cardAnimationState[`saved-${comparison.id}`] === "deselect"
                ? "dashboard-card-flip-deselect"
                : "";
          return (
            <div key={comparison.id} className="dashboard-card-shell">
              <button
                type="button"
                className={`compare-saved-card dashboard-card selectable ${
                  isSelected ? "dashboard-card-selected" : ""
                } ${animationClass}`.trim()}
                aria-pressed={isSelected}
                onClick={() => {
                  void handleSelectSavedComparison(comparison.id);
                }}
              >
                <h2 className="dashboard-card-company">{comparisonCardLabel(comparison, offersById)}</h2>
              </button>
            </div>
          );
        })}
      </section>
    </main>
  );
}
