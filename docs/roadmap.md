# Roadmap

## Phase 1 – Local prototype ✅

- PostGIS running locally via Docker
- Parcel lookup
- Natura 2000 overlap analysis
- Distance to nearest protected site
- Scoring from those indicators

---

## Phase 2 – Dynamic data loading

- Load forest stands by BBOX or by parcel ✅
- Cache downloaded forest stands, idempotent on repeated/overlapping fetches ✅
- Automatically fetch missing forest stand data on API request ✅
- Load parcels on demand from MML ✅
- Cache downloaded parcels ✅ 
- Add forest stand indicators to scoring ✅ 
- fix: if `property_id` doesn't exist in MML either, `ensure_parcel_exists` currently lets
  a raw `RuntimeError` surface as a 500 instead of a clean 404.

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
- The current point values are a self-consistent choice, not something derived from a real ecological weighting
  model. Could be thought through more carefully later.

---

## Phase 5 – Frontend


- Simple web UI
- Map view showing the parcel's own geometry alongside whatever it overlaps or is near (Natura
  2000 areas, forest stands)

---

## Phase 6 – Production

- Authentication
- Docker deployment
- Cloud database
- Background workers
