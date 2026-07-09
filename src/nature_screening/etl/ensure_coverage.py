from sqlalchemy import text

from nature_screening.db.connection import get_engine
from nature_screening.etl.import_forest_stands import (
    SOURCE_NAME,
    import_forest_stand_data_from_wfs,
)
from nature_screening.geo.aoi import DEFAULT_BUFFER_M, resolve_aoi


def has_forest_stand_coverage(bbox: tuple[float, float, float, float]) -> bool:
    minx, miny, maxx, maxy = bbox

    query = text("""
        SELECT EXISTS (
            SELECT 1
            FROM core.forest_stand_features
            WHERE source_name = :source_name
            AND ST_Intersects(geom, ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 3067))
        )
        """)

    engine = get_engine()

    with engine.connect() as connection:
        return bool(
            connection.execute(
                query,
                {
                    "source_name": SOURCE_NAME,
                    "minx": minx,
                    "miny": miny,
                    "maxx": maxx,
                    "maxy": maxy,
                },
            ).scalar()
        )


def ensure_forest_stand_coverage(
    property_id: str,
    buffer_m: float = DEFAULT_BUFFER_M,
) -> None:
    aoi = resolve_aoi(property_id=property_id, buffer_m=buffer_m)

    if has_forest_stand_coverage(aoi.bbox):
        return

    import_forest_stand_data_from_wfs(replace=False, bbox=aoi.bbox)
