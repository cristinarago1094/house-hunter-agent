import unittest

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


if __name__ == "__main__":
    unittest.main()
