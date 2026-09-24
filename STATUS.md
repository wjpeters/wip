# Opleverstatus · 24 september 2026

Release `0.2.0`, M0/M1, alleen lokaal demo/paper. Geen `LIVE_VERIFIED` provider. De gebruiker verzorgt externe aansluitingen na oplevering. De ontwikkelomgeving en alle geheimen staan buiten iCloud. Zie [README](README.md).

## Gebouwd

| Backlog | IMPLEMENTED | Afbakening |
|---|---|---|
| M0.1 | Inventarisatie en eigen lokale installatie | Oude Downloads-code en volumes behouden; eigen project/poort |
| M0.2 | ADR voor SPA, marktlaag, ledger, bus, AI en tax | Drie echte containers; geen lege Rust/NATS/AI-services |
| M0.3 | Canoniek schema en gegenereerde Python/TS/Rust | Runtimevalidatie Python; Rust compileert, geen actieve gateway |
| M0.4 | Capability-/licentiematrix | Geen veronderstelde abonnementen; externe gebruiksrechten niet bewezen |
| M0.5 | Vier schermen, gedeelde componenten en ontwerpcontract | Voor implementatie opgesteld op basis van bestaande conceptbeelden |
| M0.6 | Synthetische fixtures en modusgrenzen | Paper nooit onderdeel van echte administratie of tax |
| M1.1 | Docker, lokale auth, CSRF, Host/Origin, healthchecks | Web op 127.0.0.1:4186; API/database intern |
| M1.2 | Instrumentregistry, Kraken ticker/trade-parser en begrensde read-only probe | Parser getest; geen actieve feed of doorlopende reconnect-service |
| M1.3 | Gekoppelde watchlist/chart/ticket, bronstatus, werkruimte | Candles/volume/SMA; vier intervallen; geen docking of multichart |
| M1.4 | Spot limit IOC, bid/ask, fees, partial fills, risicolimieten | Fictieve vaste liquiditeit, 24/7 crypto; geen echte queuepositie/slippageclaim |
| M1.5 | Atomische ledger, posities en vermogenssnapshot | Decimal, balanscontrole, unieke preview/order, herstartreconciliatie |
| M1.6 | Trade Impact Preview en planbuffer | Alleen EUR-oefengeld; deterministisch cashpad, geen rendements- of belastingprognose |
| M1.7 | Lab-tutorial voor volledige flow | Zonder providerkey uitvoerbaar; voortgang binnen huidige sessie |
| Extra herstelbewijs | Versleutelde databaseback-up, lege restoretest, herstel naar nieuwe database | Handmatig; geen dagelijkse scheduler of externe back-uplocatie |

## Getest

- **52 backendtests geslaagd**, inclusief propertytests (100 voorbeelden), API, concurrentie, idempotentie, herstart en corrupte positie. Geen skips in Docker. Eén niet-blokkerende Starlette/httpx-deprecationwaarschuwing.
- **4 browsertests geslaagd**: volledige workflow en responsive/toegankelijkheidscontrole, ieder in Chromium en WebKit.
- Vijf formaten: 1440×900, 1920×1080, 3440×1440, 1024×768 en 390×844. Light/dark, reduced motion, toetsenbord, Escape en horizontale reflow.
- Axe WCAG 2 A/AA en 2.1 AA: geen gevonden overtredingen op de geteste terminal in beide thema's. Geen claim van volledige WCAG-certificering of handmatige screenreaderaudit.
- TypeScript/Vite-build, ESLint, Ruff, Rust `cargo check --locked`, gegenereerde contracten zonder drift.
- Versleutelde back-up hersteld naar nieuwe database: cash, orders en ledger identiek; gewijzigde ciphertext geweigerd.
- Warm snapshotbenchmark en lokale hostgegevens: [bewijs](docs/evidence/M1.md). Geen streaming-loadbenchmarkclaim.

## Ontbrekende toegang versus ontbrekende implementatie

| Onderdeel | Fixture/contracttest | Echte aansluiting | Nog nodig |
|---|---|---|---|
| Lokale demobron | TESTED_WITH_FIXTURES | Niet van toepassing | Geen toegang nodig |
| Kraken publieke Spot v2 | TESTED_WITH_FIXTURES | NOT_RUN_EXTERNAL_NETWORK | Publieke feed vereist geen key; eigenaar koppelt en verifieert feed, rechten, timestamps, reconnect/gaps |
| Codex | Bevoegdheids-/privacygrens getest | NOT_RUN_MISSING_CREDENTIALS | **Ook runtimebridge M4 nog niet gebouwd**, niet alleen een ontbrekende key |
| Jev/TypeSafe | ABSTAIN en privacygrens getest | NOT_RUN_MISSING_CREDENTIALS | **Ook HTTP-adapter/evaluatie M4 nog niet gebouwd** |
| Andere markt-/bank-/brokerproviders | NOT_IN_SCOPE M2/M3 | Niet aangesloten | Adapterimplementatie, rechten en verificatie |
| Nederlandse fiscale regels | Afwijzing zonder approved ruleset getest | Geen actieve ruleset | M3/M5-calculators en officiële voorbeeldtests nog niet gebouwd |

## Bekende beperkingen

De volledige M2–M5-scope uit het bouwplan is niet af: multi-source, nieuws/kalender, L2, imports, privé/BV-consolidatie, pensioen/fiscaliteit, echte AI, replay en zware prestatietests ontbreken. M6/M7 en alle live acties blijven uit.

M1 gebruikt drie vaste synthetische EUR-spotparen; er stroomt geen realtime marktdata. De UI toont maximaal de laatste 100 orders/journaalregels; het ledger-API ondersteunt paginatie en de database bewaart de volledige historie. Vermogenshistorie toont de laatste 100 ordermomenten en is geen volledige performanceberekening. Layout is vast responsief, geen dockbare workspace. Cashpad is reserve/inleg/uitgaven, geen Monte Carlo.

WebKit is de automatiseringsengine, geen apart handmatig geteste Safari-versie. Reflow bij 960×540 is getest als equivalent CSS-venster voor 200% op 1920×1080; native browserzoom is niet afzonderlijk bewezen. Alleen arm64 op deze Mac is uitgevoerd; amd64 niet getest. Sessies zijn lokaal HTTP/localhost; geen LAN/TLS-opstelling. PostgreSQL draait in het standaardimage, app/web als non-root. Audit is append-only via de API, niet bestand tegen een hostbeheerder die de database direct wijzigt.

## Reproduceren en eerstvolgende taak

Volg [INSTALLATION](docs/runbooks/INSTALLATION.md) voor exacte testcommando's en [M1](docs/evidence/M1.md) voor logs/schermafbeeldingen. Volgende concrete integratietaak: activeer een afzonderlijke read-only Kraken-stream met bronbeleid, reconnect/gaptests en actuele bronstatus. Houd `kraken:*` gescheiden van `sim:*` en behoud paperrechten. Verdere uitbreiding volgt M2 → M3 → M4 → M5; wijzig de originele backlog niet in een fictieve DONE-lijst.
