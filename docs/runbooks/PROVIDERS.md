# Provider-aansluitingen na oplevering

De app werkt zonder API-key. Alleen synthetische demo-data is actief. Er is bewust geen algemene key-invoer die ten onrechte een werkende integratie suggereert.

## Kraken

Contractcode: `services/api/app/market.py`, klasse `KrakenPublicProvider`. Methoden `normalize_ticker(raw)`, `normalize_trades(raw)` en de begrensde `probe(symbol)` gebruiken het officiële Spot v2-formaat. JSON-prijzen worden rechtstreeks als Decimal gelezen. Symboolmapping is expliciet BTC/EUR, ETH/EUR, SOL/EUR. Kraken-ID's zijn `kraken:*`; sim-ID's zijn `sim:*`. Onbekende symbolen en ongeldige quotes worden geweigerd. Een parse-succes is geen feedverbinding.

De publieke feed vereist geen key. Deze release start de probe niet en de API-container heeft geen externe netwerkroute. Voor aansluiting: maak een aparte read-only gateway/service met gecontroleerde egress naar `wss://ws.kraken.com/v2`; gebruik dezelfde schema's; implementeer reconnect, gap/stale-status, timestampsemantiek en tests; registreer exacte dekking en bronrechten. Verbind pas daarna quote/history-capabilities met de UI. De paperfill-engine accepteert uitsluitend de eigen SIMULATED-venue; uitbreiden vereist expliciete adapter- en risicotests. Een key invullen alleen is dus niet voldoende om streaming te activeren.

## Codex en Jev

`services/api/app/ai.py` legt de grens vast: Codex onderzoek/uitleg, Jev begrensde beoordeling, nooit execution/withdraw/shell/rechten. Huidige resultaten zijn `ABSTAIN` en `NOT_RUN_MISSING_CREDENTIALS`; er is geen echte modelbeoordeling. De M4-runtimeadapters en evaluaties zijn nog te bouwen. LOCAL_ONLY blijft actief tot een expliciet toegestane datascope is geconfigureerd. De lokale uitleg in de UI is deterministische tekst, geen modeloutput.

## Geheimen en overige providers

Gebruik lokale macOS-sleutelhanger waar ondersteund, anders bestanden buiten iCloud met mapmodus 700/bestandsmodus 600. `.secrets` is lokaal en gitignored. Geef credentials uitsluitend aan de service die ze nodig heeft; niet aan browser, AI of log. Exporteer nooit een credentialbestand naar WPOS/iCloud. Geen live brokerendpoint is aanwezig. M2/M3-adapters voor andere markten, banken of imports zijn niet al aangesloten of getest.

Canonieke wirecontracten: `packages/contracts/schema.json`; genereer met `rtk proxy python3 scripts/generate-contracts.py`. API-responsecontracten staan aanvullend in `packages/contracts/openapi.json`. Wijzig de schema's vóór de gegenereerde bestanden en bewijs compatibiliteit.
