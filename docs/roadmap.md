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
- Clean 404 for a `property_id` that doesn't exist in MML either ✅ 

---

## Phase 3 – Analytical depth

- Bring in more data sources to widen what the screening actually covers

---

## Phase 4 – Frontend


- Simple web UI
- Map view showing the parcel's own geometry alongside whatever it overlaps or is near

---

## Phase 5 – National scale

- Scheduled ETL and automatic data refresh for small, fully-preloaded datasets (Natura 2000,
  and future ones like groundwater areas)
- Metadata for imported datasets
- Cache computed parcel scores.

---

## Phase 6 – Production

- Authentication
- Docker deployment
- Cloud database
- Background workers
