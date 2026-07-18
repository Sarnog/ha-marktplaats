# ha-marktplaats

Een integratie voor Home Assistant om structureel naar items of diensten te zoeken op marktplaats.
A Home Assistant integration for structurally searching for items or services on Marktplaats.

**Status: onderzoeksfase (stap 1 van het plan van aanpak) — nog geen Home Assistant integratie.**
**Status: research phase (step 1 of the roadmap) — not yet a Home Assistant integration.**

## NL

Doel: een Home Assistant custom integration die je waarschuwt zodra er een nieuwe
advertentie op marktplaats.nl verschijnt die past bij een zoekopdracht (zoekterm +
straal rond een postcode), en op termijn eventueel automatisch kan bieden/kopen
binnen een vooraf ingesteld maximumbedrag.

Marktplaats heeft geen publieke "zoeken als koper"-API. Deze proof-of-concept
gebruikt daarom het interne (niet-officiele, reverse-engineered) zoek-endpoint dat
de website zelf ook aanroept. Dit kan zonder waarschuwing stoppen met werken of
verzoeken blokkeren als je te vaak/te snel zoekt. Zie `poc/search.py`.

### Gebruik van de proof-of-concept

```bash
cd poc
pip install -r requirements.txt
cp config.example.py config.py   # vul je eigen postcode/zoekterm in
python search.py --once          # eenmalige test
python search.py                 # blijft draaien, elke INTERVAL_MINUTES (min. 15)
```

`config.py` staat in `.gitignore` — je postcode wordt nooit gecommit.

### Locatie en filters

Alleen de zoekterm (`QUERY`) is verplicht. Alles hieronder is optioneel:

- **Locatie**: laat `POSTCODE` leeg om automatisch de thuislocatie van Home
  Assistant te gebruiken — het script haalt dan via `HA_URL`/`HA_TOKEN` de
  lat/lon van je HA-instantie op en zet die om naar een postcode (via
  OpenStreetMap Nominatim). Marktplaats' API filtert namelijk alleen echt op
  afstand als je een postcode meegeeft; lat/lon-parameters worden genegeerd
  (dit is empirisch geverifieerd). Vul je eigen `POSTCODE` in om een andere
  locatie te gebruiken dan je HA-thuislocatie.
- **Radius**: `RADIUS_KM`, default 25.
- **Prijs**: `MIN_PRICE` / `MAX_PRICE` in euro.
- **Conditie**: `CONDITION` — een van `nieuw`, `zo_goed_als_nieuw`, `gebruikt`,
  `refurbished`, `niet_werkend`.
- **Categorie**: `L1_CATEGORY_ID` / `L2_CATEGORY_ID` — numerieke Marktplaats
  categorie-ID's, zie `config.example.py` voor hoe je ze opzoekt.

### Bekende risico's

- Geen officiele ondersteuning: het endpoint kan zonder aankondiging wijzigen.
- Marktplaats' gebruikersvoorwaarden verbieden systematisch/herhaald opvragen van
  hun database zonder toestemming; ze blokkeren bekende scrapers op IP-niveau.
- Daarom een hard minimum van 15 minuten tussen zoekopdrachten, ook als de
  configuratie een lagere waarde bevat.
- De locatie-fallback gebruikt OpenStreetMap Nominatim (gratis, geen API-key)
  om lat/lon om te zetten naar een postcode; dit gebeurt eenmalig per run, niet
  per poll.

### Roadmap

1. **Proof-of-concept** (dit script) — bevestigen dat het endpoint bereikbaar is
   en op lage frequentie stabiel blijft werken.
2. Home Assistant custom_component: config flow met meerdere zoekopdrachten
   (elk met eigen zoekterm, radius, interval), coordinator, sensor + event per
   zoekopdracht, notificatie via een HA-automation op dat event.
3. Publiceren als HACS custom repository.
4. (Later, apart traject) Optioneel automatisch bieden/kopen met een vooraf
   ingesteld maximumbedrag — hoog risico op accountblokkade en vereist opslag
   van Marktplaats-inloggegevens, dus dit wordt pas opgepakt na een expliciete
   beslissing en waarschijnlijk eerst als "open advertentie in app"-actie in
   plaats van volledige automatisering.

## EN

Goal: a Home Assistant custom integration that alerts you as soon as a new
listing appears on marktplaats.nl matching a saved search (keyword + radius
around a postcode), and eventually may support automatic bidding/buying up to
a preconfigured maximum price.

Marktplaats has no public "search as a buyer" API. This proof-of-concept
therefore uses the internal (unofficial, reverse-engineered) search endpoint
that the website itself calls. It can stop working or start blocking requests
without notice if queried too often. See `poc/search.py`.

### Running the proof-of-concept

```bash
cd poc
pip install -r requirements.txt
cp config.example.py config.py   # fill in your own postcode/search term
python search.py --once          # one-off test
python search.py                 # runs continuously, every INTERVAL_MINUTES (min. 15)
```

`config.py` is gitignored — your postcode is never committed.

### Location and filters

Only the search term (`QUERY`) is required. Everything below is optional:

- **Location**: leave `POSTCODE` empty to automatically use your Home
  Assistant home location — the script fetches your HA instance's lat/lon via
  `HA_URL`/`HA_TOKEN` and resolves it to a postcode (via OpenStreetMap
  Nominatim). Marktplaats' API only actually filters by distance when given a
  postcode; lat/lon parameters are ignored (empirically verified). Fill in
  your own `POSTCODE` to search around a different location than your HA
  home.
- **Radius**: `RADIUS_KM`, defaults to 25.
- **Price**: `MIN_PRICE` / `MAX_PRICE` in euros.
- **Condition**: `CONDITION` — one of `nieuw` (new), `zo_goed_als_nieuw` (as
  good as new), `gebruikt` (used), `refurbished`, `niet_werkend` (not
  working).
- **Category**: `L1_CATEGORY_ID` / `L2_CATEGORY_ID` — numeric Marktplaats
  category IDs, see `config.example.py` for how to find them.

### Known risks

- No official support: the endpoint can change without warning.
- Marktplaats' terms of use prohibit systematic/repeated querying of their
  database without permission; they IP-block known scrapers.
- Hence a hard 15-minute minimum between searches, even if the config
  specifies a lower value.
- The location fallback uses OpenStreetMap Nominatim (free, no API key) to
  resolve lat/lon to a postcode; this happens once per run, not per poll.

### Roadmap

1. **Proof-of-concept** (this script) — confirm the endpoint is reachable and
   stays stable at low polling frequency.
2. Home Assistant custom_component: config flow with multiple saved searches
   (each with its own keyword, radius, interval), a coordinator, a sensor +
   event per search, notifications via a user-defined HA automation on that
   event.
3. Publish as a HACS custom repository.
4. (Later, separate effort) Optional automatic bidding/buying up to a
   preconfigured maximum price — high risk of account suspension and requires
   storing Marktplaats credentials, so this will only be picked up after an
   explicit decision, and likely starts as an "open listing in app" action
   rather than full automation.
