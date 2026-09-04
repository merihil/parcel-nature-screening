from sqlalchemy import text

from nature_screening.db.connection import get_engine
from nature_screening.db.queries import get_parcel_geometry
from nature_screening.etl.import_forest_stands import import_forest_stand_data_from_wfs
from nature_screening.etl.import_parcels import ParcelNotFoundError, import_parcels
from nature_screening.etl.import_special_habitats import import_special_habitat_data_from_wfs
from nature_screening.geo.aoi import DEFAULT_BUFFER_M, resolve_aoi


def ensure_parcel_exists(property_id: str) -> None:
    """
    Fetch the parcel from MML if it isn't already in core.parcels.

    Swallows ParcelNotFoundError deliberately: it just leaves the parcel
    absent, so the caller's existing "parcel not found -> 404" check handles
    it the same way as any other missing parcel. Other exceptions (e.g. a
    real MML API failure) are not caught here and propagate as a 500.
    """

    if get_parcel_geometry(property_id) is not None:
        return

    try:
        import_parcels(property_id=property_id)
    except ParcelNotFoundError:
        return


def has_forest_stand_coverage(property_id: str) -> bool:
    query = text("""
        SELECT EXISTS (
            SELECT 1 FROM core.forest_stand_fetch_log WHERE property_id = :property_id
        )
        """)

    engine = get_engine()

    with engine.connect() as connection:
        return bool(connection.execute(query, {"property_id": property_id}).scalar())


def mark_forest_stand_fetched(property_id: str) -> None:
    query = text("""
        INSERT INTO core.forest_stand_fetch_log (property_id, fetched_at)
        VALUES (:property_id, now())
        ON CONFLICT (property_id) DO UPDATE SET fetched_at = EXCLUDED.fetched_at
        """)

    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(query, {"property_id": property_id})


def ensure_forest_stand_coverage(
    property_id: str,
    buffer_m: float = DEFAULT_BUFFER_M,
) -> None:
    if has_forest_stand_coverage(property_id):
        return

    aoi = resolve_aoi(property_id=property_id, buffer_m=buffer_m)
    import_forest_stand_data_from_wfs(replace=False, bbox=aoi.bbox)
    mark_forest_stand_fetched(property_id)


def has_special_habitat_coverage(property_id: str) -> bool:
    query = text("""
        SELECT EXISTS (
            SELECT 1 FROM core.special_habitat_fetch_log WHERE property_id = :property_id
        )
        """)

    engine = get_engine()

    with engine.connect() as connection:
        return bool(connection.execute(query, {"property_id": property_id}).scalar())


def mark_special_habitat_fetched(property_id: str) -> None:
    query = text("""
        INSERT INTO core.special_habitat_fetch_log (property_id, fetched_at)
        VALUES (:property_id, now())
        ON CONFLICT (property_id) DO UPDATE SET fetched_at = EXCLUDED.fetched_at
        """)

    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(query, {"property_id": property_id})


def ensure_special_habitat_coverage(
    property_id: str,
    buffer_m: float = DEFAULT_BUFFER_M,
) -> None:
    if has_special_habitat_coverage(property_id):
        return

    aoi = resolve_aoi(property_id=property_id, buffer_m=buffer_m)
    import_special_habitat_data_from_wfs(replace=False, bbox=aoi.bbox)
    mark_special_habitat_fetched(property_id)
