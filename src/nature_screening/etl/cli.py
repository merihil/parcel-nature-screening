import argparse


def add_aoi_arguments(parser: argparse.ArgumentParser) -> None:
    aoi_group = parser.add_mutually_exclusive_group(required=True)

    aoi_group.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("MINX", "MINY", "MAXX", "MAXY"),
        help="Bounding box in EPSG:3067 to limit the download.",
    )

    aoi_group.add_argument(
        "--property-id",
        type=str,
        help=(
            "Cadastral property id already present in core.parcels. "
            "The AOI is derived from its geometry, buffered by --buffer-m."
        ),
    )

    parser.add_argument(
        "--buffer-m",
        type=float,
        default=500.0,
        help="Buffer distance in meters applied around --property-id geometry.",
    )
