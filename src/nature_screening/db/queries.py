import json

from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from sqlalchemy import text

from nature_screening.db.connection import get_engine


def get_parcel_geometry(property_id: str) -> BaseGeometry | None:
    query = text("""
        SELECT ST_AsGeoJSON(geom) AS geometry
        FROM core.parcels
        WHERE property_id = :property_id
        LIMIT 1
        """)

    engine = get_engine()

    with engine.connect() as connection:
        result = connection.execute(query, {"property_id": property_id}).scalar()

    if result is None:
        return None

    return shape(json.loads(result))
