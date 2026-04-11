ALTER TABLE comparisons ADD COLUMN comparison_mode TEXT NOT NULL DEFAULT 'one_to_one';
ALTER TABLE comparisons ADD COLUMN base_offer_id TEXT NOT NULL DEFAULT '';
