"""Gmail adapter for reading labeled real estate alert emails."""

import base64
import json
import os
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from config import GMAIL_IMPORT_QUERY, GMAIL_TOKEN_JSON


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_PATH = "credentials/token.json"


def fetch_alert_emails(query=GMAIL_IMPORT_QUERY, max_results=50):
    """Fetch alert emails from Gmail using the official Gmail API.

    Requires Google OAuth credentials. Until credentials are configured, use
    `fetch_sample_alert_emails` to exercise the rest of the pipeline.
    """
    try:
        from googleapiclient.discovery import build
    except ImportError as error:
        raise RuntimeError(
            "Install Gmail dependencies and configure OAuth before real import."
        ) from error

    if GMAIL_TOKEN_JSON:
        credentials = Credentials.from_authorized_user_info(
            json.loads(GMAIL_TOKEN_JSON),
            SCOPES,
        )
    else:
        credentials = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    service = build("gmail", "v1", credentials=credentials)
    response = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results,
    ).execute()

    emails = []
    for item in response.get("messages", []):
        message = service.users().messages().get(
            userId="me",
            id=item["id"],
            format="full",
        ).execute()
        emails.append(_normalize_gmail_message(message))

    return emails


def fetch_sample_alert_emails():
    """Return sample alerts that mirror Gmail-imported messages."""
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "id": "sample-immobiliare-1",
            "source": "immobiliare.it",
            "subject": "Nuovo appartamento in vendita a Roma Prati",
            "received_at": now,
            "body": """
Bilocale luminoso in Via Germanico
Roma Prati
€ 420.000
72 mq
2 locali
https://www.immobiliare.it/annunci/123456/
""",
        },
        {
            "id": "sample-casa-1",
            "source": "casa.it",
            "subject": "Casa.it: nuovo annuncio in zona Prati",
            "received_at": now,
            "body": """
Trilocale vicino Ottaviano
Roma Prati
€ 590.000
84 mq
3 locali
https://www.casa.it/immobili/987654/
""",
        },
    ]


def _normalize_gmail_message(message):
    headers = {
        header["name"].lower(): header["value"]
        for header in message.get("payload", {}).get("headers", [])
    }
    body = _extract_body(message.get("payload", {}))
    source = _detect_source(headers.get("from", ""), headers.get("subject", ""))

    return {
        "id": message["id"],
        "source": source,
        "subject": headers.get("subject", ""),
        "received_at": headers.get("date", ""),
        "body": body,
    }


def _extract_body(payload):
    plain_text = _extract_body_by_mime_type(payload, "text/plain")
    if plain_text:
        return plain_text

    html_text = _extract_body_by_mime_type(payload, "text/html")
    if html_text:
        return html_text

    data = payload.get("body", {}).get("data")
    return _decode_body(data) if data else ""


def _extract_body_by_mime_type(payload, mime_type):
    if payload.get("mimeType") == mime_type:
        data = payload.get("body", {}).get("data")
        return _decode_body(data) if data else ""

    for part in payload.get("parts", []):
        body = _extract_body_by_mime_type(part, mime_type)
        if body:
            return body

    return ""


def _decode_body(data):
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def _detect_source(sender, subject):
    text = f"{sender} {subject}".lower()
    if "casa.it" in text:
        return "casa.it"
    if "immobiliare" in text:
        return "immobiliare.it"
    return "unknown"
