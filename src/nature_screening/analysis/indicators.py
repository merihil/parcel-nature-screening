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


def get_forest_stand_summary(property_id: str) -> dict:
    """
    Summarize forest stand attributes across all stands intersecting a parcel.

    Uses MAX/BOOL_OR rather than area-weighted aggregation: this reports
    whether the parcel contains *any* stand meeting each condition, not a
    weighted average across its area.
    """

    query = text("""
        SELECT
            MAX(fs.mean_age) AS max_mean_age,
            BOOL_OR(fs.drainage_state = 6) AS has_natural_mire,
            BOOL_OR(fs.development_class = 'ER') AS has_uneven_aged_structure,
            BOOL_OR(fs.special_feature IS NOT NULL) AS has_special_feature
        FROM core.parcels p
        JOIN core.forest_stand_features fs
        ON ST_Intersects(p.geom, fs.geom)
        WHERE p.property_id = :property_id
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
        "max_mean_age": (
            int(result["max_mean_age"]) if result["max_mean_age"] is not None else None
        ),
        "has_natural_mire": bool(result["has_natural_mire"]),
        "has_uneven_aged_structure": bool(result["has_uneven_aged_structure"]),
        "has_special_feature": bool(result["has_special_feature"]),
    }


def get_special_habitat_overlap(property_id: str) -> dict:
    """
    special_habitat_count counts distinct features (rows) touching the
    parcel, but overlap_ha unions their geometries before measuring area
    """

    query = text("""
        SELECT
            COALESCE(overlap.overlap_ha, 0) AS overlap_ha,
            COALESCE(overlap.special_habitat_count, 0) AS special_habitat_count
        FROM core.parcels p
        LEFT JOIN LATERAL (
            SELECT
                ST_Area(ST_Intersection(ST_Union(nf.geom), p.geom)) / 10000.0 AS overlap_ha,
                COUNT(DISTINCT nf.source_identifier) AS special_habitat_count
            FROM core.special_habitat_features nf
            WHERE nf.feature_type = 'special_habitat'
            AND ST_Intersects(nf.geom, p.geom)
        ) overlap ON true
        WHERE p.property_id = :property_id
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
        "special_habitat_overlap_ha": float(result["overlap_ha"] or 0),
        "special_habitat_count": int(result["special_habitat_count"] or 0),
    }


def calculate_indicators(property_id: str) -> dict:
    indicators = {}

    indicators.update(get_natura_overlap(property_id))
    indicators.update(get_nearest_natura_distance(property_id))
    indicators.update(get_forest_stand_summary(property_id))
    indicators.update(get_special_habitat_overlap(property_id))

    return indicators
