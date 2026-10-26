import pytest
from shapely.geometry import Point

from nature_screening.geo.aoi import resolve_aoi


def test_resolve_aoi_with_bbox():
    bbox = (100.0, 200.0, 300.0, 400.0)

    aoi = resolve_aoi(bbox=bbox)

    assert aoi.bbox == bbox
    assert aoi.source == "bbox"


def test_resolve_aoi_with_property_id(monkeypatch):
    point = Point(500, 1000)
    monkeypatch.setattr("nature_screening.geo.aoi.get_parcel_geometry", lambda property_id: point)

    aoi = resolve_aoi(property_id="091-403-0063-0091", buffer_m=10)

    assert aoi.bbox == point.buffer(10).bounds
    assert aoi.source == "property_id"


def test_resolve_aoi_uses_default_buffer(monkeypatch):
    point = Point(0, 0)
    monkeypatch.setattr("nature_screening.geo.aoi.get_parcel_geometry", lambda property_id: point)

    aoi = resolve_aoi(property_id="091-403-0063-0091")

    assert aoi.bbox == point.buffer(500.0).bounds  # DEFAULT_BUFFER_M


def test_resolve_aoi_rejects_both_bbox_and_property_id():
    with pytest.raises(ValueError):
        resolve_aoi(bbox=(0, 0, 1, 1), property_id="091-403-0063-0091")


def test_resolve_aoi_requires_one_of_bbox_or_property_id():
    with pytest.raises(ValueError):
        resolve_aoi()


def test_resolve_aoi_raises_helpful_error_when_parcel_not_found(monkeypatch):
    monkeypatch.setattr("nature_screening.geo.aoi.get_parcel_geometry", lambda property_id: None)

    with pytest.raises(ValueError, match="091-403-0063-0091"):
        resolve_aoi(property_id="091-403-0063-0091")
