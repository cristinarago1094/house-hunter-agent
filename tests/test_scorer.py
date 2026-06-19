import unittest

from services.scorer import score_listing


class ScorerTest(unittest.TestCase):
    def test_scores_strong_prati_purchase_match(self):
        listing = {
            "title": "Bilocale in Via Germanico",
            "area": "Roma Prati",
            "price_eur": 420000,
            "size_sqm": 72,
            "rooms": 2,
        }

        scored = score_listing(listing)

        self.assertGreaterEqual(scored["score"], 80)
        self.assertIn("Roma Prati", scored["score_reasons"])


if __name__ == "__main__":
    unittest.main()
