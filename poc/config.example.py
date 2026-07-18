# Kopieer dit bestand naar config.py en vul je eigen waarden in.
# config.py staat in .gitignore en wordt dus nooit gecommit.
#
# Copy this file to config.py and fill in your own values.
# config.py is gitignored and will never be committed.

# --- Zoekopdracht (verplicht) / Search (required) ---
# Zoekterm zoals je die ook op marktplaats.nl zou intypen.
# Search term, same as you'd type into marktplaats.nl.
QUERY = "televisie"

# --- Locatie (optioneel) / Location (optional) ---
# Laat POSTCODE leeg ("") om automatisch de thuislocatie van Home Assistant
# te gebruiken (via HA_URL + HA_TOKEN hieronder, opgelost naar een postcode).
# Vul een postcode in (zonder spatie, bv. "1012JS") om een andere locatie te
# gebruiken dan je HA-thuislocatie.
#
# Leave POSTCODE empty ("") to automatically use your Home Assistant home
# location (via HA_URL + HA_TOKEN below, resolved to a postcode). Fill in a
# postcode (no space, e.g. "1012JS") to search around a different location
# than your HA home.
POSTCODE = ""

# Zoekradius in kilometers rond de postcode.
# Search radius in kilometers around the postcode.
RADIUS_KM = 25

# Alleen nodig als POSTCODE hierboven leeg is: url van je Home Assistant
# instantie en een long-lived access token (Profiel > Beveiliging onderaan
# in Home Assistant > "Long-Lived Access Tokens" > Token aanmaken).
#
# Only needed if POSTCODE above is empty: your Home Assistant URL and a
# long-lived access token (Profile > Security, at the bottom of Home
# Assistant > "Long-Lived Access Tokens" > Create Token).
HA_URL = "http://homeassistant.local:8123"
HA_TOKEN = ""

# --- Filters (allemaal optioneel) / Filters (all optional) ---
# Laat op None staan om niet op dat veld te filteren.
# Leave as None to not filter on that field.

MIN_PRICE = None  # in euro, bv. 50 / in euros, e.g. 50
MAX_PRICE = None  # in euro, bv. 200 / in euros, e.g. 200

# Een van: "nieuw", "zo_goed_als_nieuw", "gebruikt", "refurbished", "niet_werkend"
# One of: "nieuw" (new), "zo_goed_als_nieuw" (as good as new), "gebruikt" (used),
#         "refurbished", "niet_werkend" (not working)
CONDITION = None

# Numerieke categorie-ID's van marktplaats.nl. Zoek deze op door op
# marktplaats.nl een categorie te selecteren en in de browser-devtools
# (Netwerk-tab) de aanroep naar lrp/api/search te bekijken: daar staan
# l1CategoryId en l2CategoryId in.
#
# Numeric marktplaats.nl category IDs. Find these by picking a category on
# marktplaats.nl and inspecting the lrp/api/search request in your browser's
# devtools Network tab: l1CategoryId and l2CategoryId are listed there.
L1_CATEGORY_ID = None
L2_CATEGORY_ID = None

# --- Interval ---
# Pollinterval in minuten. Wordt nooit sneller dan MIN_INTERVAL_MINUTES
# uitgevoerd, ook niet als je hier een lagere waarde invult.
# Poll interval in minutes. Never runs faster than MIN_INTERVAL_MINUTES,
# even if you set a lower value here.
INTERVAL_MINUTES = 15
