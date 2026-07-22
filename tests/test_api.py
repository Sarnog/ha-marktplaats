"""Tests voor custom_components/marktplaats/api.py (geen HA-runtime nodig).

HTTP-aanroepen worden gemockt door `session.get` direct te vervangen met een
object dat dezelfde async-contextmanager-vorm heeft als aiohttp's echte
`_RequestContextManager` - geen externe mocking-library (zoals aioresponses)
nodig. Dat is bewust: aioresponses 0.7.9 bleek in deze omgeving niet te
matchen tegen aiohttp 3.14.1 (monkeypatch-incompatibiliteit), waardoor
requests er in de praktijk stilletjes doorheen glipten als een niet-
onderschepte "connection refused" - twee tests slaagden toen om de verkeerde
reden (de eigen `except aiohttp.ClientError` in api.py ving die valse fout
net zo goed op). Deze aanpak faalt in plaats daarvan hard als de mock niet
gebruikt wordt.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import aiohttp
import pytest

from custom_components.marktplaats import api
from custom_components.marktplaats.const import API_URL, NOMINATIM_URL


class _FakeResponse:
    """Bootst aiohttp's async-contextmanager response-object na."""

    def __init__(self, *, status: int = 200, json_data: Any = None) -> None:
        self.status = status
        self._json_data = json_data

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise aiohttp.ClientResponseError(
                request_info=MagicMock(),
                history=(),
                status=self.status,
            )

    async def json(self, content_type: str | None = None) -> Any:  # noqa: ARG002
        return self._json_data

    async def __aenter__(self) -> _FakeResponse:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None


def _mock_session_get(url: str, response: _FakeResponse) -> MagicMock:
    """Geeft een fake aiohttp.ClientSession terug die alleen `url` beantwoordt."""
    session = MagicMock(spec=aiohttp.ClientSession)

    def _get(requested_url: str, **_kwargs: object) -> _FakeResponse:
        if requested_url != url:
            msg = f"Onverwachte URL in test: {requested_url} (verwacht {url})"
            raise AssertionError(msg)
        return response

    session.get.side_effect = _get
    return session


def test_build_search_params_only_required_fields() -> None:
    params = api.build_search_params("televisie", "1012JS", 25, limit=30)

    assert params["query"] == "televisie"
    assert params["postcode"] == "1012JS"
    assert params["distanceMeters"] == "25000"
    assert "attributeRanges[]" not in params
    assert "attributesById[]" not in params
    assert "l1CategoryId" not in params
    assert "l2CategoryId" not in params


def test_build_search_params_price_rounding_avoids_float_truncation() -> None:
    # 19.99 * 100 == 1998.9999999999998 in floating point - round(), not
    # int(), must be used or this becomes 1998 instead of 1999 cents.
    params = api.build_search_params(
        "televisie", "1012JS", 25, limit=30, min_price=19.99, max_price=149.95
    )

    assert params["attributeRanges[]"] == "PriceCents:1999:14995"


def test_build_search_params_price_null_bounds() -> None:
    params = api.build_search_params("televisie", "1012JS", 25, limit=30, max_price=100)

    assert params["attributeRanges[]"] == "PriceCents:null:10000"


def test_build_search_params_condition() -> None:
    params = api.build_search_params("televisie", "1012JS", 25, limit=30, condition="gebruikt")

    assert params["attributesById[]"] == ["32"]


def test_build_search_params_invalid_condition_raises() -> None:
    with pytest.raises(ValueError, match="Onbekende conditie"):
        api.build_search_params("televisie", "1012JS", 25, limit=30, condition="niet-bestaand")


def test_build_search_params_categories() -> None:
    params = api.build_search_params(
        "televisie", "1012JS", 25, limit=30, l1_category_id=1234, l2_category_id=5678
    )

    assert params["l1CategoryId"] == "1234"
    assert params["l2CategoryId"] == "5678"


@pytest.mark.asyncio
async def test_fetch_listings_returns_parsed_listings() -> None:
    session = _mock_session_get(
        API_URL,
        _FakeResponse(
            json_data={
                "listings": [{"itemId": "m123", "title": "Een televisie"}],
                "totalResultCount": 1,
            }
        ),
    )

    listings, total_result_count = await api.fetch_listings(
        session, "televisie", "1012JS", 25, limit=30
    )

    assert listings == [{"itemId": "m123", "title": "Een televisie"}]
    assert total_result_count == 1


@pytest.mark.asyncio
async def test_fetch_listings_total_result_count_is_not_capped_by_len_listings() -> None:
    # Marktplaats always returns at most `limit` listings, but totalResultCount
    # reflects the real total - empirically verified live with limit=1..100 on
    # a query with thousands of matches. A regression here (e.g. accidentally
    # using len(listings) again) would silently under-report popular searches.
    session = _mock_session_get(
        API_URL,
        _FakeResponse(
            json_data={
                "listings": [{"itemId": "m1"}, {"itemId": "m2"}],
                "totalResultCount": 2698,
            }
        ),
    )

    listings, total_result_count = await api.fetch_listings(
        session, "televisie", "1012JS", 25, limit=2
    )

    assert len(listings) == 2
    assert total_result_count == 2698


@pytest.mark.asyncio
async def test_fetch_listings_missing_total_result_count_falls_back_to_len_listings() -> None:
    session = _mock_session_get(
        API_URL,
        _FakeResponse(json_data={"listings": [{"itemId": "m1"}, {"itemId": "m2"}]}),
    )

    listings, total_result_count = await api.fetch_listings(
        session, "televisie", "1012JS", 25, limit=30
    )

    assert total_result_count == len(listings) == 2


@pytest.mark.asyncio
async def test_fetch_listings_http_error_raises_marktplaats_api_error() -> None:
    session = _mock_session_get(API_URL, _FakeResponse(status=503))

    with pytest.raises(api.MarktplaatsApiError):
        await api.fetch_listings(session, "televisie", "1012JS", 25, limit=30)


@pytest.mark.asyncio
async def test_resolve_postcode_from_latlon_strips_space() -> None:
    session = _mock_session_get(
        NOMINATIM_URL, _FakeResponse(json_data={"address": {"postcode": "1012 NP"}})
    )

    postcode = await api.resolve_postcode_from_latlon(session, 52.3731, 4.8926)

    assert postcode == "1012NP"


@pytest.mark.asyncio
async def test_resolve_postcode_from_latlon_missing_postcode_raises() -> None:
    session = _mock_session_get(NOMINATIM_URL, _FakeResponse(json_data={"address": {}}))

    with pytest.raises(api.PostcodeResolutionError):
        await api.resolve_postcode_from_latlon(session, 52.3731, 4.8926)
