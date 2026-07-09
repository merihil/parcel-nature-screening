# ETL Pipelines

How data is fetched, transformed and stored.

The project uses ETL pipelines to fetch external geospatial data, normalize it into a common structure and store it in PostGIS.

## Why ETL is separated from analysis

External APIs and WFS services are not queried during every user request. Analysis always reads
from PostGIS, never from a source API directly. How data gets into PostGIS differs by
dataset size:

- **Small, bounded national datasets** (currently: Natura 2000) are imported in full, ahead of
  time. They'll be refreshed periodically ->`roadmap.md` Phase 3 ("Scheduled ETL", "Automatic data refresh").
- **Large datasets** (currently: cadastral parcels, forest stands) are never imported wholesale. Instead they're fetched per AOI (bounding box, or a buffered parcel geometry) the first
  time they're needed, and the result stays cached in PostGIS for reuse by later requests. See
  ADR-001 and ADR-002 in `decisions.md`.

Either way, analysis code itself only ever reads PostGIS.

## General ETL flow

1. Fetch data from external API/WFS
2. Convert response into GeoDataFrame
3. Reproject to EPSG:3067
4. Normalize attributes
5. Validate and clean geometries
6. Write to PostGIS
7. Query PostGIS during analysis

## Shared utility modules

### `geo/wfs.py`

Handles external data access, especially paginated WFS `GetFeature` requests.

### `geo/normalize.py`

Handles geometry and attribute normalization across differing source schemas.

### `geo/aoi.py`

Resolves an Area of Interest (AOI): either an explicit bounding box, or one derived from a
parcel's geometry (`property_id`, buffered) already stored in `core.parcels`. Every importer
that needs to scope a fetch to an area goes through this, instead of each script inventing its
own notion of "the area."

### `etl/cli.py`

Shared argparse helper (`add_aoi_arguments`) so CLI scripts that accept `--bbox`/`--property-id`
don't each redefine the same argument group.

### `db/write.py`

Writes normalized GeoDataFrames into PostGIS

## Current pipelines

### Parcel import (`etl/import_parcels.py`)

Source: MML  
Target table: `core.parcels`

Imports cadastral parcels by bounding box or by `property_id`, and stores them as
property-level geometries. Uses a plain write; a fresh import replaces the source's rows.

Currently must be run manually before a parcel can be screened. Unlike forest stands, there's
no on-demand fetch triggered automatically from the API yet — a request for a `property_id`
that isn't already in `core.parcels` returns 404 rather than fetching it from MML. Planned in
`roadmap.md` Phase 2.

### Natura import (`etl/import_nature_features.py`)

Source: SYKE WFS  
Target table: `core.nature_features`

Imports SAC, SCI and SPA areas and stores them in a shared nature feature table. Natura sites
are a small, bounded national dataset, so this pipeline always imports everything.

Currently only run manually, on demand. Periodic automatic refresh is the intended long-term
behavior for this pipeline (`roadmap.md` Phase 3) but isn't implemented yet.

### Forest stand import (`etl/import_forest_stands.py`)

Source: Finnish Forest Centre (Metsäkeskus) WFS  
Target table: `core.forest_stand_features`

Imports forest stand polygons and selected attributes relevant for biodiversity screening,
scoped to an AOI (`--bbox` or `--property-id`). Writes via upsert, since overlapping AOI
fetches (e.g. two nearby parcels) will legitimately re-request some of the same features.

### On-demand coverage (`etl/ensure_coverage.py`)

Not a standalone CLI script, called from the API. `ensure_forest_stand_coverage(property_id)`
resolves the AOI for a parcel, checks whether forest stand data already exists for that area,
and triggers the forest stand import only if it doesn't. This is what lets
`/parcels/{property_id}/analysis` work for a parcel whose area hasn't been imported yet,
without re-fetching data that's already cached.

## Scaling strategy

Two different strategies, chosen by dataset size, not one:

- **Small, bounded national datasets** (Natura 2000) are imported fully into PostGIS, kept fresh
  by periodically re-running the import — a schedule, not a per-request trigger.
- **Large datasets** — cadastral parcels and forest stands — are imported by AOI (bounding box,
  or a buffered parcel geometry) rather than nationwide, and stay cached in PostGIS
  indefinitely once fetched. A request for a new area triggers a fetch; a request for an
  already-covered area is served entirely from PostGIS.

PostGIS therefore plays two roles at once: the full analysis datastore for small datasets, and
a growing cache of previously requested areas for large ones. See ADR-001 and ADR-002 in
`decisions.md` for the reasoning, and `roadmap.md` for what's implemented vs. still planned
(scheduled refresh for small datasets, and result-level score caching for repeat requests, are
both still open).