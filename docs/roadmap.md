# Roadmap

## Phase 1 – Local prototype ✅

- PostGIS running locally via Docker, schema defined in `sql/`
- Parcel lookup by `property_id` (`analysis/parcel_lookup.py`, `GET /parcels/{property_id}`)
- Natura 2000 overlap analysis (`get_natura_overlap`)
- Distance to nearest protected site (`get_nearest_natura_distance`)
- Scoring from those indicators, exposed via `GET /parcels/{property_id}/analysis`

---

## Phase 2 – Dynamic data loading

- Load forest stands by BBOX or by parcel (AOI resolution, `geo/aoi.py`) ✅
- Cache downloaded forest stands, idempotent on repeated/overlapping fetches ✅
- Automatically fetch missing forest stand data on API request (`ensure_forest_stand_coverage`) ✅
- Fixed the naive coverage check ✅ — `has_forest_stand_coverage` used to check whether *any*
  feature intersected the new AOI's bbox, which a neighboring parcel's overlapping edge could
  satisfy without the whole AOI actually being fetched. Replaced with a per-`property_id` log
  (`core.forest_stand_fetch_log`): coverage is now tracked per parcel, not by geometric
  proximity, so there's no way for a neighbor's leftover data to produce a false "already
  covered". Trade-off: overlapping neighboring parcels each trigger their own fetch rather than
  reusing a neighbor's, but idempotent upserts mean this costs an extra WFS call, not duplicate
  rows. See ADR-002 in `decisions.md`.
- Load parcels on demand from MML by `property_id` when not already in PostGIS ✅
  (`ensure_parcel_exists`, called from `GET /parcels/{property_id}/analysis`)
- Cache downloaded parcels ✅ — stored permanently once fetched, no TTL (parcel boundaries
  change rarely and there's no change-notification from MML, so a TTL would just cause
  needless re-fetching)
- Known gap: if `property_id` doesn't exist in MML either, `ensure_parcel_exists` currently lets
  a raw `RuntimeError` surface as a 500 instead of a clean 404. Not fixed yet because the same
  error type is also raised for real failures (e.g. an expired `MML_API_KEY`) — needs a
  dedicated "not found" exception in `import_parcels.py` before the API can safely tell the two
  cases apart.

---

## Phase 3 – National scale

- Scheduled ETL and automatic data refresh for small, fully-preloaded datasets (Natura 2000,
  and future ones like groundwater areas)
- Metadata for imported datasets
- Cache computed parcel scores.

---

## Phase 4 – Analytical depth

- Bring in more data sources (e.g. groundwater areas, protected habitats) to widen what the
  screening actually covers
- Forest stand indicators added to scoring ✅ — forest age, natural (undrained) mire, uneven-aged
  structure, and flagged special habitat features, based on the official Metsäkeskus
  `avoin-metsatieto-wfs-stand-habitat` codebook (not guessed). See `analysis/indicators.py`
  (`get_forest_stand_summary`) and `analysis/scoring.py`.
- Still a placeholder in one sense: the exact point values (20/15/15/20 etc.) are a reasonable,
  internally-consistent design choice, not derived from a scientific weighting methodology.
  Natura scoring's point values (30/20/15/8/3) have the same caveat. Revisit if this needs to
  hold up to actual ecological scrutiny rather than serve as a portfolio-quality demonstration.

---

## Phase 5 – Production

- Authentication
- Docker deployment
- Cloud database
- Background workers
