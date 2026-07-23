"""Tests voor de pure helperlogica in coordinator.py (geen hass nodig)."""

from __future__ import annotations

from custom_components.marktplaats.coordinator import (
    MarktplaatsData,
    _build_notify_payload,
    _first_image_url,
    _format_price,
)


def test_first_image_url_adds_https_to_protocol_relative_url() -> None:
    item = {"imageUrls": ["//images.marktplaats.com/foo.jpg"]}

    assert _first_image_url(item) == "https://images.marktplaats.com/foo.jpg"


def test_first_image_url_leaves_absolute_url_untouched() -> None:
    item = {"imageUrls": ["https://images.marktplaats.com/foo.jpg"]}

    assert _first_image_url(item) == "https://images.marktplaats.com/foo.jpg"


def test_first_image_url_returns_none_when_no_pictures() -> None:
    assert _first_image_url({}) is None
    assert _first_image_url({"imageUrls": []}) is None


def test_marktplaats_data_defaults_to_empty_lists() -> None:
    data = MarktplaatsData(total_count=0)

    assert data.new_listings == []
    assert data.all_listings == []


def test_format_price_converts_cents_with_dutch_decimal_comma() -> None:
    item = {"priceInfo": {"priceCents": 1999}}

    assert _format_price(item) == "€ 19,99"


def test_format_price_returns_none_without_price_cents() -> None:
    # priceType (bv. "ON_REQUEST") is nooit empirisch geverifieerd als vaste
    # enum-lijst, dus geen prijs is beter dan een geraden label.
    assert _format_price({"priceInfo": {"priceType": "ON_REQUEST"}}) is None
    assert _format_price({}) is None


def test_build_notify_payload_includes_title_price_location_and_url() -> None:
    item = {
        "itemId": "m123",
        "title": "Vintage fiets",
        "priceInfo": {"priceCents": 15000},
        "location": {"cityName": "Utrecht"},
        "imageUrls": ["//images.marktplaats.com/foo.jpg"],
    }

    payload = _build_notify_payload(item)

    assert payload["title"] == "Vintage fiets"
    assert "€ 150,00" in payload["message"]
    assert "Utrecht" in payload["message"]
    assert "https://link.marktplaats.nl/m123" in payload["message"]
    assert payload["data"] == {
        "url": "https://link.marktplaats.nl/m123",
        "clickAction": "https://link.marktplaats.nl/m123",
        "image": "https://images.marktplaats.com/foo.jpg",
    }


def test_build_notify_payload_omits_image_without_picture_but_keeps_url() -> None:
    item = {"itemId": "m456", "title": "Bureau", "priceInfo": {}, "location": {}}

    payload = _build_notify_payload(item)

    assert payload["data"] == {
        "url": "https://link.marktplaats.nl/m456",
        "clickAction": "https://link.marktplaats.nl/m456",
    }
    assert payload["message"] == "https://link.marktplaats.nl/m456"
