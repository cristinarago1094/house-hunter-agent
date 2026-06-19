import unittest

from services.change_detector import detect_change


class ChangeDetectorTest(unittest.TestCase):
    def test_marks_new_listing_when_not_in_database(self):
        listing = {"source": "immobiliare.it", "source_listing_id": "123", "price_eur": 420000}

        change = detect_change(listing, None)

        self.assertEqual(change["type"], "new")

    def test_marks_price_drop_against_existing_listing(self):
        listing = {"source": "immobiliare.it", "source_listing_id": "123", "price_eur": 400000}
        existing = {"price_eur": 420000}

        change = detect_change(listing, existing)

        self.assertEqual(change["type"], "price_drop")
        self.assertEqual(change["old_price_eur"], 420000)
        self.assertEqual(change["new_price_eur"], 400000)


if __name__ == "__main__":
    unittest.main()
