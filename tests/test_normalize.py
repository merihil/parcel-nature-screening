import geopandas as gpd
from shapely.geometry import GeometryCollection, LineString, MultiPolygon, Point, Polygon

from nature_screening.geo.normalize import (
    ensure_valid_multipolygons,
    force_multipolygon,
    geometry_identifier,
    pick_column,
)

VALID_SQUARE = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])

# Classic self-intersecting "bowtie" — invalid under OGC rules, the shape
# make_valid() is specifically meant to repair.
BOWTIE = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])


def test_geometry_identifier_is_deterministic():
    assert geometry_identifier(VALID_SQUARE) == geometry_identifier(VALID_SQUARE)


def test_geometry_identifier_differs_for_different_geometries():
    other_square = Polygon([(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)])
    assert geometry_identifier(VALID_SQUARE) != geometry_identifier(other_square)


def test_geometry_identifier_is_sha1_hex():
    result = geometry_identifier(VALID_SQUARE)
    assert len(result) == 40
    int(result, 16)  # raises ValueError if not valid hex


def test_pick_column_returns_first_matching_candidate():
    gdf = gpd.GeoDataFrame({"b": [1], "a": [2]}, geometry=[Point(0, 0)])
    assert pick_column(gdf, ["a", "b"]) == "a"


def test_pick_column_returns_none_when_no_candidate_present():
    gdf = gpd.GeoDataFrame({"c": [1]}, geometry=[Point(0, 0)])
    assert pick_column(gdf, ["a", "b"]) is None


def test_force_multipolygon_none_returns_none():
    assert force_multipolygon(None) is None


def test_force_multipolygon_empty_geometry_returns_none():
    assert force_multipolygon(Polygon()) is None


def test_force_multipolygon_wraps_single_polygon():
    result = force_multipolygon(VALID_SQUARE)
    assert isinstance(result, MultiPolygon)
    assert len(result.geoms) == 1


def test_force_multipolygon_passes_through_multipolygon():
    multi = MultiPolygon([VALID_SQUARE])
    result = force_multipolygon(multi)
    assert isinstance(result, MultiPolygon)
    assert result.equals(multi)


def test_force_multipolygon_repairs_self_intersecting_polygon():
    assert not BOWTIE.is_valid

    result = force_multipolygon(BOWTIE)

    assert isinstance(result, MultiPolygon)
    assert result.is_valid


def test_force_multipolygon_keeps_only_polygons_from_geometry_collection():
    collection = GeometryCollection([VALID_SQUARE, LineString([(0, 0), (1, 1)])])

    result = force_multipolygon(collection)

    assert isinstance(result, MultiPolygon)
    assert len(result.geoms) == 1


def test_force_multipolygon_geometry_collection_without_polygons_returns_none():
    collection = GeometryCollection([LineString([(0, 0), (1, 1)])])
    assert force_multipolygon(collection) is None


def test_ensure_valid_multipolygons_drops_none_geometries_and_converts_rest():
    gdf = gpd.GeoDataFrame(
        {"id": [1, 2]},
        geometry=[VALID_SQUARE, Polygon()],  # second is empty -> force_multipolygon -> None
        crs="EPSG:3067",
    )

    result = ensure_valid_multipolygons(gdf)

    assert len(result) == 1
    assert result.iloc[0]["id"] == 1
    assert isinstance(result.iloc[0].geometry, MultiPolygon)
