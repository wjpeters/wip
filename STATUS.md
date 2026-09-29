# Opleverstatus · 24 september 2026

Release **0.5.0**, lokale M0–M5 demo/paper/read-only-applicatie op http://localhost:4186. Ontwerpbesluit `c8ca586`; implementatie en tests `7af54c9`. Branch `codex/m0-m1`, geen remote/push. De broncode, gegevens en sleutels staan buiten iCloud. De eigenaar verzorgt externe aansluitingen na oplevering.

## Vervolgwijziging · 29 september 2026 · niet vrijgegeven

- Bevestigde volgende scope: crypto plus Amerikaanse aandelen/ETF’s, eerst met gratis bronnen en zonder betaald abonnement. Nieuwe en bestaande werkruimtes openen nu in de read-only marktstatus; een eerder opgeslagen Terminal-start wordt eenmalig naar Markten gemigreerd.
- De demo blijft beschikbaar als expliciete paper-/Lab-oefenbron. Er zijn in deze stap geen providers geactiveerd en geen externe netwerkverbindingen gestart; providerkeuze, lokale toegang en rechtenverificatie volgen apart.
- Een read-only quote-router selecteert nu per economisch instrument de eerste verse, rechten-bevestigde bron die dezelfde valuta, sessie, correctiestatus en vertraging gebruikt. De API geeft PRIMARY, AUTO_FAILOVER of NO_ELIGIBLE_SOURCE plus bronredenen terug.
- De marktenpagina toont de actieve selectie en brongezondheid. De terminal heeft een Bronnen-paneel naast de chart en een aparte live-referentie; de bestaande synthetische candlegrafiek, paperprijs en paperorders wisselen niet van venue.
- Gerichte controle: 6 market-service tests, Ruff, TypeScript, ESLint en Vite production-build geslaagd.
- Er zijn geen externe feeds geactiveerd. Failover is TESTED_WITH_FIXTURES; providerrechten en een echte netwerkverbinding zijn nog niet LIVE_VERIFIED. Releaseversie blijft 0.5.0 tot een afzonderlijke releasebeslissing.

## Gebouwd

| Mijlpaal | IMPLEMENTED binnen release-scope |
|---|---|
| M0/M1 | Behouden: lokale auth/Docker, canonieke contracten, paperpreview, atomische orders/ledger, oefenvermogen, herstelcontroles |
| M2 | Coinbase/Alpaca/Kraken read-only adapters en optionele streamservice; bronkwaliteit/rechten/prioriteiten, prijsvergelijking, FX-contract, RSS/Atom/nieuws-JSON met revisies, kalender/sessies, profielen, L2/tape/coverage; multichart/indicatoren/screener |
| M3 | DEMO/PERSONAL, privé/holding/werk-BV/eigendom en eliminaties; CSV/CAMT/broker-CSV preview/classificatie/reconciliatie; journal/correcties/kosten/FX/waarderingen/TWR/IRR; plannen/doelen/stress/Monte Carlo; afgebakende NL-2025 calculators/pensioen; entity-/versiegebonden handelsimpact |
| M4 | Afzonderlijke Codex stdio-bridge met gepind protocol en streaming; Jev HTTP choice/noul/score; beperkte tools, gegevenspreview, lokale budgetten, evidencevalidatie, ABSTAIN, synthetische shadowevaluatie |
| M5 | Officiële broncontrole en menselijke rule-review, scenariovergelijking, estateflow en encrypted vault, replay/backtest/tutorials, lokale kalendermonitor met slaap-/herstelstatus, performance/chaos/browserproeven, versleuteld herstel en documentatie |

Volledige oorspronkelijke backlog-ID's, bewijs en grenzen: [acceptatiematrix](docs/evidence/M2-M5.md). 'Gebouwd' betekent niet 'extern aangesloten'. De oorspronkelijke backlognormen zijn niet aangepast.

## Getest

- **115 backendtests geslaagd in Docker, nul skips**: financiële invarianten, importconflicten, reversals, FX, ownership, fiscale voorbeelden/grenzen, sessies/CSRF, providerfixtures, revisies, replay, jobs, vault en toegangsscheiding.
- **12 AI-adaptertests geslaagd**, ook in een container zonder netwerk. Echte Codex CLI 0.141.0 initialiseert via stdio zonder modelcall. Echte accountlogin/modelturns blijven niet uitgevoerd.
- **13 browsertests geslaagd in Chromium/WebKit**. Eén expliciete skip: de dubbele synthetische belastingsproef in WebKit; alle functionele workflows lopen in beide engines.
- Viewports 1440×900, 1920×1080, 3440×1440, 1024×768 en 390×844; licht/donker-terminal, toetsenbord, reduced motion, reflow en axe op geteste schermen. Geen gevonden axe-overtredingen; geen claim van volledige toegankelijkheidscertificering.
- TypeScript/Vite, ESLint, Ruff, Rust `cargo check --locked`, herhaalbare canonieke export en gegenereerde Pythonmodellen: geslaagd. Eén bekende niet-blokkerende Starlette/httpx-deprecationwaarschuwing.
- 500.000 synthetische events, vier charts/twintig boeken: nul sequencegaps en nul onverklaard verlies. Displaycoalescing afzonderlijk geteld. Lokale receive-to-paint p50/p95/p99 **25,7 / 33,1 / 34,1 ms**. Dit meet geen provider/netwerk of financiële requestlatentie.
- Verse Docker-installatie op nieuw volume: onboarding, lege posities/vermogen en lege PERSONAL-administratie geslaagd. Optionele services starten met lege configuratie en doen geen externe calls.
- Back-up teruggezet naar nieuwe database: **alle tien tabelhashes identiek, zeven kluisdocumenten ontsleuteld en gecontroleerd**, gewijzigde ciphertext afgewezen. Actieve gebruikersdatabase niet overschreven.
- Upgrade 0.2.0 → 0.5.0: account, één bestaande paperorder, vijf ledgerregels, gebruikersgegevens, sessie en preview onveranderd; oude auditregels behouden, één verwachte STARTUP_RECONCILIATION toegevoegd.
- Twaalf officiële fiscale bronnen succesvol opgehaald. Eerste downloadfout apart bewaard; ruleset blijft **NEEDS_HUMAN_REVIEW**.

Bewijs: [checks](docs/evidence/release-checks.json), [browserrapport](docs/evidence/e2e-results.json), [screenshots](docs/evidence/M2-M5.md), [belastingproef](docs/evidence/stream-performance.json), [restore](docs/evidence/backup-restore-m5.json), [upgrade](docs/evidence/upgrade-preservation.json), [containerhashes](docs/evidence/release-images.json).

## Ontbrekende toegang

| Aansluiting | Getest | Echte connectorstatus | Nodig van eigenaar |
|---|---|---|---|
| Synthetische demo | TESTED_WITH_FIXTURES + end-to-end | Niet van toepassing | Niets |
| Kraken/Coinbase publieke feeds | Normalisatie, subscribe, gaps, disconnect/stale | NOT_RUN_EXTERNAL_NETWORK | Expliciete read-only activatie, bronrechten, werkelijke feedverificatie; publieke kanalen hebben geen accountkey nodig |
| Alpaca aandelen | TESTED_WITH_FIXTURES | NOT_RUN_MISSING_CREDENTIALS | Eigen key/secret, exacte feed-entitlements en gebruiksrechten |
| ECB/SEC | XML/companyfacts-contracttests, begrensde probe gebouwd | NOT_RUN_EXTERNAL_NETWORK | Providerverificatie, SEC-contact; geen actieve backfill |
| Nieuws-/kalenderleveranciers | RSS/Atom/JSON-import + lokale/synthetische events | BLOCKED_ACCESS voor echte betaalde/licensed feed | Toegestane bronnen/licentie; geen leverancierdata verondersteld |
| Codex/Jev | Protocol/HTTP/privacy/budgetfixtures; echte offline CLI-init | NOT_RUN_MISSING_CREDENTIALS | Eigen toegang, beschikbare gepinde modellen, expliciete kosten-/datascopekeuze, kwaliteitsevaluatie |
| Bank/broker | Lokale CSV/CAMT/broker-CSV | Geen accountverbinding | De import werkt zonder API; een eventuele directe bankadapter is aanvullende integratie |
| Fiscale review | Officiële bronnen + deterministische tests | NEEDS_HUMAN_REVIEW | Menselijke beoordeling van ondersteunde scope/formule/bronbinding |

## Afbakening en beperkingen

- Fiscaliteit ondersteunt uitsluitend de beschreven **NL-2025-scope**. Geen volledige IB-aangifte, automatisch netto pensioen/AOW, internationale situaties of fiscaal certificaat. Zie [TAX_SCOPE](docs/runbooks/TAX_SCOPE.md).
- Geen wereldwijde realtimehistorie, ETF-holdingsfeed, historische providerbackfill of automatische volledige corporate-actionadministratie. Profielvelden zonder bron blijven onbekend. Handmatige splits en cash/assetwaarderingen zijn gebouwd. Nieuwsclustering is exact, geen semantische eventherkenning.
- Bronprioriteit is configureerbaar; incompatibele venue/feed/session/delay kan niet geruisloos als equivalent worden gekozen. Realtimebronweergave gebruikt snapshots om de twee seconden; de synthetic engineeringbenchmark is geen end-to-end live-servicebenchmark.
- De scenario-engine gebruikt expliciete aannames; geen automatische actuariële uitkeringsfase of fiscaal afgeleide huishoudfeiten. TWR/IRR vereisen juiste historische waarden en kasstromen.
- Documentvault is lokaal versleuteld. De automatische broncontrole is handmatig gestart, geen dagelijkse scheduler. Lokale kalenderwaarschuwingen werken alleen terwijl Docker draait; geen e-mail/push/Apple Agenda-koppeling. Gemiste monitoring wordt zichtbaar.
- Back-ups staan lokaal; geen off-device beleid, automatische rotatie of back-up van providerconfig/AI-volume. Geen bescherming tegen hostverlies zonder eigen veilige externe kopie.
- Alleen arm64 op deze Mac getest; WebKit is de testengine, geen afzonderlijke handmatige Safari-versie. 200% reflow via equivalent CSS-venster; geen native zoomaudit. Geen LAN/TLS/multi-user installatie of onafhankelijke pentest.
- **M6 liveorders en M7 derivaten: NOT_IN_SCOPE.** Geen betaalde dienst of vertrouwelijke cloudupload geactiveerd.

## Volgende concrete stap

Gebruik de lokale workflows nu; configureer daarna de gewenste providers volgens [PROVIDERS](docs/runbooks/PROVIDERS.md) en voer de echte read-only/modeltests uit voordat hun status naar LIVE_VERIFIED kan worden gezet. Een providerkey alleen vervangt rechtencontrole en verificatie niet. Installatie/testcommando's: [INSTALLATION](docs/runbooks/INSTALLATION.md).
