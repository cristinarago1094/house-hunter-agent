"""Verify brightness for low-floor listings using listing photos."""

import io
import re
from html import unescape

from PIL import Image, ImageStat
import requests

from services.email_parser import find_floor


BRIGHTNESS_THRESHOLD = 115
MAX_IMAGES_TO_CHECK = 6


def enrich_listing_from_page(listing, http_get=requests.get):
    """Add useful page metadata, such as floor text, before scoring."""
    enriched = listing.copy()
    try:
        page = http_get(
            listing["url"],
            headers={"User-Agent": "HouseHunterAgent/1.0"},
            timeout=20,
        )
        page.raise_for_status()
    except Exception as error:
        enriched["page_enrichment_status"] = "error"
        enriched["page_enrichment_error"] = str(error)
        return enriched

    page_text = extract_page_description_text(page.text)
    if page_text:
        current_text = str(enriched.get("description_text", ""))
        enriched["description_text"] = f"{current_text}\n{page_text}".strip()

    if enriched.get("floor_level") is None and page_text:
        floor_level, floor_label = find_floor(page_text)
        enriched["floor_level"] = floor_level
        enriched["floor_label"] = floor_label

    enriched["page_enrichment_status"] = "ok"
    return enriched


def is_low_floor_listing(listing):
    """Return True when a listing is on the first or second floor."""
    return listing.get("floor_level") in {1, 2}


def verify_listing_photos(listing, http_get=requests.get):
    """Fetch listing photos and mark whether at least one looks bright enough."""
    verified = listing.copy()
    if not is_low_floor_listing(listing):
        verified["photo_verification_status"] = "not_required"
        verified["photo_brightness_ok"] = True
        return verified

    try:
        page = http_get(
            listing["url"],
            headers={"User-Agent": "HouseHunterAgent/1.0"},
            timeout=20,
        )
        page.raise_for_status()
        image_urls = extract_listing_image_urls(page.text)
        if not image_urls:
            verified["photo_verification_status"] = "no_image"
            verified["photo_brightness_ok"] = False
            return verified

        scores = []
        checked_urls = []
        for image_url in image_urls[:MAX_IMAGES_TO_CHECK]:
            image_response = http_get(
                image_url,
                headers={"User-Agent": "HouseHunterAgent/1.0"},
                timeout=20,
            )
            image_response.raise_for_status()
            scores.append(image_brightness(image_response.content))
            checked_urls.append(image_url)
    except Exception as error:
        verified["photo_verification_status"] = "error"
        verified["photo_verification_error"] = str(error)
        verified["photo_brightness_ok"] = False
        return verified

    if not scores:
        verified["photo_verification_status"] = "no_image"
        verified["photo_brightness_ok"] = False
        return verified

    best_brightness = max(scores)
    best_index = scores.index(best_brightness)
    verified["photo_image_url"] = checked_urls[best_index]
    verified["photo_checked_image_urls"] = checked_urls
    verified["photo_verified_images"] = len(scores)
    verified["photo_brightness_score"] = round(best_brightness, 1)
    if best_brightness >= BRIGHTNESS_THRESHOLD:
        verified["photo_verification_status"] = "bright"
        verified["photo_brightness_ok"] = True
    else:
        verified["photo_verification_status"] = "dark"
        verified["photo_brightness_ok"] = False

    return verified


def extract_primary_image_url(html):
    """Extract the most likely primary image URL from listing HTML."""
    urls = extract_listing_image_urls(html)
    return urls[0] if urls else ""


def extract_listing_image_urls(html):
    """Extract likely listing image URLs from metadata and image tags."""
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
        r'<img[^>]+src=["\']([^"\']+)["\']',
    ]
    urls = []
    for pattern in patterns:
        for match in re.finditer(pattern, html, flags=re.IGNORECASE):
            url = match.group(1)
            if _looks_like_image_url(url) and url not in urls:
                urls.append(url)
    return urls


def extract_page_description_text(html):
    """Extract compact listing text from meta description tags."""
    patterns = [
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']',
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
    ]
    parts = []
    for pattern in patterns:
        for match in re.finditer(pattern, html, flags=re.IGNORECASE):
            text = unescape(match.group(1)).strip()
            if text and text not in parts:
                parts.append(text)
    return "\n".join(parts)


def _looks_like_image_url(url):
    lower = url.lower()
    return lower.startswith("http") and any(
        extension in lower
        for extension in [".jpg", ".jpeg", ".png", ".webp"]
    )


def image_brightness(image_bytes):
    """Return average grayscale brightness from 0 to 255."""
    with Image.open(io.BytesIO(image_bytes)) as image:
        grayscale = image.convert("L")
        return ImageStat.Stat(grayscale).mean[0]
