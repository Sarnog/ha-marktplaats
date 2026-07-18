"""Constanten voor de Marktplaats-integratie.

Constants for the Marktplaats integration.
"""

from __future__ import annotations

DOMAIN = "marktplaats"

API_URL = "https://www.marktplaats.nl/lrp/api/search"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
# Nominatim's gebruiksvoorwaarden vereisen een identificerende User-Agent.
NOMINATIM_USER_AGENT = "ha-marktplaats (github.com/Sarnog/ha-marktplaats)"

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# Marktplaats' interne conditie-attribuut-ID's (empirisch geverifieerd tijdens
# de PoC: elke waarde geeft alleen advertenties met die exacte conditie terug).
CONDITIONS: dict[str, int] = {
    "nieuw": 30,
    "zo_goed_als_nieuw": 31,
    "gebruikt": 32,
    "refurbished": 14050,
    "niet_werkend": 13940,
}

CONF_QUERY = "query"
CONF_POSTCODE = "postcode"
CONF_RADIUS_KM = "radius_km"
CONF_MIN_PRICE = "min_price"
CONF_MAX_PRICE = "max_price"
CONF_CONDITION = "condition"
CONF_L1_CATEGORY_ID = "l1_category_id"
CONF_L2_CATEGORY_ID = "l2_category_id"
CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"

DEFAULT_RADIUS_KM = 25
DEFAULT_SCAN_INTERVAL_MINUTES = 15
# Marktplaats blokkeert bekende scrapers op IP-niveau en hun voorwaarden
# verbieden systematisch/herhaald opvragen zonder toestemming - dit minimum
# geldt altijd, ook als een gebruiker een lagere waarde configureert.
MIN_SCAN_INTERVAL_MINUTES = 15

EVENT_NEW_LISTING = "marktplaats_new_listing"

SEARCH_RESULT_LIMIT = 30
