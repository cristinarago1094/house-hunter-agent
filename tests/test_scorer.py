import unittest

from services.scorer import score_listing


class ScorerTest(unittest.TestCase):
    def test_scores_strong_prati_purchase_match(self):
        listing = {
            "title": "Trilocale in Via Germanico",
            "area": "Roma Prati",
            "price_eur": 420000,
            "size_sqm": 78,
            "rooms": 3,
            "floor_level": 4,
        }

        scored = score_listing(listing)

        self.assertGreaterEqual(scored["score"], 80)
        self.assertTrue(scored["matches_preferences"])
        self.assertIn("Roma Prati", scored["score_reasons"])

    def test_rejects_non_trilocale(self):
        scored = score_listing(
            {
                "title": "Quadrilocale in Via Cunfida",
                "area": "Roma Prati",
                "price_eur": 450000,
                "size_sqm": 145,
                "rooms": 4,
                "floor_level": 4,
            }
        )

        self.assertFalse(scored["matches_preferences"])
        self.assertIn("non è trilocale", scored["disqualify_reasons"])

    def test_rejects_small_listing(self):
        scored = score_listing(
            {
                "title": "Trilocale piccolo",
                "area": "Roma Prati",
                "price_eur": 430000,
                "size_sqm": 65,
                "rooms": 3,
                "floor_level": 4,
            }
        )

        self.assertFalse(scored["matches_preferences"])
        self.assertIn("meno di 70 mq", scored["disqualify_reasons"])

    def test_rejects_ground_floor(self):
        scored = score_listing(
            {
                "title": "Trilocale piano terra",
                "area": "Roma Prati",
                "price_eur": 430000,
                "size_sqm": 80,
                "rooms": 3,
                "floor_level": 0,
                "floor_label": "piano terra",
            }
        )

        self.assertFalse(scored["matches_preferences"])
        self.assertIn("piano terra", scored["disqualify_reasons"])

    def test_rejects_low_floor_without_photo_verification(self):
        scored = score_listing(
            {
                "title": "Trilocale al primo piano",
                "area": "Roma Prati",
                "price_eur": 430000,
                "size_sqm": 80,
                "rooms": 3,
                "floor_level": 1,
            }
        )

        self.assertFalse(scored["matches_preferences"])
        self.assertIn("piano basso senza foto luminose verificate", scored["disqualify_reasons"])

    def test_accepts_low_floor_with_bright_photo_verification(self):
        scored = score_listing(
            {
                "title": "Trilocale al secondo piano",
                "area": "Roma Prati",
                "price_eur": 430000,
                "size_sqm": 80,
                "rooms": 3,
                "floor_level": 2,
                "photo_brightness_ok": True,
                "photo_brightness_score": 180,
            }
        )

        self.assertTrue(scored["matches_preferences"])
        self.assertIn("piano basso con foto luminose verificate", scored["score_reasons"])


if __name__ == "__main__":
    unittest.main()
