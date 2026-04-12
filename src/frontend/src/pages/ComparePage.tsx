import { type CSSProperties, useEffect, useMemo, useState } from "react";

import {
  createComparison,
  deleteComparison,
  fetchComparisonById,
  fetchComparisons,
  generateComparisonAISection,
  generateComparisonDraft
} from "../services/comparisonsApi";
import { fetchOfferSchema, fetchOffers } from "../services/offersApi";
import type { ComparisonPayload } from "../types/comparisons";
import type { OfferSchemaPayload, OfferSummaryPayload } from "../types/offers";
import { asStringList, asText, formatFieldValue, formatUsd, getDerivedMonetary, getPath, isPresent } from "../utils/offerDisplay";

interface ComparePageProps {
  prefillSelectedOfferIds?: string[];
  onPrefillConsumed?: () => void;
  onUnsavedDraftStateChange?: (hasUnsaved: boolean) => void;
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

function renderMarkdownText(markdown: string): JSX.Element {
  const nodes: JSX.Element[] = [];
  let paragraphLines: string[] = [];
  let listItems: string[] = [];
  let listType: "ul" | "ol" | null = null;

  const flushParagraph = (): void => {
    if (paragraphLines.length === 0) {
      return;
    }
    const text = paragraphLines.join(" ").trim();
    if (text !== "") {
      nodes.push(<p key={`p-${nodes.length}`}>{text}</p>);
    }
    paragraphLines = [];
  };

  const flushList = (): void => {
    if (listType === null || listItems.length === 0) {
      listType = null;
      listItems = [];
      return;
    }
    const key = `${listType}-${nodes.length}`;
    if (listType === "ul") {
      nodes.push(
        <ul key={key}>
          {listItems.map((item, index) => (
            <li key={`${key}-${index}`}>{item}</li>
          ))}
        </ul>
      );
    } else {
      nodes.push(
        <ol key={key}>
          {listItems.map((item, index) => (
            <li key={`${key}-${index}`}>{item}</li>
          ))}
        </ol>
      );
    }
    listType = null;
    listItems = [];
  };

  for (const line of markdown.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (trimmed === "") {
      flushParagraph();
      flushList();
      continue;
    }

    const unordered = trimmed.match(/^[-*]\s+(.*)$/);
    const ordered = trimmed.match(/^\d+\.\s+(.*)$/);
    if (unordered || ordered) {
      flushParagraph();
      const nextType: "ul" | "ol" = unordered ? "ul" : "ol";
      if (listType !== null && listType !== nextType) {
        flushList();
      }
      listType = nextType;
      listItems.push((unordered ?? ordered)?.[1].trim() ?? "");
      continue;
    }

    flushList();
    const heading = trimmed.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      flushParagraph();
      const level = heading[1].length;
      const title = heading[2].trim();
      if (level <= 1) {
        nodes.push(<h4 key={`h4-${nodes.length}`}>{title}</h4>);
      } else if (level === 2) {
        nodes.push(<h5 key={`h5-${nodes.length}`}>{title}</h5>);
      } else {
        nodes.push(<h6 key={`h6-${nodes.length}`}>{title}</h6>);
      }
      continue;
    }
    paragraphLines.push(trimmed);
  }

  flushParagraph();
  flushList();

  return <div className="compare-markdown">{nodes.length > 0 ? nodes : <p>{markdown}</p>}</div>;
}

function aiSectionToMarkdown(aiSection: unknown): string {
  if (typeof aiSection === "string") {
    return aiSection;
  }
  if (aiSection && typeof aiSection === "object" && !Array.isArray(aiSection)) {
    const record = aiSection as Record<string, unknown>;
    const markdownCandidate = record.markdown ?? record.text ?? record.content;
    if (typeof markdownCandidate === "string") {
      return markdownCandidate;
    }
    return JSON.stringify(record, null, 2);
  }
  if (Array.isArray(aiSection)) {
    return JSON.stringify(aiSection, null, 2);
  }
  return "";
}

function normalizeMetricLabel(metricLabel: string): string {
  const withoutUnits = metricLabel.replace(/\s*\(USD\)\s*/gi, " ").trim();
  if (withoutUnits === "") {
    return "Value";
  }
  return withoutUnits;
}

export function ComparePage({
  prefillSelectedOfferIds = [],
  onPrefillConsumed,
  onUnsavedDraftStateChange
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
  const [generatedDraftId, setGeneratedDraftId] = useState<string | null>(null);
  const [generatedCodeSection, setGeneratedCodeSection] = useState<Record<string, unknown> | null>(null);
  const [generatedAISection, setGeneratedAISection] = useState<unknown | null>(null);
  const [isGeneratingCode, setIsGeneratingCode] = useState(false);
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const hasUnsavedGenerated = generatedDraftId !== null;

  const offersById = useMemo(() => {
    return new Map(offers.map((offer) => [offer.id, offer]));
  }, [offers]);

  const metricSentence = (codeSection: Record<string, unknown>, row: Record<string, unknown>): JSX.Element => {
    const metric = normalizeMetricLabel(asText(row.metric_label));
    const mode = asText(codeSection.mode);

    if (mode === "one_to_one") {
      const percent = row.percentage_difference;
      if (typeof percent === "number") {
        if (percent > 0) {
          return (
            <>
              {`← ${metric}: `}
              <strong>{`${percent.toFixed(2)}%`}</strong>
              {" lower"}
            </>
          );
        }
        if (percent < 0) {
          return (
            <>
              {`← ${metric}: `}
              <strong>{`${Math.abs(percent).toFixed(2)}%`}</strong>
              {" higher"}
            </>
          );
        }
        return <>{`↔ ${metric}: equal`}</>;
      }
      return <>{`↔ ${metric}: unavailable`}</>;
    }

    const percent = row.percentage_difference_to_highest;
    if (typeof percent === "number") {
      if (percent > 0) {
        return (
          <>
            {`← ${metric}: `}
            <strong>{`${percent.toFixed(2)}%`}</strong>
            {" lower"}
          </>
        );
      }
      if (percent < 0) {
        return (
          <>
            {`← ${metric}: `}
            <strong>{`${Math.abs(percent).toFixed(2)}%`}</strong>
            {" higher"}
          </>
        );
      }
      return <>{`↔ ${metric}: equal`}</>;
    }
    return <>{`↔ ${metric}: unavailable`}</>;
  };

  useEffect(() => {
    onUnsavedDraftStateChange?.(hasUnsavedGenerated);
  }, [hasUnsavedGenerated, onUnsavedDraftStateChange]);

  useEffect(() => {
    const onBeforeUnload = (event: BeforeUnloadEvent): void => {
      if (!hasUnsavedGenerated) {
        return;
      }
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => {
      window.removeEventListener("beforeunload", onBeforeUnload);
    };
  }, [hasUnsavedGenerated]);

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

  const requestDiscardGeneratedIfNeeded = (): boolean => {
    if (!hasUnsavedGenerated) {
      return true;
    }
    return window.confirm("Discard unsaved generated comparison?");
  };

  const clearGeneratedDraft = (): void => {
    setGeneratedDraftId(null);
    setGeneratedCodeSection(null);
    setGeneratedAISection(null);
    setSaveError(null);
  };

  const toggleDraftOfferSelection = (offerId: string): void => {
    if (!requestDiscardGeneratedIfNeeded()) {
      return;
    }
    clearGeneratedDraft();
    setDraftSelectedOfferIds((current) => {
      if (current.includes(offerId)) {
        return current.filter((id) => id !== offerId);
      }
      if (current.length < 2) {
        return [...current, offerId];
      }
      return [current[1], offerId];
    });
  };

  const handleSelectSavedComparison = async (comparisonId: string): Promise<void> => {
    if (!requestDiscardGeneratedIfNeeded()) {
      return;
    }
    setErrorText(null);
    clearGeneratedDraft();
    if (activeSavedComparisonId === comparisonId) {
      setActiveSavedComparisonId(null);
      setActiveSavedComparison(null);
      return;
    }
    setActiveSavedComparisonId(comparisonId);
    try {
      const detail = await fetchComparisonById(comparisonId);
      setActiveSavedComparison(detail);
    } catch (error: unknown) {
      setErrorText(error instanceof Error ? error.message : "Unable to load saved comparison detail.");
    }
  };

  const handleDeleteComparisonClick = async (comparisonId: string): Promise<void> => {
    setErrorText(null);
    try {
      await deleteComparison(comparisonId);
      setComparisons((current) => current.filter((comparison) => comparison.id !== comparisonId));
      if (activeSavedComparisonId === comparisonId) {
        setActiveSavedComparisonId(null);
        setActiveSavedComparison(null);
      }
    } catch (error: unknown) {
      setErrorText(error instanceof Error ? error.message : "Unable to delete saved comparison.");
    }
  };

  const handleGenerateComparison = async (): Promise<void> => {
    if (draftSelectedOfferIds.length === 0) {
      return;
    }
    setIsGeneratingCode(true);
    setGeneratedAISection(null);
    setSaveError(null);
    try {
      const mode = draftSelectedOfferIds.length === 1 ? "one_to_all" : "one_to_one";
      const codeResult = await generateComparisonDraft({
        mode,
        selected_offer_ids: draftSelectedOfferIds,
        base_offer_id: draftSelectedOfferIds[0],
        note: draftNote || null
      });
      if (codeResult.status !== "draft_ready" || codeResult.draft_id === null) {
        setSaveError(codeResult.errors[0] ?? "Unable to generate comparison.");
        return;
      }
      setGeneratedDraftId(codeResult.draft_id);
      setGeneratedCodeSection(codeResult.code_section);

      setIsGeneratingAI(true);
      const aiResult = await generateComparisonAISection(codeResult.draft_id);
      if (aiResult.status === "completed") {
        setGeneratedAISection(aiResult.ai_section);
      } else {
        setSaveError(aiResult.errors[0] ?? "Unable to generate AI section.");
      }
    } catch (error: unknown) {
      setSaveError(error instanceof Error ? error.message : "Unable to generate comparison.");
    } finally {
      setIsGeneratingCode(false);
      setIsGeneratingAI(false);
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
      const generatedSummary = generatedAISection ? aiSectionToMarkdown(generatedAISection).trim() : "";
      const result = await createComparison({
        mode,
        selected_offer_ids: draftSelectedOfferIds,
        base_offer_id: draftSelectedOfferIds[0],
        summary_text: generatedSummary || null,
        code_section: generatedCodeSection,
        ai_section: generatedAISection,
        note: draftNote || null
      });
      if (result.status !== "saved") {
        setSaveError(result.errors[0] ?? "Unable to save comparison.");
        return;
      }
      clearGeneratedDraft();
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
    const derivedMonetary = getDerivedMonetary(payload);

    return (
      <article className={`dashboard-card compare-static-card compare-canvas-panel-${side}`} data-testid={`compare-panel-${side}`}>
        <h2 className="dashboard-card-company">{companyName}</h2>
        <p className="dashboard-card-role">{roleAndLocation}</p>

        {derivedMonetary.annualBenefits !== null || derivedMonetary.monthlyTakeHome !== null ? (
          <section className="dashboard-card-section dashboard-card-derived-section">
            <h3>
              Estimated Monetary Snapshot{" "}
              {derivedMonetary.explanation ? (
                <span className="info-pill" title={derivedMonetary.explanation} aria-label="Monetary calculation details">
                  i
                </span>
              ) : null}
            </h3>
            {derivedMonetary.annualBenefits !== null ? (
              <p>{`Total Annual Monetary Benefits: ${formatUsd(derivedMonetary.annualBenefits)}`}</p>
            ) : null}
            {derivedMonetary.monthlyTakeHome !== null ? (
              <p>{`Monthly Take-Home: ${formatUsd(derivedMonetary.monthlyTakeHome)}`}</p>
            ) : null}
          </section>
        ) : null}

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

  const renderCodeSection = (): JSX.Element | null => {
    if (!generatedCodeSection) {
      return null;
    }
    const metricsRaw = generatedCodeSection.metrics;
    const metrics = Array.isArray(metricsRaw) ? metricsRaw : [];
    return (
      <section className="compare-generated-section compare-generated-code">
        <h3>Code-Generated Comparison</h3>
        <p>{asText(generatedCodeSection.notes)}</p>
        {metrics.length > 0 ? (
          <ul className="compare-generated-metrics-list">
            {metrics.map((item, index) => {
              if (!item || typeof item !== "object" || Array.isArray(item)) {
                return null;
              }
              const row = item as Record<string, unknown>;
              const label = asText(row.metric_label);
              return <li key={`${label}-${index}`}>{metricSentence(generatedCodeSection, row)}</li>;
            })}
          </ul>
        ) : (
          <p>No deterministic metric rows were available for this selection.</p>
        )}
      </section>
    );
  };

  const renderAISection = (): JSX.Element => {
    const aiText = generatedAISection ? aiSectionToMarkdown(generatedAISection) : "";
    const generatingLabel = "generating...";
    return (
      <section className="compare-generated-section compare-generated-ai">
        <h3>AI-Generated Comparison</h3>
        {isGeneratingAI ? (
          <p className="compare-generated-pending audio-main-label-processing">
            {generatingLabel.split("").map((character, index) => (
              <span
                key={`compare-processing-char-${index}-${character === " " ? "space" : character}`}
                className="processing-label-char"
                style={{ ["--processing-index" as string]: index } as CSSProperties}
              >
                {character}
              </span>
            ))}
          </p>
        ) : null}
        {!isGeneratingAI && generatedAISection ? renderMarkdownText(aiText) : null}
        {!isGeneratingAI && !generatedAISection ? <p className="compare-generated-pending">Pending...</p> : null}
      </section>
    );
  };

  const renderSavedCodeSection = (codeSection: Record<string, unknown>): JSX.Element => {
    const metricsRaw = codeSection.metrics;
    const metrics = Array.isArray(metricsRaw) ? metricsRaw : [];
    return (
      <section className="compare-generated-section compare-generated-code">
        <h3>Saved Calculations</h3>
        <p>{asText(codeSection.notes)}</p>
        {metrics.length > 0 ? (
          <ul className="compare-generated-metrics-list">
            {metrics.map((item, index) => {
              if (!item || typeof item !== "object" || Array.isArray(item)) {
                return null;
              }
              const row = item as Record<string, unknown>;
              const label = asText(row.metric_label);
              return <li key={`${label}-${index}`}>{metricSentence(codeSection, row)}</li>;
            })}
          </ul>
        ) : (
          <p>No deterministic metric rows were available for this selection.</p>
        )}
      </section>
    );
  };

  const renderCanvas = (): JSX.Element => {
    const activeComparison = activeSavedComparison;
    if (activeComparison !== null) {
      const ids = activeComparison.selected_offer_ids;
      const savedAIText = activeComparison.ai_section ? aiSectionToMarkdown(activeComparison.ai_section) : "";
      return (
        <section className="compare-canvas-grid">
          {renderOfferPanel(activeComparison.base_offer_id, "left")}
          <article className="compare-canvas-middle">
            <div className="compare-summary-content">
              <h3>Saved Comparison</h3>
              {activeComparison.code_section ? renderSavedCodeSection(activeComparison.code_section) : null}
              {savedAIText ? (
                <section className="compare-generated-section compare-generated-ai">
                  <h3>Saved AI Summary</h3>
                  {renderMarkdownText(savedAIText)}
                </section>
              ) : (
                <p>{activeComparison.summary_text}</p>
              )}
              {activeComparison.note ? (
                <section className="compare-generated-section">
                  <h3>Saved Notes</h3>
                  <p>{activeComparison.note}</p>
                </section>
              ) : null}
            </div>
          </article>
          {activeComparison.comparison_mode === "one_to_one" ? (
            renderOfferPanel(ids[1], "right")
          ) : (
            <article className="compare-canvas-right-placeholder">
              <div className="compare-summary-content">
                <h3>All Other Entries</h3>
                <p>{`Snapshot includes ${Math.max(ids.length - 1, 0)} other offers.`}</p>
              </div>
            </article>
          )}
        </section>
      );
    }

    if (draftSelectedOfferIds.length > 0) {
      const mode = draftSelectedOfferIds.length === 1 ? "one_to_all" : "one_to_one";
      return (
        <>
          <section className="compare-canvas-grid">
            {renderOfferPanel(draftSelectedOfferIds[0], "left")}
            <article className="compare-canvas-middle compare-canvas-middle-stage8">
              <div className="compare-summary-content compare-summary-content-stage8">
                <h3>Comparison Draft</h3>
                {renderCodeSection()}
                {generatedDraftId !== null ? renderAISection() : <p>Generate comparison to populate code and AI sections.</p>}
                <label className="input-label compare-note-label" htmlFor="compare-note">
                  Notes
                </label>
                <textarea
                  id="compare-note"
                  className="job-entry-input compare-note-input"
                  value={draftNote}
                  onChange={(event) => setDraftNote(event.target.value)}
                  placeholder="Add optional notes before saving..."
                />
                <div className="compare-stage8-actions">
                  <button
                    type="button"
                    className="action-button selectable"
                    onClick={() => {
                      void handleGenerateComparison();
                    }}
                    disabled={isGeneratingCode || isGeneratingAI || draftSelectedOfferIds.length === 0}
                  >
                    {isGeneratingCode ? "Generating..." : "Generate Comparison"}
                  </button>
                  <button
                    type="button"
                    className="action-button selectable compare-save-button-inline"
                    onClick={() => {
                      void handleSaveDraft();
                    }}
                    disabled={isSaving || draftSelectedOfferIds.length === 0}
                  >
                    {isSaving ? "Saving..." : "Save Comparison"}
                  </button>
                </div>
              </div>
            </article>
            {mode === "one_to_one" ? (
              renderOfferPanel(draftSelectedOfferIds[1], "right")
            ) : (
              <article className="compare-canvas-right-placeholder">
                <div className="compare-summary-content">
                  <h3>All Other Entries</h3>
                  <p>One-to-all compares selected base against all other saved offers.</p>
                </div>
              </article>
            )}
          </section>
          {saveError ? <p className="error-text">{saveError}</p> : null}
        </>
      );
    }

    return <p className="compare-empty-message">Create new comparison or select previously saved comparison</p>;
  };

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
        <>
          <p className="compare-row-label">Job Entries</p>
          <section className="compare-row" aria-label="Available offers">
            {offers.map((offer) => {
              const isSelected = draftSelectedOfferIds.includes(offer.id);
              return (
                <div key={offer.id} className="dashboard-card-shell">
                  <article
                    className={`compare-offer-card dashboard-card selectable ${
                      isSelected ? "dashboard-card-selected" : ""
                    }`.trim()}
                    role="button"
                    tabIndex={0}
                    aria-pressed={isSelected}
                    onClick={() => {
                      toggleDraftOfferSelection(offer.id);
                    }}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        toggleDraftOfferSelection(offer.id);
                      }
                    }}
                  >
                    <h2 className="dashboard-card-company">{offer.company_name}</h2>
                  </article>
                </div>
              );
            })}
          </section>
        </>
      ) : null}

      <p className="compare-row-label">Saved Comparisons</p>
      <section className="compare-row compare-saved-row" aria-label="Saved comparisons">
        {comparisons.map((comparison) => {
          const isSelected = comparison.id === activeSavedComparisonId;
          return (
            <div key={comparison.id} className="dashboard-card-shell compare-saved-shell">
              <button
                type="button"
                className="compare-entry-delete-button"
                aria-label={`Delete ${comparisonCardLabel(comparison, offersById)}`}
                onClick={(event) => {
                  event.stopPropagation();
                  void handleDeleteComparisonClick(comparison.id);
                }}
              >
                <span className="compare-entry-delete-label">×</span>
              </button>
              <article
                className={`compare-saved-card dashboard-card selectable ${
                  isSelected ? "dashboard-card-selected" : ""
                }`.trim()}
                role="button"
                tabIndex={0}
                aria-pressed={isSelected}
                onClick={() => {
                  void handleSelectSavedComparison(comparison.id);
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    void handleSelectSavedComparison(comparison.id);
                  }
                }}
              >
                <h2 className="dashboard-card-company">{comparisonCardLabel(comparison, offersById)}</h2>
              </article>
            </div>
          );
        })}
      </section>
    </main>
  );
}
