-- Tracks which parcels have already triggered a forest stand fetch, so
-- ensure_forest_stand_coverage can decide per property_id rather than by
-- checking whether *any* geometry happens to intersect the new AOI (which
-- produced false positives for overlapping neighboring parcels — see ADR-002
-- and roadmap.md Phase 2).
CREATE TABLE IF NOT EXISTS core.forest_stand_fetch_log (
    property_id TEXT PRIMARY KEY,
    fetched_at TIMESTAMP DEFAULT now()
);
