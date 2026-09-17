# Highest raw point total any parcel can reach (all indicators triggered,
# Natura overlap taking the 30-point branch instead of natura_distance):
# 30 + 20 + 15 + 15 + 20 + 20 + 10 = 130. score_indicators() divides by this
# to express score_total on a 0-100 scale.
MAX_RAW_SCORE = 130


def classify_score(score: float) -> str:

    if score >= 80.8:
        return "very_high"
    if score >= 60.8:
        return "high"
    if score >= 30.8:
        return "moderate"
    return "low"


def score_natura_overlap(natura_overlap_ha: float) -> dict:
    if natura_overlap_ha > 0:
        return {
            "points": 30,
            "evidence": {
                "indicator": "natura_overlap",
                "points": 30,
                "reason": "Parcel intersects a Natura 2000 area.",
                "value": round(natura_overlap_ha, 3),
                "unit": "ha",
            },
            "no_points_evidence": None,
        }

    # No "not overlapping" explanation here — score_natura_distance() covers
    # the no-overlap case with a more specific reason (near/far/unknown).
    return {
        "points": 0,
        "evidence": None,
        "no_points_evidence": None,
    }


def score_natura_distance(nearest_natura_distance_m: float | None) -> dict:
    """
    Give points based on distance to the nearest Natura 2000 area.

    Closer Natura areas indicate better ecological connectivity potential.
    """

    if nearest_natura_distance_m is None:
        return {
            "points": 0,
            "evidence": None,
            "no_points_evidence": {
                "indicator": "natura_distance",
                "reason": "Distance to the nearest Natura 2000 area is not known.",
                "value": None,
                "unit": None,
            },
        }

    if nearest_natura_distance_m == 0:
        points = 20
        reason = "Parcel intersects a Natura 2000 area."
    elif nearest_natura_distance_m <= 250:
        points = 15
        reason = "Parcel is very close to a Natura 2000 area."
    elif nearest_natura_distance_m <= 1000:
        points = 8
        reason = "Parcel is within 1 km of a Natura 2000 area."
    elif nearest_natura_distance_m <= 5000:
        points = 3
        reason = "Parcel is within 5 km of a Natura 2000 area."
    else:
        points = 0
        reason = None

    if points == 0:
        return {
            "points": 0,
            "evidence": None,
            "no_points_evidence": {
                "indicator": "natura_distance",
                "reason": "Parcel is more than 5 km from the nearest Natura 2000 area.",
                "value": round(nearest_natura_distance_m, 1),
                "unit": "m",
            },
        }

    return {
        "points": points,
        "evidence": {
            "indicator": "natura_distance",
            "points": points,
            "reason": reason,
            "value": round(nearest_natura_distance_m, 1),
            "unit": "m",
        },
        "no_points_evidence": None,
    }


def score_forest_age(max_mean_age: int | None) -> dict:
    """
    Give points for old forest stands, a well-established biodiversity signal
    (deadwood accumulation, structural complexity).
    """

    if max_mean_age is None:
        return {
            "points": 0,
            "evidence": None,
            "no_points_evidence": {
                "indicator": "forest_age",
                "reason": "Forest stand age data is not available.",
                "value": None,
                "unit": "years",
            },
        }

    if max_mean_age > 100:
        points = 20
        reason = "Parcel contains forest stand(s) older than 100 years."
    elif max_mean_age >= 60:
        points = 10
        reason = "Parcel contains forest stand(s) 60-100 years old."
    else:
        return {
            "points": 0,
            "evidence": None,
            "no_points_evidence": {
                "indicator": "forest_age",
                "reason": "No forest stand on the parcel is 60 years or older.",
                "value": max_mean_age,
                "unit": "years",
            },
        }

    return {
        "points": points,
        "evidence": {
            "indicator": "forest_age",
            "points": points,
            "reason": reason,
            "value": max_mean_age,
            "unit": "years",
        },
        "no_points_evidence": None,
    }


def score_natural_mire(has_natural_mire: bool) -> dict:

    if not has_natural_mire:
        return {
            "points": 0,
            "evidence": None,
            "no_points_evidence": {
                "indicator": "natural_mire",
                "reason": "No undrained natural mire (Luonnontilainen suo) found on parcel.",
                "value": False,
                "unit": None,
            },
        }

    return {
        "points": 15,
        "evidence": {
            "indicator": "natural_mire",
            "points": 15,
            "reason": "Parcel contains an undrained natural mire (Luonnontilainen suo).",
            "value": True,
            "unit": None,
        },
        "no_points_evidence": None,
    }


def score_uneven_aged_structure(has_uneven_aged_structure: bool) -> dict:
    """
    Uneven-aged (continuous-cover) stand structure indicates greater
    structural diversity than even-aged rotation forestry.
    """

    if not has_uneven_aged_structure:
        return {
            "points": 0,
            "evidence": None,
            "no_points_evidence": {
                "indicator": "uneven_aged_structure",
                "reason": (
                    "No uneven-aged (continuous-cover) stand structure "
                    "(Eri-ikäisrakenteinen metsikkö) found on parcel."
                ),
                "value": False,
                "unit": None,
            },
        }

    return {
        "points": 15,
        "evidence": {
            "indicator": "uneven_aged_structure",
            "points": 15,
            "reason": "Parcel contains an uneven-aged stand (Eri-ikäisrakenteinen metsikkö).",
            "value": True,
            "unit": None,
        },
        "no_points_evidence": None,
    }


def score_special_feature(has_special_feature: bool) -> dict:

    if not has_special_feature:
        return {
            "points": 0,
            "evidence": None,
            "no_points_evidence": {
                "indicator": "special_feature",
                "reason": "No flagged special habitat feature found on parcel's forest stands.",
                "value": False,
                "unit": None,
            },
        }

    return {
        "points": 20,
        "evidence": {
            "indicator": "special_feature",
            "points": 20,
            "reason": "Parcel contains a stand with a flagged special habitat feature.",
            "value": True,
            "unit": None,
        },
        "no_points_evidence": None,
    }


def score_special_habitat_overlap(special_habitat_overlap_ha: float) -> dict:
    """
    Tiered by overlap area —> more overlap gives more points.
    """

    if special_habitat_overlap_ha > 5:
        points = 20
        reason = "Parcel has substantial special habitat overlap (over 5 ha)."
    elif special_habitat_overlap_ha > 1:
        points = 12
        reason = "Parcel has notable special habitat overlap (over 1 ha)."
    elif special_habitat_overlap_ha > 0.01:
        points = 5
        reason = "Parcel has minor special habitat overlap."
    else:
        return {
            "points": 0,
            "evidence": None,
            "no_points_evidence": {
                "indicator": "special_habitat_overlap",
                "reason": "No special habitat overlap found on parcel.",
                "value": round(special_habitat_overlap_ha, 3),
                "unit": "ha",
            },
        }

    return {
        "points": points,
        "evidence": {
            "indicator": "special_habitat_overlap",
            "points": points,
            "reason": reason,
            "value": round(special_habitat_overlap_ha, 3),
            "unit": "ha",
        },
        "no_points_evidence": None,
    }


def score_special_habitat_diversity(special_habitat_count: int) -> dict:
    """
    Bonus for touching many distinct special habitat features, not just a
    single large one — additive on top of score_special_habitat_overlap,
    since area and diversity are different signals.
    """

    if special_habitat_count < 5:
        return {
            "points": 0,
            "evidence": None,
            "no_points_evidence": {
                "indicator": "special_habitat_diversity",
                "reason": (
                    f"Parcel touches fewer than 5 distinct special habitat areas "
                    f"({special_habitat_count} found)."
                ),
                "value": special_habitat_count,
                "unit": "areas",
            },
        }

    return {
        "points": 10,
        "evidence": {
            "indicator": "special_habitat_diversity",
            "points": 10,
            "reason": f"Parcel touches {special_habitat_count} separate special habitat areas.",
            "value": special_habitat_count,
            "unit": "areas",
        },
        "no_points_evidence": None,
    }


def score_indicators(indicators: dict) -> dict:
    total_score = 0
    evidence = []
    no_points_evidence = []

    def record(result: dict) -> None:
        total_score_delta = result["points"]
        nonlocal total_score
        total_score += total_score_delta

        if result["evidence"] is not None:
            evidence.append(result["evidence"])
        if result["no_points_evidence"] is not None:
            no_points_evidence.append(result["no_points_evidence"])

    natura_overlap_ha = indicators.get("natura_overlap_ha", 0)
    nearest_natura_distance_m = indicators.get("nearest_natura_distance_m")

    # 1) Natura overlap always checked first
    record(score_natura_overlap(natura_overlap_ha))

    # 2) Natura distance only if parcel does NOT overlap Natura
    if natura_overlap_ha <= 0:
        record(score_natura_distance(nearest_natura_distance_m))

    # 3) Forest stand indicators, independent of Natura proximity
    for result in [
        score_forest_age(indicators.get("max_mean_age")),
        score_natural_mire(indicators.get("has_natural_mire", False)),
        score_uneven_aged_structure(indicators.get("has_uneven_aged_structure", False)),
        score_special_feature(indicators.get("has_special_feature", False)),
    ]:
        record(result)

    # 4) Special habitat indicators, independent of everything else
    for result in [
        score_special_habitat_overlap(indicators.get("special_habitat_overlap_ha", 0)),
        score_special_habitat_diversity(indicators.get("special_habitat_count", 0)),
    ]:
        record(result)

    scaled_score = round(total_score / MAX_RAW_SCORE * 100, 1)

    return {
        "score_total": scaled_score,
        "score_class": classify_score(scaled_score),
        "evidence": evidence,
        "no_points_evidence": no_points_evidence,
    }
