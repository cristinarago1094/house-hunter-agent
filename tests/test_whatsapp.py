import unittest
from unittest.mock import patch

from services.whatsapp import build_daily_digest, send_daily_house_hunter_template, template_parameter_text


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

        self.assertIn("Ho trovato 2 annunci", message)
        self.assertIn("NUOVO", message)
        self.assertIn("RIBASSO", message)
        self.assertIn("€450.000 -> €430.000", message)
        self.assertIn("Dimmi pure cosa vuoi fare.", message)
        self.assertNotIn("CONTATTA 1", message)
        self.assertNotIn("SALVA 1", message)
        self.assertNotIn("SCARTA 1", message)

    def test_builds_empty_digest_without_contact_prompt(self):
        message = build_daily_digest([])

        self.assertIn("Nessun nuovo annuncio", message)
        self.assertNotIn("CONTATTA", message)

    def test_template_parameter_text_removes_disallowed_whitespace(self):
        text = template_parameter_text("NUOVO 1\n\tBilocale    in Prati\n\nScore: 92")

        self.assertEqual(text, "NUOVO 1 | Bilocale in Prati | Score: 92")
        self.assertNotIn("\n", text)
        self.assertNotIn("\t", text)
        self.assertNotIn("    ", text)

    @patch("services.whatsapp._send_meta_text_message")
    @patch("services.whatsapp._send_meta_template_message")
    def test_daily_update_sends_only_dynamic_text_by_default(self, send_template, send_text):
        send_template.return_value = {"sent": True, "response": {"messages": []}}
        send_text.return_value = {"sent": True, "response": {"messages": []}}

        result = send_daily_house_hunter_template("RIBASSO 1 - Casa")

        self.assertTrue(result["sent"])
        send_text.assert_called_once_with("RIBASSO 1 - Casa")
        send_template.assert_not_called()


if __name__ == "__main__":
    unittest.main()
