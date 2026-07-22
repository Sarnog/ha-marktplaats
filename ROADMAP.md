# ROADMAP.md

## NL

Dit bestand is de volledige, actuele planning van ha-marktplaats: alles wat af is,
alles wat gepland staat, en alle ideeën - ook nog niet besproken of goedgekeurde. Het
wordt bij **elke** wijziging aan de integratie en bij **elk** nieuw idee bijgewerkt, niet
alleen als daar expliciet om gevraagd wordt. De korte roadmap-lijst in
[`README.md`](README.md) verwijst hiernaar in plaats van de details te herhalen.

### Afgerond

1. **Proof-of-concept** (`poc/search.py`) - bevestigd dat het interne Marktplaats
   zoek-endpoint bereikbaar en betrouwbaar is; radius/prijs/conditie-filters werken;
   HA-thuislocatie kan naar een postcode omgezet worden (Marktplaats filtert alleen
   echt op afstand met een postcode, niet met lat/lon).
2. **Home Assistant custom_component** (`custom_components/marktplaats/`) - config
   flow (aanmaken + herconfigureren, alleen zoekterm verplicht), coordinator met
   dedupe-opslag en `marktplaats_new_listing`-event, sensor-platform met aantal
   matchende advertenties.
3. **Publiceren als HACS custom repository** - LICENSE, hassfest/HACS-validatie-
   workflows, brand-icoon (`custom_components/marktplaats/brand/`, Marktplaats' eigen
   "coin"-logo), GitHub Releases (v0.1.0 t/m v0.1.3, zie versiegeschiedenis onderaan).
   Installeerbaar via de HACS-badge in de README.
4. **Aanmelding bij de standaard HACS-store** - PR [hacs/default#9338](https://github.com/hacs/default/pull/9338)
   staat in de reviewwachtrij (niet automatisch afgewezen, wacht op een menselijke
   reviewer - dit kan maanden duren). Geen actie nodig totdat een reviewer reageert;
   niet zelf op de PR reageren of een dubbele PR openen (hacs-bot vraagt daar expliciet
   niet om).

### Gepland - direct gevraagd door de gebruiker

**Rijkere, direct zichtbare informatie over nieuwe advertenties (titel, prijs, locatie)**

Op dit moment toont de sensor alleen het *aantal* matchende advertenties als status;
de volledige details (titel, prijs, locatie, foto) zitten al in de data
(`marktplaats_new_listing`-event en de `latest_new_listings`-attributen van de sensor),
maar daar moet je zelf een automation voor bouwen. De gebruiker wil dit prominenter en
directer beschikbaar hebben. Uit te werken, in volgorde van voorkeur:

1. **Ingebouwde notificatie-optie in de config flow.** Bij het instellen van een
   zoekopdracht kies je een `notify`-doel (bv. `notify.mobile_app_telefoon`); de
   integratie stuurt dan zelf een pushmelding met titel, prijs en locatie in de tekst
   en de foto als bijlage, zonder dat de gebruiker een automation hoeft te bouwen. Dit
   sluit het dichtst aan bij de oorspronkelijke wens ("ik krijg een melding op mijn
   telefoon").
2. **Kant-en-klare Home Assistant Blueprint** voor wie liever zelf een automation
   bouwt/aanpast: trigger op `marktplaats_new_listing`, notify-actie met titel/prijs/
   locatie/foto al ingevuld. Lagere drempel dan zelf YAML schrijven, meer controle dan
   optie 1.
3. **Losse "laatste nieuwe advertentie"-sensor/entity** per zoekopdracht, met titel,
   prijs en locatie als eigen attributen (in plaats van de huidige lijst van de laatste
   5 in één attribuut) - handiger om direct op een dashboard te zetten.

Voorstel: begin met optie 1 als hoofdfunctionaliteit (lost de vraag rechtstreeks op),
daarna optie 2 als aanvulling voor gevorderde gebruikers, optie 3 alleen als er
concrete dashboard-behoefte blijkt.

**Optie 1 - gebouwd, wacht op verificatie in een echte HA-instantie.** Nieuw
optioneel veld `notify_service` in de config flow: een klassieke, per-doel
notify-servicenaam (bv. `mobile_app_telefoon`, geen `notify.`-prefix nodig -
die wordt automatisch gestript). De coordinator stuurt bij elke nieuwe
advertentie een melding met titel, prijs, locatie, link en foto.

**Belangrijke bevinding tijdens de bouw:** de moderne, entity-gebaseerde
`notify.send_message`-service (aan te roepen via een notify-entity) accepteert
sinds het HA-herontwerp naar notify-entities geen `data`-veld meer - empirisch
geverifieerd tegen HA 2026.7.3 (`vol.Invalid: extra keys not allowed`), en ook
bevestigd in mobile_app's eigen `MobileAppNotifyEntity.async_send_message`,
die letterlijk geen `data`-parameter heeft. Een foto-bijlage is daarmee alleen
mogelijk via de **klassieke, per-doel notify-service** (zoals mobile_app die
nog steeds registreert náást zijn entity, bv. `notify.mobile_app_telefoon`) -
dat is dus bewust de aanpak geworden, ook al is dat de "oudere" stijl en
minder toekomstbestendig dan een entity-selector. Werkt alleen voor
notify-integraties die nog zo'n klassieke service registreren; voor
entity-only notify-integraties komt er geen melding aan (wordt alleen gelogd
als waarschuwing, de sensor/het event blijven gewoon werken).
Pure logica (`_build_notify_payload`, `_format_price`,
`_normalize_notify_service`) is gedekt door tests; de daadwerkelijke
servicecall zelf is - net als de rest van de coordinator - alleen handmatig
te verifiëren in een echte Home Assistant-instantie (zie
[`tests/README.md`](tests/README.md)).

**Optie 2 - gebouwd, herontworpen na gebruikersfeedback (v0.2.2).**
[`blueprints/automation/marktplaats/new_listing_notify.yaml`](blueprints/automation/marktplaats/new_listing_notify.yaml),
met een import-badge in de README. Trigger op `marktplaats_new_listing`, met
een `config_entry`-input om optioneel tot één zoekopdracht te beperken.

**Eerste versie (v0.2.1) gebruikte een `action`-input** (ActionSelector) waarin
de gebruiker zélf een willekeurige melding-actie configureerde. Bleek in de
praktijk niet te werken zoals de beschrijving beloofde: de door de gebruiker
gekozen actie (bv. "Stuur melding" naar `notify.mobile_app_xxx`) kwam met een
lege berichttekst binnen, omdat de blueprint geen controle heeft over de
inhoud van een actie die de gebruiker zelf via de UI configureert - je zou
zelf een Jinja-sjabloon in dat actie-veld moeten typen, wat het doel van de
blueprint (niets hoeven typen) tenietdeed.

**Herontworpen (v0.2.2) met een `entity`-input** (domeinen `notify` + `script`)
i.p.v. een `action`-input: de gebruiker geeft alleen áán welke actie/entity de
melding moet versturen, de blueprint bouwt de daadwerkelijke servicecall zelf,
met titel/bericht/foto al ingevuld:

- **notify-doel** (bv. `notify.mobile_app_telefoon`) → `notify.send_message`
  met titel en bericht; geen foto (zelfde HA-beperking als optie 1: de
  entity-gebaseerde service ondersteunt geen `data`-veld).
- **script-doel** (bv. `script.stuur_notificatie`) → `script.turn_on` met
  `variables: {title, message, price, location, url, image_url}` - een
  officieel ondersteund HA-mechanisme om willekeurige data in een eigen script
  te injecteren (`ATTR_VARIABLES`, gevalideerd tegen `SCRIPT_TURN_ONOFF_SCHEMA`).
  Zo kán een foto wél meegestuurd worden, via het eigen script van de
  gebruiker.

Rekent drie sjabloonvariabelen voor: `listing_price_text` (bv. "€ 19,99"),
`listing_subtitle` (prijs + locatie) en `listing_message` (subtitle + link).
Gevalideerd tegen HA's eigen `Blueprint`/`BlueprintInputs`-schema's (metadata,
input-substitutie voor zowel een notify- als een script-doel) en alle
Jinja-templates apart gerenderd met kale Jinja2 tegen de daadwerkelijke,
YAML-gevouwen tekst (niet een met de hand overgetypte kopie - zie de
v0.2.1-les hieronder) met meerdere testgevallen (mét/zonder prijs, mét/zonder
locatie, notify- vs. script-doel). De diepere `cv.template`-compilatie zelf
vereist een draaiende `hass`-event-loop en kon dus niet lokaal gevalideerd
worden (dezelfde bekende beperking als de rest van deze repo) - test dit dus
ook zelf door de blueprint te importeren in een echte Home Assistant-instantie.

### Gepland - ideeën van Claude (nog niet besproken/goedgekeurd - graag prioriteren of afkeuren)

- **HA Repair issue bij herhaalde blokkades.** Stond al in het allereerste ontwerp
  (onderzoeksfase), maar is nooit gebouwd: als Marktplaats herhaaldelijk foutmeldingen
  geeft (mogelijk een IP-blokkade), toon een Repair issue in de HA-UI in plaats van
  alleen een falende sensor/log-regel.
- **Prijsdaling-detectie op al geziene advertenties.** Nu wordt alleen een compleet
  nieuwe advertentie gemeld; een prijsverlaging op een advertentie die al eerder
  gezien is, wordt niet apart gemeld. Zou nuttig zijn voor wie op een prijsdaling wacht.
- **Hulpmiddel om categorie-ID's op te zoeken.** Nu moet je `L1_CATEGORY_ID`/
  `L2_CATEGORY_ID` handmatig opzoeken via de browser-devtools. Een klein script of een
  HA-service die categorieën doorzoekt zou dit een stuk toegankelijker maken.
- **Paginering / limiet-verbetering.** Marktplaats geeft maximaal de 30 nieuwste
  advertenties per zoekopdracht terug; bij een zeer brede zoekterm of een lange
  periode zonder poll (HA uit geweest, netwerkstoring) kunnen advertenties tussen de
  30 nieuwste doorheen glippen zonder melding. Zou opgelost kunnen worden met
  paginering of een tijdstempel-gebaseerde aanvullende opvraging.
- **Diagnostics-platform** voor eenvoudiger troubleshooten (HA's ingebouwde
  "download diagnostics"-functie), zodat een gebruiker bij een supportvraag makkelijk
  relevante info kan delen zonder gevoelige data (zoals de postcode) prijs te geven.
- **Volledige geautomatiseerde testdekking** van config flow/coordinator/sensor via
  `pytest-homeassistant-custom-component`, wat op dit Windows-ontwikkelsysteem niet
  werkt (zie [`tests/README.md`](tests/README.md)) maar wel zou kunnen via WSL, een
  devcontainer, of puur in de al aanwezige GitHub Actions CI (Linux-runners).

### Later, apart traject

**Optioneel automatisch bieden/kopen** met een vooraf ingesteld maximumbedrag - hoog
risico op accountblokkade en vereist opslag van Marktplaats-inloggegevens. Wordt pas
opgepakt na een expliciete beslissing, en waarschijnlijk eerst als "open advertentie in
app"-actie in plaats van volledige automatisering. Zie de "Bekende risico's" in
[`README.md`](README.md).

### Versiegeschiedenis (samenvatting)

- **v0.1.0** - eerste werkende custom_component + HACS-publicatievoorbereiding.
- **v0.1.1** - fix: brand-icoon lokaal in de eigen repo i.p.v. via home-assistant/brands
  (die repo accepteert sinds HA 2026.3.0 geen nieuwe custom-integratie-iconen meer).
- **v0.1.2** - fix: `icon.png` (256x256) werd afgesneden/verschoven gerenderd door een
  bug in de render-pipeline (headless Chrome); `icon@2x.png` was altijd al goed.
- **v0.1.3** - fix: de sensorwaarde toonde `len(listings)`, dat altijd afgekapt is op
  de interne poll-limiet van 30 - bij een brede zoekterm (bv. "televisie") werd het
  aantal dus ernstig te laag weergegeven (30 in plaats van bv. 2698 werkelijke
  treffers). Gebruikt nu Marktplaats' eigen `totalResultCount`-veld uit de API-respons,
  empirisch geverifieerd dat dit *niet* afgekapt wordt door de `limit`-parameter.
  Gevonden doordat de gebruiker een afwijkend aantal zag t.o.v. handmatig zoeken op
  marktplaats.nl.
- **v0.2.0** - nieuw: optioneel `notify_service`-veld in de config flow - stuurt bij
  elke nieuwe advertentie een pushmelding (titel, prijs, locatie, link, foto) via een
  klassieke, per-doel notify-service (bv. `mobile_app_telefoon`). Zie hierboven onder
  "Gepland - direct gevraagd door de gebruiker" voor de belangrijke technische
  bevinding (de moderne notify-entity-service ondersteunt geen foto-bijlage) die de
  aanpak bepaald heeft.
- **v0.2.1** - aanvulling op v0.2.0: kant-en-klare automation-blueprint
  (`blueprints/automation/marktplaats/new_listing_notify.yaml`) met een import-badge
  bovenaan de README, plus uitleg over `notify_service` in de README zelf (stond er
  nog niet). Tijdens de actieve bug-review vóór deze release zijn twee echte bugs in
  de blueprint gevonden en gefixt: (1) een YAML-gevouwen (`>-`) meerregelig
  `{% if %}`/`{% endif %}`-blok voegde spaties toe als letterlijke tekst tussen de
  tags, waardoor de prijstekst met overtollige spaties gerenderd werd - opgelost door
  het als één samenhangende Jinja-expressie te schrijven, ongevoelig voor line-folding;
  (2) een ontbrekende locatie (`None`, geen lege string) werd letterlijk als de tekst
  "None" in de melding getoond - opgelost met een truthy `select`-filter i.p.v. een
  `!= ''`-check. Beide zijn gevonden door de daadwerkelijke, YAML-gevouwen templates
  met Jinja2 en testdata te renderen, niet door er alleen over te redeneren.
- **v0.2.2** - fix: de v0.2.1-blueprint werkte in de praktijk niet zoals beloofd - de
  door de gebruiker zelf gekozen melding-actie kwam met een lege berichttekst binnen,
  omdat een `action`-input de gebruiker zelf verantwoordelijk maakt voor het invullen
  van sjablonen, wat nergens werd afgedwongen. Herontworpen met een `entity`-input
  (notify- of script-doel): de blueprint bouwt nu zelf de servicecall, waarbij titel,
  bericht, prijs en locatie automatisch worden ingevuld (`notify.send_message` voor
  een notify-doel; `script.turn_on` met `variables` voor een eigen script, wat ook een
  foto mogelijk maakt). README bijgewerkt om het nieuwe gedrag correct te beschrijven.
  Daarnaast de README-lay-out overgenomen van de eigen wijzigingen die de gebruiker op
  GitHub aanbracht: gecentreerde titel, NL/EN-navigatielinks bovenaan, badges en
  status-regel nu per taal herhaald, `---`-scheidingslijn tussen de secties -
  vastgelegd in het algemene geheugen om bij alle (toekomstige) integraties toe te
  passen.

## EN

This file is the complete, current plan for ha-marktplaats: everything that's done,
everything that's planned, and every idea - including ones not yet discussed or
approved. It gets updated on **every** change to the integration and **every** new
idea, not only when explicitly asked. The short roadmap list in
[`README.md`](README.md) points here instead of repeating the details.

### Done

1. **Proof-of-concept** (`poc/search.py`) - confirmed the internal Marktplaats search
   endpoint is reachable and reliable; radius/price/condition filters work; the HA home
   location can be resolved to a postcode (Marktplaats only actually filters by
   distance with a postcode, not lat/lon).
2. **Home Assistant custom_component** (`custom_components/marktplaats/`) - config
   flow (add + reconfigure, only the search term required), a coordinator with dedupe
   storage and a `marktplaats_new_listing` event, a sensor platform with the number of
   matching listings.
3. **Publish as a HACS custom repository** - LICENSE, hassfest/HACS validation
   workflows, a brand icon (`custom_components/marktplaats/brand/`, Marktplaats' own
   "coin" mark), GitHub Releases (v0.1.0 through v0.1.3, see version history below).
   Installable via the HACS badge in the README.
4. **Submission to the default HACS store** - PR [hacs/default#9338](https://github.com/hacs/default/pull/9338)
   is in the review queue (not auto-rejected, waiting on a human reviewer - this can
   take months). No action needed until a reviewer responds; don't comment on the PR
   or open a duplicate one (hacs-bot explicitly asks against that).

### Planned - directly requested by the user

**Richer, directly visible information about new listings (title, price, location)**

Right now the sensor only shows the *count* of matching listings as its state; the
full details (title, price, location, photo) already exist in the data (the
`marktplaats_new_listing` event and the sensor's `latest_new_listings` attributes),
but you need to build your own automation to do anything with them. The user wants
this to be more prominent and directly available. To be worked out, in order of
preference:

1. **A built-in notification option in the config flow.** When setting up a search,
   pick a `notify` target (e.g. `notify.mobile_app_phone`); the integration sends a
   push notification itself with title, price, and location in the text and the photo
   as an attachment, no automation required. Closest match to the original ask
   ("I get a notification on my phone").
2. **A ready-made Home Assistant Blueprint** for anyone who'd rather build/customize
   their own automation: triggers on `marktplaats_new_listing`, with a notify action
   already filled in with title/price/location/photo. Lower barrier than hand-writing
   YAML, more control than option 1.
3. **A separate "latest new listing" sensor/entity** per search, with title, price,
   and location as their own attributes (instead of the current list of the last 5 in
   one attribute) - more convenient for putting directly on a dashboard.

Proposal: start with option 1 as the main feature (directly solves the request), then
option 2 as an add-on for advanced users, option 3 only if there's concrete dashboard
demand.

**Option 1 - built, awaiting verification on a real HA instance.** New optional
`notify_service` field in the config flow: a classic, per-target notify service name
(e.g. `mobile_app_phone`, no `notify.` prefix needed - it's stripped automatically).
The coordinator sends a notification with title, price, location, link and photo for
every new listing.

**Important finding made while building this:** the modern, entity-based
`notify.send_message` service (called through a notify entity) no longer accepts a
`data` field since HA's redesign to notify entities - empirically verified against HA
2026.7.3 (`vol.Invalid: extra keys not allowed`), and also confirmed in mobile_app's
own `MobileAppNotifyEntity.async_send_message`, which literally has no `data`
parameter. A photo attachment is therefore only possible via the **classic, per-target
notify service** (the one mobile_app still registers alongside its entity, e.g.
`notify.mobile_app_phone`) - so that's the deliberate approach taken here, even though
it's the "older" style and less future-proof than an entity selector. Only works for
notify integrations that still register such a classic service; entity-only notify
integrations simply won't receive a notification (logged as a warning, the
sensor/event keep working regardless). Pure logic (`_build_notify_payload`,
`_format_price`, `_normalize_notify_service`) is covered by tests; the actual service
call itself - like the rest of the coordinator - can only be verified manually on a
real Home Assistant instance (see [`tests/README.md`](tests/README.md)).

**Option 2 - built, redesigned after user feedback (v0.2.2).**
[`blueprints/automation/marktplaats/new_listing_notify.yaml`](blueprints/automation/marktplaats/new_listing_notify.yaml),
with an import badge in the README. Triggers on `marktplaats_new_listing`, with a
`config_entry` input to optionally restrict it to a single search.

**First version (v0.2.1) used an `action` input** (ActionSelector) where the user
configured any notification action themselves. Turned out not to work as the
description promised: the action the user picked (e.g. "Send a notification" to
`notify.mobile_app_xxx`) arrived with an empty message, because the blueprint has no
control over the content of an action the user configures themselves through the UI -
you'd have to type a Jinja template into that action's field yourself, which defeated
the blueprint's whole point (nothing to type).

**Redesigned (v0.2.2) with an `entity` input** (domains `notify` + `script`) instead of
an `action` input: the user only specifies which action/entity should send the
notification, and the blueprint builds the actual service call itself, with
title/message/photo already filled in:

- **notify target** (e.g. `notify.mobile_app_phone`) → `notify.send_message` with title
  and message; no photo (same HA limitation as option 1: the entity-based service
  doesn't support a `data` field).
- **script target** (e.g. `script.send_notification`) → `script.turn_on` with
  `variables: {title, message, price, location, url, image_url}` - an officially
  supported HA mechanism for injecting arbitrary data into a user's own script
  (`ATTR_VARIABLES`, validated against `SCRIPT_TURN_ONOFF_SCHEMA`). This does let a
  photo be sent, via the user's own script.

Pre-computes three template variables: `listing_price_text` (e.g. "€ 19,99" - Dutch
decimal comma, matching the rest of this integration), `listing_subtitle` (price +
location), and `listing_message` (subtitle + link). Validated against HA's own
`Blueprint`/`BlueprintInputs` schemas (metadata, input substitution for both a notify
and a script target) and every Jinja template was separately rendered with plain
Jinja2 against the actual, YAML-folded text (not a hand-retyped copy - see the v0.2.1
lesson below) across several cases (with/without price, with/without location, notify
vs. script target). The deeper `cv.template` compilation itself requires a running
`hass` event loop and couldn't be validated locally (the same known limitation as the
rest of this repo) - so also test this yourself by importing the blueprint into a real
Home Assistant instance.

### Planned - Claude's own ideas (not yet discussed/approved - please prioritize or reject)

- **HA Repair issue on repeated blocking.** Was in the very first design (research
  phase) but never built: if Marktplaats keeps returning errors (possibly an IP
  block), show a Repair issue in the HA UI instead of just a failing sensor/log line.
- **Price-drop detection on already-seen listings.** Currently only a completely new
  listing is reported; a price drop on a listing already seen before isn't reported
  separately. Would be useful for anyone waiting for a price to drop.
- **A helper for looking up category IDs.** Right now you have to find
  `L1_CATEGORY_ID`/`L2_CATEGORY_ID` manually via browser devtools. A small script or an
  HA service that searches categories would make this much more accessible.
- **Pagination / limit improvement.** Marktplaats returns at most the 30 newest
  listings per search; with a very broad search term or a long gap without polling (HA
  down, network outage), listings beyond the newest 30 can slip through without a
  notification. Could be addressed with pagination or an additional timestamp-based
  fetch.
- **A diagnostics platform** for easier troubleshooting (HA's built-in "download
  diagnostics" feature), so a user can easily share relevant info for a support
  question without exposing sensitive data (like their postcode).
- **Full automated test coverage** of config flow/coordinator/sensor via
  `pytest-homeassistant-custom-component`, which doesn't work on this Windows dev
  machine (see [`tests/README.md`](tests/README.md)) but could via WSL, a devcontainer,
  or purely in the already-present GitHub Actions CI (Linux runners).

### Later, separate effort

**Optional automatic bidding/buying** up to a preconfigured maximum price - high risk
of account suspension and requires storing Marktplaats credentials. Will only be
picked up after an explicit decision, and likely starts as an "open listing in app"
action rather than full automation. See "Known risks" in [`README.md`](README.md).

### Version history (summary)

- **v0.1.0** - first working custom_component + HACS publishing prep.
- **v0.1.1** - fix: brand icon provided locally in the repo instead of via
  home-assistant/brands (that repo no longer accepts new custom integration icons as
  of HA 2026.3.0).
- **v0.1.2** - fix: `icon.png` (256x256) rendered cropped/off-center due to a bug in
  the render pipeline (headless Chrome); `icon@2x.png` was always fine.
- **v0.1.3** - fix: the sensor state showed `len(listings)`, which is always capped at
  the internal poll limit of 30 - for a broad search term (e.g. "televisie") the count
  was therefore severely under-reported (30 instead of e.g. 2698 real matches). Now
  uses Marktplaats' own `totalResultCount` field from the API response, empirically
  verified to *not* be capped by the `limit` parameter. Found because the user saw a
  mismatched count compared to a manual search on marktplaats.nl.
- **v0.2.0** - new: optional `notify_service` field in the config flow - sends a push
  notification (title, price, location, link, photo) for every new listing via a
  classic, per-target notify service (e.g. `mobile_app_phone`). See "Planned - directly
  requested by the user" above for the important technical finding (the modern
  notify-entity service doesn't support a photo attachment) that shaped this approach.
- **v0.2.1** - addition to v0.2.0: a ready-made automation blueprint
  (`blueprints/automation/marktplaats/new_listing_notify.yaml`) with an import badge
  at the top of the README, plus an explanation of `notify_service` in the README
  itself (it wasn't there yet). The active bug review before this release found and
  fixed two real bugs in the blueprint: (1) a YAML-folded (`>-`) multi-line
  `{% if %}`/`{% endif %}` block was inserting spaces as literal text between the
  tags, so the price text rendered with stray whitespace - fixed by rewriting it as
  one contiguous Jinja expression, which is immune to line-folding; (2) a missing
  location (`None`, not an empty string) rendered as the literal text "None" in the
  notification - fixed with a truthy `select` filter instead of a `!= ''` check. Both
  were found by rendering the actual, YAML-folded templates with Jinja2 and test
  data, not by reasoning about them in the abstract.
- **v0.2.2** - fix: the v0.2.1 blueprint didn't actually work as promised - the
  notification action the user picked themselves arrived with an empty message body,
  because an `action` input makes the user responsible for filling in templates
  themselves, which nothing enforced. Redesigned with an `entity` input (notify or
  script target): the blueprint now builds the service call itself with title,
  message, price, and location filled in automatically (`notify.send_message` for a
  notify target; `script.turn_on` with `variables` for a user's own script, which also
  makes a photo possible). README updated to correctly describe the new behavior.
  Also adopted the README layout from the user's own GitHub edits: centered title,
  NL/EN nav links at the top, badges and status line now repeated per language, an
  `---` divider between the sections - saved to general memory to apply to all
  (future) integrations.
