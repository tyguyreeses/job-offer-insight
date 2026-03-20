import { useEffect, useMemo, useState } from "react";

import type { Offer, OfferInput } from "../types";

type Props = {
  onSubmit: (payload: OfferInput) => Promise<void>;
  editingOffer: Offer | null;
  onCancelEdit: () => void;
  isSubmitting: boolean;
};

type FormState = {
  company: string;
  role: string;
  location: string;
  base_salary: string;
  annual_bonus: string;
  annual_equity: string;
  sign_on_bonus: string;
  col_index: string;
};

const emptyState: FormState = {
  company: "",
  role: "",
  location: "",
  base_salary: "",
  annual_bonus: "",
  annual_equity: "",
  sign_on_bonus: "",
  col_index: "1",
};

function offerToState(offer: Offer): FormState {
  return {
    company: offer.company,
    role: offer.role,
    location: offer.location,
    base_salary: String(offer.base_salary),
    annual_bonus: String(offer.annual_bonus),
    annual_equity: String(offer.annual_equity),
    sign_on_bonus: String(offer.sign_on_bonus),
    col_index: String(offer.col_index),
  };
}

function parseNumber(value: string, fallback: number): number {
  const trimmed = value.trim();
  if (!trimmed) {
    return fallback;
  }
  return Number(trimmed);
}

export function OfferForm({ onSubmit, editingOffer, onCancelEdit, isSubmitting }: Props) {
  const [state, setState] = useState<FormState>(emptyState);

  useEffect(() => {
    if (editingOffer) {
      setState(offerToState(editingOffer));
      return;
    }
    setState(emptyState);
  }, [editingOffer]);

  const isEditMode = Boolean(editingOffer);

  const isValid = useMemo(() => {
    return (
      state.company.trim().length > 0 &&
      state.role.trim().length > 0 &&
      state.location.trim().length > 0 &&
      Number(state.base_salary) >= 0 &&
      Number(state.col_index) > 0
    );
  }, [state]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isValid) {
      return;
    }

    await onSubmit({
      company: state.company.trim(),
      role: state.role.trim(),
      location: state.location.trim(),
      base_salary: parseNumber(state.base_salary, 0),
      annual_bonus: parseNumber(state.annual_bonus, 0),
      annual_equity: parseNumber(state.annual_equity, 0),
      sign_on_bonus: parseNumber(state.sign_on_bonus, 0),
      col_index: parseNumber(state.col_index, 1),
    });

    if (!isEditMode) {
      setState(emptyState);
    }
  }

  return (
    <section className="panel">
      <div className="panel__header">
        <h2>{isEditMode ? "Edit offer" : "Add offer"}</h2>
        {isEditMode ? <button onClick={onCancelEdit}>Cancel</button> : null}
      </div>

      <form className="offer-form" onSubmit={handleSubmit}>
        <label>
          Company
          <input
            value={state.company}
            onChange={(event) => setState((prev) => ({ ...prev, company: event.target.value }))}
            required
          />
        </label>

        <label>
          Role
          <input
            value={state.role}
            onChange={(event) => setState((prev) => ({ ...prev, role: event.target.value }))}
            required
          />
        </label>

        <label>
          Location
          <input
            value={state.location}
            onChange={(event) => setState((prev) => ({ ...prev, location: event.target.value }))}
            required
          />
        </label>

        <label>
          Base salary (USD)
          <input
            type="number"
            min="0"
            value={state.base_salary}
            onChange={(event) => setState((prev) => ({ ...prev, base_salary: event.target.value }))}
            required
          />
        </label>

        <label>
          Annual bonus (USD)
          <input
            type="number"
            min="0"
            value={state.annual_bonus}
            onChange={(event) => setState((prev) => ({ ...prev, annual_bonus: event.target.value }))}
          />
        </label>

        <label>
          Annual equity (USD)
          <input
            type="number"
            min="0"
            value={state.annual_equity}
            onChange={(event) => setState((prev) => ({ ...prev, annual_equity: event.target.value }))}
          />
        </label>

        <label>
          Sign-on bonus (USD)
          <input
            type="number"
            min="0"
            value={state.sign_on_bonus}
            onChange={(event) => setState((prev) => ({ ...prev, sign_on_bonus: event.target.value }))}
          />
        </label>

        <label>
          COL index
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={state.col_index}
            onChange={(event) => setState((prev) => ({ ...prev, col_index: event.target.value }))}
          />
        </label>

        <button type="submit" disabled={!isValid || isSubmitting}>
          {isSubmitting ? "Saving..." : isEditMode ? "Update offer" : "Create offer"}
        </button>
      </form>
    </section>
  );
}
