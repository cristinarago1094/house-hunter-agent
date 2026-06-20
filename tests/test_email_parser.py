import unittest

from services.email_parser import parse_listing_email


class EmailParserTest(unittest.TestCase):
    def test_parses_price_area_and_link_from_alert_email(self):
        email = {
            "id": "gmail-1",
            "source": "immobiliare.it",
            "subject": "Nuovo appartamento in vendita a Prati",
            "received_at": "2026-06-18T09:00:00",
            "body": """
Bilocale luminoso in Via Germanico
Roma Prati
€ 420.000
72 mq
2 locali
https://www.immobiliare.it/annunci/123456/
""",
        }

        listing = parse_listing_email(email)

        self.assertEqual(listing["source"], "immobiliare.it")
        self.assertEqual(listing["source_listing_id"], "123456")
        self.assertEqual(listing["price_eur"], 420000)
        self.assertEqual(listing["size_sqm"], 72)
        self.assertEqual(listing["rooms"], 2)
        self.assertEqual(listing["area"], "Roma Prati")

    def test_ignores_html_boilerplate_when_parsing_alert_email(self):
        email = {
            "id": "gmail-html-1",
            "source": "immobiliare.it",
            "subject": "Nuovi annunci in zona Prati",
            "received_at": "2026-06-18T09:00:00",
            "body": """
<!doctype html>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><style>#outlook a { padding:0; }</style></head>
  <body>
    <h1>Bilocale ristrutturato in Via Cola di Rienzo</h1>
    <p>Roma Prati</p>
    <p>€ 515.000</p>
    <p>68 mq</p>
    <p>2 locali</p>
    <a href="https://www.immobiliare.it/annunci/765432/">Vedi annuncio</a>
  </body>
</html>
""",
        }

        listing = parse_listing_email(email)

        self.assertEqual(listing["title"], "Bilocale ristrutturato in Via Cola di Rienzo")
        self.assertEqual(listing["url"], "https://www.immobiliare.it/annunci/765432/")
        self.assertEqual(listing["price_eur"], 515000)
        self.assertEqual(listing["size_sqm"], 68)

    def test_parses_size_written_with_square_meter_symbol(self):
        email = {
            "id": "gmail-size-symbol",
            "source": "casa.it",
            "subject": "Nuovo annuncio Prati",
            "received_at": "2026-06-18T09:00:00",
            "body": """
Trilocale vicino metro Ottaviano
Roma Prati
€ 590.000
Superficie 84 m²
3 locali
https://www.casa.it/immobili/987654/
""",
        }

        listing = parse_listing_email(email)

        self.assertEqual(listing["size_sqm"], 84)

    def test_parses_size_written_as_metri_quadrati(self):
        email = {
            "id": "gmail-size-words",
            "source": "immobiliare.it",
            "subject": "Nuovo annuncio Prati",
            "received_at": "2026-06-18T09:00:00",
            "body": """
Appartamento in Via Germanico
Roma Prati
€ 470.000
72 metri quadrati
2 locali
https://www.immobiliare.it/annunci/555555/
""",
        }

        listing = parse_listing_email(email)

        self.assertEqual(listing["size_sqm"], 72)

    def test_does_not_use_greeting_as_title(self):
        email = {
            "id": "gmail-casa-greeting",
            "source": "casa.it",
            "subject": "Nuovo annuncio Casa.it",
            "received_at": "2026-06-18T09:00:00",
            "body": """
Ciao,
Trilocale in Vendita in Via Carlo Mirabello a Roma
Roma Prati
€ 425.000
93 mq
3 locali
https://www.casa.it/immobili/54156696/
""",
        }

        listing = parse_listing_email(email)

        self.assertEqual(listing["title"], "Trilocale in Vendita in Via Carlo Mirabello a Roma")
        self.assertNotEqual(listing["title"], "Ciao,")


if __name__ == "__main__":
    unittest.main()
