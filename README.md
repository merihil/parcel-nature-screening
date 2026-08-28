# Parcel Nature Screening

A GIS backend that evaluates environmental conservation value for cadastral parcels in Finland by
combining several spatial datasets — Natura 2000 protected areas, forest stand data, and
cadastral parcel boundaries — into a single biodiversity-potential screening result.

Given a parcel's `property_id`, the API returns a preliminary score and the spatial evidence
behind it: Natura 2000 overlap, distance to the nearest protected site, forest stand age,
natural mire, uneven-aged forest structure, and flagged special habitat features. More
indicators planned. It is a learning/portfolio project, not an official conservation assessment
tool.

## Tech stack

Python · GeoPandas · PostGIS · PostgreSQL · SQLAlchemy · FastAPI · WFS APIs (MML, SYKE,
Metsäkeskus) · Docker

## Architecture

```
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
```

Full breakdown of each layer's responsibility: [`docs/architecture.md`](docs/architecture.md).
Why things are structured this way, including tradeoffs considered: [`docs/decisions.md`](docs/decisions.md).

## Getting started

### 1. Prerequisites

- Docker
- Python 3.11+

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env` with your own values — a database password for local use, and API
credentials/endpoints for MML, SYKE and Metsäkeskus (see comments in `.env.example` for where to
request access).

### 3. Start PostGIS

```bash
docker compose up -d
```

This starts PostgreSQL/PostGIS and pgAdmin, and applies `sql/001` through `sql/005` on first
run (fresh database volume only — see below if you're applying a new migration to an existing
database).

### 4. Install the package

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 5. Import some data

Migrations under `docker-entrypoint-initdb.d` only run once, when the database volume is first
created. If your database already existed before a new file was added to `sql/`, apply it by
hand:

```bash
docker compose exec -T db psql -U nature -d naturedb < sql/004_forest_stand_features.sql
docker compose exec -T db psql -U nature -d naturedb < sql/005_forest_stand_fetch_log.sql
```

Import the Natura 2000 dataset (small, always imported in full):

```bash
python -m nature_screening.etl.import_nature_features
```

Parcels and forest stand data don't need a separate manual import — both are fetched
automatically, scoped to the parcel being screened, the first time it's requested through the
API (see [`docs/etl_pipelines.md`](docs/etl_pipelines.md)). You can still import a parcel by
hand if you want:

```bash
python -m nature_screening.etl.import_parcels --property-id 091-403-0063-0091
```

### 6. Run the API

```bash
uvicorn nature_screening.api.main:app --reload
```

Open `http://localhost:8000/docs` for interactive Swagger UI, or:

```bash
curl http://localhost:8000/parcels/091-403-0063-0091/analysis
```

## Project structure

```
src/nature_screening/
    config.py       application settings (pydantic-settings)
    db/              PostGIS connection, reads, writes
    geo/             WFS fetching, geometry normalization, AOI resolution
    etl/             one importer per data source, plus on-demand coverage fetch
    analysis/        indicators and scoring for a given parcel
    api/             FastAPI routes
sql/                 database schema, applied in order
docs/                architecture notes, data sources, ADRs, learning notes, roadmap
tests/
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — layers and module responsibilities
- [`docs/data_sources.md`](docs/data_sources.md) — what each external dataset is and why it's used
- [`docs/etl_pipelines.md`](docs/etl_pipelines.md) — how data is fetched, normalized and stored
- [`docs/decisions.md`](docs/decisions.md) — architecture decision records (ADRs)
- [`docs/learning_notes.md`](docs/learning_notes.md) — informal notes on why things are built this way
- [`docs/roadmap.md`](docs/roadmap.md) — what's done and what's planned

## Disclaimer

This is a preliminary geospatial screening tool. Its output does not replace field surveys,
official conservation assessments, or authority decisions.

## License

MIT — see [`LICENSE`](LICENSE).
