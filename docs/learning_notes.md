# Learning Notes

Different questions thought out during the making of the project.

## How did I actually use Claude Code on this project and what did I learn about using it well?

When I started this project, my real goal was to learn how programs like this get built.
How databases work and how they're used, how geospatial data connects to software
development, and everything around that. I started building it with Claude Code, because
that seems to be how a lot of coding gets done today, and I also wanted to learn how to
use it well. My end goal was to become a convincing developer and actually get hired into
the field.

So I built the project with AI's help, and it let me quickly get the architecture, the
database, the first data imports, normalization, and scoring up and running. I even built
the API with AI's help.

At some point, though, I realized that even though I'd been trying to understand
everything I'd built with AI (asking it to explain step by step what it was about to do,
then explain afterward what it did and why, and asking for deeper explanations whenever
something didn't click). I still didn't fully understand the code I'd written. I didn't
know everything my project actually contained, or exactly how every part worked. My goal,
though, was to understand how these things are done, not just to end up with a good-looking
project.

So I decided to stop. I went back to the question that had gotten me started in the first
place. As I said, I wanted to learn these things and, alongside that, produce something
that would let me show I'd learned them. That's genuinely hard these days since having
an impressive-looking project on GitHub doesn't necessarily mean I actually know any of
what's in it. What matters most to me is that I myself know I understand what's in my own
project.

So I changed how I worked. Before continuing development, I went through my code piece by
piece and tried to understand what it actually contained. That's easier said than done. 
Once code is already written, fully understanding every part of it after the
fact is harder. I used AI to help identify the parts I didn't fully understand, tried to
explain them myself first, and let AI fill in what I couldn't. Once I felt like I'd
actually gotten a solid grip on my own project, I kept going.

But I also changed my development style: instead of trying to move fast, I did more
things myself, because I believe that's how I learn to understand existing code better
too. And even when I didn't write a piece entirely myself, I did it more slowly together
with AI, so I'd actually think it through myself (what was being done, why, what it
changed in the code, and what problems it could introduce). I started using AI more as a
thinking partner than as a developer doing the work directly.

I'm not claiming AI wasn't used heavily in this project. But I do think knowing
how to use AI well is a real, valuable skill today. If the actual goal is to learn,
though, it's very easy to get dazzled by AI and produce a lot of impressive-looking
things without learning much along the way, which is exactly why I wanted to call this
out as an important lesson and write it here out in the open in Learning notes.

I don't think my goal was ever to avoid AI. It was to make sure I could explain, defend,
and, if I had to, rebuild every part of this project myself. That matters to me because I
want to actually know these things, not just look like I do on paper.

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