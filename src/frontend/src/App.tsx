import { useEffect, useState } from "react";

import { Navbar } from "./components/Navbar";
import { AddEntryPage } from "./pages/AddEntryPage";
import { DashboardPage } from "./pages/DashboardPage";
import { fetchOffers } from "./services/offersApi";

type NavItem = "Dashboard" | "Add Entry" | "Compare";

export default function App(): JSX.Element {
  const [activeItem, setActiveItem] = useState<NavItem>("Add Entry");

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
      <Navbar activeItem={activeItem} onNavigate={setActiveItem} />
      {activeItem === "Dashboard" ? <DashboardPage /> : null}
      {activeItem === "Add Entry" ? (
        <AddEntryPage
          onOfferSaved={() => {
            setActiveItem("Dashboard");
          }}
        />
      ) : null}
      {activeItem === "Compare" ? (
        <main className="main-panel">
          <h1 className="main-title">Compare</h1>
          <p className="edit-later-note">Stage 7 will complete compare workflows.</p>
        </main>
      ) : null}
    </div>
  );
}
