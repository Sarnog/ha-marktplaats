"""Tests voor de pure helperlogica in coordinator.py (geen hass nodig)."""

from __future__ import annotations

from custom_components.marktplaats.coordinator import MarktplaatsData, _first_image_url


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
