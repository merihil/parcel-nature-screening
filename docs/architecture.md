# Architecture

## Layers

External APIs (MML, SYKE, Metsäkeskus WFS)
        │
        ▼
      ETL            fetch + normalize + write
        │
        ▼
     PostGIS         single spatial datastore, also acts as a cache
        │
        ▼
    Analysis         reads PostGIS, computes indicators
        │
        ▼
     Scoring         turns indicators into a biodiversity-potential score
        │
        ▼
      FastAPI        exposes parcel lookup and analysis over HTTP

## Why these layers are separated

**ETL is separated from analysis.** External WFS/API calls are slow and depend on services
outside this project's control. Analysis code should never make a network call, it only reads
from PostGIS. This is what lets `/parcels/{property_id}/analysis` respond quickly and
consistently, and lets ETL be retried, scheduled or triggered on demand independently of how
analysis is used.

**Normalization is separated from fetching.** Each data source (MML, SYKE, Metsäkeskus) returns
different column names, geometry quirks and encodings. `geo/normalize.py` is the one place that
turns any of them into a consistent shape (valid multipolygons, EPSG:3067) before writing to
PostGIS, so downstream code never has to think about source-specific quirks again.

**Analysis is separated from scoring.** `analysis/indicators.py` computes raw spatial facts
(e.g. Natura 2000 overlap area, distance to nearest protected site). `analysis/scoring.py` turns
those facts into a score and an explanation ("evidence"). Keeping these separate means the
scoring rules can change without touching any spatial-query code, and vice versa.

**The API layer is an adapter** `api/main.py` translates HTTP
requests into calls against `analysis/` and `etl/`.
This keeps the core logic usable outside of HTTP, e.g. directly from the CLI ETL scripts or
from tests.

## Module responsibilities

| Module | Responsibility |
|---|---|
| `config.py` | Application settings (env vars / `.env`), including the database URL. |
| `db/connection.py` | Creates the SQLAlchemy engine. |
| `db/write.py` | Writes GeoDataFrames to PostGIS (plain append, and idempotent upsert). |
| `db/queries.py` | Shared low-level reads used by more than one layer (e.g. parcel geometry lookup). |
| `geo/wfs.py` | Fetches paginated features from a WFS endpoint. |
| `geo/normalize.py` | Reshapes/cleans geometries and picks columns across differing source schemas. |
| `geo/aoi.py` | Resolves an Area of Interest (bbox, or derived from a parcel's buffered geometry). |
| `etl/*.py` | One importer per external data source, plus `ensure_coverage.py` for on-demand fetch. |
| `analysis/*.py` | Reads PostGIS, computes indicators and scores for a given parcel. |
| `api/main.py` | FastAPI routes. |
