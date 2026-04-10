const NAV_ITEMS = ["Dashboard", "Add Entry", "Compare"];

export function Navbar(): JSX.Element {
  return (
    <header className="app-navbar motion-fade-enter" style={{ ["--motion-delay" as string]: "0ms" }}>
      <div className="brand">Job Offer Insight</div>
      <nav aria-label="Main Navigation">
        <ul className="nav-list">
          {NAV_ITEMS.map((item) => (
            <li key={item}>
              <button
                type="button"
                className={item === "Add Entry" ? "nav-link nav-link-active selectable" : "nav-link selectable"}
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
