"""
Proof-of-concept: bevraagt de (onofficiele, reverse-engineered) interne
zoek-API van marktplaats.nl en meldt nieuwe advertenties sinds de vorige run.

Dit is stap 1 van het ha-marktplaats onderzoek: puur bedoeld om te testen of
het endpoint betrouwbaar bereikbaar blijft op lage frequentie, voordat dit
wordt ingebouwd in een echte Home Assistant custom_component.

Gebruik:
    cp config.example.py config.py   # en vul je eigen postcode/filters in
    python search.py --once          # eenmalige testrun
    python search.py                 # blijft draaien op INTERVAL_MINUTES
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

# Zorgt dat euro-tekens etc. goed printen op Windows-consoles (cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import config
except ModuleNotFoundError:
    sys.exit(
        "config.py ontbreekt. Kopieer config.example.py naar config.py en vul je eigen postcode in."
    )

API_URL = "https://www.marktplaats.nl/lrp/api/search"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
MIN_INTERVAL_MINUTES = 15
SEEN_FILE = Path(__file__).parent / "seen_listings.json"

# Marktplaats' interne conditie-attribuut-ID's (empirisch geverifieerd:
# elke waarde geeft alleen advertenties met die exacte conditie terug).
CONDITIONS = {
    "nieuw": 30,
    "zo_goed_als_nieuw": 31,
    "gebruikt": 32,
    "refurbished": 14050,
    "niet_werkend": 13940,
}

# Headers die de request laten lijken op een gewone browser-request.
# Zonder (een variant van) deze headers antwoordt de API met een 4xx.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def resolve_postcode_from_home_assistant(ha_url: str, ha_token: str) -> str:
    """Haalt de HA-thuislocatie op en zet die om naar een postcode.

    Marktplaats' zoek-API filtert alleen daadwerkelijk op afstand als je een
    postcode meegeeft (lat/lon parameters worden genegeerd - empirisch
    geverifieerd), dus HA's lat/lon moet hiervoor omgezet worden.
    """
    config_response = requests.get(
        f"{ha_url.rstrip('/')}/api/config",
        headers={"Authorization": f"Bearer {ha_token}"},
        timeout=10,
    )
    config_response.raise_for_status()
    ha_config = config_response.json()
    latitude = ha_config["latitude"]
    longitude = ha_config["longitude"]

    geo_response = requests.get(
        NOMINATIM_URL,
        params={
            "lat": latitude,
            "lon": longitude,
            "format": "json",
            "addressdetails": 1,
        },
        # Nominatim's gebruiksvoorwaarden vereisen een identificerende User-Agent.
        headers={"User-Agent": "ha-marktplaats-poc (github.com/Sarnog/ha-marktplaats)"},
        timeout=10,
    )
    geo_response.raise_for_status()
    postcode = geo_response.json().get("address", {}).get("postcode")
    if not postcode:
        sys.exit(
            "Kon geen postcode afleiden uit de HA-thuislocatie "
            f"({latitude}, {longitude}). Vul POSTCODE handmatig in in config.py."
        )
    return postcode.replace(" ", "")


def resolve_postcode() -> str:
    if config.POSTCODE:
        return config.POSTCODE.replace(" ", "")
    if not (getattr(config, "HA_URL", "") and getattr(config, "HA_TOKEN", "")):
        sys.exit(
            "Geen POSTCODE ingesteld en geen HA_URL/HA_TOKEN om de "
            "thuislocatie van Home Assistant op te halen. Vul een van "
            "beide in in config.py."
        )
    return resolve_postcode_from_home_assistant(config.HA_URL, config.HA_TOKEN)


def fetch_listings(
    query: str,
    postcode: str,
    radius_km: int,
    *,
    limit: int = 30,
    min_price: float | None = None,
    max_price: float | None = None,
    condition: str | None = None,
    l1_category_id: int | None = None,
    l2_category_id: int | None = None,
) -> list[dict]:
    params: dict[str, str | list[str]] = {
        "limit": str(limit),
        "offset": "0",
        "query": query,
        "searchInTitleAndDescription": "true",
        "viewOptions": "list-view",
        "distanceMeters": str(radius_km * 1000),
        "postcode": postcode,
        "sortBy": "SORT_INDEX",  # op datum, nieuwste eerst
        "sortOrder": "DECREASING",
    }

    if min_price is not None or max_price is not None:
        # round(), niet int(): floats zoals 19.99 * 100 == 1998.9999999999998
        # zouden anders 1 cent afgekapt worden, wat MAX_PRICE-grenzen net te
        # streng en MIN_PRICE-grenzen net te soepel maakt.
        min_cents = "null" if min_price is None else str(round(min_price * 100))
        max_cents = "null" if max_price is None else str(round(max_price * 100))
        params["attributeRanges[]"] = f"PriceCents:{min_cents}:{max_cents}"

    if condition is not None:
        if condition not in CONDITIONS:
            sys.exit(f"Onbekende CONDITION '{condition}'. Kies uit: {', '.join(CONDITIONS)}.")
        params["attributesById[]"] = [str(CONDITIONS[condition])]

    if l1_category_id is not None:
        params["l1CategoryId"] = str(l1_category_id)
    if l2_category_id is not None:
        params["l2CategoryId"] = str(l2_category_id)

    response = requests.get(API_URL, params=params, headers=REQUEST_HEADERS, timeout=15)
    response.raise_for_status()
    body = response.json()
    return body.get("listings", [])


def load_seen_ids() -> set[str]:
    if not SEEN_FILE.exists():
        return set()
    return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))


def save_seen_ids(ids: set[str]) -> None:
    SEEN_FILE.write_text(json.dumps(sorted(ids)), encoding="utf-8")


def run_once(postcode: str) -> None:
    listings = fetch_listings(
        config.QUERY,
        postcode,
        config.RADIUS_KM,
        min_price=getattr(config, "MIN_PRICE", None),
        max_price=getattr(config, "MAX_PRICE", None),
        condition=getattr(config, "CONDITION", None),
        l1_category_id=getattr(config, "L1_CATEGORY_ID", None),
        l2_category_id=getattr(config, "L2_CATEGORY_ID", None),
    )
    seen_ids = load_seen_ids()
    new_listings = [item for item in listings if item["itemId"] not in seen_ids]

    timestamp = datetime.now(UTC).isoformat(timespec="seconds")
    print(f"[{timestamp}] {len(listings)} resultaten opgehaald, {len(new_listings)} nieuw.")

    for item in new_listings:
        price_cents = item.get("priceInfo", {}).get("priceCents")
        price = f"€{price_cents / 100:.2f}" if price_cents is not None else "n.v.t."
        location = item.get("location", {}).get("cityName", "?")
        url = "https://link.marktplaats.nl/" + item["itemId"]
        print(f"  NIEUW: {item['title']} - {price} - {location} - {url}")

    seen_ids.update(item["itemId"] for item in listings)
    save_seen_ids(seen_ids)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--once", action="store_true", help="Voer een enkele zoekopdracht uit en stop."
    )
    args = parser.parse_args()

    interval_minutes = max(config.INTERVAL_MINUTES, MIN_INTERVAL_MINUTES)
    if config.INTERVAL_MINUTES < MIN_INTERVAL_MINUTES:
        print(
            f"Let op: INTERVAL_MINUTES={config.INTERVAL_MINUTES} is lager dan het "
            f"minimum van {MIN_INTERVAL_MINUTES}. Er wordt {MIN_INTERVAL_MINUTES} "
            "minuten aangehouden."
        )

    postcode = resolve_postcode()

    if args.once:
        run_once(postcode)
        return

    print(
        f"Start doorlopend zoeken naar '{config.QUERY}' binnen {config.RADIUS_KM}km "
        f"van {postcode}, elke {interval_minutes} minuten. Ctrl+C om te stoppen."
    )
    while True:
        try:
            run_once(postcode)
        except requests.RequestException as exc:
            # Vangt ook netwerkfouten (timeouts, verbroken verbinding) af,
            # niet alleen HTTP-foutstatussen - anders stopt de hele
            # meerdaagse polling-run bij de eerste hapering.
            print(f"Fout bij ophalen (mogelijk geblokkeerd of netwerkprobleem): {exc}")
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    main()
