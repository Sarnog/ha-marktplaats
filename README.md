  <a href="#nl">NL</a> | <a href="#en">EN</a>

<div align="center">
  <!-- align="center" centreert alles binnen deze div -->
  <h1>
    <!-- h1 = grootste kop, standaard al dikgedrukt en groot -->
    <ins>Marktplaats</ins>
    <!-- ins = onderstreepte tekst op GitHub -->
  </h1>
</div>


##### <ins>NL</ins>

Een integratie voor Home Assistant om structureel naar items of diensten te zoeken op marktplaats.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Sarnog&repository=ha-marktplaats&category=integration)
**Blueprint (Android):** [![Open your Home Assistant instance and show the blueprint import dialog for the Android notification blueprint.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FSarnog%2Fha-marktplaats%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fmarktplaats%2Fnew_listing_notify.yaml)
**Blueprint (iOS):** [![Open your Home Assistant instance and show the blueprint import dialog for the iOS notification blueprint.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FSarnog%2Fha-marktplaats%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fmarktplaats%2Fnew_listing_notify_ios.yaml)

**Status: installeerbaar als HACS custom repository; aanmelding bij de standaard HACS-store staat in de reviewwachtrij. Zie [`ROADMAP.md`](ROADMAP.md) voor de volledige planning.**

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

**Via HACS** (aanbevolen): klik de HACS-badge bovenaan dit bestand, of voeg deze repository
handmatig toe als **custom repository** in HACS (HACS > drie puntjes > Aangepaste
repositories > deze GitHub-URL, categorie "Integratie"). Dit is nog geen opname in de
standaard HACS-store zelf (dat vereist een aparte aanmelding/review bij HACS), maar
werkt verder identiek.

**Handmatig**, als alternatief:

1. Kopieer de map `custom_components/marktplaats` naar de `custom_components`-map van
   je Home Assistant-configuratie.
2. Herstart Home Assistant.
3. **Instellingen > Apparaten & diensten > Integratie toevoegen** en zoek naar
   "Marktplaats".

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

### Meldingen ontvangen

Er zijn twee manieren, van simpel naar flexibel:

1. **Ingebouwd, geen automation nodig.** Vul bij het (her)instellen van een
   zoekopdracht een **notify-servicenaam** in (bv. `mobile_app_telefoon` -
   te vinden via **Ontwikkelaarstools > Acties**, zoek op "notify", de naam
   ná de punt is de servicenaam; een volledig `notify.xxx` mag ook, de
   `notify.`-prefix wordt automatisch gestript). De integratie stuurt dan
   zelf bij elke nieuwe advertentie een melding met titel, prijs, locatie,
   link én foto - tikken op de melding zelf opent de advertentie (in de
   Marktplaats-app indien geïnstalleerd, anders in de browser). **Let op:**
   dit moet een klassieke, per-doel notify-service
   zijn (zoals de HA Companion App die registreert), geen notify-entity - de
   moderne, entity-gebaseerde `notify.send_message`-service ondersteunt sinds
   Home Assistant's notify-entity-herontwerp geen foto-bijlage meer
   (empirisch geverifieerd; zie [`ROADMAP.md`](ROADMAP.md) voor de technische
   toelichting). Werkt de opgegeven service niet (meer), dan wordt dat alleen
   als waarschuwing gelogd - de sensor en het event hieronder blijven gewoon
   werken.
2. **Kant-en-klare blueprint**, voor wie liever een keuzemenu met toestellen
   heeft, of de automation verder wil aanpassen. Titel, prijs, locatie, link
   en foto worden automatisch ingevuld, geen sjablonen zelf typen nodig, en
   tikken op de melding zelf opent de advertentie (in de Marktplaats-app
   indien geïnstalleerd, anders in de browser). Twee varianten, functioneel
   verder identiek:
   - [`new_listing_notify.yaml`](blueprints/automation/marktplaats/new_listing_notify.yaml)
     (Android) - klik de **Blueprint (Android)**-badge bovenaan dit bestand
     om 'm te importeren.
   - [`new_listing_notify_ios.yaml`](blueprints/automation/marktplaats/new_listing_notify_ios.yaml)
     (iOS) - klik de **Blueprint (iOS)**-badge.
   - **Telefoon**: een keuzemenu met je toestellen die de HA Companion App
     draaien (Home Assistant's ingebouwde "device notify"-actie - lost zelf
     de juiste, klassieke notify-service voor dat toestel op, inclusief
     foto-ondersteuning).
   - **Meldingskanaal** (optioneel, alleen Android): naam van een kanaal dat
     je al in de Companion App gebruikt, voor een eigen ringtone/prioriteit
     specifiek voor Marktplaats-meldingen.
   - **Aangepast geluid** (optioneel, alleen iOS): iOS kent geen
     meldingskanalen zoals Android; de bestandsnaam van een aangepast
     geluid dat je al via de Companion App hebt toegevoegd (Instellingen >
     Meldingen > Geluiden) is het dichtstbijzijnde alternatief.
   - Optioneel te beperken tot één specifieke zoekopdracht.
   - Home Assistant vraagt bij het opslaan zelf om een naam voor de
     automation. Krijg je die vraag niet, of hebben meerdere automations van
     deze blueprint dezelfde naam: geef ze een eigen naam via het **⋮-menu >
     Naam wijzigen** in de automation-editor.
3. **Zelf een automation bouwen**, voor volledige controle. Voor elke nieuwe
   advertentie wordt het event `marktplaats_new_listing` gevuurd, met in
   `event_data`: `entry_id`, `query`, `item_id`, `title`, `price_cents`,
   `price_type`, `url`, `location`, `image_url`.

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
- Marktplaats retourneert maximaal de 30 nieuwste advertenties per zoekopdracht (de
  sensorwaarde zelf toont wel het echte totaal aantal treffers, dat is niet afgekapt);
  bij een zeer brede zoekterm en een lange tijd zonder poll (HA uit geweest,
  netwerkstoring) kunnen advertenties tussen de 30 nieuwste "doorheen glippen" zonder
  melding.
- Advertenties verschijnen en verdwijnen continu op Marktplaats - het aantal treffers
  kan dus al bij de volgende poll weer anders zijn, ook al is er niets aan je
  zoekopdracht veranderd.
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

Stap 1 (proof-of-concept), stap 2 (custom_component) en stap 3 (HACS custom
repository) zijn af; stap 4 (aanmelding standaard HACS-store) staat in de
reviewwachtrij. Volledige, actuele planning - inclusief geplande functionaliteit
(rijkere meldingen met titel/prijs/locatie) en toekomstideeën - staat in
[`ROADMAP.md`](ROADMAP.md), dat bij elke wijziging wordt bijgewerkt.


---



##### <ins>EN</ins>

A Home Assistant integration for structurally searching for items or services on Marktplaats.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Sarnog&repository=ha-marktplaats&category=integration)
**Blueprint (Android):** [![Open your Home Assistant instance and show the blueprint import dialog for the Android notification blueprint.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FSarnog%2Fha-marktplaats%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fmarktplaats%2Fnew_listing_notify.yaml)
**Blueprint (iOS):** [![Open your Home Assistant instance and show the blueprint import dialog for the iOS notification blueprint.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FSarnog%2Fha-marktplaats%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fmarktplaats%2Fnew_listing_notify_ios.yaml)

**Status: installable as a HACS custom repository; submission to the default HACS store is in the review queue. See [`ROADMAP.md`](ROADMAP.md) for the full plan.**

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

**Via HACS** (recommended): click the HACS badge at the top of this file, or add this
repository manually as a **custom repository** in HACS (HACS > three dots > Custom
repositories > this GitHub URL, category "Integration"). This isn't inclusion in the
default HACS store itself yet (that requires a separate submission/review with HACS),
but otherwise works identically.

**Manually**, as an alternative:

1. Copy the `custom_components/marktplaats` folder into your Home Assistant
   configuration's `custom_components` folder.
2. Restart Home Assistant.
3. **Settings > Devices & services > Add integration** and search for "Marktplaats".

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

### Getting notified

There are two ways, from simple to flexible:

1. **Built in, no automation needed.** When (re)configuring a search, fill in a
   **notify service name** (e.g. `mobile_app_phone` - found under **Developer
   Tools > Actions**, search for "notify"; the part after the dot is the
   service name; a full `notify.xxx` also works, the `notify.` prefix is
   stripped automatically). The integration then sends a notification itself
   for every new listing, with title, price, location, link, and photo -
   tapping the notification itself opens the listing (in the Marktplaats app
   if installed, otherwise in the browser). **Note:** this must be a
   classic, per-target notify service (like the one
   the HA Companion App registers), not a notify entity - the modern,
   entity-based `notify.send_message` service no longer supports a photo
   attachment since Home Assistant's notify-entity redesign (empirically
   verified; see [`ROADMAP.md`](ROADMAP.md) for the technical explanation).
   If the configured service stops working, it's only logged as a warning -
   the sensor and the event below keep working regardless.
2. **Ready-made blueprint**, for a device picker instead of typing a service
   name, or to customize the automation further. Title, price, location,
   link, and photo are filled in automatically - no templates to write
   yourself - and tapping the notification itself opens the listing (in the
   Marktplaats app if installed, otherwise in the browser). Two variants,
   otherwise functionally identical:
   - [`new_listing_notify.yaml`](blueprints/automation/marktplaats/new_listing_notify.yaml)
     (Android) - click the **Blueprint (Android)** badge at the top of this
     file to import it.
   - [`new_listing_notify_ios.yaml`](blueprints/automation/marktplaats/new_listing_notify_ios.yaml)
     (iOS) - click the **Blueprint (iOS)** badge.
   - **Phone**: a picker listing your devices running the HA Companion App
     (Home Assistant's built-in "device notify" action - resolves the right
     classic notify service for that device itself, including photo
     support).
   - **Notification channel** (optional, Android only): the name of a
     channel you already use in the Companion App, for a dedicated
     ringtone/priority just for Marktplaats notifications.
   - **Custom sound** (optional, iOS only): iOS has no notification channels
     like Android; the filename of a custom sound you've already added via
     the Companion App (Settings > Notifications > Sounds) is the closest
     equivalent.
   - Optionally restrict it to a single search.
   - Home Assistant itself prompts you for a name when saving. If it doesn't,
     or if multiple automations from this blueprint end up with the same
     name, give them their own name via the **⋮ menu > Rename** in the
     automation editor.
3. **Build your own automation**, for full control. For every new listing, the
   `marktplaats_new_listing` event fires, with in `event_data`: `entry_id`,
   `query`, `item_id`, `title`, `price_cents`, `price_type`, `url`,
   `location`, `image_url`.

Each search also gets a sensor (`sensor.<name>_listings`) whose state is the number of
currently matching listings, with attributes for the number of new listings in the last
poll plus the latest few new listings - handy for a dashboard.

### Known risks

- No official support: the endpoint can change without warning.
- Marktplaats' terms of use prohibit systematic/repeated querying of their database
  without permission; they IP-block known scrapers. Hence a hard 15-minute minimum
  between searches, even if you configure a lower value.
- Marktplaats returns at most the 30 newest listings per search (the sensor's state
  itself shows the real total match count, that isn't capped); with a very broad
  search term and a long gap without polling (HA down, network outage), listings beyond
  the newest 30 can slip through without a notification.
- Listings on Marktplaats constantly appear and disappear - the match count can
  legitimately differ from one poll to the next even if your search hasn't changed.
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

Step 1 (proof-of-concept), step 2 (custom_component), and step 3 (HACS custom
repository) are done; step 4 (default HACS store submission) is in the review queue.
The complete, current plan - including planned functionality (richer notifications
with title/price/location) and future ideas - lives in [`ROADMAP.md`](ROADMAP.md),
which gets updated on every change.
