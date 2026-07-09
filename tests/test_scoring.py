from nature_screening.analysis.scoring import score_indicators


def test_natura_overlap_gets_points():
    indicators = {
        "natura_overlap_ha": 1.2,
        "nearest_natura_distance_m": 0,
    }

    result = score_indicators(indicators)

    assert result["score_total"] == 30
    assert result["score_class"] == "low"
    assert len(result["evidence"]) == 1
    assert result["evidence"][0]["indicator"] == "natura_overlap"


def test_natura_distance_gets_points_when_no_overlap():
    indicators = {
        "natura_overlap_ha": 0,
        "nearest_natura_distance_m": 200,
    }

    result = score_indicators(indicators)

    assert result["score_total"] == 15
    assert len(result["evidence"]) == 1
    assert result["evidence"][0]["indicator"] == "natura_distance"


def test_no_double_points_when_parcel_overlaps_natura():
    indicators = {
        "natura_overlap_ha": 1.2,
        "nearest_natura_distance_m": 0,
    }

    result = score_indicators(indicators)

    indicators_in_evidence = [item["indicator"] for item in result["evidence"]]

    assert result["score_total"] == 30
    assert "natura_overlap" in indicators_in_evidence
    assert "natura_distance" not in indicators_in_evidence


def test_far_from_natura_gets_no_points():
    indicators = {
        "natura_overlap_ha": 0,
        "nearest_natura_distance_m": 10000,
    }

    result = score_indicators(indicators)

    assert result["score_total"] == 0
    assert result["score_class"] == "low"
    assert result["evidence"] == []


def test_missing_distance_does_not_crash():
    indicators = {
        "natura_overlap_ha": 0,
        "nearest_natura_distance_m": None,
    }

    result = score_indicators(indicators)

    assert result["score_total"] == 0
    assert result["evidence"] == []
