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
  const [isAddEntryProcessing, setIsAddEntryProcessing] = useState(false);
  const [isCompareProcessing, setIsCompareProcessing] = useState(false);

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

  const processingItems: NavItem[] = [
    ...(isAddEntryProcessing ? (["Add Entry"] as const) : []),
    ...(isCompareProcessing ? (["Compare"] as const) : [])
  ];

  return (
    <div className="app-shell">
      <Navbar
        activeItem={activeItem}
        processingItems={processingItems}
        onNavigate={(item) => {
          if (item === activeItem) {
            return;
          }
          setActiveItem(item);
        }}
      />
      <section className={activeItem === "Dashboard" ? "app-page app-page-visible" : "app-page app-page-hidden"}>
        <DashboardPage
          isActive={activeItem === "Dashboard"}
          onCompareSelected={(selectedOfferIds) => {
            setComparePrefillSelectedOfferIds(selectedOfferIds);
            setActiveItem("Compare");
          }}
        />
      </section>
      <section className={activeItem === "Add Entry" ? "app-page app-page-visible" : "app-page app-page-hidden"}>
        <AddEntryPage
          onProcessingStateChange={setIsAddEntryProcessing}
          onOfferSaved={() => {
            setActiveItem("Dashboard");
          }}
        />
      </section>
      <section className={activeItem === "Compare" ? "app-page app-page-visible" : "app-page app-page-hidden"}>
        <ComparePage
          isActive={activeItem === "Compare"}
          prefillSelectedOfferIds={comparePrefillSelectedOfferIds}
          onPrefillConsumed={() => {
            setComparePrefillSelectedOfferIds([]);
          }}
          onProcessingStateChange={setIsCompareProcessing}
        />
      </section>
    </div>
  );
}
