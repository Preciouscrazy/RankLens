"""Deterministic, hypothetical rating-change model for synthetic match records."""

import math

K_FACTOR = 24.0
REQUIRED = {"player_id", "rating_before", "opponent_rating", "result", "uncertainty"}
ACTUAL_SCORES = {"win": 1.0, "draw": 0.5, "loss": 0.0}


def _finite_number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def expected_score(rating, opponent_rating):
    """Toy logistic expectation; bound exponent safely for extreme finite ratings."""
    own = _finite_number(rating, "rating")
    other = _finite_number(opponent_rating, "opponent_rating")
    # Divide first to avoid overflow when subtracting opposite-sign finite ratings.
    exponent = max(-20.0, min(20.0, (other / 400.0) - (own / 400.0)))
    return 1.0 / (1.0 + 10.0 ** exponent)


def analyze_match(record):
    if not isinstance(record, dict):
        raise ValueError("Each match record must be an object")
    missing = REQUIRED - record.keys()
    if missing:
        raise ValueError("Missing fields: " + ", ".join(sorted(missing)))

    player_id = record["player_id"]
    if not isinstance(player_id, str) or not player_id.strip():
        raise ValueError("player_id must be a non-empty string")
    rating = _finite_number(record["rating_before"], "rating_before")
    opponent = _finite_number(record["opponent_rating"], "opponent_rating")
    uncertainty = _finite_number(record["uncertainty"], "uncertainty")
    if not 0.0 <= uncertainty <= 1.0:
        raise ValueError("uncertainty must be between 0 and 1")

    outcome = record["result"]
    if not isinstance(outcome, str) or outcome not in ACTUAL_SCORES:
        raise ValueError("result must be win, draw, or loss")

    expected = expected_score(rating, opponent)
    actual = ACTUAL_SCORES[outcome]
    change = round(K_FACTOR * (0.5 + uncertainty) * (actual - expected), 2)
    updated = rating + change
    if not math.isfinite(updated):
        raise ValueError("illustrative rating after match must be finite")

    return {
        "player_id": player_id,
        "result": outcome,
        "rating_before": rating,
        "opponent_rating": opponent,
        "expected_score": round(expected, 4),
        "actual_score": actual,
        "illustrative_change": change,
        "illustrative_rating_after": round(updated, 2),
        "explanation": f"Illustrative change: {change:+.2f}; based on this documented toy model only.",
        "notice": "Not a real game's ranking formula.",
    }


def analyze_records(records):
    """Retain input ordering and attribute validation failures to record numbers."""
    if not isinstance(records, list):
        raise ValueError("Input must be a JSON array")
    reports = []
    for index, record in enumerate(records, 1):
        try:
            reports.append(analyze_match(record))
        except ValueError as exc:
            raise ValueError(f"record {index}: {exc}") from exc
    return {
        "project": "RankLens",
        "records_analyzed": len(reports),
        "reports": reports,
        "notice": "Hypothetical model; not proprietary game data.",
    }
