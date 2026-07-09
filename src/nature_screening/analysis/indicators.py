from sqlalchemy import text

from nature_screening.db.connection import get_engine


def get_natura_overlap(property_id: str) -> dict:
    query = text("""
        SELECT
            COALESCE(
                SUM(
                    ST_Area(
                        ST_Intersection(p.geom, nf.geom)
                    )
                ) / 10000.0,
                0
            ) AS overlap_ha,
            COUNT(DISTINCT nf.source_identifier) AS natura_site_count
        FROM core.parcels p
        JOIN core.nature_features nf
        ON ST_Intersects(p.geom, nf.geom)
        WHERE p.property_id = :property_id
        AND nf.feature_type = 'natura'
        """)

    engine = get_engine()

    with engine.connect() as connection:
        result = (
            connection.execute(
                query,
                {"property_id": property_id},
            )
            .mappings()
            .first()
        )

    return {
        "natura_overlap_ha": float(result["overlap_ha"] or 0),
        "natura_site_count": int(result["natura_site_count"] or 0),
    }


def get_nearest_natura_distance(property_id: str) -> dict:
    """
    Calculate distance from a parcel to the nearest Natura 2000 area.

    Returns distance in meters.
    If the parcel intersects a Natura area, distance is 0.
    """

    query = text("""
        SELECT
            nf.name,
            nf.feature_subtype,
            ST_Distance(p.geom, nf.geom) AS distance_m
        FROM core.parcels p
        JOIN core.nature_features nf
        ON nf.feature_type = 'natura'
        WHERE p.property_id = :property_id
        ORDER BY p.geom <-> nf.geom
        LIMIT 1
        """)

    engine = get_engine()

    with engine.connect() as connection:
        result = (
            connection.execute(
                query,
                {"property_id": property_id},
            )
            .mappings()
            .first()
        )

    if result is None:
        return {
            "nearest_natura_name": None,
            "nearest_natura_type": None,
            "nearest_natura_distance_m": None,
        }

    return {
        "nearest_natura_name": result["name"],
        "nearest_natura_type": result["feature_subtype"],
        "nearest_natura_distance_m": float(result["distance_m"]),
    }


def calculate_indicators(property_id: str) -> dict:
    indicators = {}

    indicators.update(get_natura_overlap(property_id))
    indicators.update(get_nearest_natura_distance(property_id))

    return indicators
