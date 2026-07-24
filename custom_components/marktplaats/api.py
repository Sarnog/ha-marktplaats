"""Asynchrone client voor de (onofficiële) Marktplaats zoek-API.

Async client for the (unofficial) Marktplaats search API.
"""

from __future__ import annotations

from typing import Any

import aiohttp

from .const import (
    API_URL,
    CONDITIONS,
    NOMINATIM_URL,
    NOMINATIM_USER_AGENT,
    REQUEST_HEADERS,
)


class MarktplaatsApiError(Exception):
    """Raised when the Marktplaats search request fails."""


class PostcodeResolutionError(Exception):
    """Raised when a Home Assistant location cannot be resolved to a postcode."""


def _price_to_cents(price: float | None) -> str:
    # round(), niet int(): floats zoals 19.99 * 100 == 1998.9999999999998
    # zouden anders 1 cent afgekapt worden (empirisch gevonden bug in de
    # PoC-versie van dit script - zie poc/search.py).
    return "null" if price is None else str(round(price * 100))


def build_search_params(
    query: str,
    postcode: str,
    radius_km: int,
    *,
    limit: int,
    title_only: bool = False,
    min_price: float | None = None,
    max_price: float | None = None,
    condition: str | None = None,
    l1_category_id: int | None = None,
    l2_category_id: int | None = None,
) -> dict[str, Any]:
    """Bouwt de querystring-parameters voor een Marktplaats-zoekopdracht.

    `title_only=True` beperkt de zoekterm tot alleen de advertentietitel;
    standaard (False) matcht Marktplaats zowel de titel als de advertentietekst
    (searchInTitleAndDescription - dezelfde optie als de "Ook in advertentietekst
    zoeken"-checkbox op marktplaats.nl zelf).
    """
    params: dict[str, Any] = {
        "limit": str(limit),
        "offset": "0",
        "query": query,
        "searchInTitleAndDescription": "false" if title_only else "true",
        "viewOptions": "list-view",
        "distanceMeters": str(radius_km * 1000),
        "postcode": postcode,
        "sortBy": "SORT_INDEX",  # op datum, nieuwste eerst
        "sortOrder": "DECREASING",
    }

    if min_price is not None or max_price is not None:
        params["attributeRanges[]"] = (
            f"PriceCents:{_price_to_cents(min_price)}:{_price_to_cents(max_price)}"
        )

    if condition is not None:
        if condition not in CONDITIONS:
            msg = f"Onbekende conditie '{condition}'. Kies uit: {', '.join(CONDITIONS)}."
            raise ValueError(msg)
        params["attributesById[]"] = [str(CONDITIONS[condition])]

    if l1_category_id is not None:
        params["l1CategoryId"] = str(l1_category_id)
    if l2_category_id is not None:
        params["l2CategoryId"] = str(l2_category_id)

    return params


async def fetch_listings(
    session: aiohttp.ClientSession,
    query: str,
    postcode: str,
    radius_km: int,
    *,
    limit: int,
    title_only: bool = False,
    min_price: float | None = None,
    max_price: float | None = None,
    condition: str | None = None,
    l1_category_id: int | None = None,
    l2_category_id: int | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Haalt actuele advertenties op die aan de zoekopdracht voldoen.

    Let op: Marktplaats' zoek-API filtert alleen daadwerkelijk op afstand als
    een postcode wordt meegegeven; lat/lon-parameters worden genegeerd (dit is
    empirisch geverifieerd tijdens de PoC-fase). `postcode` is dus verplicht.

    Geeft `(listings, total_result_count)` terug. `listings` bevat maximaal
    `limit` items (de nieuwste eerst), maar `total_result_count` is het
    werkelijke totaal aantal treffers - empirisch geverifieerd dat dit veld
    onafhankelijk is van `limit` (getest met limit=1 t/m 100 op een query met
    duizenden treffers). Gebruik dus `total_result_count` voor een getoond
    "aantal advertenties", niet `len(listings)`, anders wordt dat bij een
    brede zoekterm ernstig te laag weergegeven (afgekapt op `limit`).
    """
    params = build_search_params(
        query,
        postcode,
        radius_km,
        limit=limit,
        title_only=title_only,
        min_price=min_price,
        max_price=max_price,
        condition=condition,
        l1_category_id=l1_category_id,
        l2_category_id=l2_category_id,
    )
    try:
        async with session.get(API_URL, params=params, headers=REQUEST_HEADERS) as response:
            response.raise_for_status()
            body = await response.json(content_type=None)
    except aiohttp.ClientError as err:
        msg = f"Kon geen verbinding maken met Marktplaats: {err}"
        raise MarktplaatsApiError(msg) from err

    listings = body.get("listings", [])
    total_result_count = body.get("totalResultCount", len(listings))
    return listings, total_result_count


async def resolve_postcode_from_latlon(
    session: aiohttp.ClientSession, latitude: float, longitude: float
) -> str:
    """Zet HA-coordinaten om naar een postcode via OpenStreetMap Nominatim."""
    try:
        async with session.get(
            NOMINATIM_URL,
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "addressdetails": 1,
            },
            headers={"User-Agent": NOMINATIM_USER_AGENT},
        ) as response:
            response.raise_for_status()
            body = await response.json(content_type=None)
    except aiohttp.ClientError as err:
        msg = f"Kon de thuislocatie niet omzetten naar een postcode: {err}"
        raise PostcodeResolutionError(msg) from err

    postcode = body.get("address", {}).get("postcode")
    if not postcode:
        msg = (
            f"Geen postcode gevonden voor coordinaten ({latitude}, {longitude}). "
            "Vul handmatig een postcode in."
        )
        raise PostcodeResolutionError(msg)
    return postcode.replace(" ", "")
