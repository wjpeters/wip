# Installatie en reproduceerbare controles

Werkmap: `/Users/wp/WPOS-local/projects/modern-trade-terminal`. Niet verplaatsen naar iCloud, Desktop of Documents. Docker Desktop moet actief zijn. Shellvoorbeelden uitvoeren vanuit de projectmap.

## Start en stop

```sh
rtk proxy python3 scripts/setup-local.py
rtk proxy docker compose -f infra/compose/compose.yaml up --build -d --wait
rtk proxy docker compose -f infra/compose/compose.yaml ps
```

Open http://localhost:4186 en kies je eigen wachtwoord. Alleen de webpoort wordt gepubliceerd, uitsluitend op 127.0.0.1. Datavolume `wpos-mtt_mtt-data` blijft bij `stop` en `down` bewaard. Gebruik geen `down -v` op je gebruikersomgeving. Herstart reconciliëert cash, journaal, kostprijzen en positiehoeveelheden vóór ordertoegang.

```sh
rtk proxy docker compose -f infra/compose/compose.yaml stop
```

De eerdere installatie op 4173 is een ander project. Testomgeving `wpos-mtt-qa` gebruikt 4187 en een eigen datavolume. Vermeng deze niet.

## Ontwikkel- en testafhankelijkheden

De draaiende app heeft alleen Docker nodig; lokaal testen vraagt Python 3.13, Node/npm en Cargo. Versies zijn vastgelegd in lockfiles.

```sh
rtk proxy python3 -m venv .venv
rtk proxy .venv/bin/pip install -r services/api/requirements.lock -r scripts/requirements-backup.lock
rtk proxy npm --prefix apps/web ci
rtk proxy npm --prefix apps/web exec -- playwright install chromium webkit
rtk proxy python3 scripts/setup-local.py --qa
rtk proxy env WEB_PORT=4187 docker compose -p wpos-mtt-qa -f infra/compose/compose.yaml up --build -d --wait
```

## Controles

```sh
rtk proxy .venv/bin/ruff check services/api/app services/api/tests scripts
rtk proxy npm --prefix apps/web run lint
rtk proxy npm --prefix apps/web run build
rtk proxy python3 scripts/generate-contracts.py
rtk git diff --exit-code -- packages/contracts/generated.ts packages/contracts/generated.py packages/contracts/rust/src/lib.rs apps/web/src/generated.ts services/api/app/contracts_generated.py
rtk proxy cargo check --locked --manifest-path packages/contracts/rust/Cargo.toml
rtk proxy env WEB_PORT=4187 docker compose -p wpos-mtt-qa -f infra/compose/compose.yaml exec -T api python -m pytest tests -q -p no:cacheprovider
rtk proxy python3 scripts/run-browser-tests.py
rtk proxy .venv/bin/python scripts/benchmark.py
```

De API-tests maken zelf een tijdelijke database en verwijderen die na afloop. De browsertests plaatsen fictieve orders in de aparte QA-database; elke run heeft effect op die oefenrekening. Het QA-wachtwoord is lokaal willekeurig gegenereerd en wordt niet afgedrukt. Browserresultaten en PNG's worden vernieuwd onder `docs/evidence/`. Testtraces zijn uitgesloten van Git en kunnen testauth bevatten: niet delen.

Stop QA na gebruik, zonder gebruikersdata te raken:

```sh
rtk proxy env WEB_PORT=4187 docker compose -p wpos-mtt-qa -f infra/compose/compose.yaml stop
```

## Bij problemen

Geen verbinding: controleer Docker en de drie healthchecks. Poort bezet: wijzig de webpoort via WEB_PORT voor alle services en gebruik dezelfde origin. Wachtwoord kwijt: maak eerst een versleutelde back-up; er is geen verborgen resetendpoint. Startup-reconciliatiefout: gebruik restore naar een nieuwe database en onderzoek de afwijking; wijzig niet blind een geldsaldo. In de app verlopen preview of andere rekeningversie: maak een nieuwe preview. Gepauzeerde fixture: hervat via Bronnen.

## Eerste ingebruikname en lege staten opnieuw testen

Gebruik een nieuwe, uitsluitend voor deze test bedoelde Compose-omgeving. Deze poort is alleen voor het testscript. Het script verwacht dat het gebruikersaccount nog niet is ingericht.

```sh
rtk proxy env WEB_PORT=4188 docker compose -p wpos-mtt-empty -f infra/compose/compose.yaml up -d --no-build --wait
rtk proxy python3 scripts/run-fresh-test.py
```

De wrapper geeft het Node-script de vereiste werkmap `apps/web`. Voor opnieuw bewijzen van eerste installatie is een nieuw, leeg testvolume nodig; een bestaande testaccount geeft terecht geen setupknop.

Na de proef mag uitsluitend deze wegwerpomgeving worden opgeruimd; gebruik nooit de gebruikersprojectnaam in dat opruimcommando. In de oplevering is de tijdelijke omgeving gestopt, de testdatabase blijft voor inspectie beschikbaar.
