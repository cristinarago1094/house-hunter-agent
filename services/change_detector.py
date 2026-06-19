"""Detect meaningful changes between imported and stored listings."""


def detect_change(listing, existing_listing):
    """Classify an imported listing as new, price drop, price rise, or unchanged."""
    if existing_listing is None:
        return {"type": "new", "listing": listing}

    old_price = existing_listing.get("price_eur") or 0
    new_price = listing.get("price_eur") or 0

    if old_price and new_price and new_price < old_price:
        return {
            "type": "price_drop",
            "listing": listing,
            "old_price_eur": old_price,
            "new_price_eur": new_price,
        }

    if old_price and new_price and new_price > old_price:
        return {
            "type": "price_rise",
            "listing": listing,
            "old_price_eur": old_price,
            "new_price_eur": new_price,
        }

    return {"type": "unchanged", "listing": listing}
