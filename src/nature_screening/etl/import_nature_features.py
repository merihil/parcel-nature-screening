import geopandas as gpd
import pandas as pd

from nature_screening.config import settings
from nature_screening.db.write import delete_source_rows, write_gdf_to_postgis
from nature_screening.geo.wfs import fetch_wfs_layer
from nature_screening.geo.normalize import ensure_valid_multipolygons, pick_column

# Importing Natura 2000 features


def normalize_natura_gdf(
    gdf: gpd.GeoDataFrame,
    subtype: str,
) -> gpd.GeoDataFrame:
    name_column = pick_column(
        gdf,
        ["nimisuomi", "NIMISUOMI", "nimi", "name"],
    )

    id_column = pick_column(
        gdf,
        ["naturatunn", "NATURATUNN", "sitecode", "SITECODE"],
    )

    cleaned = gpd.GeoDataFrame(
        {
            "source_name": "syke_natura2000",
            "feature_type": "natura",
            "feature_subtype": subtype,
            "name": gdf[name_column] if name_column else None,
            "legal_status": "Natura 2000",
            "source_identifier": gdf[id_column] if id_column else None,
            "geometry": gdf.geometry,
        },
        geometry="geometry",
        crs="EPSG:3067",
    )

    return ensure_valid_multipolygons(cleaned)


def import_natura_from_wfs(replace: bool = False) -> None:
    wfs_url = settings.syke_natura_wfs_url
    sac_typename = settings.syke_natura_sac_typename
    sci_typename = settings.syke_natura_sci_typename
    spa_typename = settings.syke_natura_spa_typename

    if not wfs_url:
        raise RuntimeError("Missing SYKE_NATURA_WFS_URL in .env")

    layer_configs = [
        ("SAC", sac_typename),
        ("SCI", sci_typename),
        ("SPA", spa_typename),
    ]

    layers = []

    for subtype, type_name in layer_configs:
        if not type_name:
            print(f"Skipping {subtype}: typename missing")
            continue

        print(f"Fetching Natura {subtype}: {type_name}")

        gdf = fetch_wfs_layer(
            url=wfs_url,
            type_name=type_name,
        )

        if gdf.empty:
            print(f"No features returned for {subtype}")
            continue

        layers.append(normalize_natura_gdf(gdf, subtype))

    if not layers:
        raise RuntimeError("No Natura layers were fetched.")

    natura = pd.concat(layers, ignore_index=True)
    natura = gpd.GeoDataFrame(
        natura,
        geometry="geometry",
        crs="EPSG:3067",
    )

    if replace:
        delete_source_rows(
            table="nature_features",
            source_name="syke_natura2000",
            schema="core",
        )

    write_gdf_to_postgis(
        natura,
        table="nature_features",
        schema="core",
        if_exists="append",
    )

    print(f"Imported {len(natura)} Natura features into core.nature_features")


if __name__ == "__main__":
    import_natura_from_wfs(replace=True)
