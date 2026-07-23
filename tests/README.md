# Tests

## NL

Deze tests draaien op gewone `pytest` + een normale `homeassistant`-package-installatie
(voor type-imports en om echte Home Assistant API-signaturen te kunnen verifieren),
maar **niet** tegen een echte draaiende `hass`-testinstantie.

**Waarom niet:** de gangbare testomgeving voor custom components,
[`pytest-homeassistant-custom-component`](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component),
importeert bij het laden `homeassistant.runner`, dat op module-niveau Unix-only
stdlib-modules gebruikt (`fcntl`, `resource`). Op het Windows-ontwikkelsysteem
waarop dit project gebouwd is, bestaan die simpelweg niet - er is geen WSL of
Docker beschikbaar om dit te omzeilen.

**Wat dit wel/niet dekt:**

- `test_api.py` - volledig getest, inclusief HTTP-aanroepen (gemockt met een
  eigen minimale async-contextmanager-nabootsing van `aiohttp.ClientSession.get`,
  zie de docstring bovenin dat bestand voor waarom niet met `aioresponses`).
- `test_config_flow_schema.py` - test de pure schema-validatie en de
  unique-id-logica (`_build_unique_id`) uit `config_flow.py`, zonder een
  draaiende `hass`.
- `test_coordinator_helpers.py` - test de pure helperfuncties uit
  `coordinator.py` (`_first_image_url`, `MarktplaatsData`).
- **Niet automatisch getest:** de daadwerkelijke `ConfigFlow`-stappen
  (`async_step_user`, `async_step_reconfigure`), de `DataUpdateCoordinator`
  zelf, en het `sensor`-platform - die hebben een echte `hass`-instantie
  nodig. Deze zijn wel zorgvuldig handmatig gereviewd tegen de daadwerkelijk
  geïnstalleerde `homeassistant`-broncode (methode-signaturen zijn stuk voor
  stuk met `grep` in de geïnstalleerde package geverifieerd, niet alleen uit
  het geheugen aangenomen). Test dit gedrag in de praktijk door de integratie
  in een echte Home Assistant-instantie te installeren.

**Update (2026-07-22):** de `pytest-homeassistant-custom-component`-blokkade
zit specifiek in `homeassistant.runner`, niet in de kale
`homeassistant.core.HomeAssistant`-klasse zelf - die construeert prima op
Windows. Voor ad-hoc, diepere validatie (bv. van blueprints/automations,
inclusief echte trigger-platformresolutie en `cv.template`-compilatie) is dit
bruikbaar: `hass = HomeAssistant('.')`, dan `homeassistant.loader.async_setup(hass)`,
en daarna eventuele `KeyError`s op ontbrekende `hass.data`-caches (bv.
`triggers`) opvangen door ze op `{}` te zetten en opnieuw te proberen -
convergeert in een paar iteraties. Zie `ROADMAP.md`'s v0.2.3-notitie voor een
concreet voorbeeld. Dit is (nog) niet verweven in de `pytest`-suite zelf
(zou een per-test `HomeAssistant()`-instantie plus dezelfde lazy-seeding
vereisen) - voorlopig alleen gebruikt voor losse, gerichte verificatie.

**Belangrijke grens van deze techniek (v0.2.4):** `async_validate_config_item`
valideert schema's en Jinja-sjabloonsyntax, maar niet of een
sjabloon-variabele op het moment dat een automation daadwerkelijk draait ook
echt bestaat. Zo compileerde `{{ inputs.marktplaats_search }}` prima, maar
faalde pas live in de gebruiker's eigen Home Assistant met
`UndefinedError: 'inputs' is undefined`, omdat Home Assistant helemaal geen
`inputs`-object in de runtime-context van een `condition: template`-stap
zet. Dat soort fouten vind je alleen door de HA-broncode na te lopen op waar
zo'n object gevuld zou worden, of door de automation echt te laten draaien -
niet door alleen deze validatietechniek te gebruiken. Zie `ROADMAP.md`'s
v0.2.4-notitie.

Als je dit project op Linux/macOS ontwikkelt (of via WSL), kun je wel de
volledige `pytest-homeassistant-custom-component`-suite gebruiken voor
config-flow- en coordinator-tests.

## EN

These tests run on plain `pytest` plus a regular `homeassistant` package
install (for type imports and to verify real Home Assistant API signatures),
but **not** against a real running `hass` test instance.

**Why not:** the standard test harness for custom components,
[`pytest-homeassistant-custom-component`](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component),
imports `homeassistant.runner` on load, which uses Unix-only stdlib modules
at module level (`fcntl`, `resource`). On the Windows development machine
this project was built on, those simply don't exist - and no WSL or Docker
is available to work around it.

**What this does/doesn't cover:**

- `test_api.py` - fully tested, including HTTP calls (mocked with a small
  hand-rolled async-context-manager stand-in for `aiohttp.ClientSession.get`,
  see that file's docstring for why not `aioresponses`).
- `test_config_flow_schema.py` - tests the pure schema validation and the
  unique-id logic (`_build_unique_id`) from `config_flow.py`, without a
  running `hass`.
- `test_coordinator_helpers.py` - tests the pure helper functions from
  `coordinator.py` (`_first_image_url`, `MarktplaatsData`).
- **Not automatically tested:** the actual `ConfigFlow` steps
  (`async_step_user`, `async_step_reconfigure`), the `DataUpdateCoordinator`
  itself, and the `sensor` platform - those need a real `hass` instance.
  These were carefully reviewed manually against the actually-installed
  `homeassistant` source (method signatures were individually verified with
  `grep` against the installed package, not assumed from memory). Verify
  this behavior in practice by installing the integration on a real Home
  Assistant instance.

**Update (2026-07-22):** the `pytest-homeassistant-custom-component` blocker
is specifically in `homeassistant.runner`, not in the bare
`homeassistant.core.HomeAssistant` class itself - that constructs fine on
Windows. For ad-hoc, deeper validation (e.g. of blueprints/automations,
including real trigger-platform resolution and `cv.template` compilation)
this is usable: `hass = HomeAssistant('.')`, then
`homeassistant.loader.async_setup(hass)`, then catch any `KeyError`s on
missing `hass.data` caches (e.g. `triggers`) by setting them to `{}` and
retrying - converges within a few iterations. See `ROADMAP.md`'s v0.2.3 note
for a concrete example. This isn't (yet) wired into the `pytest` suite itself
(would need a per-test `HomeAssistant()` instance plus the same lazy
seeding) - for now it's only used for one-off, targeted verification.

**Important limit of this technique (v0.2.4):** `async_validate_config_item`
validates schemas and Jinja template syntax, but not whether a template
variable actually exists at the moment an automation really runs. For
example, `{{ inputs.marktplaats_search }}` compiled fine, but only failed
live in the user's own Home Assistant with `UndefinedError: 'inputs' is
undefined`, because Home Assistant never puts an `inputs` object into the
runtime context of a `condition: template` step at all. Bugs like that are
only found by reading the HA source for wherever such an object would be
populated, or by actually running the automation - not by this validation
technique alone. See `ROADMAP.md`'s v0.2.4 note.

If you develop this project on Linux/macOS (or via WSL), you can use the
full `pytest-homeassistant-custom-component` suite for config-flow and
coordinator tests.
