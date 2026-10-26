import pytest

from nature_screening.geo.wfs import fetch_wfs_layer


def _feature(x: float, y: float) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [x, y]},
        "properties": {"name": f"point-{x}-{y}"},
    }


class FakeResponse:
    def __init__(self, payload=None, *, not_json=False, status_code=200):
        self._payload = payload
        self._not_json = not_json
        self.status_code = status_code
        self.headers = {"Content-Type": "application/json"}
        self.text = "" if not not_json else "<html>not json</html>"

    def raise_for_status(self):
        pass

    def json(self):
        if self._not_json:
            raise ValueError("not JSON")
        return self._payload


def test_fetch_wfs_layer_single_page(monkeypatch):
    calls = []

    def fake_get(url, params, timeout, headers):
        calls.append(params)
        return FakeResponse({"features": [_feature(1, 2), _feature(3, 4)]})

    monkeypatch.setattr("nature_screening.geo.wfs.requests.get", fake_get)

    gdf = fetch_wfs_layer("https://example.com/wfs", "ns:layer", page_size=10)

    assert len(gdf) == 2
    assert gdf.crs.to_epsg() == 3067
    assert len(calls) == 1


def test_fetch_wfs_layer_paginates_until_short_page(monkeypatch):
    pages = [
        {"features": [_feature(i, i) for i in range(5)]},  # full page -> fetch more
        {"features": [_feature(5, 5)]},  # short page -> stop
    ]
    calls = []

    def fake_get(url, params, timeout, headers):
        calls.append(params["startIndex"])
        return FakeResponse(pages[len(calls) - 1])

    monkeypatch.setattr("nature_screening.geo.wfs.requests.get", fake_get)

    gdf = fetch_wfs_layer("https://example.com/wfs", "ns:layer", page_size=5)

    assert len(gdf) == 6
    assert calls == [0, 5]


def test_fetch_wfs_layer_empty_response_returns_empty_gdf(monkeypatch):
    def fake_get(url, params, timeout, headers):
        return FakeResponse({"features": []})

    monkeypatch.setattr("nature_screening.geo.wfs.requests.get", fake_get)

    gdf = fetch_wfs_layer("https://example.com/wfs", "ns:layer")

    assert gdf.empty
    assert gdf.crs.to_epsg() == 3067


def test_fetch_wfs_layer_raises_on_non_json_response(monkeypatch):
    def fake_get(url, params, timeout, headers):
        return FakeResponse(not_json=True)

    monkeypatch.setattr("nature_screening.geo.wfs.requests.get", fake_get)

    with pytest.raises(RuntimeError):
        fetch_wfs_layer("https://example.com/wfs", "ns:layer")


def test_fetch_wfs_layer_includes_bbox_param_when_given(monkeypatch):
    captured = {}

    def fake_get(url, params, timeout, headers):
        captured.update(params)
        return FakeResponse({"features": []})

    monkeypatch.setattr("nature_screening.geo.wfs.requests.get", fake_get)

    fetch_wfs_layer("https://example.com/wfs", "ns:layer", bbox=(1.0, 2.0, 3.0, 4.0))

    assert captured["bbox"] == "1.0,2.0,3.0,4.0,urn:ogc:def:crs:EPSG::3067"


def test_fetch_wfs_layer_omits_bbox_param_when_not_given(monkeypatch):
    captured = {}

    def fake_get(url, params, timeout, headers):
        captured.update(params)
        return FakeResponse({"features": []})

    monkeypatch.setattr("nature_screening.geo.wfs.requests.get", fake_get)

    fetch_wfs_layer("https://example.com/wfs", "ns:layer")

    assert "bbox" not in captured
