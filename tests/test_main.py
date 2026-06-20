import unittest
from unittest.mock import patch

import main
from services.database import connect, list_recent_digest_listings


class MainWorkflowTest(unittest.TestCase):
    @patch("main.send_daily_house_hunter_template")
    @patch("main.fetch_sample_alert_emails")
    @patch("main.connect")
    def test_daily_import_records_digest_order_from_inserted_listing_ids(
        self,
        connect_mock,
        fetch_emails,
        send_message,
    ):
        connection = connect(":memory:")
        connect_mock.return_value = connection
        fetch_emails.return_value = [
            {
                "id": "gmail-1",
                "source": "casa.it",
                "subject": "Nuovo annuncio",
                "received_at": "2026-06-18T09:00:00",
                "body": """
Trilocale luminoso in Via Germanico
Roma Prati
€ 420.000
80 mq
3 locali
4° piano
https://www.casa.it/immobili/111111/
""",
            }
        ]
        send_message.return_value = {"sent": True}

        main.run_daily_import(use_sample_data=True)

        recent = list_recent_digest_listings(connection)

        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["source_listing_id"], "111111")


if __name__ == "__main__":
    unittest.main()
