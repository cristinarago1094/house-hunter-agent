import unittest

from services.database import connect, list_recent_listings, upsert_listing
from services.feedback import parse_feedback_command


class FeedbackTest(unittest.TestCase):
    def test_parses_discard_command(self):
        command = parse_feedback_command("SCARTA 2")

        self.assertEqual(command["action"], "discard")
        self.assertEqual(command["item_number"], 2)

    def test_parses_favorite_command(self):
        command = parse_feedback_command("salva 1")

        self.assertEqual(command["action"], "favorite")
        self.assertEqual(command["item_number"], 1)

    def test_parses_contact_command(self):
        command = parse_feedback_command("contatta 3")

        self.assertEqual(command["action"], "contact_agency")
        self.assertEqual(command["item_number"], 3)

    def test_parses_natural_favorite_command(self):
        command = parse_feedback_command("salva il primo")

        self.assertEqual(command["action"], "favorite")
        self.assertEqual(command["item_number"], 1)

    def test_parses_natural_contact_command(self):
        command = parse_feedback_command("contatta l'agenzia per il secondo")

        self.assertEqual(command["action"], "contact_agency")
        self.assertEqual(command["item_number"], 2)

    def test_parses_natural_details_command(self):
        command = parse_feedback_command("approfondisci il primo")

        self.assertEqual(command["action"], "details")
        self.assertEqual(command["item_number"], 1)

    def test_recent_listings_are_ordered_like_digest_priority(self):
        connection = connect(":memory:")
        upsert_listing(
            connection,
            {
                "source": "casa.it",
                "source_listing_id": "2",
                "title": "Lower score",
                "area": "Roma Prati",
                "price_eur": 590000,
                "size_sqm": 84,
                "rooms": 3,
                "url": "https://www.casa.it/immobili/2/",
                "score": 70,
                "score_reasons": [],
                "first_seen_at": "2026-06-18T09:00:00",
                "last_seen_at": "2026-06-18T09:00:00",
            },
        )
        upsert_listing(
            connection,
            {
                "source": "immobiliare.it",
                "source_listing_id": "1",
                "title": "Higher score",
                "area": "Roma Prati",
                "price_eur": 420000,
                "size_sqm": 72,
                "rooms": 2,
                "url": "https://www.immobiliare.it/annunci/1/",
                "score": 90,
                "score_reasons": [],
                "first_seen_at": "2026-06-18T09:00:00",
                "last_seen_at": "2026-06-18T09:00:00",
            },
        )

        listings = list_recent_listings(connection)

        self.assertEqual(listings[0]["title"], "Higher score")


if __name__ == "__main__":
    unittest.main()
