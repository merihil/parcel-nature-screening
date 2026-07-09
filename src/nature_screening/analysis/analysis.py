from nature_screening.analysis.indicators import calculate_indicators
from nature_screening.analysis.parcel_lookup import get_parcel_by_property_id
from nature_screening.analysis.scoring import score_indicators


def analyze_parcel(property_id: str) -> dict | None:
    parcel = get_parcel_by_property_id(property_id)

    if parcel is None:
        return None

    indicators = calculate_indicators(property_id)
    scoring = score_indicators(indicators)

    area_m2 = parcel.get("area_m2") or 0

    return {
        "property_id": parcel["property_id"],
        "parcel": {
            "municipality_code": parcel.get("municipality_code"),
            "area_m2": round(area_m2, 1),
            "area_ha": round(area_m2 / 10000, 3),
        },
        "biodiversity_potential": {
            "score": scoring["score_total"],
            "class": scoring["score_class"],
        },
        "indicators": indicators,
        "evidence": scoring["evidence"],
        "disclaimer": (
            "This is a preliminary geospatial screening result. "
            "It does not replace field surveys, official conservation assessments "
            "or authority decisions."
        ),
    }
