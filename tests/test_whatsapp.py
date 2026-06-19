import unittest

from services.whatsapp import build_daily_digest


class WhatsAppTest(unittest.TestCase):
    def test_builds_digest_with_new_and_price_drop_sections(self):
        changes = [
            {
                "type": "new",
                "listing": {
                    "title": "Bilocale in Via Germanico",
                    "price_eur": 420000,
                    "size_sqm": 72,
                    "rooms": 2,
                    "score": 88,
                    "url": "https://www.immobiliare.it/annunci/123/",
                },
            },
            {
                "type": "price_drop",
                "old_price_eur": 450000,
                "new_price_eur": 430000,
                "listing": {
                    "title": "Trilocale vicino Ottaviano",
                    "price_eur": 430000,
                    "size_sqm": 80,
                    "rooms": 3,
                    "score": 82,
                    "url": "https://www.casa.it/immobili/456/",
                },
            },
        ]

        message = build_daily_digest(changes)

        self.assertIn("NUOVO", message)
        self.assertIn("RIBASSO", message)
        self.assertIn("€450.000 -> €430.000", message)
        self.assertIn("Vuoi che contatti l'agenzia", message)
        self.assertIn("CONTATTA 1", message)
        self.assertIn("SALVA 1", message)
        self.assertIn("SCARTA 1", message)

    def test_builds_empty_digest_without_contact_prompt(self):
        message = build_daily_digest([])

        self.assertIn("Nessun nuovo annuncio", message)
        self.assertNotIn("CONTATTA", message)


if __name__ == "__main__":
    unittest.main()
