"""Verify brightness for low-floor listings using the main listing photo."""

import io
import re

from PIL import Image, ImageStat
import requests


BRIGHTNESS_THRESHOLD = 115


def is_low_floor_listing(listing):
    """Return True when a listing is on the first or second floor."""
    return listing.get("floor_level") in {1, 2}


def verify_listing_photos(listing, http_get=requests.get):
    """Fetch the main listing photo and mark whether it looks bright enough."""
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
        image_url = extract_primary_image_url(page.text)
        if not image_url:
            verified["photo_verification_status"] = "no_image"
            verified["photo_brightness_ok"] = False
            return verified

        image_response = http_get(
            image_url,
            headers={"User-Agent": "HouseHunterAgent/1.0"},
            timeout=20,
        )
        image_response.raise_for_status()
        brightness = image_brightness(image_response.content)
    except Exception as error:
        verified["photo_verification_status"] = "error"
        verified["photo_verification_error"] = str(error)
        verified["photo_brightness_ok"] = False
        return verified

    verified["photo_image_url"] = image_url
    verified["photo_brightness_score"] = round(brightness, 1)
    if brightness >= BRIGHTNESS_THRESHOLD:
        verified["photo_verification_status"] = "bright"
        verified["photo_brightness_ok"] = True
    else:
        verified["photo_verification_status"] = "dark"
        verified["photo_brightness_ok"] = False

    return verified


def extract_primary_image_url(html):
    """Extract the most likely primary image URL from listing HTML."""
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def image_brightness(image_bytes):
    """Return average grayscale brightness from 0 to 255."""
    with Image.open(io.BytesIO(image_bytes)) as image:
        grayscale = image.convert("L")
        return ImageStat.Stat(grayscale).mean[0]
