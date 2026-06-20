import unittest
from unittest.mock import patch

from app import app


class WebAppTest(unittest.TestCase):
    def test_health_endpoint_returns_ok(self):
        client = app.test_client()

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_webhook_verification_accepts_matching_token(self):
        client = app.test_client()

        response = client.get(
            "/webhook",
            query_string={
                "hub.mode": "subscribe",
                "hub.verify_token": "change-me",
                "hub.challenge": "abc123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "abc123")

    def test_webhook_verification_rejects_wrong_token(self):
        client = app.test_client()

        response = client.get(
            "/webhook",
            query_string={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong",
                "hub.challenge": "abc123",
            },
        )

        self.assertEqual(response.status_code, 403)

    @patch("app.send_whatsapp_message_to")
    @patch("app.apply_feedback_command")
    def test_webhook_error_reply_is_natural(self, apply_feedback, send_message):
        apply_feedback.side_effect = ValueError("Non trovo un annuncio con quel numero.")
        send_message.return_value = {"sent": True}
        client = app.test_client()

        response = client.post(
            "/webhook",
            json={
                "entry": [
                    {
                        "changes": [
                            {
                                "value": {
                                    "messages": [
                                        {
                                            "from": "393331234567",
                                            "type": "text",
                                            "text": {"body": "Salva il 6"},
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            },
        )

        reply = response.get_json()["replies"][0]["reply"]

        self.assertEqual(response.status_code, 200)
        self.assertIn("Non ho capito bene", reply)
        self.assertNotIn("salva il primo", reply)
        self.assertNotIn("contatta il primo", reply)


if __name__ == "__main__":
    unittest.main()
