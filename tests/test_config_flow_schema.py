"""Tests voor de pure schema/unique-id-logica in config_flow.py.

Deze tests hebben geen draaiende Home Assistant-instantie nodig (in
tegenstelling tot de volledige config flow zelf, die wel echte hass-fixtures
vereist - zie tests/README.md voor waarom dat hier niet automatisch getest
wordt).
"""

from __future__ import annotations

import pytest
import voluptuous as vol

from custom_components.marktplaats.config_flow import (
    DATA_SCHEMA,
    _build_unique_id,
    _normalize_notify_service,
)


def test_only_query_is_required() -> None:
    result = DATA_SCHEMA({"query": "televisie"})

    assert result["query"] == "televisie"
    assert result["radius_km"] == 25
    assert result["scan_interval_minutes"] == 15
    assert result["postcode"] == ""
    assert "min_price" not in result
    assert "condition" not in result


def test_scan_interval_below_minimum_is_rejected() -> None:
    with pytest.raises(vol.Invalid):
        DATA_SCHEMA({"query": "televisie", "scan_interval_minutes": 5})


def test_price_fields_coerce_string_input_to_float() -> None:
    # HA forms submit numeric fields as strings.
    result = DATA_SCHEMA({"query": "televisie", "min_price": "19.99"})

    assert result["min_price"] == pytest.approx(19.99)
    assert isinstance(result["min_price"], float)


def test_unknown_condition_is_rejected() -> None:
    with pytest.raises(vol.Invalid):
        DATA_SCHEMA({"query": "televisie", "condition": "niet-bestaand"})


def test_build_unique_id_is_stable_for_identical_data() -> None:
    data_a = {
        "query": "Televisie",
        "postcode": "1012JS",
        "radius_km": 25,
    }
    data_b = {
        "query": "televisie",  # andere hoofdlettering, moet toch matchen
        "postcode": "1012JS",
        "radius_km": 25,
    }

    assert _build_unique_id(data_a) == _build_unique_id(data_b)


def test_build_unique_id_differs_when_filters_differ() -> None:
    base = {"query": "televisie", "postcode": "1012JS", "radius_km": 25}
    with_price = {**base, "min_price": 50.0}

    assert _build_unique_id(base) != _build_unique_id(with_price)


def test_normalize_notify_service_strips_notify_prefix_and_whitespace() -> None:
    assert _normalize_notify_service(" notify.mobile_app_telefoon ") == "mobile_app_telefoon"


def test_normalize_notify_service_leaves_bare_service_name_untouched() -> None:
    assert _normalize_notify_service("mobile_app_telefoon") == "mobile_app_telefoon"
