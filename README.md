# Modern Trade Terminal · lokale M0/M1-release

Een werkende paperworkflow: **instrument → grafiek → broncontrole → Trade Impact Preview → paperorder → journaal → oefenvermogen → planbuffer**.

De applicatie staat buiten iCloud: `/Users/wp/WPOS-local/projects/modern-trade-terminal`. Alleen de projectverwijzing staat in WPOS. Geen cloud-AI, live orders, abonnementen of echte rekeninggegevens. De eerdere Downloads-installatie is behouden.

## Openen

[Open de applicatie](http://localhost:4186). Kies bij de eerste opening zelf een lokaal wachtwoord van minimaal 12 tekens. Er is geen standaardwachtwoord. Het startsaldo van € 100.000 en alle koersen zijn fictief.

Voor volgende starts: dubbelklik **Start Modern Trade Terminal.command**. Docker Desktop moet draaien; Python 3 en RTK moeten beschikbaar zijn. De eerste build haalt publieke pakketten en containerimages op. De draaiende app heeft geen externe API nodig.

Handmatig, vanuit deze projectmap:

```sh
rtk proxy python3 scripts/setup-local.py
rtk proxy docker compose -f infra/compose/compose.yaml up --build -d --wait
```

Stop zonder data te wissen:

```sh
rtk proxy docker compose -f infra/compose/compose.yaml stop
```

## Gebruik

1. Kies BTC, ETH of SOL. Controleer het label **SIMULATED** en de bron.
2. Bekijk candles, volume, SMA 20 en de koerstabel. Ctrl/Cmd+K zoekt instrumenten en schermen.
3. Vul een hoeveelheid en limiet in. De preview toont exacte kosten, cash, positie en doelbuffer vóór en na uitvoering.
4. Bevestig binnen 60 seconden. De limietorder voert het direct beschikbare deel uit; het restant vervalt (IOC). Dubbele verzending maakt geen dubbele order.
5. Bekijk dezelfde mutatie in Journaal, Vermogen en Planning. Pas daar de oefenreserve en maandelijkse kasstromen aan.
6. Pauzeer de fixture in Bronnen om de storingstoestand te oefenen. Nieuwe orders worden dan geblokkeerd.

Op mobiel is de terminal een leesomgeving; orderinvoer is uitgeschakeld. De tutorial staat in Lab. Light/dark en de laatste instrument-/schermkeuze worden lokaal bewaard.

## Scope en bewijs

[STATUS.md](STATUS.md) scheidt gebouwd, getest, ontbrekende toegang en niet gebouwde onderdelen. M0 en de demo/paperdoorsnede van M1 zijn geleverd. **Dit is niet de volledige M2–M5 finance-assistent uit het bredere bouwplan.** AI-runtime, imports, belasting- en pensioenrekenwerk en extra marktdekking zijn niet als werkend voorgesteld.

- [M0-besluiten](docs/evidence/M0.md)
- [M1-tests en browserbeelden](docs/evidence/M1.md)
- [Providercontracten en aansluiten](docs/runbooks/PROVIDERS.md)
- [Installeren en testen](docs/runbooks/INSTALLATION.md)
- [Versleutelde back-up en herstel](docs/runbooks/BACKUP_RESTORE.md)
- [Privacy en veiligheidsgrenzen](docs/runbooks/PRIVACY.md)
- [Ontwerp en vergelijking met referenties](docs/design/fidelity-log.md)
