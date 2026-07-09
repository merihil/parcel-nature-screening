# Learning Notes

Different questions thought out during the making of the project.

### Why does `geo/normalize.py` exist?

Different data sources return different column names and geometry quirks. Normalizing once,
during ETL, means analysis code never has to special-case the source of the data it's reading.

### Why PostGIS instead of querying source APIs directly?

PostGIS is the analysis datastore and makes spatial queries fast. External APIs are only used to
fetch or refresh data, not on every analysis request.

## Why create small reusable helper modules?
Operations such as downloading WFS data writing GeoDataFrames to PostGIS
validating geometries are needed by many ETL pipelines.
Keeping these in reusable modules avoids duplicated code and makes new import pipelines much simpler to build.

## Why use pagination when reading WFS?
Large WFS services usually limit the number of returned features. Requesting data page by page
avoids request size limits reduces memory spikes works for arbitrarily large datasets.

## Why use environment variables?
External configuration should not be hardcoded. Using .env files allows the application to run in different environments (local development, Docker, production) without changing the source code.
Sensitive information such as API keys and passwords also stays outside version control.

## Why SQLAlchemy instead of opening database connections everywhere?
The project has a single place responsible for creating database connections.
If the connection settings ever change, only one file needs to be modified.

## Why convert polygons to multipolygons?
Different datasets may represent areas as either Polygon or MultiPolygon.
Using a single geometry type throughout the database makes later processing much simpler.

## Why separate configuration from code?
Configuration changes much more frequently than application logic.
Database credentials, API endpoints and typenames belong in configuration, allowing code to stay unchanged across environments.

### Why does an Area of Interest (AOI) concept exist, instead of every importer just taking a bbox?

I wanted an alternative to typing raw bbox coordinates by hand. A bbox is
still the right thing to send to a WFS server underneath, but it's a poor way for a human (or
the API) to say "the area around this parcel." So `geo/aoi.py` resolves either an explicit bbox
or one derived from a parcel's buffered geometry, and every caller (CLI scripts and the API)
goes through the same resolver instead of each one inventing its own notion of "the area."