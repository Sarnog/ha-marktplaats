# ha-marktplaats

Een integratie voor Home Assistant om structureel naar items of diensten te zoeken op marktplaats.
A Home Assistant integration for structurally searching for items or services on Marktplaats.

**Status: stap 2 van de roadmap is klaar (werkende custom_component), nog niet gepubliceerd als HACS custom repository (stap 3).**
**Status: roadmap step 2 is done (working custom_component), not yet published as a HACS custom repository (step 3).**

## NL

### Wat doet dit

Je stelt een of meer zoekopdrachten in (elk een aparte Home Assistant-integratie-entry).
Zodra er een nieuwe advertentie op marktplaats.nl verschijnt die aan een zoekopdracht
voldoet, krijg je dat te weten via een event op de HA event bus - zo bouw je zelf een
notificatie-automation naar je telefoon, zoals oorspronkelijk gevraagd.

Alleen de zoekterm is verplicht. Optioneel: minimum-/maximumprijs, conditie, categorie,
een zoekradius (standaard je Home Assistant-thuislocatie, met een straal in km) en het
zoekinterval (minimaal 15 minuten - zie "Bekende risico's").

Marktplaats heeft geen publieke "zoeken als koper"-API; deze integratie gebruikt het
interne (niet-officiële, reverse-engineered) zoek-endpoint dat de website zelf ook
aanroept. Zie "Bekende risico's" hieronder.

### Installatie

Nog niet beschikbaar via de HACS-store (dat is stap 3). Tot die tijd, handmatig:

1. Kopieer de map `custom_components/marktplaats` naar de `custom_components`-map van
   je Home Assistant-configuratie.
2. Herstart Home Assistant.
3. **Instellingen > Apparaten & diensten > Integratie toevoegen** en zoek naar
   "Marktplaats".

Of voeg deze repository toe als **custom repository** in HACS
(HACS > drie puntjes > Aangepaste repositories > deze GitHub-URL, categorie
"Integratie").

### Een zoekopdracht toevoegen

Elke zoekopdracht is een aparte integratie-entry - voeg de integratie dus opnieuw toe
voor elk item of elke dienst waar je apart een melding van wilt.

- **Zoekterm** - verplicht, de rest is optioneel.
- **Postcode** - laat leeg om automatisch je Home Assistant-thuislocatie te gebruiken
  (via reverse-geocoding met OpenStreetMap Nominatim, want Marktplaats' API filtert
  alleen daadwerkelijk op afstand met een postcode, niet met lat/lon - empirisch
  geverifieerd tijdens de PoC-fase). Vul zelf een postcode in om een andere locatie te
  doorzoeken.
- **Straal in km**, **min-/maximumprijs**, **conditie**, **categorie-ID's** - allemaal
  optioneel.
- **Zoekinterval in minuten** - minimaal 15, wel trager instelbaar. Bij het opslaan wordt
  meteen een test-zoekopdracht uitgevoerd om te controleren dat de combinatie werkt.

Een bestaande zoekopdracht aanpassen kan via **herconfigureren** op de integratie-entry -
ook zoekterm en filters wijzigen is toegestaan (dat telt dan als een nieuwe
zoekopdracht: eerder geziene advertenties worden niet meegenomen, zodat je niet in één
keer overspoeld wordt met "nieuwe" meldingen voor advertenties die er al stonden).

### Automations bouwen

Voor elke nieuwe advertentie wordt het event `marktplaats_new_listing` gevuurd, met in
`event_data`: `entry_id`, `query`, `item_id`, `title`, `price_cents`, `price_type`,
`url`, `location`, `image_url`. Bouw hier een automation op met een `notify`-actie naar
je telefoon.

Daarnaast krijgt elke zoekopdracht een sensor (`sensor.<naam>_advertenties`) met als
waarde het aantal momenteel matchende advertenties, en als attributen het aantal nieuwe
advertenties bij de laatste poll plus de laatste paar nieuwe advertenties - handig voor
een dashboard.

### Bekende risico's

- Geen officiële ondersteuning: het endpoint kan zonder aankondiging wijzigen.
- Marktplaats' gebruikersvoorwaarden verbieden systematisch/herhaald opvragen van hun
  database zonder toestemming; ze blokkeren bekende scrapers op IP-niveau. Daarom een
  hard minimum van 15 minuten tussen zoekopdrachten, ook als je een lagere waarde
  invult.
- Marktplaats retourneert maximaal de 30 nieuwste advertenties per zoekopdracht; bij een
  zeer brede zoekterm en een lange tijd zonder poll (HA uit geweest, netwerkstoring)
  kunnen advertenties tussen de 30 nieuwste "doorheen glippen" zonder melding.
- De locatie-fallback gebruikt OpenStreetMap Nominatim (gratis, geen API-key) om
  lat/lon om te zetten naar een postcode; dit gebeurt alleen bij het instellen/
  herconfigureren van een zoekopdracht, niet bij elke poll.

### Testdekking

Zie [`tests/README.md`](tests/README.md): de pure logica (API-parameters, prijsafronding,
postcode-resolutie, unique-id-logica) is met `pytest` getest. De HA-runtime-afhankelijke
delen (config flow, coordinator, sensor) zijn zorgvuldig handmatig gereviewd tegen de
daadwerkelijk geïnstalleerde Home Assistant-broncode, maar niet automatisch getest op dit
Windows-ontwikkelsysteem (`pytest-homeassistant-custom-component` vereist Unix-only
stdlib-modules). Test dit gedrag dus ook zelf in een echte Home Assistant-instantie.

### Proof-of-concept script

`poc/search.py` was het losse onderzoeksscript van stap 1, gebruikt om te bevestigen dat
het Marktplaats-endpoint sowieso bereikbaar en betrouwbaar is voordat dit werd ingebouwd
in de echte integratie hierboven. Nog steeds bruikbaar als je zonder Home
Assistant wil testen; zie de instructies eronder.

```bash
cd poc
pip install -r requirements.txt
cp config.example.py config.py   # vul je eigen postcode/zoekterm/filters in
python search.py --once          # eenmalige test
python search.py                 # blijft draaien, elke INTERVAL_MINUTES (min. 15)
```

### Roadmap

1. ~~Proof-of-concept~~ - bevestigd: het endpoint werkt, radius/prijs/conditie-filters
   werken, HA-thuislocatie kan naar een postcode omgezet worden.
2. ~~Home Assistant custom_component~~ - config flow (aanmaken + herconfigureren) met
   optionele filters, coordinator met dedupe-opslag en event, sensor-platform.
3. Publiceren als HACS custom repository.
4. (Later, apart traject) Optioneel automatisch bieden/kopen met een vooraf ingesteld
   maximumbedrag - hoog risico op accountblokkade en vereist opslag van
   Marktplaats-inloggegevens, dus dit wordt pas opgepakt na een expliciete beslissing en
   waarschijnlijk eerst als "open advertentie in app"-actie in plaats van volledige
   automatisering.

## EN

### What this does

You configure one or more searches (each its own Home Assistant integration entry). As
soon as a new listing appears on marktplaats.nl matching a search, you're notified via
an event on the HA event bus - build your own notification automation to your phone from
there, as originally requested.

Only the search term is required. Optional: minimum/maximum price, condition, category,
a search radius (defaults to your Home Assistant home location, radius in km), and the
poll interval (15 minutes minimum - see "Known risks").

Marktplaats has no public "search as a buyer" API; this integration uses the internal
(unofficial, reverse-engineered) search endpoint the website itself calls. See "Known
risks" below.

### Installation

Not yet available via the HACS store (that's step 3). Until then, manually:

1. Copy the `custom_components/marktplaats` folder into your Home Assistant
   configuration's `custom_components` folder.
2. Restart Home Assistant.
3. **Settings > Devices & services > Add integration** and search for "Marktplaats".

Or add this repository as a **custom repository** in HACS (HACS > three dots > Custom
repositories > this GitHub URL, category "Integration").

### Adding a search

Each search is a separate integration entry - add the integration again for each item
or service you want a separate notification for.

- **Search term** - required, everything else is optional.
- **Postcode** - leave empty to automatically use your Home Assistant home location (via
  reverse geocoding with OpenStreetMap Nominatim, since Marktplaats' API only actually
  filters by distance with a postcode, not lat/lon - empirically verified during the PoC
  phase). Fill in your own postcode to search around a different location.
- **Radius in km**, **min/max price**, **condition**, **category IDs** - all optional.
- **Search interval in minutes** - 15 minimum, can be set slower. Saving runs a live test
  search to confirm the combination works.

Edit an existing search via **reconfigure** on the integration entry - changing the
search term and filters is allowed too (that counts as a new search: previously-seen
listings aren't carried over, so you don't get flooded with "new" notifications for
listings that were already there).

### Building automations

For every new listing, the `marktplaats_new_listing` event fires, with in `event_data`:
`entry_id`, `query`, `item_id`, `title`, `price_cents`, `price_type`, `url`, `location`,
`image_url`. Build an automation on this with a `notify` action to your phone.

Each search also gets a sensor (`sensor.<name>_listings`) whose state is the number of
currently matching listings, with attributes for the number of new listings in the last
poll plus the latest few new listings - handy for a dashboard.

### Known risks

- No official support: the endpoint can change without warning.
- Marktplaats' terms of use prohibit systematic/repeated querying of their database
  without permission; they IP-block known scrapers. Hence a hard 15-minute minimum
  between searches, even if you configure a lower value.
- Marktplaats returns at most the 30 newest listings per search; with a very broad
  search term and a long gap without polling (HA down, network outage), listings beyond
  the newest 30 can slip through without a notification.
- The location fallback uses OpenStreetMap Nominatim (free, no API key) to resolve
  lat/lon to a postcode; this only happens when setting up/reconfiguring a search, not
  on every poll.

### Test coverage

See [`tests/README.md`](tests/README.md): the pure logic (API parameters, price
rounding, postcode resolution, unique-id logic) is tested with `pytest`. The
HA-runtime-dependent parts (config flow, coordinator, sensor) were carefully reviewed
manually against the actually-installed Home Assistant source, but not automatically
tested on this Windows development machine (`pytest-homeassistant-custom-component`
requires Unix-only stdlib modules). So also verify this behavior yourself on a real
Home Assistant instance.

### Proof-of-concept script

`poc/search.py` was the standalone research script from step 1, used to confirm the
Marktplaats endpoint is reachable and reliable at all before it was built into the real
integration above. Still usable if you want to test without Home Assistant; see the
instructions below.

```bash
cd poc
pip install -r requirements.txt
cp config.example.py config.py   # fill in your own postcode/search term/filters
python search.py --once          # one-off test
python search.py                 # runs continuously, every INTERVAL_MINUTES (min. 15)
```

### Roadmap

1. ~~Proof-of-concept~~ - confirmed: the endpoint works, radius/price/condition filters
   work, the HA home location can be resolved to a postcode.
2. ~~Home Assistant custom_component~~ - config flow (add + reconfigure) with optional
   filters, a coordinator with dedupe storage and an event, a sensor platform.
3. Publish as a HACS custom repository.
4. (Later, separate effort) Optional automatic bidding/buying up to a preconfigured
   maximum price - high risk of account suspension and requires storing Marktplaats
   credentials, so this will only be picked up after an explicit decision, and likely
   starts as an "open listing in app" action rather than full automation.
