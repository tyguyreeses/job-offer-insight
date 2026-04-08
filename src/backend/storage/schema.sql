CREATE TABLE IF NOT EXISTS offers (
    id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    role_title TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_offers_created_at ON offers (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_offers_company_name ON offers (company_name);

CREATE TABLE IF NOT EXISTS comparisons (
    id TEXT PRIMARY KEY,
    selected_offer_ids_json TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_comparisons_created_at ON comparisons (created_at DESC);
