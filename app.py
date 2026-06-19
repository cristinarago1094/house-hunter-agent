"""Web app for Render: health check, daily run, and Meta WhatsApp webhook."""

from flask import Flask, jsonify, request

from config import DAILY_RUN_SECRET, DATABASE_PATH, WEBHOOK_VERIFY_TOKEN
from main import run_daily_import
from services.database import connect
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
            "Puoi scrivere, per esempio: salva il primo, scarta il secondo, "
            "approfondisci il primo, contatta il primo."
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
