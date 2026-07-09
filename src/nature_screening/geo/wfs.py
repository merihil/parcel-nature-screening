from typing import Any

import geopandas as gpd
import requests


def fetch_wfs_layer(
    url: str,
    type_name: str,
    target_crs: str = "EPSG:3067",
    output_format: str = "application/json",
    page_size: int = 5000,
    max_pages: int = 100,
    bbox: tuple[float, float, float, float] | None = None,
) -> gpd.GeoDataFrame:
    features = []
    start_index = 0

    for _ in range(max_pages):
        params: dict[str, Any] = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": type_name,
            "outputFormat": output_format,
            "count": page_size,
            "startIndex": start_index,
        }
        if bbox is not None:
            minx, miny, maxx, maxy = bbox
            params["bbox"] = f"{minx},{miny},{maxx},{maxy}," "urn:ogc:def:crs:EPSG::3067"
        response = requests.get(
            url,
            params=params,
            timeout=120,
            headers={"User-Agent": "parcel-nature-screening/0.1"},
        )
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as error:
            print("Response was not JSON.")
            print("Status code:", response.status_code)
            print("Content-Type:", response.headers.get("Content-Type"))
            print("First 1000 characters of response:")
            print(response.text[:1000])
            raise RuntimeError(
                "WFS response was not JSON. Check URL, typename and outputFormat."
            ) from error
        page_features = data.get("features", [])

        if not page_features:
            break

        features.extend(page_features)

        if len(page_features) < page_size:
            break

        start_index += page_size

    if not features:
        return gpd.GeoDataFrame(geometry=[], crs=target_crs)

    gdf = gpd.GeoDataFrame.from_features(features)

    if gdf.crs is None:
        gdf = gdf.set_crs(target_crs, allow_override=True)
    else:
        gdf = gdf.to_crs(target_crs)

    return gdf
