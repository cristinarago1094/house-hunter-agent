import io
import unittest

from PIL import Image

from services.photo_verifier import (
    extract_primary_image_url,
    is_low_floor_listing,
    verify_listing_photos,
)


class FakeResponse:
    def __init__(self, text="", content=b"", status_code=200):
        self.text = text
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP error")


class PhotoVerifierTest(unittest.TestCase):
    def test_extracts_open_graph_image(self):
        html = '<meta property="og:image" content="https://example.com/photo.jpg">'

        image_url = extract_primary_image_url(html)

        self.assertEqual(image_url, "https://example.com/photo.jpg")

    def test_identifies_low_floor_listing(self):
        self.assertTrue(is_low_floor_listing({"floor_level": 1}))
        self.assertTrue(is_low_floor_listing({"floor_level": 2}))
        self.assertFalse(is_low_floor_listing({"floor_level": 3}))

    def test_marks_low_floor_listing_bright_when_photo_is_bright(self):
        listing = {
            "url": "https://www.casa.it/immobili/1/",
            "floor_level": 1,
        }
        image = _jpeg_with_brightness(230)

        def fake_get(url, **kwargs):
            if url == listing["url"]:
                return FakeResponse(
                    text='<meta property="og:image" content="https://example.com/photo.jpg">'
                )
            return FakeResponse(content=image)

        verified = verify_listing_photos(listing, http_get=fake_get)

        self.assertTrue(verified["photo_brightness_ok"])
        self.assertEqual(verified["photo_verification_status"], "bright")

    def test_marks_low_floor_listing_dark_when_photo_is_dark(self):
        listing = {
            "url": "https://www.casa.it/immobili/1/",
            "floor_level": 2,
        }
        image = _jpeg_with_brightness(35)

        def fake_get(url, **kwargs):
            if url == listing["url"]:
                return FakeResponse(
                    text='<meta property="og:image" content="https://example.com/photo.jpg">'
                )
            return FakeResponse(content=image)

        verified = verify_listing_photos(listing, http_get=fake_get)

        self.assertFalse(verified["photo_brightness_ok"])
        self.assertEqual(verified["photo_verification_status"], "dark")

    def test_marks_low_floor_listing_unverified_when_no_image_is_found(self):
        listing = {
            "url": "https://www.casa.it/immobili/1/",
            "floor_level": 1,
        }

        def fake_get(url, **kwargs):
            return FakeResponse(text="<html>No image</html>")

        verified = verify_listing_photos(listing, http_get=fake_get)

        self.assertFalse(verified["photo_brightness_ok"])
        self.assertEqual(verified["photo_verification_status"], "no_image")


def _jpeg_with_brightness(value):
    image = Image.new("RGB", (10, 10), color=(value, value, value))
    output = io.BytesIO()
    image.save(output, format="JPEG")
    return output.getvalue()


if __name__ == "__main__":
    unittest.main()
