"""Parse and record user feedback commands."""

import re

from services.database import (
    add_feedback,
    list_favorite_listings,
    list_recent_digest_listings,
    list_recent_listings,
)


ACTION_ALIASES = {
    "approfondisci": "details",
    "dettagli": "details",
    "dettaglio": "details",
    "fammi vedere": "details",
    "invia": "details",
    "manda": "details",
    "mandami": "details",
    "mostra": "details",
    "mostrami": "details",
    "scarta": "discard",
    "salva": "favorite",
    "preferito": "favorite",
    "preferiti": "favorite",
    "contatta": "contact_agency",
}

LIST_FAVORITES_PHRASES = {
    "mostra salvati",
    "mostrami salvati",
    "vedi salvati",
    "lista salvati",
    "mostra preferiti",
    "vedi preferiti",
    "lista preferiti",
    "preferiti salvati",
}

NUMBER_WORDS = {
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "primo": 1,
    "prima": 1,
    "secondo": 2,
    "seconda": 2,
    "terzo": 3,
    "terza": 3,
    "quarto": 4,
    "quarta": 4,
    "quinto": 5,
    "quinta": 5,
    "sesto": 6,
    "sesta": 6,
    "settimo": 7,
    "settima": 7,
    "ottavo": 8,
    "ottava": 8,
}


def parse_feedback_command(text):
    """Parse commands such as 'SCARTA 1', 'SALVA 2', or 'CONTATTA 1'."""
    normalized = text.strip().lower()
    if _is_list_favorites_command(normalized):
        return {"action": "list_favorites", "item_number": None}

    action = _find_action(normalized)
    item_number = _find_item_number(normalized)

    if not action:
        raise ValueError("Non ho capito se vuoi contattare, salvare o scartare.")

    if item_number is not None and item_number < 1:
        raise ValueError("Il numero dell'annuncio deve essere almeno 1.")

    return {"action": action, "item_number": item_number}


def _find_action(text):
    for alias, action in ACTION_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return action
    return None


def _is_list_favorites_command(text):
    normalized = re.sub(r"\s+", " ", text).strip(" .,!").lower()
    return normalized in LIST_FAVORITES_PHRASES


def _find_item_number(text):
    for token in re.findall(r"[\w']+", text):
        if token in NUMBER_WORDS:
            return NUMBER_WORDS[token]
    return None


def apply_feedback_command(connection, command_text):
    """Apply a feedback command to the latest listings shown to the user."""
    command = parse_feedback_command(command_text)
    if command["action"] == "list_favorites":
        return build_favorites_message(list_favorite_listings(connection))

    listings = list_recent_digest_listings(connection) or list_recent_listings(connection)
    if command["item_number"] is None:
        if len(listings) == 1:
            command["item_number"] = 1
        else:
            raise ValueError(
                "Quale annuncio intendi? Puoi scrivere, per esempio: "
                "contatta il primo, salva il secondo, mandami il terzo."
            )

    index = command["item_number"] - 1

    if index >= len(listings):
        raise ValueError("Non trovo un annuncio con quel numero nel riepilogo recente.")

    listing = listings[index]
    add_feedback(connection, listing["id"], command["action"], command_text)

    if command["action"] == "contact_agency":
        draft = build_agency_contact_draft(listing)
        return (
            f"Ho preparato questa bozza per l'agenzia:\n\n"
            f"{draft}\n\n"
            "Per ora non la invio automaticamente. "
            "Quando vuoi, copiala e inviala all'agenzia oppure scrivimi se vuoi modificarla."
        )
    if command["action"] == "details":
        return (
            f"Ecco il link dell'annuncio: {listing['title']}\n"
            f"{listing['url']}"
        )
    if command["action"] == "favorite":
        return (
            f"Salvato nei preferiti dell'agente: {listing['title']}\n"
            "Nota: lo salvo nel database di House Hunter Agent, non su casa.it "
            "o immobiliare.it."
        )
    if command["action"] == "discard":
        return f"Scartato: {listing['title']}"

    return f"Feedback registrato: {listing['title']}"


def build_favorites_message(listings):
    """Build a compact WhatsApp message with saved favorite listings."""
    if not listings:
        return "Non hai ancora annunci salvati nei preferiti dell'agente."

    lines = ["Preferiti salvati nell'agente:"]
    for index, listing in enumerate(listings, start=1):
        details = []
        if listing.get("price_eur"):
            details.append(f"€{listing['price_eur']:,.0f}".replace(",", "."))
        if listing.get("size_sqm"):
            details.append(f"{listing['size_sqm']} mq")
        if listing.get("rooms"):
            details.append(f"{listing['rooms']} locali")

        lines.append("")
        lines.append(f"{index}. {listing['title']}")
        if details:
            lines.append(" | ".join(details))
        lines.append(listing["url"])

    return "\n".join(lines)


def build_agency_contact_draft(listing):
    """Create a polite agency contact draft for one listing."""
    details = []
    if listing.get("area"):
        details.append(str(listing["area"]))
    if listing.get("price_eur"):
        details.append(f"prezzo {listing['price_eur']:,} euro".replace(",", "."))
    if listing.get("size_sqm"):
        details.append(f"{listing['size_sqm']} mq")
    if listing.get("rooms"):
        details.append(f"{listing['rooms']} locali")

    detail_text = ", ".join(details)
    if detail_text:
        detail_text = f" ({detail_text})"

    listing_reference = _listing_reference(listing)
    return (
        "Buongiorno, sono interessata a "
        f"{listing_reference}{detail_text}. "
        "Vorrei sapere se e ancora disponibile e se fosse possibile organizzare "
        "una visita nei prossimi giorni.\n\n"
        f"Link annuncio: {listing['url']}\n\n"
        "Grazie, resto in attesa di un gentile riscontro."
    )


def _listing_reference(listing):
    title = str(listing.get("title", "")).strip()
    if title.lower().strip(".,! ") in {"ciao", "buongiorno", "salve"}:
        return "questo immobile"
    return f"questo immobile: '{title}'"
