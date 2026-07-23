import geopandas as gpd
from geoalchemy2.shape import from_shape
from sqlalchemy import MetaData, Table, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from nature_screening.db.connection import get_engine


def write_gdf_to_postgis(
    gdf: gpd.GeoDataFrame,
    table: str,
    schema: str = "core",
    if_exists: str = "append",
) -> None:
    engine = get_engine()

    gdf_to_write = gdf.rename_geometry("geom")

    gdf_to_write.to_postgis(
        name=table,
        schema=schema,
        con=engine,
        if_exists=if_exists,
        index=False,
    )


def upsert_gdf_to_postgis(
    gdf: gpd.GeoDataFrame,
    table: str,
    conflict_columns: list[str],
    schema: str = "core",
    batch_size: int = 500,
) -> int:
    if gdf.empty:
        return 0

    engine = get_engine()
    gdf_to_write = gdf.rename_geometry("geom")
    srid = gdf_to_write.crs.to_epsg()

    attribute_columns = [col for col in gdf_to_write.columns if col != "geom"]
    update_columns = [col for col in attribute_columns + ["geom"] if col not in conflict_columns]

    records = [
        {
            **{col: row[col] for col in attribute_columns},
            "geom": from_shape(row["geom"], srid=srid),
        }
        for _, row in gdf_to_write.iterrows()
    ]

    metadata = MetaData(schema=schema)
    reflected_table = Table(table, metadata, autoload_with=engine)

    # Postgres allows at most 65535 bind parameters per statement. A single
    # INSERT with every row inline can exceed that for large fetches (a wide
    # table times a few thousand rows adds up fast), so this batches instead
    # of sending everything as one statement.
    with engine.begin() as connection:
        for start in range(0, len(records), batch_size):
            batch = records[start : start + batch_size]

            statement = pg_insert(reflected_table).values(batch)
            statement = statement.on_conflict_do_update(
                index_elements=conflict_columns,
                set_={col: getattr(statement.excluded, col) for col in update_columns},
            )

            connection.execute(statement)

    return len(records)


def delete_source_rows(
    table: str,
    source_name: str,
    schema: str = "core",
) -> None:
    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(
            text(f"""
                DELETE FROM {schema}.{table}
                WHERE source_name = :source_name
                """),
            {"source_name": source_name},
        )
