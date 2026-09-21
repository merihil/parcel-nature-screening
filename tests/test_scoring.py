from nature_screening.analysis.scoring import score_indicators


def test_natura_overlap_gets_points():
    indicators = {
        "natura_overlap_ha": 1.2,
        "nearest_natura_distance_m": 0,
    }

    result = score_indicators(indicators)

    assert result["score_total"] == 23.1
    assert result["score_class"] == "low"
    assert len(result["evidence"]) == 1
    assert result["evidence"][0]["indicator"] == "natura_overlap"


def test_natura_distance_gets_points_when_no_overlap():
    indicators = {
        "natura_overlap_ha": 0,
        "nearest_natura_distance_m": 200,
    }

    result = score_indicators(indicators)

    assert result["score_total"] == 11.5
    assert len(result["evidence"]) == 1
    assert result["evidence"][0]["indicator"] == "natura_distance"


def test_no_double_points_when_parcel_overlaps_natura():
    indicators = {
        "natura_overlap_ha": 1.2,
        "nearest_natura_distance_m": 0,
    }

    result = score_indicators(indicators)

    indicators_in_evidence = [item["indicator"] for item in result["evidence"]]

    assert result["score_total"] == 23.1
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


def test_evidence_points_sum_to_score_total():
    indicators = {
        "natura_overlap_ha": 0,
        "nearest_natura_distance_m": 200,
        "max_mean_age": 120,
        "has_natural_mire": True,
        "has_uneven_aged_structure": True,
        "has_special_feature": True,
        "special_habitat_overlap_ha": 6,
        "special_habitat_count": 5,
    }

    result = score_indicators(indicators)

    assert round(sum(item["points"] for item in result["evidence"]), 1) == result["score_total"]


def test_no_points_evidence_explains_unscored_indicators():
    indicators = {
        "natura_overlap_ha": 0,
        "nearest_natura_distance_m": 10000,
    }

    result = score_indicators(indicators)

    no_points_indicators = [item["indicator"] for item in result["no_points_evidence"]]

    assert "natura_distance" in no_points_indicators
    assert "forest_age" in no_points_indicators
    assert "natural_mire" in no_points_indicators
    assert "uneven_aged_structure" in no_points_indicators
    assert "special_feature" in no_points_indicators
    assert "special_habitat_overlap" in no_points_indicators
    assert "special_habitat_diversity" in no_points_indicators
    assert all(item["reason"] for item in result["no_points_evidence"])
