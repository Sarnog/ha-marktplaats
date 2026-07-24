# ARCHITECTURE.md

## NL

Technisch ontwerpdocument voor wie aan de code werkt (geen gebruikershandleiding —
dat is [`README.md`](README.md)). Elke laag heeft precies één verantwoordelijkheid.

### Overzicht

```
Internet
  ├─ Marktplaats zoek-API (intern, niet-officieel, JSON)
  └─ OpenStreetMap Nominatim (reverse-geocoding, alleen bij (her)configureren)
        │
        ▼
   api.py            querystring bouwen, ophalen, JSON teruggeven
        │            (pure aiohttp, geen Home Assistant-imports)
        ▼
   coordinator.py    DataUpdateCoordinator: pollen, dedupe-opslag,
        │            marktplaats_new_listing-event, optionele notify-push
        ▼
   sensor.py         entiteit: leest alleen coordinator-data

   config_flow.py    (her)configureren + live testopvraag; schrijft de
                     config entry die de coordinator uitleest
```

### api.py — API-client

Uitsluitend verantwoordelijk voor het praten met de externe endpoints; bevat
**geen** Home Assistant-imports en is los te testen.

- `build_search_params()` — pure functie die de querystring bouwt (zoekterm,
  postcode + afstand, prijsgrenzen, conditie, categorie-ID's, en of alleen in de
  titel gezocht wordt).
- `fetch_listings()` — roept de zoek-API aan en geeft `(listings, total_result_count)`
  terug. `total_result_count` is Marktplaats' eigen totaal, niet `len(listings)`
  (dat is afgekapt op de opvraaglimiet).
- `resolve_postcode_from_latlon()` — zet de HA-thuislocatie om naar een postcode via
  Nominatim, omdat de zoek-API alleen op afstand filtert met een postcode, niet met
  lat/lon.
- Netwerkfouten worden vertaald naar `MarktplaatsApiError` / `PostcodeResolutionError`.

### const.py — Constanten

Endpoints, request-headers, de conditie-attribuut-ID's, de config-sleutels, de
standaardwaarden en de harde minima/limieten (minimaal zoekinterval, opvraaglimiet)
en de event-naam. Geen logica.

### config_flow.py — Configuratie

De stappen voor toevoegen en herconfigureren. Lost de postcode op (indien leeg) en
voert bij opslaan een live testopvraag uit om de combinatie te valideren.
`_build_unique_id()` maakt een stabiele identifier zodat een identieke zoekopdracht
niet twee keer kan bestaan, maar varianten (andere filters) wel apart mogen. Bij een
echte criteria-wijziging wordt de "geziene advertenties"-opslag gewist, zodat de
eerstvolgende poll een schone baseline krijgt in plaats van alles als "nieuw" te melden.

### coordinator.py — Coordinator

`MarktplaatsCoordinator` (een `DataUpdateCoordinator`) pollt via `api.fetch_listings`,
houdt per config entry de geziene item-ID's bij in een `Store` (met onderscheid tussen
"nog nooit gepolld" en "gepolld, toen 0 treffers"), en levert een `MarktplaatsData`
(`total_count`, `new_listings`, `all_listings`). Voor elke nieuwe advertentie vuurt hij
het `marktplaats_new_listing`-event en stuurt hij — als er een notify-service is
ingesteld — een pushmelding via `_build_notify_payload` (titel, prijs, locatie, link,
foto; zowel `url` als `clickAction` zodat tikken op iOS én Android de advertentie opent).
Een mislukte melding wordt alleen gelogd; een mislukte fetch wordt `UpdateFailed`.

### __init__.py — Setup

`async_setup_entry` maakt de coordinator, doet de eerste refresh, zet 'm in
`entry.runtime_data` en forward naar het sensor-platform; `async_unload_entry` ontlaadt.
Het enige platform is `sensor`.

### sensor.py — Entiteiten

`MarktplaatsListingsSensor` (`CoordinatorEntity` + `SensorEntity`) doet zelf geen
netwerkverzoeken en leest alleen uit de coordinator: de waarde is het totale aantal
treffers, met als attributen het aantal nieuwe bij de laatste poll plus de laatste paar
nieuwe advertenties. Krijgt een eigen service-device per config entry.

### Meldingen en events

Naast de sensor zijn er twee uitgangen: het `marktplaats_new_listing`-event (met de
volledige advertentiegegevens, om zelf automations op te bouwen) en de ingebouwde
notify-push. De kant-en-klare blueprints in `blueprints/automation/marktplaats/`
triggeren op datzelfde event.

### Conventies

Alle I/O is asynchroon (`aiohttp`); `api.py` blijft vrij van Home Assistant-imports zodat
de pure logica (querystring, prijsafronding, postcode-resolutie, unique-id,
notify-payload) met `pytest` te dekken is. Geen `print()`.

### Uitbreidbaarheid

Een nieuw zoekfilter of nieuwe parameter komt in `build_search_params` (api.py), het
config-flow-schema en de `unique_id`; nieuwe afgeleide gegevens komen in de coordinator
en/of de sensor. De rest van de pijplijn blijft ongewijzigd. Concrete ideeën voor
uitbreidingen staan in [ROADMAP.md](ROADMAP.md).

## EN

Technical design document for anyone working on the code (not a user manual — that is
[`README.md`](README.md)). Each layer has exactly one responsibility.

### Overview

```
Internet
  ├─ Marktplaats search API (internal, unofficial, JSON)
  └─ OpenStreetMap Nominatim (reverse geocoding, only when (re)configuring)
        │
        ▼
   api.py            build the querystring, fetch, return JSON
        │            (pure aiohttp, no Home Assistant imports)
        ▼
   coordinator.py    DataUpdateCoordinator: polling, dedupe storage,
        │            marktplaats_new_listing event, optional notify push
        ▼
   sensor.py         entity: only reads coordinator data

   config_flow.py    (re)configure + live test fetch; writes the config
                     entry the coordinator reads
```

### api.py — API client

Responsible only for talking to the external endpoints; contains **no** Home Assistant
imports and is testable in isolation.

- `build_search_params()` — a pure function that builds the querystring (search term,
  postcode + distance, price bounds, condition, category IDs, and whether to search the
  title only).
- `fetch_listings()` — calls the search API and returns `(listings, total_result_count)`.
  `total_result_count` is Marktplaats' own total, not `len(listings)` (which is capped at
  the fetch limit).
- `resolve_postcode_from_latlon()` — resolves the HA home location to a postcode via
  Nominatim, because the search API only filters by distance with a postcode, not lat/lon.
- Network errors are translated to `MarktplaatsApiError` / `PostcodeResolutionError`.

### const.py — Constants

Endpoints, request headers, the condition attribute IDs, the config keys, the defaults
and the hard minimums/limits (minimum search interval, fetch limit) and the event name.
No logic.

### config_flow.py — Configuration

The add and reconfigure steps. Resolves the postcode (when left empty) and runs a live
test fetch on save to validate the combination. `_build_unique_id()` produces a stable
identifier so an identical search cannot exist twice, while variants (different filters)
may coexist. On a real criteria change the "seen listings" storage is cleared so the next
poll gets a clean baseline instead of reporting everything as "new".

### coordinator.py — Coordinator

`MarktplaatsCoordinator` (a `DataUpdateCoordinator`) polls via `api.fetch_listings`, keeps
the seen item IDs per config entry in a `Store` (distinguishing "never polled" from
"polled, 0 results then"), and returns a `MarktplaatsData` (`total_count`, `new_listings`,
`all_listings`). For each new listing it fires the `marktplaats_new_listing` event and —
if a notify service is configured — sends a push via `_build_notify_payload` (title,
price, location, link, photo; both `url` and `clickAction` so tapping opens the listing on
iOS and Android). A failed notification is only logged; a failed fetch becomes
`UpdateFailed`.

### __init__.py — Setup

`async_setup_entry` creates the coordinator, does the first refresh, stores it in
`entry.runtime_data` and forwards to the sensor platform; `async_unload_entry` unloads.
The only platform is `sensor`.

### sensor.py — Entities

`MarktplaatsListingsSensor` (`CoordinatorEntity` + `SensorEntity`) performs no network
requests itself and only reads from the coordinator: its value is the total match count,
with attributes for the number of new listings in the last poll plus the latest few new
listings. Gets its own service device per config entry.

### Notifications and events

Besides the sensor there are two outputs: the `marktplaats_new_listing` event (with the
full listing data, to build your own automations) and the built-in notify push. The
ready-made blueprints in `blueprints/automation/marktplaats/` trigger on that same event.

### Conventions

All I/O is asynchronous (`aiohttp`); `api.py` stays free of Home Assistant imports so the
pure logic (querystring, price rounding, postcode resolution, unique id, notify payload)
can be covered with `pytest`. No `print()`.

### Extensibility

A new search filter or parameter goes into `build_search_params` (api.py), the config-flow
schema and the `unique_id`; new derived data goes into the coordinator and/or the sensor.
The rest of the pipeline stays unchanged. Concrete ideas for extensions live in
[ROADMAP.md](ROADMAP.md).
