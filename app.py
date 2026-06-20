"""Web app for Render: health check, daily run, and Meta WhatsApp webhook."""

from html import escape

from flask import Flask, jsonify, request

from config import DAILY_RUN_SECRET, DATABASE_PATH, WEBHOOK_VERIFY_TOKEN
from main import run_daily_import
from services.database import connect, list_favorite_listings
from services.feedback import apply_feedback_command
from services.whatsapp import send_whatsapp_message_to


app = Flask(__name__)


@app.get("/health")
def health():
    """Render health check endpoint."""
    return jsonify({"status": "ok", "service": "house-hunter-agent"})


@app.route("/daily-run", methods=["GET", "POST"])
def daily_run():
    """Run the daily Gmail import and WhatsApp notification."""
    if not _request_has_daily_secret(request):
        return jsonify({"error": "unauthorized"}), 401

    message, send_result = run_daily_import(use_sample_data=False)
    return jsonify({"message": message, "send_result": send_result})


@app.get("/favorites")
def favorites_page():
    """Show saved favorite listings in a simple web page."""
    connection = connect(DATABASE_PATH)
    favorites = list_favorite_listings(connection)
    return _render_favorites_html(favorites)


@app.get("/webhook")
def verify_webhook():
    """Verify the Meta WhatsApp webhook subscription."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        return challenge or "", 200

    return "Forbidden", 403


@app.post("/webhook")
def receive_webhook():
    """Receive inbound WhatsApp messages from Meta."""
    payload = request.get_json(silent=True) or {}
    replies = []

    for inbound in _extract_text_messages(payload):
        reply = handle_inbound_whatsapp_message(
            from_number=inbound["from"],
            text=inbound["text"],
        )
        replies.append(reply)

    return jsonify({"status": "ok", "processed": len(replies), "replies": replies})


def handle_inbound_whatsapp_message(from_number, text):
    """Apply one WhatsApp reply and send an answer back to the user."""
    connection = connect(DATABASE_PATH)

    try:
        reply_text = apply_feedback_command(connection, text)
    except ValueError as error:
        reply_text = (
            f"Non ho capito bene: {error}\n"
            "Dimmi con parole tue se vuoi salvare, scartare, approfondire "
            "o contattare l'agenzia per un annuncio."
        )

    send_result = send_whatsapp_message_to(from_number, reply_text)
    return {"to": from_number, "reply": reply_text, "send_result": send_result}


def _extract_text_messages(payload):
    messages = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                messages.append(
                    {
                        "from": message.get("from", ""),
                        "text": message.get("text", {}).get("body", ""),
                    }
                )
    return messages


def _request_has_daily_secret(flask_request):
    auth_header = flask_request.headers.get("Authorization", "")
    expected_bearer = f"Bearer {DAILY_RUN_SECRET}"
    return (
        flask_request.args.get("secret") == DAILY_RUN_SECRET
        or flask_request.headers.get("X-House-Hunter-Secret") == DAILY_RUN_SECRET
        or auth_header == expected_bearer
    )


def _render_favorites_html(favorites):
    rows = "\n".join(_favorite_card(listing) for listing in favorites)
    if not rows:
        rows = '<p class="empty">Nessun annuncio salvato per ora.</p>'

    return f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Preferiti House Hunter Agent</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 0;
      background: #f7f3ea;
      color: #222;
    }}
    main {{
      max-width: 920px;
      margin: 0 auto;
      padding: 32px 18px 48px;
    }}
    h1 {{
      font-size: 30px;
      margin: 0 0 8px;
    }}
    .subtitle {{
      color: #5f665f;
      margin: 0 0 24px;
    }}
    .listing {{
      background: #fff;
      border: 1px solid #e2ded4;
      border-radius: 8px;
      padding: 18px;
      margin-bottom: 14px;
    }}
    .listing h2 {{
      font-size: 20px;
      margin: 0 0 10px;
    }}
    .meta {{
      color: #4a514a;
      margin-bottom: 12px;
    }}
    a {{
      color: #0b7a3b;
      overflow-wrap: anywhere;
    }}
    .empty {{
      background: #fff;
      border: 1px solid #e2ded4;
      border-radius: 8px;
      padding: 18px;
    }}
  </style>
</head>
<body>
  <main>
    <h1>Preferiti House Hunter Agent</h1>
    <p class="subtitle">Annunci salvati dentro l'agente. Non sono sincronizzati con casa.it o immobiliare.it.</p>
    {rows}
  </main>
</body>
</html>"""


def _favorite_card(listing):
    details = []
    if listing.get("price_eur"):
        details.append(f"€{listing['price_eur']:,.0f}".replace(",", "."))
    if listing.get("size_sqm"):
        details.append(f"{listing['size_sqm']} mq")
    if listing.get("rooms"):
        details.append(f"{listing['rooms']} locali")

    detail_text = " | ".join(details)
    title = escape(str(listing.get("title", "Annuncio immobiliare")))
    url = escape(str(listing.get("url", "")))
    source = escape(str(listing.get("source", "")))
    return f"""
    <article class="listing">
      <h2>{title}</h2>
      <div class="meta">{escape(detail_text)}{f" | {source}" if source else ""}</div>
      <a href="{url}" target="_blank" rel="noopener">Apri annuncio</a>
    </article>
    """
