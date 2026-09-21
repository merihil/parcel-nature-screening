import json
from pathlib import Path

from sqlalchemy import text

from nature_screening.db.connection import get_engine

# Matches the >5000m cutoff in scoring.score_natura_distance(), beyond which
# proximity to a Natura area no longer earns points.
NATURA_DISTANCE_SCORING_CUTOFF_M = 5000

# Finnish-only label lookup for Metsakeskus's coded fields, extracted from
# their published WFS stand/habitat code list (CC BY 4.0):
# https://www.metsakeskus.fi/sites/default/files/document/avoin-metsatieto-wfs-stand-habitat-koodisto-ja-tietokantakuvaus.xlsx
_CODE_LABELS = json.loads((Path(__file__).parent / "metsakeskus_codes.json").read_text())


def _is_missing_code(code) -> bool:
    # NaN can end up here from rows written before optional_column()'s NaN
    # normalization (see import_forest_stands.py) — treat it as "no value",
    # same as None, rather than a code we just don't have a label for.
    return code is None or (isinstance(code, float) and code != code)


def _code_label(field: str, code) -> str | None:
    if _is_missing_code(code):
        return None

    if isinstance(code, float) and code.is_integer():
        code = int(code)

    return _CODE_LABELS.get(field, {}).get(str(code))


def get_parcel_geometry_geojson(property_id: str) -> dict | None:
    query = text("""
        SELECT ST_AsGeoJSON(ST_Transform(geom, 4326)) AS geometry
        FROM core.parcels
        WHERE property_id = :property_id
        LIMIT 1
        """)

    engine = get_engine()

    with engine.connect() as connection:
        result = connection.execute(query, {"property_id": property_id}).scalar()

    if result is None:
        return None

    return json.loads(result)


def get_natura_features_geojson(property_id: str) -> list[dict]:
    """
    Includes Natura areas within NATURA_DISTANCE_SCORING_CUTOFF_M, not just
    overlapping ones, since score_natura_distance() still awards points for
    proximity alone (see scoring.py). Each feature's "overlaps" property lets
    the frontend distinguish the two cases visually.
    """

    query = text("""
        SELECT
            nf.name,
            nf.feature_subtype,
            ST_Intersects(p.geom, nf.geom) AS overlaps,
            ST_AsGeoJSON(ST_Transform(nf.geom, 4326)) AS geometry
        FROM core.parcels p
        JOIN core.nature_features nf
        ON ST_DWithin(p.geom, nf.geom, :max_distance_m)
        WHERE p.property_id = :property_id
        AND nf.feature_type = 'natura'
        """)

    engine = get_engine()

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {"property_id": property_id, "max_distance_m": NATURA_DISTANCE_SCORING_CUTOFF_M},
        ).mappings().all()

    return [
        {
            "type": "Feature",
            "geometry": json.loads(row["geometry"]),
            "properties": {
                "name": row["name"],
                "subtype": row["feature_subtype"],
                "overlaps": bool(row["overlaps"]),
            },
        }
        for row in rows
    ]


def get_forest_stand_features_geojson(property_id: str) -> list[dict]:
    """
    Only returns stands that individually satisfy one of score_forest_age /
    score_natural_mire / score_uneven_aged_structure / score_special_feature's
    conditions (scoring.py) — a stand below every threshold doesn't explain
    any of the parcel's score, so it's left off the map instead of shown as
    unstyled clutter. age_tier mirrors score_forest_age's own tiers (>100
    vs. 60-100) so the frontend can color old-growth apart from merely
    mature stands.
    """

    query = text("""
        SELECT
            fs.mean_age,
            fs.development_class,
            fs.drainage_state,
            fs.special_feature,
            ST_AsGeoJSON(ST_Transform(fs.geom, 4326)) AS geometry
        FROM core.parcels p
        JOIN core.forest_stand_features fs
        ON ST_Intersects(p.geom, fs.geom)
        WHERE p.property_id = :property_id
        AND (
            fs.mean_age >= 60
            OR fs.drainage_state = 6
            OR fs.development_class = 'ER'
            OR (fs.special_feature IS NOT NULL AND fs.special_feature != 'NaN'::float8)
        )
        """)

    engine = get_engine()

    with engine.connect() as connection:
        rows = connection.execute(query, {"property_id": property_id}).mappings().all()

    def age_tier(mean_age: float | None) -> str | None:
        if mean_age is None:
            return None
        if mean_age > 100:
            return "old"
        if mean_age >= 60:
            return "mid"
        return None

    return [
        {
            "type": "Feature",
            "geometry": json.loads(row["geometry"]),
            "properties": {
                "mean_age": row["mean_age"],
                "age_tier": age_tier(row["mean_age"]),
                "development_class": row["development_class"],
                "development_class_label": _code_label("DEVELOPMENTCLASS", row["development_class"]),
                "is_natural_mire": row["drainage_state"] == 6,
                "has_special_feature": not _is_missing_code(row["special_feature"]),
                "special_feature_label": _code_label("SPECIALFEATURECODE", row["special_feature"]),
            },
        }
        for row in rows
    ]


def get_special_habitat_features_geojson(property_id: str) -> list[dict]:
    """
    special_feature holds the SPECIALFEATURECODE identifying which kind of
    special habitat this is (e.g. "Puro", "Lehto") — translated via
    special_feature_label, this is the human-readable description a map
    popup needs, which the raw code alone doesn't provide.
    """

    query = text("""
        SELECT
            sh.source_identifier,
            sh.special_feature,
            sh.cutting_restriction,
            sh.silviculture_restriction,
            sh.development_class,
            ST_AsGeoJSON(ST_Transform(sh.geom, 4326)) AS geometry
        FROM core.parcels p
        JOIN core.special_habitat_features sh
        ON ST_Intersects(p.geom, sh.geom)
        WHERE p.property_id = :property_id
        AND sh.feature_type = 'special_habitat'
        """)

    engine = get_engine()

    with engine.connect() as connection:
        rows = connection.execute(query, {"property_id": property_id}).mappings().all()

    return [
        {
            "type": "Feature",
            "geometry": json.loads(row["geometry"]),
            "properties": {
                "source_identifier": row["source_identifier"],
                "special_feature_label": _code_label("SPECIALFEATURECODE", row["special_feature"]),
                "cutting_restriction_label": _code_label(
                    "CUTTINGRESTRICTION", row["cutting_restriction"]
                ),
                "silviculture_restriction_label": _code_label(
                    "SILVICULTURERESTRICTION", row["silviculture_restriction"]
                ),
                "development_class_label": _code_label(
                    "DEVELOPMENTCLASS", row["development_class"]
                ),
            },
        }
        for row in rows
    ]


def get_parcel_map_data(property_id: str) -> dict | None:
    parcel = get_parcel_geometry_geojson(property_id)

    if parcel is None:
        return None

    return {
        "parcel": parcel,
        "layers": {
            "natura": get_natura_features_geojson(property_id),
            "forest_stands": get_forest_stand_features_geojson(property_id),
            "special_habitats": get_special_habitat_features_geojson(property_id),
        },
    }
