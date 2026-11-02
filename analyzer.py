import math

K_FACTOR = 24.0

def expected_score(rating, opponent_rating):
    exponent = max(-20.0, min(20.0, (opponent_rating - rating) / 400.0))
    return 1.0 / (1.0 + 10.0 ** exponent)

def analyze_match(record):
    required = {"player_id", "rating_before", "opponent_rating", "result", "uncertainty"}
    missing = required - record.keys()
    if missing:
        raise ValueError("Missing fields: " + ", ".join(sorted(missing)))
    if not isinstance(record["player_id"], str) or not record["player_id"].strip():
        raise ValueError("player_id must be a non-empty string")
    nums = {}
    for key in ("rating_before", "opponent_rating", "uncertainty"):
        value = record[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{key} must be a finite number")
        nums[key] = float(value)
    if not 0 <= nums["uncertainty"] <= 1:
        raise ValueError("uncertainty must be between 0 and 1")
    scores = {"win": 1.0, "draw": 0.5, "loss": 0.0}
    result = record["result"]
    if result not in scores:
        raise ValueError("result must be win, draw, or loss")
    expected = expected_score(nums["rating_before"], nums["opponent_rating"])
    change = round(K_FACTOR * (0.5 + nums["uncertainty"]) * (scores[result] - expected), 2)
    return {
        "player_id": record["player_id"], "result": result,
        "rating_before": nums["rating_before"], "opponent_rating": nums["opponent_rating"],
        "expected_score": round(expected, 4), "actual_score": scores[result],
        "illustrative_change": change, "illustrative_rating_after": round(nums["rating_before"] + change, 2),
        "explanation": f"Illustrative change: {change:+.2f}; based on this documented toy model only.",
        "notice": "Not a real game's ranking formula."
    }

def analyze_records(records):
    if not isinstance(records, list):
        raise ValueError("Input must be a JSON array")
    return {"project": "RankLens", "records_analyzed": len(records),
            "reports": [analyze_match(row) for row in records],
            "notice": "Hypothetical model; not proprietary game data."}
