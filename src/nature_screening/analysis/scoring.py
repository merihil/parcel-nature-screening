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

    return {
        "score_total": total_score,
        "score_class": classify_score(total_score),
        "evidence": evidence,
    }
