# Architecture

## Layers

External APIs -> ETL -> PostGIS -> Analysis -> Scoring -> FastAPI

## Module responsibilities

| Module | Responsibility |
|---|---|
| `config.py` | Application settings (env vars / `.env`), including the database URL. |
| `db/connection.py` | Creates the SQLAlchemy engine. |
| `db/write.py` | Writes GeoDataFrames to PostGIS. |
| `db/queries.py` | Shared low-level reads used by more than one layer (e.g. parcel geometry lookup). |
| `geo/wfs.py` | Fetches paginated features from a WFS endpoint. |
| `geo/normalize.py` | Reshapes/cleans geometries and picks columns across differing source schemas. |
| `geo/aoi.py` | Resolves an Area of Interest (bbox, or derived from a parcel's buffered geometry). |
| `etl/*.py` | One importer per external data source, plus `ensure_coverage.py` for on-demand fetch. |
| `analysis/*.py` | Reads PostGIS, computes indicators and scores for a given parcel. |
| `api/main.py` | FastAPI routes. |
