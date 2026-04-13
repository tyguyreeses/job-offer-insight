import type { CSSProperties } from "react";

const NAV_ITEMS = ["Add Entry", "Dashboard", "Compare"] as const;
type NavItem = (typeof NAV_ITEMS)[number];

interface NavbarProps {
  activeItem: NavItem;
  processingItems?: readonly NavItem[];
  onNavigate: (item: NavItem) => void;
}

function renderProcessingLabel(label: NavItem): JSX.Element {
  return (
    <span className="audio-main-label-processing">
      {label.split("").map((character, index) => (
        <span
          key={`nav-processing-char-${label}-${index}-${character === " " ? "space" : character}`}
          className="processing-label-char"
          style={{ ["--processing-index" as string]: index } as CSSProperties}
        >
          {character}
        </span>
      ))}
    </span>
  );
}

export function Navbar({ activeItem, processingItems = [], onNavigate }: NavbarProps): JSX.Element {
  return (
    <header className="app-navbar motion-fade-enter" style={{ ["--motion-delay" as string]: "0ms" }}>
      <div className="brand">Job Offer Insight</div>
      <nav aria-label="Main Navigation">
        <ul className="nav-list">
          {NAV_ITEMS.map((item) => {
            const isActive = item === activeItem;
            const isProcessing = !isActive && processingItems.includes(item);
            return (
              <li key={item}>
                <button
                  type="button"
                  className={`nav-link selectable ${isActive ? "nav-link-active" : ""} ${
                    isProcessing ? "nav-link-processing" : ""
                  }`.trim()}
                  onClick={() => onNavigate(item)}
                >
                  {isProcessing ? renderProcessingLabel(item) : item}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
    </header>
  );
}
