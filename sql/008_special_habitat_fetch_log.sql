-- Tracks which parcels have already triggered a special habitat fetch, same
-- pattern as core.forest_stand_fetch_log (sql/005) — coverage tracked per
-- property_id, not by geometric proximity to existing data.
CREATE TABLE IF NOT EXISTS core.special_habitat_fetch_log (
    property_id TEXT PRIMARY KEY,
    fetched_at TIMESTAMP DEFAULT now()
);
