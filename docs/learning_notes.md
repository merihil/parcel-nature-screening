# Learning Notes

Different questions thought out during the making of the project.

### Why does `geo/normalize.py` exist?

Different data sources return different column names and geometry quirks. Normalizing once,
during ETL, means analysis code never has to special-case the source of the data it's reading.

## Why create small reusable helper modules?
Operations such as downloading WFS data, writing GeoDataFrames to PostGIS and 
validating geometries are needed by many ETL pipelines.
Keeping these in reusable modules avoids duplicated code and makes new import pipelines much simpler to build.

## Why use pagination when reading WFS?
Large WFS services usually limit the number of returned features. Requesting data page by page
avoids request size limits reduces memory spikes works for arbitrarily large datasets.

## Why do MML and WFS pagination look different in the code?
MML's parcel data is ODC API Feature and the other used data uses classic WFS 2.0.0. The OGC API Features have a spec that tells when there's more data and the classic WFS 2.0.0. doesn't have such mechanism. 

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

## Why does `upsert_gdf_to_postgis` write in batches instead of one INSERT?

Found this by actually testing with a large parcel: a single INSERT with every fetched row inlined works fine for a small AOI, but Postgres rejects any statement with more than 65535 bind parameters. A wide table (15 columns here) times a fewthousand rows blows past that easily for a big parcel's buffered area. The fix is chunking the rows into fixed-size batches inside one transaction.