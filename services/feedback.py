"""Parse and record user feedback commands."""

import re

from services.database import add_feedback, list_recent_listings


ACTION_ALIASES = {
    "approfondisci": "details",
    "dettagli": "details",
    "dettaglio": "details",
    "scarta": "discard",
    "salva": "favorite",
    "preferito": "favorite",
    "preferiti": "favorite",
    "contatta": "contact_agency",
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
    action = _find_action(normalized)
    item_number = _find_item_number(normalized)

    if not action:
        raise ValueError("Non ho capito se vuoi contattare, salvare o scartare.")

    if not item_number:
        raise ValueError("Non ho capito a quale annuncio ti riferisci.")

    if item_number < 1:
        raise ValueError("Il numero dell'annuncio deve essere almeno 1.")

    return {"action": action, "item_number": item_number}


def _find_action(text):
    for alias, action in ACTION_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return action
    return None


def _find_item_number(text):
    for token in re.findall(r"[\w']+", text):
        if token in NUMBER_WORDS:
            return NUMBER_WORDS[token]
    return None


def apply_feedback_command(connection, command_text):
    """Apply a feedback command to the latest listings shown to the user."""
    command = parse_feedback_command(command_text)
    listings = list_recent_listings(connection)
    index = command["item_number"] - 1

    if index >= len(listings):
        raise ValueError("Non trovo un annuncio con quel numero nel riepilogo recente.")

    listing = listings[index]
    add_feedback(connection, listing["id"], command["action"], command_text)

    if command["action"] == "contact_agency":
        return (
            f"Ok, preparo il contatto per: {listing['title']}\n"
            f"Link: {listing['url']}"
        )
    if command["action"] == "details":
        return (
            f"Ecco il link dell'annuncio: {listing['title']}\n"
            f"{listing['url']}"
        )
    if command["action"] == "favorite":
        return f"Salvato tra i preferiti: {listing['title']}"
    if command["action"] == "discard":
        return f"Scartato: {listing['title']}"

    return f"Feedback registrato: {listing['title']}"
