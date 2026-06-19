"""Preference model placeholder updated from explicit user feedback."""


def normalize_feedback(text):
    """Map free-form WhatsApp feedback to stable preference signals."""
    value = text.strip().lower()
    if value in {"salva", "preferito", "preferiti", "mi interessa"}:
        return "favorite"
    if value in {"scarta", "non interessa", "no"}:
        return "discard"
    if value in {"contatta", "contatta agenzia", "agenzia"}:
        return "contact_agency"
    return "note"
