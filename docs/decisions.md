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

## ADR-003 – Alembic for schema migrations

**Problem**

Schema changes lived as numbered files in `sql/` (001-009), applied either by Postgres's
`docker-entrypoint-initdb.d` on first container start, or by hand with `psql` for databases
that already existed. Nothing tracked which files a given database had already applied and 
keeping an existing database in sync meant remembering and running the right commands from
the README.

**Decision**

Use Alembic to track and apply schema changes. `sql/001` through `sql/009` are squashed into
one baseline revision that applies them in order; future schema changes are new Alembic
revisions. `alembic upgrade head` is now the one command to bring any database up to date, and
it's safe to run again on a database that's already current.

**Alternatives considered**

- A small hand-written migration runner: a script reading `sql/*.sql` in order and tracking
  applied filenames in a table. No new dependency, but a custom tool is less recognizable than
  a standard one, and the project already depends on SQLAlchemy, which Alembic builds on.

**Why this solution**

- No ORM models are used here, but Alembic doesn't require them, migrations run plain SQL,
  same as the old `sql/*.sql` files did.
- `alembic stamp head` marks an existing database current without re-running already-applied
  SQL.
- A standard, widely recognized tool in the Python/SQLAlchemy ecosystem.

**Known limitations, not yet addressed**

- Alembic manages only the base schema (tables, indexes, fetch logs). A planned dbt layer for
  analysis will be a separate tool.