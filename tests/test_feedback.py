import unittest

from services.database import (
    add_feedback,
    connect,
    list_favorite_listings,
    list_recent_digest_listings,
    list_recent_listings,
    record_recent_digest,
    upsert_listing,
)
from services.feedback import build_agency_contact_draft, parse_feedback_command


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

    def test_parses_send_first_as_details(self):
        command = parse_feedback_command("manda il primo")

        self.assertEqual(command["action"], "details")
        self.assertEqual(command["item_number"], 1)

    def test_parses_show_third_as_details(self):
        command = parse_feedback_command("fammi vedere il terzo")

        self.assertEqual(command["action"], "details")
        self.assertEqual(command["item_number"], 3)

    def test_contact_without_number_uses_single_listing(self):
        connection = connect(":memory:")
        upsert_listing(
            connection,
            {
                "source": "immobiliare.it",
                "source_listing_id": "1",
                "title": "Only listing",
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

        from services.feedback import apply_feedback_command

        response = apply_feedback_command(connection, "contatta")

        self.assertIn("Ho preparato questa bozza", response)

    def test_contact_without_number_asks_which_listing_when_multiple_exist(self):
        connection = connect(":memory:")
        for index in [1, 2]:
            upsert_listing(
                connection,
                {
                    "source": "immobiliare.it",
                    "source_listing_id": str(index),
                    "title": f"Listing {index}",
                    "area": "Roma Prati",
                    "price_eur": 420000,
                    "size_sqm": 72,
                    "rooms": 2,
                    "url": f"https://www.immobiliare.it/annunci/{index}/",
                    "score": 90 - index,
                    "score_reasons": [],
                    "first_seen_at": "2026-06-18T09:00:00",
                    "last_seen_at": "2026-06-18T09:00:00",
                },
            )

        from services.feedback import apply_feedback_command

        with self.assertRaises(ValueError) as error:
            apply_feedback_command(connection, "contatta")

        self.assertIn("Quale annuncio", str(error.exception))

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

    def test_feedback_uses_last_digest_order(self):
        connection = connect(":memory:")
        first_id = upsert_listing(
            connection,
            {
                "source": "immobiliare.it",
                "source_listing_id": "1",
                "title": "Shown first",
                "area": "Roma Prati",
                "price_eur": 420000,
                "size_sqm": 72,
                "rooms": 2,
                "url": "https://www.immobiliare.it/annunci/1/",
                "score": 70,
                "score_reasons": [],
                "first_seen_at": "2026-06-18T09:00:00",
                "last_seen_at": "2026-06-18T09:00:00",
            },
        )
        second_id = upsert_listing(
            connection,
            {
                "source": "casa.it",
                "source_listing_id": "2",
                "title": "Shown second",
                "area": "Roma Prati",
                "price_eur": 450000,
                "size_sqm": 80,
                "rooms": 3,
                "url": "https://www.casa.it/immobili/2/",
                "score": 95,
                "score_reasons": [],
                "first_seen_at": "2026-06-18T09:00:00",
                "last_seen_at": "2026-06-18T09:00:00",
            },
        )
        record_recent_digest(connection, [first_id, second_id])

        from services.feedback import apply_feedback_command

        response = apply_feedback_command(connection, "salva il secondo")

        self.assertIn("Shown second", response)

    def test_recent_digest_listings_keep_display_order(self):
        connection = connect(":memory:")
        listing_ids = []
        for index in [1, 2]:
            listing_ids.append(
                upsert_listing(
                    connection,
                    {
                        "source": "immobiliare.it",
                        "source_listing_id": str(index),
                        "title": f"Listing {index}",
                        "area": "Roma Prati",
                        "price_eur": 420000,
                        "size_sqm": 72,
                        "rooms": 2,
                        "url": f"https://www.immobiliare.it/annunci/{index}/",
                        "score": 90,
                        "score_reasons": [],
                        "first_seen_at": "2026-06-18T09:00:00",
                        "last_seen_at": "2026-06-18T09:00:00",
                    },
                )
            )
        record_recent_digest(connection, [listing_ids[1], listing_ids[0]])

        listings = list_recent_digest_listings(connection)

        self.assertEqual([listing["title"] for listing in listings], ["Listing 2", "Listing 1"])

    def test_favorite_reply_explains_local_agent_storage(self):
        connection = connect(":memory:")
        listing_id = upsert_listing(
            connection,
            {
                "source": "casa.it",
                "source_listing_id": "1",
                "title": "Trilocale in Via Mirabello",
                "area": "Roma Prati",
                "price_eur": 425000,
                "size_sqm": 93,
                "rooms": 3,
                "url": "https://www.casa.it/immobili/1/",
                "score": 100,
                "score_reasons": [],
                "first_seen_at": "2026-06-18T09:00:00",
                "last_seen_at": "2026-06-18T09:00:00",
            },
        )
        record_recent_digest(connection, [listing_id])

        from services.feedback import apply_feedback_command

        response = apply_feedback_command(connection, "salva il primo")

        self.assertIn("Salvato nei preferiti dell'agente", response)
        self.assertIn("non su casa.it", response)

    def test_show_saved_returns_favorite_list(self):
        connection = connect(":memory:")
        listing_id = upsert_listing(
            connection,
            {
                "source": "casa.it",
                "source_listing_id": "1",
                "title": "Trilocale in Via Mirabello",
                "area": "Roma Prati",
                "price_eur": 425000,
                "size_sqm": 93,
                "rooms": 3,
                "url": "https://www.casa.it/immobili/1/",
                "score": 100,
                "score_reasons": [],
                "first_seen_at": "2026-06-18T09:00:00",
                "last_seen_at": "2026-06-18T09:00:00",
            },
        )
        add_feedback(connection, listing_id, "favorite", "salva il primo")

        from services.feedback import apply_feedback_command

        response = apply_feedback_command(connection, "mostra salvati")

        self.assertIn("Preferiti salvati", response)
        self.assertIn("Trilocale in Via Mirabello", response)
        self.assertIn("https://www.casa.it/immobili/1/", response)

    def test_list_favorite_listings_returns_saved_items(self):
        connection = connect(":memory:")
        saved_id = upsert_listing(
            connection,
            {
                "source": "immobiliare.it",
                "source_listing_id": "1",
                "title": "Saved listing",
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
        upsert_listing(
            connection,
            {
                "source": "casa.it",
                "source_listing_id": "2",
                "title": "Unsaved listing",
                "area": "Roma Prati",
                "price_eur": 450000,
                "size_sqm": 80,
                "rooms": 3,
                "url": "https://www.casa.it/immobili/2/",
                "score": 85,
                "score_reasons": [],
                "first_seen_at": "2026-06-18T09:00:00",
                "last_seen_at": "2026-06-18T09:00:00",
            },
        )
        add_feedback(connection, saved_id, "favorite", "salva il primo")

        favorites = list_favorite_listings(connection)

        self.assertEqual(len(favorites), 1)
        self.assertEqual(favorites[0]["title"], "Saved listing")

    def test_builds_agency_contact_draft(self):
        listing = {
            "title": "Bilocale in Via Germanico",
            "area": "Roma Prati",
            "price_eur": 420000,
            "size_sqm": 72,
            "rooms": 2,
            "url": "https://www.immobiliare.it/annunci/1/",
        }

        draft = build_agency_contact_draft(listing)

        self.assertIn("Buongiorno", draft)
        self.assertIn("Bilocale in Via Germanico", draft)
        self.assertIn("ancora disponibile", draft)
        self.assertIn("visita", draft)

    def test_agency_contact_draft_does_not_use_greeting_title(self):
        listing = {
            "title": "Ciao,",
            "area": "Roma Prati",
            "price_eur": 425000,
            "size_sqm": 93,
            "rooms": 3,
            "url": "https://www.casa.it/immobili/1/",
        }

        draft = build_agency_contact_draft(listing)

        self.assertNotIn("'Ciao,'", draft)
        self.assertIn("questo immobile", draft)


if __name__ == "__main__":
    unittest.main()
