# AGENTS.md

## NL

Dit bestand is de duurzame, canonieke bron voor de samenwerkingsafspraken van
dit project (blijft bestaan ook als externe geheugenopslag ooit leeg raakt).

### Samenwerkingsafspraken

- **Aparte repo**: `ha-marktplaats` is een volledig los project van andere
  Home Assistant integraties van deze gebruiker (zoals `ha-cure-afvalbeheer`),
  elk in zijn eigen map/repo. Nooit bestanden, commits of lookups laten
  weglekken tussen deze repo's.
- **Tweetalige documentatie**: elk `*.md` bestand in deze repo moet bij
  iedere wijziging die de status/mogelijkheden van de integratie raakt,
  bijgewerkt worden in het Nederlands (primair) en Engels (secundair), zodat
  beide altijd overeenkomen met de actuele stand van zaken. Komen er later
  meer talen bij, dan geldt dezelfde regel voor die talen.
- **Commit- en testritueel**, bij elke wijziging, zonder dat erom gevraagd
  hoeft te worden:
  1. Commits opsplitsen per logisch onderdeel (scaffolding / feature / docs),
     nooit alles in één commit.
  2. `ruff check` + `ruff format --check` en de `pytest`-suite laten slagen.
  3. Een actieve, kritische bug-review van de daadwerkelijke wijziging doen —
     niet alleen vertrouwen op ruff/pytest. Zoek naar edge cases, state die
     ergens anders bijgewerkt had moeten worden, en dergelijke. Verifieer
     vermoede bugs waar mogelijk empirisch in plaats van er alleen over te
     redeneren.
  4. Pas daarna committen en pushen.

## EN

This file is the durable, canonical source for this project's collaboration
agreements (survives even if external memory storage is ever cleared).

### Collaboration agreements

- **Separate repo**: `ha-marktplaats` is a fully independent project from
  this user's other Home Assistant integrations (such as
  `ha-cure-afvalbeheer`), each in its own folder/repo. Never let files,
  commits, or lookups leak between these repos.
- **Bilingual documentation**: every `*.md` file in this repo must be updated
  on every change affecting the integration's status/capabilities, in Dutch
  (primary) and English (secondary), so both always match the current state.
  If more languages are added later, the same rule applies to those too.
- **Commit and test ritual**, on every change, unprompted:
  1. Split commits by logical concern (scaffolding / feature / docs), never
     one giant commit.
  2. Pass `ruff check` + `ruff format --check` and the `pytest` suite.
  3. Do an active, critical bug review of the actual change — not just
     trusting ruff/pytest. Look for edge cases, state that should have been
     updated elsewhere too, and similar issues. Verify suspected bugs
     empirically where possible rather than only reasoning about them
     abstractly.
  4. Only then commit and push.
