import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { compareOffers, createOffer, deleteOffer, seedOffers, updateOffer } from "./api";
import { OfferChart } from "./components/OfferChart";
import { OfferForm } from "./components/OfferForm";
import { OfferTable } from "./components/OfferTable";
import type { CompareOffer, Metric, Offer, OfferInput } from "./types";

function App() {
  const queryClient = useQueryClient();
  const [sortBy, setSortBy] = useState<Metric>("total_comp_annual");
  const [editingOffer, setEditingOffer] = useState<Offer | null>(null);

  const compareQuery = useQuery({
    queryKey: ["offers", sortBy],
    queryFn: () => compareOffers(sortBy),
  });

  const createMutation = useMutation({
    mutationFn: (payload: OfferInput) => createOffer(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["offers"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ offerId, payload }: { offerId: number; payload: Partial<OfferInput> }) => updateOffer(offerId, payload),
    onSuccess: () => {
      setEditingOffer(null);
      void queryClient.invalidateQueries({ queryKey: ["offers"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (offerId: number) => deleteOffer(offerId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["offers"] });
    },
  });

  const seedMutation = useMutation({
    mutationFn: () => seedOffers(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["offers"] });
    },
  });

  async function handleSubmit(payload: OfferInput) {
    if (editingOffer) {
      await updateMutation.mutateAsync({ offerId: editingOffer.id, payload });
      return;
    }
    await createMutation.mutateAsync(payload);
  }

  const isBusy = createMutation.isPending || updateMutation.isPending;

  const offers: CompareOffer[] = useMemo(() => compareQuery.data?.offers ?? [], [compareQuery.data]);

  return (
    <main className="layout">
      <header className="hero">
        <div>
          <p className="kicker">Job Offer Insight</p>
          <h1>Compare offers with clarity</h1>
          <p>Track compensation, adjust for cost-of-living, and rank options in one dashboard.</p>
        </div>
        <button onClick={() => seedMutation.mutate()} disabled={seedMutation.isPending}>
          {seedMutation.isPending ? "Seeding..." : "Load sample offers"}
        </button>
      </header>

      {compareQuery.isError ? <p className="error">Could not load offers. Start the backend and refresh.</p> : null}

      <section className="grid">
        <OfferForm
          onSubmit={handleSubmit}
          editingOffer={editingOffer}
          onCancelEdit={() => setEditingOffer(null)}
          isSubmitting={isBusy}
        />
        <OfferChart offers={offers} metric={sortBy} />
      </section>

      <OfferTable
        offers={offers}
        sortBy={sortBy}
        onSortByChange={setSortBy}
        onEdit={(offer) => setEditingOffer(offer)}
        onDelete={(offer) => {
          void deleteMutation.mutateAsync(offer.id);
          if (editingOffer?.id === offer.id) {
            setEditingOffer(null);
          }
        }}
      />
    </main>
  );
}

export default App;
