"""Transparent scoring rules for purchase listings in Roma Prati."""

from config import (
    IDEAL_PRICE_EUR,
    IDEAL_SIZE_SQM,
    MAX_PRICE_EUR,
    MIN_SIZE_SQM,
    REQUIRED_ROOMS,
)


def score_listing(listing):
    """Return a scored copy of one listing with human-readable reasons."""
    disqualify_reasons = preference_disqualify_reasons(listing)
    if disqualify_reasons:
        scored = listing.copy()
        scored["score"] = 0
        scored["score_reasons"] = []
        scored["matches_preferences"] = False
        scored["disqualify_reasons"] = disqualify_reasons
        return scored

    score = 0
    reasons = []

    area = listing.get("area", "").lower()
    if "prati" in area:
        score += 30
        reasons.append("Roma Prati")

    price = listing.get("price_eur") or 0
    if price and price <= IDEAL_PRICE_EUR:
        score += 30
        reasons.append("prezzo entro target ideale")
    elif price and price <= MAX_PRICE_EUR:
        score += 18
        reasons.append("prezzo entro budget massimo")

    size = listing.get("size_sqm") or 0
    if size >= IDEAL_SIZE_SQM:
        score += 20
        reasons.append("metratura ideale")
    elif size >= MIN_SIZE_SQM:
        score += 12
        reasons.append("metratura accettabile")

    rooms = listing.get("rooms") or 0
    if rooms == REQUIRED_ROOMS:
        score += 20
        reasons.append("trilocale")

    floor_level = listing.get("floor_level")
    if floor_level and floor_level >= 3:
        score += 10
        reasons.append("piano alto preferibile")
    elif floor_level in {1, 2}:
        reasons.append("piano basso con foto luminose verificate")

    scored = listing.copy()
    scored["score"] = min(score, 100)
    scored["score_reasons"] = reasons
    scored["matches_preferences"] = True
    scored["disqualify_reasons"] = []
    return scored


def preference_disqualify_reasons(listing):
    """Return hard preference mismatches that should not be sent to the user."""
    reasons = []

    area = listing.get("area", "").lower()
    if "prati" not in area:
        reasons.append("fuori zona Prati")

    rooms = listing.get("rooms") or 0
    if rooms != REQUIRED_ROOMS:
        reasons.append("non è trilocale")

    size = listing.get("size_sqm") or 0
    if size < MIN_SIZE_SQM:
        reasons.append("meno di 70 mq")

    floor_level = listing.get("floor_level")
    floor_label = str(listing.get("floor_label", "")).lower()
    if floor_level == 0 or "piano terra" in floor_label:
        reasons.append("piano terra")
    elif floor_level in {1, 2} and not listing.get("photo_brightness_ok"):
        reasons.append("piano basso senza foto luminose verificate")

    return reasons


def score_listings(listings):
    """Score listings and return the highest-priority ones first."""
    scored = [score_listing(listing) for listing in listings]
    return sorted(scored, key=lambda listing: listing.get("score", 0), reverse=True)
