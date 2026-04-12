const NAV_ITEMS = ["Add Entry", "Dashboard", "Compare"] as const;
type NavItem = (typeof NAV_ITEMS)[number];

interface NavbarProps {
  activeItem: NavItem;
  onNavigate: (item: NavItem) => void;
}

export function Navbar({ activeItem, onNavigate }: NavbarProps): JSX.Element {
  return (
    <header className="app-navbar motion-fade-enter" style={{ ["--motion-delay" as string]: "0ms" }}>
      <div className="brand">Job Offer Insight</div>
      <nav aria-label="Main Navigation">
        <ul className="nav-list">
          {NAV_ITEMS.map((item) => (
            <li key={item}>
              <button
                type="button"
                className={item === activeItem ? "nav-link nav-link-active selectable" : "nav-link selectable"}
                onClick={() => onNavigate(item)}
              >
                {item}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
