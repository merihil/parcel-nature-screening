import hashlib

import geopandas as gpd
from shapely import make_valid
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry


def geometry_identifier(geometry: BaseGeometry) -> str:
    return hashlib.sha1(geometry.wkb).hexdigest()


def pick_column(
    gdf: gpd.GeoDataFrame,
    candidates: list[str],
) -> str | None:
    for column in candidates:
        if column in gdf.columns:
            return column

    return None


def force_multipolygon(geometry: BaseGeometry | None) -> MultiPolygon | None:
    if geometry is None or geometry.is_empty:
        return None

    valid_geometry = make_valid(geometry)

    if isinstance(valid_geometry, Polygon):
        return MultiPolygon([valid_geometry])

    if isinstance(valid_geometry, MultiPolygon):
        return valid_geometry

    if isinstance(valid_geometry, GeometryCollection):
        polygons = [geom for geom in valid_geometry.geoms if isinstance(geom, Polygon)]

        if not polygons:
            return None

        return MultiPolygon(polygons)

    return None


def ensure_valid_multipolygons(
    gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    cleaned = gdf.copy()
    cleaned["geometry"] = cleaned.geometry.apply(force_multipolygon)
    cleaned = cleaned.dropna(subset=["geometry"])
    return cleaned
