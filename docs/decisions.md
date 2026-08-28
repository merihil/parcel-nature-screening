# Architecture Decision Records

Each entry follows the same three questions: what was the problem, what alternatives were
considered, and why the chosen solution won.

## ADR-001 – PostGIS as the analysis datastore

**Problem**

The application combines data from several external providers (MML, SYKE, Metsäkeskus).
Fetching all datasets directly during every API request would make the application slow and
dependent on external services being up.

**Decision**

Use PostGIS as the application's primary analysis datastore. External APIs are used only during
ETL processes or on-demand when data is missing.

**Alternatives considered**

- Fetch everything directly from source APIs on every request.

**Why this solution**

- Faster spatial queries and joins as some of the data can be fetched in advance.
- Naturally supports caching previously downloaded data.

## ADR-002 – Area of Interest (AOI) resolution and on-demand fetch with idempotent writes

**Problem**

The end goal is to screen any cadastral parcel in Finland by property_id, but national-scale
datasets like forest stand polygons (millions of features) are far too large to import
wholesale into PostGIS.

**Decision**

Use an AOI abstraction that resolves either an explicit bounding box or a
bounding box derived from a parcel's buffered geometry. ETL importers and the API both go through this same resolver. The API calls `ensure_forest_stand_coverage` before running
analysis: if the AOI isn't already covered by previously fetched data, it triggers the same
fetch pipeline the CLI uses, on demand.

Because AOIs for different parcels can overlap, the same source feature can be fetched more
than once. Writes for AOI-scoped data therefore use `upsert_gdf_to_postgis` instead of a plain
append, backed by a unique index on `(source_name, source_identifier)`.

**Alternatives considered**

- Import all forest stand data nationwide up front, same as Natura 2000. Rejected due to
  dataset size.

**Why this solution**

- Makes it possible to use forest stands data even if it's too big to import fully to PostGIS
- Idempotent writes make overlapping fetches safe

**Known limitations, not yet addressed**

- The on-demand fetch runs synchronously inside the API request. The first request for a new
  area can take several seconds to tens of seconds (WFS pagination + write), and a WFS failure
  surfaces as a raw 500.