import { useEffect, useState } from "react";

import { Navbar } from "./components/Navbar";
import { AddEntryPage } from "./pages/AddEntryPage";
import { ComparePage } from "./pages/ComparePage";
import { DashboardPage } from "./pages/DashboardPage";
import { fetchOffers } from "./services/offersApi";

type NavItem = "Dashboard" | "Add Entry" | "Compare";

export default function App(): JSX.Element {
  const [activeItem, setActiveItem] = useState<NavItem>("Add Entry");
  const [comparePrefillSelectedOfferIds, setComparePrefillSelectedOfferIds] = useState<string[]>([]);
  const [compareHasUnsavedDraft, setCompareHasUnsavedDraft] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void fetchOffers()
      .then((response) => {
        if (cancelled) {
          return;
        }
        setActiveItem(response.offers.length > 0 ? "Dashboard" : "Add Entry");
      })
      .catch(() => {
        if (!cancelled) {
          setActiveItem("Add Entry");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="app-shell">
      <Navbar
        activeItem={activeItem}
        onNavigate={(item) => {
          if (item === activeItem) {
            return;
          }
          if (activeItem === "Compare" && compareHasUnsavedDraft) {
            const shouldDiscard = window.confirm("Discard unsaved generated comparison?");
            if (!shouldDiscard) {
              return;
            }
          }
          setActiveItem(item);
        }}
      />
      {activeItem === "Dashboard" ? (
        <DashboardPage
          onCompareSelected={(selectedOfferIds) => {
            setComparePrefillSelectedOfferIds(selectedOfferIds);
            setActiveItem("Compare");
          }}
        />
      ) : null}
      {activeItem === "Add Entry" ? (
        <AddEntryPage
          onOfferSaved={() => {
            setActiveItem("Dashboard");
          }}
        />
      ) : null}
      {activeItem === "Compare" ? (
        <ComparePage
          prefillSelectedOfferIds={comparePrefillSelectedOfferIds}
          onPrefillConsumed={() => {
            setComparePrefillSelectedOfferIds([]);
          }}
          onUnsavedDraftStateChange={setCompareHasUnsavedDraft}
        />
      ) : null}
    </div>
  );
}
