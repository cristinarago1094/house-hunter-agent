"""Run the House Hunter Agent daily import and digest workflow."""

import argparse
from pathlib import Path

from config import (
    DATABASE_PATH,
    ENV_FILE_PATH,
    META_WHATSAPP_ACCESS_TOKEN,
    META_WHATSAPP_PHONE_NUMBER_ID,
    MAX_DIGEST_ITEMS,
    NOTIFY_WHEN_NO_CHANGES,
    WHATSAPP_ENABLED,
    WHATSAPP_TO_NUMBER,
)
from services.change_detector import detect_change
from services.database import (
    connect,
    find_listing,
    record_recent_digest,
    reset_database,
    upsert_listing,
)
from services.email_parser import clean_email_body, parse_listing_email
from services.feedback import apply_feedback_command
from services.gmail_client import fetch_alert_emails, fetch_sample_alert_emails
from services.scorer import score_listing
from services.whatsapp import (
    build_daily_digest,
    send_daily_house_hunter_template,
    send_whatsapp_hello_world_template,
    send_whatsapp_message,
)


def run_daily_import(use_sample_data=False):
    """Import Gmail alerts, update the database, and return the digest message."""
    emails = fetch_sample_alert_emails() if use_sample_data else fetch_alert_emails()
    connection = connect(DATABASE_PATH)
    relevant_changes = []

    for email in emails:
        listing = score_listing(parse_listing_email(email))
        existing = find_listing(
            connection,
            listing["source"],
            listing["source_listing_id"],
        )
        change = detect_change(listing, existing)
        upsert_listing(connection, listing)

        if change["type"] in {"new", "price_drop"} and listing.get("matches_preferences"):
            relevant_changes.append(change)

    relevant_changes = sorted(
        relevant_changes,
        key=lambda change: change["listing"].get("score", 0),
        reverse=True,
    )
    message = build_daily_digest(relevant_changes)
    record_recent_digest(
        connection,
        [
            find_listing(
                connection,
                change["listing"]["source"],
                change["listing"]["source_listing_id"],
            )["id"]
            for change in relevant_changes[:MAX_DIGEST_ITEMS]
        ],
    )
    if relevant_changes or NOTIFY_WHEN_NO_CHANGES:
        send_result = send_daily_house_hunter_template(message)
    else:
        send_result = {
            "sent": False,
            "reason": "No relevant changes, WhatsApp skipped",
            "message": message,
        }
    return message, send_result


def save_debug_email_bodies(use_sample_data=False):
    """Save cleaned email bodies and parsed fields for troubleshooting."""
    emails = fetch_sample_alert_emails() if use_sample_data else fetch_alert_emails()
    debug_dir = Path("data/debug")
    debug_dir.mkdir(parents=True, exist_ok=True)

    for index, email in enumerate(emails, start=1):
        listing = parse_listing_email(email)
        cleaned_body = clean_email_body(email.get("body", ""))
        debug_file = debug_dir / f"email_{index:02d}_{email['source']}.txt"
        debug_file.write_text(
            "\n".join(
                [
                    f"Subject: {email.get('subject', '')}",
                    f"Source: {email.get('source', '')}",
                    "",
                    "Parsed:",
                    f"- title: {listing.get('title')}",
                    f"- price_eur: {listing.get('price_eur')}",
                    f"- size_sqm: {listing.get('size_sqm')}",
                    f"- rooms: {listing.get('rooms')}",
                    f"- url: {listing.get('url')}",
                    "",
                    "Cleaned body:",
                    cleaned_body,
                ]
            ),
            encoding="utf-8",
        )

    return debug_dir, len(emails)


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="House Hunter Agent")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Use sample alert emails instead of Gmail API.",
    )
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Delete the local database before importing emails.",
    )
    parser.add_argument(
        "--debug-email-bodies",
        action="store_true",
        help="Save cleaned Gmail alert bodies to data/debug for parser troubleshooting.",
    )
    parser.add_argument(
        "--feedback",
        help='Record local feedback, for example: "SALVA 1", "SCARTA 1", "CONTATTA 1".',
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Show non-secret configuration values.",
    )
    parser.add_argument(
        "--test-whatsapp-template",
        action="store_true",
        help="Send Meta's built-in hello_world WhatsApp template.",
    )
    args = parser.parse_args()

    if args.check_config:
        print(f"ENV file: {ENV_FILE_PATH}")
        print(f"ENV file exists: {ENV_FILE_PATH.exists()}")
        print(f"WhatsApp enabled: {WHATSAPP_ENABLED}")
        print(f"WhatsApp recipient set: {bool(WHATSAPP_TO_NUMBER)}")
        if WHATSAPP_TO_NUMBER:
            print(f"WhatsApp recipient preview: ...{WHATSAPP_TO_NUMBER[-4:]}")
        print(f"Meta phone number ID set: {bool(META_WHATSAPP_PHONE_NUMBER_ID)}")
        if META_WHATSAPP_PHONE_NUMBER_ID:
            print(f"Meta phone number ID preview: ...{META_WHATSAPP_PHONE_NUMBER_ID[-4:]}")
        print(f"Meta access token set: {bool(META_WHATSAPP_ACCESS_TOKEN)}")
        return

    if args.test_whatsapp_template:
        send_result = send_whatsapp_hello_world_template()
        if send_result["sent"]:
            print("Template WhatsApp inviato correttamente.")
            print(send_result["response"])
        else:
            print(f"Template WhatsApp non inviato: {send_result['reason']}")
        return

    if args.feedback:
        connection = connect(DATABASE_PATH)
        print(apply_feedback_command(connection, args.feedback))
        return

    if args.debug_email_bodies:
        debug_dir, email_count = save_debug_email_bodies(use_sample_data=args.sample)
        print(f"Salvate {email_count} email pulite in {debug_dir}")
        return

    if args.reset_db:
        removed = reset_database(DATABASE_PATH)
        if removed:
            print("Database locale cancellato. Reimporto gli annunci...\n")
        else:
            print("Nessun database locale da cancellare. Importo gli annunci...\n")

    message, send_result = run_daily_import(use_sample_data=args.sample)
    print(message)
    if send_result["sent"]:
        print("\nWhatsApp inviato correttamente.")
    else:
        print(f"\nWhatsApp non inviato: {send_result['reason']}")


if __name__ == "__main__":
    main()
