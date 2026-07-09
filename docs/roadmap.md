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
- Replace the naive coverage check with true extent tracking. `has_forest_stand_coverage` only
  checks whether *any* feature intersects the new AOI, not whether the whole AOI was actually
  fetched — a neighboring parcel's overlapping edge can cause a false "already covered". Fix:
  log each fetch's AOI geometry and check `ST_Covers(union of past AOIs, new AOI)`. Not urgent
  until a forest-stand-based indicator is added to scoring. See ADR-002 in `decisions.md`.
- Load parcels on demand from MML by `property_id` when not already in PostGIS
- Cache downloaded parcels (already partially supported — `import_parcels.py --property-id`
  fetches a single parcel, but isn't yet triggered automatically from the API)

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
- Rework the scoring logic in `analysis/scoring.py` so it reflects a defensible biodiversity
  assessment methodology. Current weights/thresholds are a placeholder, not derived from any
  real domain criteria

---

## Phase 5 – Production

- Authentication
- Docker deployment
- Cloud database
- Background workers
