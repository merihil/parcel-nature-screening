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
- Store all Finnish datasets permanently in PostGIS ahead of time.

**Why this solution**

- Fast spatial queries and joins, independent of external API availability.
- Naturally supports caching previously downloaded data.
- Lets the same architecture scale from a single test municipality to national coverage without
  a redesign

## ADR-002 – Area of Interest (AOI) resolution and on-demand fetch with idempotent writes

**Problem**

The end goal is to screen any cadastral parcel in Finland by property_id, but national-scale
datasets like forest stand polygons (millions of features) are far too large to import
wholesale into PostGIS. Importing "one municipality at a time" by hand doesn't generalize to
"any parcel in Finland" without a rewrite, unless the acquisition pattern is designed for that
from the start.

**Decision**

Use an AOI abstraction that resolves either an explicit bounding box or a
bounding box derived from a parcel's buffered geometry. ETL importers and the API both go through this same resolver. The API calls `ensure_forest_stand_coverage` before running
analysis: if the AOI isn't already covered by previously fetched data, it triggers the same
fetch pipeline the CLI uses, on demand.

Because AOIs for different parcels can overlap, the same source feature can be fetched more
than once. Writes for AOI-scoped data therefore use `upsert_gdf_to_postgis` instead of a plain
append, backed by a unique index on `(source_name, source_identifier)`.

**Alternatives considered**

- Keep the acquisition flow bbox-only, manually run per municipality, and rewrite it later for
  per-parcel use. Rejected because the final and MVP versions would then be different systems
  rather than the same pipeline exercised at different scales.
- Import all forest stand data nationwide up front, same as Natura 2000. Rejected due to
  dataset size.
- Keep plain-append writes and rely on a "do we already have this AOI" check to avoid
  duplicates. Rejected because any partial bbox overlap between two AOI fetches can still
  re-request the same feature; only a uniqueness constraint at the write layer guarantees no
  duplicates regardless of how precise the coverage check is.

**Why this solution**

- The same code path serves both a manually-run single-municipality import and an
  automatic per-parcel fetch triggered by the API.
- Idempotent writes make overlapping fetches safe
- Small, bounded national datasets (Natura 2000) are deliberately exempt from AOI scoping.

**Known limitations, not yet addressed**

- The on-demand fetch runs synchronously inside the API request. The first request for a new
  area can take several seconds to tens of seconds (WFS pagination + write), and a WFS failure
  surfaces as a raw 500.