import geopandas as gpd
import pytest
from shapely.geometry import Point

from nature_screening.etl.import_parcels import (
    find_property_id_column,
    normalize_property_id,
    property_id_to_mml_query_value,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("09140300630091", "091-403-0063-0091"),  # 14 consecutive digits
        ("091-403-0063-0091", "091-403-0063-0091"),  # already formatted
        ("  091-403-0063-0091  ", "091-403-0063-0091"),  # surrounding whitespace
        ("49-441-9-20", "049-441-0009-0020"),  # unpadded, needs zero-padding
        ("91.403.63.91", "091-403-0063-0091"),  # non-dash separators
    ],
)
def test_normalize_property_id_valid_formats(value, expected):
    assert normalize_property_id(value) == expected


def test_normalize_property_id_none_returns_none():
    assert normalize_property_id(None) is None


def test_normalize_property_id_nan_returns_none():
    assert normalize_property_id(float("nan")) is None


@pytest.mark.parametrize(
    "value",
    [
        "not a property id",
        "091-403",  # only two groups
        "091-403-0063-0091-1234",  # five groups, and 18 digits total
        "",
    ],
)
def test_normalize_property_id_invalid_formats_return_none(value):
    assert normalize_property_id(value) is None


def test_normalize_property_id_only_counts_digits_not_structure():
    # The 14-digit branch checks digit count only, so trailing garbage
    # after a valid run is silently ignored rather than rejected.
    assert normalize_property_id("091-403-0063-0091-abc") == "091-403-0063-0091"


def test_property_id_to_mml_query_value_strips_dashes():
    assert property_id_to_mml_query_value("091-403-0063-0091") == "09140300630091"


def test_property_id_to_mml_query_value_raises_for_invalid_id():
    with pytest.raises(ValueError):
        property_id_to_mml_query_value("not a property id")


def test_find_property_id_column_returns_first_candidate_present():
    gdf = gpd.GeoDataFrame(
        {"kiinteistotunnus": ["091-403-0063-0091"], "other": [1]},
        geometry=[Point(0, 0)],
    )
    assert find_property_id_column(gdf) == "kiinteistotunnus"


def test_find_property_id_column_respects_candidate_priority_order():
    # kiinteistotunnuksenEsitysmuoto is earlier in PROPERTY_ID_CANDIDATES
    # than kiinteistotunnus, so it should win when both are present.
    gdf = gpd.GeoDataFrame(
        {
            "kiinteistotunnus": ["091-403-0063-0091"],
            "kiinteistotunnuksenEsitysmuoto": ["091-403-0063-0091"],
        },
        geometry=[Point(0, 0)],
    )
    assert find_property_id_column(gdf) == "kiinteistotunnuksenEsitysmuoto"


def test_find_property_id_column_raises_when_no_candidate_present():
    gdf = gpd.GeoDataFrame({"unrelated": [1]}, geometry=[Point(0, 0)])

    with pytest.raises(RuntimeError):
        find_property_id_column(gdf)
