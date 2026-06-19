"""Parse real estate alert emails into normalized listing dictionaries."""

from html import unescape
from html.parser import HTMLParser
import re


URL_PATTERN = re.compile(r"https?://[^\s)>\"]+")
PRICE_PATTERN = re.compile(r"€\s*([0-9. ]+)")
SIZE_PATTERN = re.compile(
    r"([0-9]{1,4})\s*(mq|m²|m2|metri quadri|metri quadrati|metro quadro|metro quadrato)",
    re.IGNORECASE,
)
ROOMS_PATTERN = re.compile(r"([0-9]+)\s*(locali|locale|stanze|stanza)", re.IGNORECASE)


def parse_listing_email(email):
    """Extract the first listing-like item from a Gmail alert message."""
    body = clean_email_body(email.get("body", ""))
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    text = "\n".join(lines)

    url = _find_listing_url(text, email["source"])
    price = _parse_int(_first_group(PRICE_PATTERN, text))
    size = _parse_int(_first_group(SIZE_PATTERN, text))
    rooms = _parse_int(_first_group(ROOMS_PATTERN, text))

    title = lines[0] if lines else email.get("subject", "Annuncio immobiliare")
    area = _find_area(lines)

    return {
        "source": email["source"],
        "source_listing_id": _source_listing_id(url),
        "gmail_message_id": email["id"],
        "title": title,
        "area": area,
        "price_eur": price,
        "size_sqm": size,
        "rooms": rooms,
        "url": url,
        "first_seen_at": email.get("received_at"),
        "last_seen_at": email.get("received_at"),
    }


def _first_match(pattern, text):
    match = pattern.search(text)
    return match.group(0) if match else ""


def _first_group(pattern, text):
    match = pattern.search(text)
    return match.group(1) if match else ""


def _parse_int(value):
    cleaned = re.sub(r"[^0-9]", "", value or "")
    return int(cleaned) if cleaned else 0


def _find_area(lines):
    for line in lines:
        lower = line.lower()
        if "prati" in lower:
            return line
    return "Roma Prati"


def _source_listing_id(url):
    numbers = re.findall(r"[0-9]{4,}", url or "")
    return numbers[-1] if numbers else url


def clean_email_body(body):
    """Convert HTML alert emails into readable plain text."""
    if "<html" not in body.lower() and "<!doctype" not in body.lower():
        return body

    parser = _HTMLTextExtractor()
    parser.feed(body)
    return parser.text()


def _find_listing_url(text, source):
    source_domain = "immobiliare.it" if source == "immobiliare.it" else "casa.it"
    urls = [url.rstrip("].,;") for url in URL_PATTERN.findall(text)]

    for url in urls:
        if source_domain in url and "w3.org" not in url:
            return url

    for url in urls:
        if "w3.org" not in url:
            return url

    return ""


class _HTMLTextExtractor(HTMLParser):
    """Small HTML-to-text converter for email alert bodies."""

    def __init__(self):
        super().__init__()
        self._parts = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"style", "script", "head"}:
            self._skip_depth += 1
            return

        if tag in {"p", "div", "br", "tr", "h1", "h2", "h3", "li"}:
            self._parts.append("\n")

        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._parts.append(f"\n{href}\n")

    def handle_endtag(self, tag):
        if tag in {"style", "script", "head"} and self._skip_depth:
            self._skip_depth -= 1
            return

        if tag in {"p", "div", "tr", "h1", "h2", "h3", "li"}:
            self._parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth:
            return
        cleaned = unescape(data).strip()
        if cleaned:
            self._parts.append(cleaned)

    def text(self):
        raw_text = " ".join(self._parts)
        raw_text = re.sub(r"[ \t]+", " ", raw_text)
        raw_text = re.sub(r" *\n+ *", "\n", raw_text)
        return raw_text.strip()
