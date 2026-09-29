# Providers aansluiten na oplevering

De applicatie werkt volledig in de ondersteunde demoscope zonder API-key. Er is bij oplevering geen LIVE_VERIFIED feed of model. Credentials en providerrechten worden door de eigenaar na oplevering geregeld. Deze pagina beschrijft de daadwerkelijk gebouwde adapters en hun grenzen.

## Lokale configuratie

`setup-local.py` maakt ontbrekende configuraties aan zonder bestaande bestanden te overschrijven. `.secrets/` heeft modus 700, bestanden 600, buiten iCloud en Git. Bewerk daar `providers.json` en `ai_config.json`; zet echte sleutels nooit in chat, shellargumenten, screenshots of WPOS. De voorbeelden in `services/api/providers.example.json` en `services/assistant/config.example.json` bevatten alleen lege waarden.

## Read-only markten

Optioneel Compose-bestand `infra/compose/market.yaml`, profiel `market`, start een geïsoleerde service zonder financiële database, orderendpoint of hostpoort. Alle providers hebben standaard `enabled:false`. Ook weergaverechten moeten expliciet worden bevestigd. De browser leest maximaal iedere twee seconden een snapshot; dit is geen bewezen submilliseconde-stream.

- Kraken Spot v2: publieke ticker en trades voor BTC/EUR, ETH/EUR, SOL/EUR. Geen accountkey nodig; rechten en echte feedtest blijven nodig. Ontbrekende providertijd wordt als RECEIVED_ONLY gemarkeerd.
- Coinbase Advanced Trade: ticker, market_trades, level2 met eigen verbinding/sequence-scope en heartbeat. Maker-side wordt naar taker-side vertaald. Gaps/disconnects wissen de vertrouwensstatus van het boek en vereisen snapshot.
- Alpaca: quotes/trades/bars/updatedBars en correcties/cancels voor de expliciete symbolen in `AlpacaAdapter.symbols`. Vul feed en entitlements in naast key/secret. IEX wordt niet automatisch SIP. Oudere revisies buiten het geheugenvenster worden als ontbrekend gemeld. Geen historische backfill of brokerorderadapter.


### Automatische failover voor referentiequotes

GET /market/live bouwt per economisch instrument een read-only displayroute op basis van de opgeslagen bronvolgorde. De router kiest de eerste verse quote waarvan de feed RECEIVING is, de displayrechten zijn bevestigd en valuta, sessie, correctiestatus en vertraging overeenkomen. Een quote ouder dan vijf seconden, een disconnect of onbevestigde rechten maakt de bron ongeschikt. Incompatibele realtime- en vertraagde feeds blijven aparte routes.

AUTO_FAILOVER betekent alleen dat een lagere compatibele bronvoorkeur wordt getoond nadat een hoger gerangschikte kandidaat ongeschikt is. De UI toont provider, venue, prijs en reden. De selectie is uitsluitend voor analyse en chartreferentie; zij wijzigt nooit een paper- of live ordervenue. Zonder aangesloten feeds blijft de status Geen geschikte feed; fixtures worden niet als live vervanger gebruikt. Deze router is met fixtures getest maar nog niet live geverifieerd.

Start uitsluitend na je eigen keuze voor deze read-only providers:

```sh
rtk proxy docker compose -f infra/compose/compose.yaml -f infra/compose/market.yaml --profile market up -d --wait
```

Controleer Markten → Read-only koppelingen. Het feit dat bytes binnenkomen is geen voltooide onafhankelijke integratieverificatie: status `live_verified` wordt niet automatisch waar. Test symbols, tijdstempels, valuta, vertraging, licentie, disconnect/stale, gaps en herstel. `scripts/provider-check.py --help` biedt daarnaast een begrensde handmatige diagnose met `--confirm-readonly`. Deze is niet uitgevoerd tegen providers bij oplevering.

ECB XML en SEC companyfacts hebben geteste normalisatiecontracts; de begrensde diagnose kan publieke bronnen ophalen. SEC vereist een eigen contact in de User-Agent. Ze zijn geen actieve historische marktdatadienst: kalenderdekking, permanente backfill, alle SEC-companyfacts en ETF-holdings worden niet verondersteld aanwezig. De UI laat onbekende velden leeg. De SEC-parser respecteert filed/first-available tijd en revisies.

Nieuwsimport accepteert RSS/Atom of canonieke JSON: `{"articles":[{"title":"...","url":"https://...","published_at":"2025-01-01T12:00:00Z","snippet":"...","language":"nl","instruments":["BTC"]}]}`. `updated_at` is optioneel. Maximaal 100 items; hoofdlijnen/snippets/links, geen licentie op volledige artikelen verondersteld. Provider-specifieke leveranciers moeten naar dit contract mappen. Clustering is op exact genormaliseerde kop/URL; bronfamilies zijn geen bewijs van semantische onafhankelijkheid.

## Codex en Jev

Optioneel `infra/compose/ai.yaml`, profiel `ai`. Eigen container en statevolume, geen financiële DB/kluis/brokersecret. Codex CLI is gepind op 0.141.0, protocolschemas staan in `services/assistant/protocol`. Echte CLI-initialisatie is offline bewezen; echte accountlogin en modelturns niet. De bridge ondersteunt stdio, auth, threads/resume, streaming, cancel en usage. Alleen drie read-only tools met vooraf goedgekeurde context. Onverwachte shell/approval/toolrequests worden geweigerd.

Jev gebruikt de officiële TypeSafe HTTP-API met keuze-, noul- en scorecontracten. Configureer een beschikbare expliciete `jev-x.y.z` modelversie; de fixtureversie in tests is geen beschikbaarheidsclaim. Modelwijziging, timeout of ongeldige output geeft ABSTAIN; 429/529 wordt niet automatisch herhaald. De gelabelde shadowset en rapportage per taak zijn gebouwd; de meegeleverde voorspellingen zijn uitsluitend synthetische fixtures.

Vul in lokale AI-config expliciete modelnamen, eigen keys en positieve daglimieten in. De standaardlimieten nul blokkeren calls. `max_daily_microusd` en `reserve_per_request_microusd` zijn lokale reserveringsgrenzen, geen afdwingbare factuurlimiet bij een leverancier. Stel aanvullend providerbudgetten in; de app koopt niets in. Activeer pas na toestemming voor kosten en de datascope.

```sh
rtk proxy docker compose -f infra/compose/compose.yaml -f infra/compose/ai.yaml --profile ai up --build -d --wait
```

De gebruiker bevestigt vervolgens elke gegevenspreview. Alleen publieke/synthetische bronnen zijn toegelaten. Persoonlijke cloudverwerking is niet beschikbaar in deze release. Beide optionele Compose-bestanden kunnen samen worden gebruikt. De diensten hebben met lege/defaultconfig in Docker gedraaid zonder externe calls; alle echte modeltests blijven NOT_RUN_MISSING_CREDENTIALS.

## Bank en broker

CSV/CAMT.053 en broker-CSV-mapping zijn lokaal werkend. Er is geen banklogin, PSD2-koppeling of echte orderadapter. Een sleutel invullen activeert die niet. Live-executie M6 en derivaten M7 zijn afzonderlijke projecten/releasepoorten.
