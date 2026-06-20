"""WhatsApp digest builder and Meta Cloud API sender."""

import re

import requests

from config import (
    MAX_DIGEST_ITEMS,
    META_WHATSAPP_ACCESS_TOKEN,
    META_WHATSAPP_API_VERSION,
    META_WHATSAPP_DAILY_TEMPLATE_LANGUAGE,
    META_WHATSAPP_DAILY_TEMPLATE_NAME,
    META_WHATSAPP_DAILY_TEMPLATE_PARAM_COUNT,
    META_WHATSAPP_DAILY_USE_TEMPLATE,
    META_WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_ENABLED,
    WHATSAPP_TO_NUMBER,
)


def format_eur(value):
    """Format an integer euro value for Italian readers."""
    return f"€{value:,.0f}".replace(",", ".")


def build_daily_digest(changes):
    """Build the daily WhatsApp message from new listings and price drops."""
    if not changes:
        return "Nessun nuovo annuncio o ribasso rilevante oggi su Roma Prati."

    visible_changes = changes[:MAX_DIGEST_ITEMS]
    count = len(visible_changes)
    plural = "annuncio" if count == 1 else "annunci"
    lines = [f"Ho trovato {count} {plural} in linea con Roma Prati.", ""]

    for change in visible_changes:
        listing = change["listing"]
        prefix = "NUOVO" if change["type"] == "new" else "RIBASSO"
        item_number = len([line for line in lines if line.startswith(("NUOVO", "RIBASSO"))]) + 1

        lines.append(f"{prefix} {item_number} - {listing['title']}")
        if change["type"] == "price_drop":
            old_price = format_eur(change["old_price_eur"])
            new_price = format_eur(change["new_price_eur"])
            lines.append(f"Prezzo: {old_price} -> {new_price}")
        else:
            lines.append(f"Prezzo: {format_eur(listing['price_eur'])}")

        lines.append(f"{listing.get('size_sqm', 'n/d')} mq | {listing.get('rooms', 'n/d')} locali")
        lines.append(f"Score: {listing.get('score', 0)}/100")

        reasons = listing.get("score_reasons") or []
        if reasons:
            lines.append(f"Motivi: {', '.join(reasons)}")

        lines.append(listing["url"])
        lines.append("")

    lines.append("Dimmi pure cosa vuoi fare.")
    return "\n".join(lines).strip()


def send_whatsapp_message(message):
    """Send a WhatsApp text message through Meta WhatsApp Cloud API."""
    return _send_meta_text_message(message)


def send_whatsapp_message_to(to_number, message):
    """Send a WhatsApp text message to a specific recipient."""
    return _send_meta_text_message(message, to_number=to_number)


def send_daily_house_hunter_template(message):
    """Send the approved daily House Hunter template."""
    if not META_WHATSAPP_DAILY_USE_TEMPLATE:
        return _send_meta_text_message(message)

    if META_WHATSAPP_DAILY_TEMPLATE_PARAM_COUNT == 0:
        template_result = _send_meta_template_message(
            template_name=META_WHATSAPP_DAILY_TEMPLATE_NAME,
            language_code=META_WHATSAPP_DAILY_TEMPLATE_LANGUAGE,
            body_parameters=[],
        )
        if not template_result["sent"]:
            return template_result

        return template_result

    return _send_meta_template_message(
        template_name=META_WHATSAPP_DAILY_TEMPLATE_NAME,
        language_code=META_WHATSAPP_DAILY_TEMPLATE_LANGUAGE,
        body_parameters=[template_parameter_text(message)],
    )


def template_parameter_text(message):
    """Make text safe for Meta template parameters."""
    single_line = re.sub(r"[\n\t]+", " | ", message)
    single_line = re.sub(r" {2,}", " ", single_line)
    single_line = re.sub(r"( \| ){2,}", " | ", single_line)
    return single_line.strip(" |")


def _send_meta_text_message(message, to_number=None):
    """Send a free-form text message through Meta WhatsApp Cloud API."""
    if not WHATSAPP_ENABLED:
        return {"sent": False, "reason": "WhatsApp sending disabled", "message": message}

    missing = []
    if not META_WHATSAPP_ACCESS_TOKEN:
        missing.append("META_WHATSAPP_ACCESS_TOKEN")
    if not META_WHATSAPP_PHONE_NUMBER_ID:
        missing.append("META_WHATSAPP_PHONE_NUMBER_ID")
    recipient = to_number or WHATSAPP_TO_NUMBER
    if not recipient:
        missing.append("HOUSE_HUNTER_WHATSAPP_TO")

    if missing:
        return {
            "sent": False,
            "reason": f"Missing Meta WhatsApp configuration: {', '.join(missing)}",
            "message": message,
        }

    url = (
        f"https://graph.facebook.com/{META_WHATSAPP_API_VERSION}/"
        f"{META_WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {META_WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": True, "body": message},
        },
        timeout=30,
    )

    if response.status_code >= 400:
        return {
            "sent": False,
            "reason": f"Meta WhatsApp API error {response.status_code}: {response.text}",
            "message": message,
        }

    return {"sent": True, "response": response.json()}


def send_whatsapp_hello_world_template():
    """Send Meta's built-in hello_world template for delivery testing."""
    return _send_meta_template_message("hello_world", "en_US", [])


def _send_meta_template_message(template_name, language_code, body_parameters):
    """Send a WhatsApp template message through Meta Cloud API."""
    if not WHATSAPP_ENABLED:
        return {"sent": False, "reason": "WhatsApp sending disabled"}

    missing = []
    if not META_WHATSAPP_ACCESS_TOKEN:
        missing.append("META_WHATSAPP_ACCESS_TOKEN")
    if not META_WHATSAPP_PHONE_NUMBER_ID:
        missing.append("META_WHATSAPP_PHONE_NUMBER_ID")
    if not WHATSAPP_TO_NUMBER:
        missing.append("HOUSE_HUNTER_WHATSAPP_TO")

    if missing:
        return {
            "sent": False,
            "reason": f"Missing Meta WhatsApp configuration: {', '.join(missing)}",
        }

    components = []
    if body_parameters:
        components.append(
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": value}
                    for value in body_parameters
                ],
            }
        )

    url = (
        f"https://graph.facebook.com/{META_WHATSAPP_API_VERSION}/"
        f"{META_WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {META_WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "messaging_product": "whatsapp",
            "to": WHATSAPP_TO_NUMBER,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                **({"components": components} if components else {}),
            },
        },
        timeout=30,
    )

    if response.status_code >= 400:
        return {
            "sent": False,
            "reason": f"Meta WhatsApp API error {response.status_code}: {response.text}",
        }

    return {"sent": True, "response": response.json()}
