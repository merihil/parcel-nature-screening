# ETL Pipelines

How data is fetched, transformed and stored.

The project uses ETL pipelines to fetch external geospatial data, normalize it into a common structure and store it in PostGIS.

## Why ETL is separated from analysis

External APIs and WFS services are not queried during every user request. Analysis always reads
from PostGIS, never from a source API directly. How data gets into PostGIS differs by
dataset size:

- **Small, bounded national datasets** are imported in full, ahead of
  time. They'll be refreshed periodically in Phase 3 of the project.
- **Large datasets** are never imported wholesale. Instead they're fetched per AOI (Area of Interest)
  when they're needed, and the result stays cached in PostGIS for reuse by later requests.

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

Handles external data access, especially paginated WFS requests.

### `geo/normalize.py`

Handles geometry and attribute normalization across differing source schemas.

### `geo/aoi.py`

Resolves an Area of Interest (AOI): either an explicit bounding box, or one derived from buffered
parcel's geometry.

### `etl/cli.py`

Shared argparse helper (`add_aoi_arguments`) so CLI scripts that accept `--bbox`/`--property-id`
don't each redefine the same argument group.

### `db/write.py`

Writes normalized GeoDataFrames into PostGIS

## Current pipelines

### Parcel import (`etl/import_parcels.py`)

Source: MML  
Target table: `core.parcels`

Imports cadastral parcels by bounding box or by property_id, and stores them as
property-level geometries. 

### Natura import (`etl/import_nature_features.py`)

Source: SYKE WFS  
Target table: `core.nature_features`

Imports SAC, SCI and SPA areas and stores them in a shared nature feature table.

### Forest stand import (`etl/import_forest_stands.py`)

Source: Finnish Forest Centre (Metsäkeskus) WFS  
Target table: `core.forest_stand_features`

Imports forest stand polygons and selected attributes relevant for biodiversity screening,
scoped to an AOI.

### Special habitat import (`etl/import_special_habitats.py`)

Source: Finnish Forest Centre (Metsäkeskus) WFS 
Target table: `core.special_habitat_features`

Imports Metsäkeskus's own narrower selection of especially important habitats, scoped to an
AOI. `source_identifier` is derived from the geometry, not a WFS id.

### On-demand coverage (`etl/ensure_coverage.py`)

Called from the API, for both forest stands and special habitats. For each, checks whether a
fetch has already been logged for this specific property_id (`core.forest_stand_fetch_log` /
`core.special_habitat_fetch_log`). If not logged, resolves the AOI for the parcel and triggers
that source's import.