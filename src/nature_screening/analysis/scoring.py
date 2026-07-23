def classify_score(score: float) -> str:
    if score >= 81:
        return "very_high"
    if score >= 61:
        return "high"
    if score >= 31:
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
        }

    return {
        "points": 0,
        "evidence": None,
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
    }


def score_natural_mire(has_natural_mire: bool) -> dict:
    """
    Natural (undrained) mire is a recognized valuable habitat type in
    Finland, distinct from mire that has been ditched for forestry
    (DRAINAGESTATE codes 2, 3, 7, 8, 9), which is not scored here.
    """

    if not has_natural_mire:
        return {
            "points": 0,
            "evidence": None,
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
    }


def score_special_feature(has_special_feature: bool) -> dict:
    """
    SPECIALFEATURECODE flags a stand as having a notable habitat feature
    (e.g. old forest, herb-rich forest types, springs, cliffs) — Metsäkeskus
    has already identified it as biodiversity-relevant.
    """

    if not has_special_feature:
        return {
            "points": 0,
            "evidence": None,
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
    }


def score_indicators(indicators: dict) -> dict:
    total_score = 0
    evidence = []

    natura_overlap_ha = indicators.get("natura_overlap_ha", 0)
    nearest_natura_distance_m = indicators.get("nearest_natura_distance_m")

    # 1) Natura overlap always checked first
    natura_overlap_result = score_natura_overlap(natura_overlap_ha)
    total_score += natura_overlap_result["points"]

    if natura_overlap_result["evidence"] is not None:
        evidence.append(natura_overlap_result["evidence"])

    # 2) Natura distance only if parcel does NOT overlap Natura
    if natura_overlap_ha <= 0:
        natura_distance_result = score_natura_distance(nearest_natura_distance_m)
        total_score += natura_distance_result["points"]

        if natura_distance_result["evidence"] is not None:
            evidence.append(natura_distance_result["evidence"])

    # 3) Forest stand indicators, independent of Natura proximity
    forest_indicator_results = [
        score_forest_age(indicators.get("max_mean_age")),
        score_natural_mire(indicators.get("has_natural_mire", False)),
        score_uneven_aged_structure(indicators.get("has_uneven_aged_structure", False)),
        score_special_feature(indicators.get("has_special_feature", False)),
    ]

    for result in forest_indicator_results:
        total_score += result["points"]

        if result["evidence"] is not None:
            evidence.append(result["evidence"])

    return {
        "score_total": total_score,
        "score_class": classify_score(total_score),
        "evidence": evidence,
    }
