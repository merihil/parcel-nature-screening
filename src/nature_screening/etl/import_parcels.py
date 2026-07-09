from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from sqlalchemy import bindparam, text
from sqlalchemy.engine import Engine

from nature_screening.config import settings
from nature_screening.db.connection import get_engine
from nature_screening.geo.normalize import ensure_valid_multipolygons

MML_BASE_URL = (
    "https://avoin-paikkatieto.maanmittauslaitos.fi/" "kiinteisto-avoin/simple-features/v3"
)

COLLECTION = "PalstanSijaintitiedot"
EPSG_3067_URI = "http://www.opengis.net/def/crs/EPSG/0/3067"

SOURCE_NAME = "mml_palstan_sijaintitiedot"

RAW_SCHEMA = "raw"
RAW_TABLE = "mml_parcel_parts"

CORE_SCHEMA = "core"
CORE_TABLE = "parcels"

PROPERTY_ID_CANDIDATES = [
    "kiinteistotunnuksenEsitysmuoto",
    "kiinteistotunnusEsitysmuoto",
    "kiinteistotunnus",
    "kiinteistotunnusNro",
    "rekisteriyksikkotunnus",
]


def get_mml_api_key() -> str:
    if not settings.mml_api_key:
        raise RuntimeError("MML_API_KEY is missing from environment settings.")

    return settings.mml_api_key


def normalize_property_id(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None

    value_str = str(value).strip()
    digits = re.sub(r"\D", "", value_str)

    if len(digits) == 14:
        return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}-{digits[10:14]}"

    parts = re.findall(r"\d+", value_str)

    if len(parts) == 4:
        return (
            f"{parts[0].zfill(3)}-"
            f"{parts[1].zfill(3)}-"
            f"{parts[2].zfill(4)}-"
            f"{parts[3].zfill(4)}"
        )

    return None


def property_id_to_mml_query_value(property_id: str) -> str:
    normalized = normalize_property_id(property_id)

    if normalized is None:
        raise ValueError(f"Invalid property identifier: {property_id}")

    return re.sub(r"\D", "", normalized)


def create_session(api_key: str) -> requests.Session:
    session = requests.Session()
    session.auth = HTTPBasicAuth(api_key, "")
    session.headers.update(
        {
            "Accept": "application/geo+json, application/json",
            "User-Agent": "parcel-nature-screening/0.1",
        }
    )
    return session


def build_items_url() -> str:
    return f"{MML_BASE_URL}/collections/{COLLECTION}/items"


def get_next_link(geojson: dict[str, Any]) -> str | None:
    for link in geojson.get("links", []):
        if link.get("rel") == "next" and link.get("href"):
            return link["href"]

    return None


def fetch_features(
    *,
    bbox: tuple[float, float, float, float] | None = None,
    property_id: str | None = None,
    limit: int = 1000,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    if bbox is None and property_id is None:
        raise ValueError("Provide either bbox or property_id.")

    if bbox is not None and property_id is not None:
        raise ValueError("Provide only bbox or property_id, not both.")

    session = create_session(get_mml_api_key())

    params: dict[str, Any] = {
        "f": "json",
        "crs": EPSG_3067_URI,
        "limit": limit,
    }

    if bbox is not None:
        minx, miny, maxx, maxy = bbox
        params["bbox"] = f"{minx},{miny},{maxx},{maxy}"
        params["bbox-crs"] = EPSG_3067_URI

    if property_id is not None:
        params["kiinteistotunnus"] = property_id_to_mml_query_value(property_id)

    url = build_items_url()
    all_features: list[dict[str, Any]] = []
    page = 1

    while url:
        print(f"Fetching page {page}: {url}")

        response = session.get(
            url,
            params=params if page == 1 else None,
            timeout=timeout_seconds,
        )

        if response.status_code == 401:
            raise RuntimeError("MML API returned 401 Unauthorized.")

        response.raise_for_status()

        data = response.json()
        features = data.get("features", [])

        all_features.extend(features)

        print(f"Fetched {len(features)} features; total {len(all_features)}")

        url = get_next_link(data)
        params = None
        page += 1

    return {
        "type": "FeatureCollection",
        "features": all_features,
    }


def save_raw_geojson(
    feature_collection: dict[str, Any],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(feature_collection, file, ensure_ascii=False)

    print(f"Saved raw GeoJSON to {output_path}")


def feature_collection_to_gdf(
    feature_collection: dict[str, Any],
) -> gpd.GeoDataFrame:
    features = feature_collection.get("features", [])

    if not features:
        raise RuntimeError("No features returned from MML API.")

    gdf = gpd.GeoDataFrame.from_features(features)

    if gdf.empty:
        raise RuntimeError("GeoDataFrame is empty after reading features.")

    return gdf.set_crs("EPSG:3067", allow_override=True)


def find_property_id_column(gdf: gpd.GeoDataFrame) -> str:
    for column in PROPERTY_ID_CANDIDATES:
        if column in gdf.columns:
            return column

    raise RuntimeError(
        "Could not find property id column. " f"Available columns: {list(gdf.columns)}"
    )


def sanitize_for_postgis(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    cleaned = gdf.copy()
    geometry_column = cleaned.geometry.name

    for column in cleaned.columns:
        if column == geometry_column:
            continue

        cleaned[column] = cleaned[column].apply(
            lambda value: (
                json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
            )
        )

    return cleaned


def prepare_core_parcels(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    property_id_column = find_property_id_column(gdf)

    working = gdf.copy()
    working["property_id"] = working[property_id_column].apply(normalize_property_id)
    working = working.dropna(subset=["property_id"])

    if working.empty:
        raise RuntimeError("No features with valid property_id found.")

    working["municipality_code"] = working["property_id"].str.slice(0, 3)
    working["source_name"] = SOURCE_NAME

    working = ensure_valid_multipolygons(working)

    core = working[
        [
            "property_id",
            "municipality_code",
            "source_name",
            "geometry",
        ]
    ].dissolve(
        by="property_id",
        as_index=False,
        aggfunc={
            "municipality_code": "first",
            "source_name": "first",
        },
    )

    core = ensure_valid_multipolygons(core)
    core["area_m2"] = core.geometry.area

    core = core[
        [
            "property_id",
            "municipality_code",
            "area_m2",
            "source_name",
            "geometry",
        ]
    ]

    return gpd.GeoDataFrame(core, geometry="geometry", crs="EPSG:3067")


def write_raw_to_postgis(
    gdf: gpd.GeoDataFrame,
    engine: Engine,
    *,
    replace: bool,
) -> None:
    raw = sanitize_for_postgis(gdf).rename_geometry("geom")

    raw.to_postgis(
        name=RAW_TABLE,
        con=engine,
        schema=RAW_SCHEMA,
        if_exists="replace" if replace else "append",
        index=False,
    )

    print(f"Wrote {len(raw)} rows to {RAW_SCHEMA}.{RAW_TABLE}")


def delete_existing_core_parcels(
    core: gpd.GeoDataFrame,
    engine: Engine,
) -> None:
    property_ids = core["property_id"].dropna().unique().tolist()

    if not property_ids:
        return

    statement = text(f"""
        DELETE FROM {CORE_SCHEMA}.{CORE_TABLE}
        WHERE source_name = :source_name
        AND property_id IN :property_ids
        """).bindparams(bindparam("property_ids", expanding=True))

    with engine.begin() as connection:
        connection.execute(
            statement,
            {
                "source_name": SOURCE_NAME,
                "property_ids": property_ids,
            },
        )


def write_core_to_postgis(
    core: gpd.GeoDataFrame,
    engine: Engine,
) -> None:
    delete_existing_core_parcels(core, engine)

    core_to_write = core.rename_geometry("geom")

    core_to_write.to_postgis(
        name=CORE_TABLE,
        con=engine,
        schema=CORE_SCHEMA,
        if_exists="append",
        index=False,
    )

    print(f"Wrote {len(core_to_write)} rows to {CORE_SCHEMA}.{CORE_TABLE}")


def import_parcels(
    *,
    bbox: tuple[float, float, float, float] | None = None,
    property_id: str | None = None,
    limit: int = 1000,
    replace_raw: bool = False,
    raw_output_path: Path = Path("data/raw/mml_palstan_sijaintitiedot.geojson"),
) -> None:
    feature_collection = fetch_features(
        bbox=bbox,
        property_id=property_id,
        limit=limit,
    )

    save_raw_geojson(feature_collection, raw_output_path)

    gdf = feature_collection_to_gdf(feature_collection)
    core = prepare_core_parcels(gdf)

    engine = get_engine()

    write_raw_to_postgis(gdf, engine, replace=replace_raw)
    write_core_to_postgis(core, engine)

    print("Parcel import completed successfully.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import MML cadastral parcels into PostGIS.")

    input_group = parser.add_mutually_exclusive_group(required=True)

    input_group.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("MINX", "MINY", "MAXX", "MAXY"),
    )

    input_group.add_argument(
        "--property-id",
        type=str,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
    )

    parser.add_argument(
        "--replace-raw",
        action="store_true",
    )

    parser.add_argument(
        "--raw-output-path",
        type=Path,
        default=Path("data/raw/mml_palstan_sijaintitiedot.geojson"),
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    bbox_tuple = tuple(args.bbox) if args.bbox else None

    import_parcels(
        bbox=bbox_tuple,
        property_id=args.property_id,
        limit=args.limit,
        replace_raw=args.replace_raw,
        raw_output_path=args.raw_output_path,
    )
