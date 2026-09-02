# Importing special habitats

import argparse

import geopandas as gpd

from nature_screening.config import settings
from nature_screening.db.write import delete_source_rows, upsert_gdf_to_postgis
from nature_screening.etl.cli import add_aoi_arguments
from nature_screening.geo.aoi import resolve_aoi
from nature_screening.geo.wfs import fetch_wfs_layer
from nature_screening.geo.normalize import ensure_valid_multipolygons, geometry_identifier

SOURCE_NAME = "metsakeskus_special_habitats"


def optional_column(gdf: gpd.GeoDataFrame, column: str):
    if column in gdf.columns:
        return gdf[column]
    return None


def normalize_special_habitat_gdf(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    cleaned = gpd.GeoDataFrame(
        {
            "source_name": SOURCE_NAME,
            "feature_type": "special_habitat",
            "source_identifier": gdf.geometry.apply(geometry_identifier),
            "stand_number": optional_column(gdf, "STANDNUMBER"),
            "special_feature": optional_column(gdf, "SPECIALFEATURECODE"),
            "standclass": optional_column(gdf, "STANDCLASS"),
            "development_class": optional_column(gdf, "DEVELOPMENTCLASS"),
            "mean_age": optional_column(gdf, "MEANAGE"),
            "fertility_class": optional_column(gdf, "FERTILITYCLASS"),
            "drainage_state": optional_column(gdf, "DRAINAGESTATE"),
            "soil_type": optional_column(gdf, "SOILTYPE"),
            "cutting_restriction": optional_column(gdf, "CUTTINGRESTRICTION"),
            "silviculture_restriction": optional_column(gdf, "SILVICULTURERESTRICTION"),
            "cutting_proposal_year": optional_column(gdf, "CUTTINGPROPOSALYEAR"),
            "geometry": gdf.geometry,
        },
        geometry="geometry",
        crs="EPSG:3067",
    )

    return ensure_valid_multipolygons(cleaned)


def import_special_habitat_data_from_wfs(
    replace: bool = False,
    bbox: tuple[float, float, float, float] | None = None,
) -> None:
    wfs_url = settings.special_habitat_wfs
    type_name = settings.special_habitat_typename

    if not wfs_url:
        raise RuntimeError("Missing SPECIAL_HABITAT_WFS in .env")

    print(f"Fetching Special Habitat features from WFS: {wfs_url}")
    print(f"Typename: {type_name}")

    if bbox:
        print(f"BBOX: {bbox}")

    gdf = fetch_wfs_layer(
        url=wfs_url,
        type_name=type_name,
        bbox=bbox,
        page_size=1000,
        max_pages=20,
    )

    if gdf.empty:
        print("No Special habitat features found for this area.")
        return

    special_habitat = normalize_special_habitat_gdf(gdf)

    if replace:
        delete_source_rows(
            table="special_habitat_features",
            source_name=SOURCE_NAME,
            schema="core",
        )

    written = upsert_gdf_to_postgis(
        special_habitat,
        table="special_habitat_features",
        conflict_columns=["source_name", "source_identifier"],
        schema="core",
    )

    print(f"Imported {written} Special Habitat features into core.special_habitat_features")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import Metsakeskus special habitats into PostGIS."
    )

    add_aoi_arguments(parser)

    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing rows for this source before importing.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    aoi = resolve_aoi(
        bbox=tuple(args.bbox) if args.bbox else None,
        property_id=args.property_id,
        buffer_m=args.buffer_m,
    )

    import_special_habitat_data_from_wfs(
        replace=args.replace,
        bbox=aoi.bbox,
    )
