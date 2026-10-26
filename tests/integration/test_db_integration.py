import geopandas as gpd
import pytest
from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import text

from nature_screening.db.connection import get_engine
from nature_screening.db.queries import get_parcel_geometry
from nature_screening.db.write import upsert_gdf_to_postgis
from nature_screening.geo.aoi import resolve_aoi

pytestmark = pytest.mark.integration

TEST_SQUARE = MultiPolygon(
    [Polygon([(100000, 6700000), (100100, 6700000), (100100, 6700100), (100000, 6700100)])]
)


def test_get_parcel_geometry_returns_none_for_unknown_property_id():
    assert get_parcel_geometry("999-999-9999-9999") is None


def test_get_parcel_geometry_roundtrips_inserted_geometry(clean_test_parcel):
    property_id = clean_test_parcel

    with get_engine().begin() as connection:
        connection.execute(
            text("""
                INSERT INTO core.parcels (property_id, municipality_code, area_m2, source_name, geom)
                VALUES (:property_id, '999', 10000, 'test', ST_GeomFromText(:wkt, 3067))
                """),
            {"property_id": property_id, "wkt": TEST_SQUARE.wkt},
        )

    result = get_parcel_geometry(property_id)

    assert result is not None
    assert result.geom_type == "MultiPolygon"
    assert result.equals(TEST_SQUARE)


def test_upsert_gdf_to_postgis_inserts_then_updates_on_conflict(clean_test_parcel):
    property_id = clean_test_parcel
    gdf = gpd.GeoDataFrame(
        {
            "property_id": [property_id],
            "municipality_code": ["999"],
            "area_m2": [10000.0],
            "source_name": ["test"],
        },
        geometry=[TEST_SQUARE],
        crs="EPSG:3067",
    )

    written = upsert_gdf_to_postgis(gdf, table="parcels", conflict_columns=["property_id"])
    assert written == 1

    with get_engine().connect() as connection:
        row = connection.execute(
            text("SELECT municipality_code FROM core.parcels WHERE property_id = :pid"),
            {"pid": property_id},
        ).one()
    assert row.municipality_code == "999"

    # Same property_id, changed attribute — should update in place, not duplicate.
    gdf.loc[0, "municipality_code"] = "888"
    upsert_gdf_to_postgis(gdf, table="parcels", conflict_columns=["property_id"])

    with get_engine().connect() as connection:
        rows = connection.execute(
            text("SELECT municipality_code FROM core.parcels WHERE property_id = :pid"),
            {"pid": property_id},
        ).all()
    assert len(rows) == 1
    assert rows[0].municipality_code == "888"


def test_resolve_aoi_with_property_id_against_real_row(clean_test_parcel):
    property_id = clean_test_parcel

    with get_engine().begin() as connection:
        connection.execute(
            text("""
                INSERT INTO core.parcels (property_id, municipality_code, area_m2, source_name, geom)
                VALUES (:property_id, '999', 10000, 'test', ST_GeomFromText(:wkt, 3067))
                """),
            {"property_id": property_id, "wkt": TEST_SQUARE.wkt},
        )

    aoi = resolve_aoi(property_id=property_id, buffer_m=50)

    assert aoi.source == "property_id"
    expected_bounds = TEST_SQUARE.buffer(50).bounds
    assert aoi.bbox == pytest.approx(expected_bounds)
