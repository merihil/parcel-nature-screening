from sqlalchemy import text

from nature_screening.db.connection import get_engine


def get_parcel_by_property_id(property_id: str):

    query = text("""
        SELECT
            property_id,
            municipality_code,
            area_m2,
            ST_AsGeoJSON(geom) AS geometry
        FROM core.parcels
        WHERE property_id = :property_id
        LIMIT 1
        """)

    engine = get_engine()

    with engine.connect() as connection:
        result = connection.execute(query, {"property_id": property_id}).mappings().first()

    if result is None:
        return None

    return dict(result)
