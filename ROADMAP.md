# ROADMAP.md

## NL

Dit bestand is de ideeënbus van ha-marktplaats: toekomstige aanpassingen, verbeteringen
en uitbreidingen die nog **niet** gebouwd zijn - geordend als *should have* (waarschijnlijk
waardevol), *could have* (leuk, situationeel) en *would have* (later, apart traject). Nog
niet alles is besproken of goedgekeurd; het is een verzamelplek om uit te kiezen, te
prioriteren of af te wijzen.

De geschiedenis van wat er al gebouwd en gewijzigd is, staat **niet** hier maar in de
[release notes](https://github.com/Sarnog/ha-marktplaats/releases) van elke versie.

### Status: HACS-opname in behandeling

Er is al een pull request ingediend bij [hacs/default](https://github.com/hacs/default/pull/9338)
om ha-marktplaats in de standaard HACS-store op te nemen. Zodra deze is goedgekeurd, is de
integratie rechtstreeks in HACS te vinden en te installeren - **zonder** eerst een custom
repository toe te voegen. De PR wacht op review door de HACS-maintainers; de goedkeuringsstatus
wordt wekelijks (elke vrijdag) gecontroleerd.

### Should have

- **Paginering / limiet-verbetering.** Marktplaats geeft maximaal de 30 nieuwste
  advertenties per zoekopdracht terug. Bij een zeer brede zoekterm of een lange periode
  zonder poll (HA uit geweest, netwerkstoring) kunnen advertenties tussen de 30 nieuwste
  doorheen glippen zonder melding. Op te lossen met paginering of een tijdstempel-
  gebaseerde aanvullende opvraging.
- **HA Repair issue bij herhaalde blokkades.** Als Marktplaats herhaaldelijk
  foutmeldingen geeft (mogelijk een IP-blokkade), toon een Repair issue in de HA-UI in
  plaats van alleen een falende sensor en een regel in het log.

### Could have

- **Losse "laatste nieuwe advertentie"-sensor/entity** per zoekopdracht, met titel, prijs
  en locatie als eigen attributen - handiger om direct op een dashboard te zetten dan de
  huidige lijst van de laatste paar in één attribuut.
- **Prijsdaling-detectie op al geziene advertenties.** Nu wordt alleen een compleet
  nieuwe advertentie gemeld; een prijsverlaging op een al eerder geziene advertentie
  niet. Nuttig voor wie juist op een prijsdaling wacht.
- **Hulpmiddel om categorie-ID's op te zoeken.** De categorie-ID's moeten nu handmatig
  via de browser-devtools opgezocht worden; een klein script of een HA-service die
  categorieën doorzoekt maakt dit een stuk toegankelijker.
- **Diagnostics-platform** (HA's ingebouwde "download diagnostics") voor eenvoudiger
  troubleshooten, zodat relevante info gedeeld kan worden zonder gevoelige gegevens
  (zoals de postcode) prijs te geven.
- **Volledige geautomatiseerde testdekking** van config flow, coordinator en sensor via
  `pytest-homeassistant-custom-component`. Werkt niet op dit Windows-ontwikkelsysteem,
  maar wel via WSL, een devcontainer of de GitHub Actions CI (Linux-runners).

### Would have (later, apart traject)

- **Optioneel automatisch bieden/kopen** met een vooraf ingesteld maximumbedrag. Hoog
  risico op accountblokkade en vereist opslag van Marktplaats-inloggegevens. Pas op te
  pakken na een expliciete beslissing, en waarschijnlijk eerst als "open advertentie in
  app"-actie in plaats van volledige automatisering.

## EN

This file is the ideas box for ha-marktplaats: future changes, improvements and additions
that have **not** been built yet - grouped as *should have* (likely valuable), *could
have* (nice, situational) and *would have* (later, separate effort). Not everything here
has been discussed or approved; it's a place to pick from, prioritize or reject.

The history of what has already been built and changed is **not** here but in the
[release notes](https://github.com/Sarnog/ha-marktplaats/releases) of each version.

### Status: HACS inclusion pending

A pull request has already been submitted to [hacs/default](https://github.com/hacs/default/pull/9338)
to include ha-marktplaats in the default HACS store. Once approved, the integration can be found
and installed directly through HACS - **without** first adding a custom repository. The PR is
awaiting review by the HACS maintainers; the approval status is checked weekly (every Friday).

### Should have

- **Pagination / limit improvement.** Marktplaats returns at most the 30 newest listings
  per search. With a very broad search term or a long gap without polling (HA down,
  network outage), listings beyond the newest 30 can slip through without a notification.
  Could be addressed with pagination or an additional timestamp-based fetch.
- **HA Repair issue on repeated blocking.** If Marktplaats keeps returning errors
  (possibly an IP block), show a Repair issue in the HA UI instead of just a failing
  sensor and a log line.

### Could have

- **A separate "latest new listing" sensor/entity** per search, with title, price and
  location as their own attributes - more convenient to put directly on a dashboard than
  the current list of the last few in a single attribute.
- **Price-drop detection on already-seen listings.** Right now only a completely new
  listing is reported; a price drop on a listing already seen before is not. Useful for
  anyone waiting specifically for a price to drop.
- **A helper for looking up category IDs.** The category IDs currently have to be found
  manually via browser devtools; a small script or an HA service that searches categories
  would make this much more accessible.
- **A diagnostics platform** (HA's built-in "download diagnostics") for easier
  troubleshooting, so relevant info can be shared without exposing sensitive data (like
  the postcode).
- **Full automated test coverage** of the config flow, coordinator and sensor via
  `pytest-homeassistant-custom-component`. Doesn't work on this Windows dev machine, but
  would via WSL, a devcontainer or the GitHub Actions CI (Linux runners).

### Would have (later, separate effort)

- **Optional automatic bidding/buying** up to a preconfigured maximum price. High risk of
  account suspension and requires storing Marktplaats credentials. Only to be picked up
  after an explicit decision, and likely first as an "open listing in app" action rather
  than full automation.
