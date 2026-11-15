"""Deterministic algorithm, validation and golden-evidence regression tests."""

import copy
import json
import math
from pathlib import Path
import unittest

from ranklens.analyzer import analyze_match, analyze_records, expected_score

ROOT = Path(__file__).resolve().parents[1]


def sample(**overrides):
    record = {
        "player_id": "p1", "rating_before": 1400, "opponent_rating": 1600,
        "result": "win", "uncertainty": 0.5,
    }
    record.update(overrides)
    return record


class RankLensTests(unittest.TestCase):
    def test_equal_ratings(self):
        self.assertAlmostEqual(expected_score(1500, 1500), 0.5)

    def test_expected_score_higher_for_stronger_player(self):
        self.assertGreater(expected_score(1600, 1400), 0.5)
        self.assertLess(expected_score(1400, 1600), 0.5)

    def test_expected_score_symmetry(self):
        self.assertAlmostEqual(expected_score(1500, 1700) + expected_score(1700, 1500), 1.0)

    def test_expected_score_monotonicity(self):
        self.assertLess(expected_score(1000, 1500), expected_score(1200, 1500))
        self.assertLess(expected_score(1200, 1500), expected_score(1500, 1500))

    def test_expected_score_extreme_finite_ratings(self):
        self.assertTrue(math.isfinite(expected_score(1e308, -1e308)))
        self.assertTrue(math.isfinite(expected_score(-1e308, 1e308)))
        self.assertGreater(expected_score(1e308, -1e308), 0.99)
        self.assertLess(expected_score(-1e308, 1e308), 0.01)

    def test_expected_score_clamps_large_differences(self):
        self.assertAlmostEqual(expected_score(0, 100000), expected_score(0, 200000))

    def test_expected_score_rejects_non_numeric_and_nonfinite(self):
        for value in (True, None, "1400", [], math.nan, math.inf, -math.inf, 10**400):
            with self.subTest(value=repr(value)[:25]):
                with self.assertRaises(ValueError):
                    expected_score(value, 1500)
                with self.assertRaises(ValueError):
                    expected_score(1500, value)

    def test_win_against_stronger_opponent(self):
        result = analyze_match(sample())
        self.assertGreater(result["illustrative_change"], 0)

    def test_loss_against_weaker_opponent(self):
        result = analyze_match(sample(result="loss", rating_before=1600, opponent_rating=1400))
        self.assertLess(result["illustrative_change"], 0)

    def test_draw_with_equal_ratings_has_zero_change(self):
        result = analyze_match(sample(result="draw", rating_before=1500, opponent_rating=1500))
        self.assertEqual(result["illustrative_change"], 0)
        self.assertEqual(result["illustrative_rating_after"], 1500)

    def test_draw_against_stronger_opponent_gains_rating(self):
        self.assertGreater(analyze_match(sample(result="draw"))["illustrative_change"], 0)

    def test_draw_against_weaker_opponent_loses_rating(self):
        self.assertLess(analyze_match(sample(result="draw", rating_before=1600, opponent_rating=1400))["illustrative_change"], 0)

    def test_uncertainty_changes_update_size(self):
        low = analyze_match(sample(uncertainty=0))["illustrative_change"]
        high = analyze_match(sample(uncertainty=1))["illustrative_change"]
        self.assertGreater(high, low)

    def test_uncertainty_zero_and_one_supported(self):
        for u in (0, 1):
            with self.subTest(u=u):
                self.assertTrue(math.isfinite(analyze_match(sample(uncertainty=u))["illustrative_change"]))

    def test_invalid_uncertainty(self):
        for value in (-0.01, 1.01, math.nan, math.inf, None, "0.5", True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    analyze_match(sample(uncertainty=value))

    def test_invalid_result(self):
        for value in (None, "", "WIN", 1, [], {}, True, "tie"):
            with self.subTest(value=repr(value)):
                with self.assertRaisesRegex(ValueError, "result"):
                    analyze_match(sample(result=value))

    def test_invalid_player_id(self):
        for value in ("", "  ", 12, None, [], False):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    analyze_match(sample(player_id=value))

    def test_invalid_rating_fields(self):
        for field in ("rating_before", "opponent_rating"):
            for value in (math.inf, -math.inf, math.nan, True, None, "100", 10**400):
                with self.subTest(field=field, value=repr(value)[:25]):
                    with self.assertRaises(ValueError):
                        analyze_match(sample(**{field: value}))

    def test_negative_rating_is_finite_and_supported(self):
        result = analyze_match(sample(rating_before=-120, opponent_rating=120))
        self.assertEqual(result["rating_before"], -120)

    def test_missing_required_field(self):
        record = sample()
        del record["opponent_rating"]
        with self.assertRaisesRegex(ValueError, "Missing fields: opponent_rating"):
            analyze_match(record)

    def test_missing_multiple_required_fields_sorted(self):
        with self.assertRaisesRegex(ValueError, "Missing fields: opponent_rating, player_id"):
            analyze_match({"rating_before": 10, "result": "win", "uncertainty": 0.5})

    def test_non_dictionary_record(self):
        for record in (None, [], "record", 4):
            with self.subTest(value=repr(record)):
                with self.assertRaisesRegex(ValueError, "object"):
                    analyze_match(record)

    def test_input_record_not_modified(self):
        record = sample()
        original = copy.deepcopy(record)
        analyze_match(record)
        self.assertEqual(record, original)

    def test_deterministic_repeat(self):
        record = sample()
        self.assertEqual(analyze_match(record), analyze_match(record))

    def test_change_and_updated_rating_consistent(self):
        result = analyze_match(sample())
        self.assertAlmostEqual(result["illustrative_rating_after"],
                               round(result["rating_before"] + result["illustrative_change"], 2))

    def test_reports_have_clear_limitations(self):
        result = analyze_match(sample())
        self.assertIn("toy model", result["explanation"])
        self.assertIn("Not a real game's ranking formula", result["notice"])

    def test_json_serializable_report(self):
        result = analyze_records([sample()])
        json.dumps(result, allow_nan=False)

    def test_analyze_records_requires_list(self):
        for item in ({}, "text", None, (sample(),)):
            with self.subTest(item=repr(item)):
                with self.assertRaisesRegex(ValueError, "JSON array"):
                    analyze_records(item)

    def test_analyze_records_empty_array(self):
        result = analyze_records([])
        self.assertEqual(result["reports"], [])
        self.assertEqual(result["records_analyzed"], 0)

    def test_analyze_records_indexed_error(self):
        with self.assertRaisesRegex(ValueError, "record 2:"):
            analyze_records([sample(), sample(result=[])])

    def test_analyze_records_preserves_order(self):
        result = analyze_records([sample(player_id="z"), sample(player_id="a")])
        self.assertEqual([p["player_id"] for p in result["reports"]], ["z", "a"])

    def test_fixture_golden_json_matches(self):
        records = json.loads((ROOT / "data" / "sample_matches.json").read_text(encoding="utf-8"))
        expected = json.loads((ROOT / "evidence" / "sample-report.json").read_text(encoding="utf-8"))
        self.assertEqual(analyze_records(records), expected)

    def test_fixture_has_three_synthetic_records(self):
        records = json.loads((ROOT / "data" / "sample_matches.json").read_text(encoding="utf-8"))
        self.assertEqual(len(records), 3)

    def test_extreme_rating_report_is_finite(self):
        result = analyze_match(sample(rating_before=1e308, opponent_rating=-1e308))
        self.assertTrue(math.isfinite(result["illustrative_rating_after"]))


if __name__ == "__main__":
    unittest.main()
