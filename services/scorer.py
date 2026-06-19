"""Transparent scoring rules for purchase listings in Roma Prati."""

from config import IDEAL_PRICE_EUR, IDEAL_SIZE_SQM, MAX_PRICE_EUR, MIN_ROOMS, MIN_SIZE_SQM


def score_listing(listing):
    """Return a scored copy of one listing with human-readable reasons."""
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
    if rooms >= MIN_ROOMS:
        score += 20
        reasons.append("numero locali coerente")

    scored = listing.copy()
    scored["score"] = min(score, 100)
    scored["score_reasons"] = reasons
    return scored


def score_listings(listings):
    """Score listings and return the highest-priority ones first."""
    scored = [score_listing(listing) for listing in listings]
    return sorted(scored, key=lambda listing: listing.get("score", 0), reverse=True)
