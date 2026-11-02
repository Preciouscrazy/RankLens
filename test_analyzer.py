import unittest
from ranklens.analyzer import analyze_match, expected_score

class Tests(unittest.TestCase):
    def test_equal_ratings(self): self.assertAlmostEqual(expected_score(1500, 1500), 0.5)
    def test_win_against_stronger_opponent(self):
        r = analyze_match({"player_id":"p","rating_before":1400,"opponent_rating":1600,"result":"win","uncertainty":0.5})
        self.assertGreater(r["illustrative_change"], 0)
    def test_invalid_uncertainty(self):
        with self.assertRaises(ValueError):
            analyze_match({"player_id":"p","rating_before":1,"opponent_rating":1,"result":"win","uncertainty":2})
if __name__ == "__main__": unittest.main()
