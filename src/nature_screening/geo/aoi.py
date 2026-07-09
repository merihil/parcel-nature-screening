from dataclasses import dataclass

from nature_screening.db.queries import get_parcel_geometry

Bbox = tuple[float, float, float, float]

DEFAULT_BUFFER_M = 500.0


@dataclass(frozen=True)
class AOI:
    bbox: Bbox
    source: str


def resolve_aoi(
    *,
    bbox: Bbox | None = None,
    property_id: str | None = None,
    buffer_m: float = DEFAULT_BUFFER_M,
) -> AOI:
    if bbox is not None and property_id is not None:
        raise ValueError("Provide only one of bbox or property_id, not both.")

    if bbox is not None:
        return AOI(bbox=bbox, source="bbox")

    if property_id is not None:
        geometry = get_parcel_geometry(property_id)

        if geometry is None:
            raise ValueError(
                f"Parcel {property_id} not found in core.parcels. Import it first, e.g.: "
                f"python -m nature_screening.etl.import_parcels --property-id {property_id}"
            )

        return AOI(bbox=geometry.buffer(buffer_m).bounds, source="property_id")

    raise ValueError("Provide either bbox or property_id.")
