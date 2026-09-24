# Modern Trade Terminal · 0.5.0

Lokale applicatie voor marktonderzoek, paper trading, financiële administratie en Nederlandse vermogensplanning. De M0–M5-workflows zijn gebouwd voor de hieronder beschreven demo/read-only-scope. Externe aansluitingen worden door de eigenaar na oplevering geconfigureerd en geverifieerd.

[Open de applicatie](http://localhost:4186). Het bestaande account en de paperhistorie blijven behouden. Bij een nieuwe installatie kies je zelf een wachtwoord. Geen standaardwachtwoord.

Project: `/Users/wp/WPOS-local/projects/modern-trade-terminal`, **buiten iCloud**. Alleen de verwijzing staat in WPOS. Dubbelklik `Start Modern Trade Terminal.command` om te starten; Docker Desktop moet draaien.

## Van bron naar beslissing

- **Markten → Terminal**: instrument, bronvergelijking, nieuws/kalender, L2 en tape; vier gekoppelde grafieken, indicatoren, opgeslagen paneelindeling en een apart grafiekvenster. Drie synthetische crypto-EUR-markten hebben paperorders. Aandelen/ETF/FX-metadata krijgt geen fictieve livekoers.
- **Administratie**: privé/holding/werk-BV, eigendomspercentages, CSV/CAMT-import met preview, classificatie en bevestiging, dubbel journaal, correcties, waarderingen, FX en performance. DEMO en PERSONAL zijn gescheiden; PERSONAL begint leeg.
- **Planning**: doelen, maandcashflow, basis/stress, Monte Carlo, bewaarde scenario's en vergelijking. Handelsimpact is gebonden aan eigenaar, rekening en administratieversie. Geblokkeerd pensioen en belastingreserve blijven herkenbaar.
- **Fiscaliteit en pensioen**: deterministische calculators voor afgebakende Nederlandse situaties in **2025**. Conceptstatus, bronversies, officiële voorbeeldtests en menselijke rule-review. Geen volledige aangifte of automatische regelgoedkeuring.
- **Nalatenschap en documenten**: eenvoudige verdelingsscenario's met review bij juridische complexiteit; lokale versleutelde documentkluis met versies en downloads.
- **Assistent**: lokale uitleg zonder AI; optionele Codex- en Jev-adapters met expliciete gegevenspreview, beperkte rechten, budgetten en ABSTAIN. Geen actieve modelverbinding bij oplevering.
- **Lab**: replay zonder vooruitkijken, backtest met uitvoering op volgende opening, kosten/slippage en handleiding voor volledige workflows.

De papercash van €100.000 is oefengeld. Demo-imports en scenario's zijn geen persoonlijke feiten. Mobiele terminal is leesmodus. Licht/donker, toetsenbord en bronkwaliteit horen bij de werkruimte.

## Starten en stoppen

```sh
rtk proxy python3 scripts/setup-local.py
rtk proxy docker compose -f infra/compose/compose.yaml up --build -d --wait
rtk proxy docker compose -f infra/compose/compose.yaml stop
```

Gebruik nooit `down -v` op de gebruikersomgeving. De standaardinstallatie activeert geen marktprovider, model, abonnement of liveorder.

## Oplevering

- [Gebouwd, getest en ontbrekende toegang](STATUS.md)
- [M2–M5 bewijs en acceptatiematrix](docs/evidence/M2-M5.md)
- [Gebruikershandleiding](docs/runbooks/USER_GUIDE.md)
- [Installatie en tests](docs/runbooks/INSTALLATION.md)
- [Provider- en AI-configuratie](docs/runbooks/PROVIDERS.md)
- [Fiscale scope](docs/runbooks/TAX_SCOPE.md)
- [Back-up en herstel](docs/runbooks/BACKUP_RESTORE.md)
- [Privacy](docs/runbooks/PRIVACY.md)

M6 live-executie en M7 derivaten vallen buiten deze oplevering. Geen claim van wereldwijde realtime-data, fiscaal gecertificeerde software of gegarandeerd rendement.
