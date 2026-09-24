# Modern Trade Terminal
## Bouwplan voor een persoonlijke trading- en Nederlandse finance-assistent

**Versie:** 1.0 — 24 september 2026  
**Uitvoering:** lokaal in Docker Compose, met optionele externe databronnen en AI  
**Gebruiker:** één eigenaar; architectuur voorbereid op meerdere juridische entiteiten  
**Status:** implementatiespecificatie; geen reeds gebouwde applicatie, uitgevoerde benchmark of persoonlijk financieel advies

Broncodes `[Sxx]` verwijzen naar `docs/SOURCES.md`. Productkeuzes en prestatiedoelen hieronder zijn ontwerpvoorstellen, niet door leveranciers gegarandeerde resultaten.

---

## 1. Productvisie en ontwerpbeslissing

Bouw niet alleen een scherm met koersen. Bouw één persoonlijke financiële cockpit waarin marktinformatie, handelsbeslissingen, vermogensadministratie en levensdoelen met elkaar verbonden zijn. De centrale workflow is:

**Ontdekken → begrijpen → simuleren → beoordelen → eventueel handelen → administreren → effect op het financiële plan volgen.**

De gebruiker moet vanuit nieuws of een koersgrafiek kunnen zien welke bestaande posities geraakt worden, wat een mogelijke transactie met risico en liquiditeit doet, en hoe die transactie zich verhoudt tot pensioen, belastingreserve en langetermijndoelen. Dit is de onderscheidende productfunctie: een **Trade Impact Preview** vóór een order, niet een losstaande financepagina naast een tradingdashboard.

### 1.1 Uitgangspunten

| Onderwerp | Besluit |
|---|---|
| Taal en regio | Nederlandse interface, optioneel Engels; EUR als instelbare rapportagevaluta; Europe/Amsterdam als standaardweergave |
| Werkelijke tijd | UTC voor opslag; expliciete beurs- en fiscale tijdzones; zomertijd niet zelf met vaste offsets oplossen |
| Marktbreedte | Eén uitbreidbaar instrumentmodel voor aandelen, ETF's, fondsen, indexen, valuta, crypto, obligaties, futures en opties |
| Eerste echte handel | Niet onderdeel van de eerste release; eerst read-only en paper trading |
| Standaardrisico | Cash/spot, long-only, geen leverage, geen withdrawals of automatische geldtransfers |
| Personalisatie | Werkruimtes, widgets, waarschuwingen, doelen, entiteiten, risicobudgetten, bronbeleid en AI-privacybeleid |
| Eigendomsstructuur | Privé, holding en werk-BV apart; consolideren alleen met expliciete eigendomsrelaties en eliminaties |
| AI | Codex voor diepgaand werk; Jev voor kleine snelle beoordelingen; berekeningen en harde veiligheidsregels in code |
| Deployment | Eén lokale installatie via Compose, geen verplichte Kubernetes, geen verplichte cloud-database |
| Beschikbaarheid | Alleen operationeel zolang de host, containers, internetverbinding en benodigde providers beschikbaar zijn |

De bestaande combinatie van loondienst en een holding/werk-BV hoort als configureerbaar profiel in de onboarding. De app mag niet uit eerdere gesprekken zelfstandig bedragen, fiscale kwalificaties, DGA-loonvrijstellingen of familiejuridische conclusies invullen. Persoonlijke gegevens worden door de gebruiker bevestigd.

### 1.2 Wat 'alle markten' betekent

Het datamodel en de interface zijn multi-asset; de daadwerkelijke beschikbaarheid wordt per provider, regio, instrument en abonnement bepaald. Een markt kan `metadata_only`, `historical`, `delayed`, `realtime_l1`, `realtime_l2`, `paper_supported` of `live_supported` zijn. Toon deze mogelijkheden afzonderlijk, niet als één groen verbindingslampje.

Een index is doorgaans een benchmark en krijgt geen generieke koopknop. Een fonds met dagelijkse NAV is niet hetzelfde als een continu verhandeld aandeel. Een fysiek goudbezit krijgt een waarderingsbron en liquiditeitskenmerk, geen fictief orderboek. Een BTC/USD-paar bij de ene exchange is niet dezelfde ordermarkt als BTC/USDT bij een andere exchange. Derivaten mogen pas verhandelbaar worden wanneer hun volledige contract- en afwikkelgedrag is geïmplementeerd.

**Vermijd de belofte dat één gratis databron alle markten volledig en realtime dekt.** De documentatie van Alpaca en IBKR laat juist verschillende feeds, toegangsrechten en abonnementsvereisten zien. [S19, S20]

## 2. Werkruimtes en verplichte functionaliteit

Gebruik een vaste app-shell met een smalle navigatierail, contextuele werkruimtetabs, een command palette en een inklapbaar AI-paneel. Binnen de Trading-werkruimte zijn panelen dockable; Wealth en Planning krijgen een rustiger ritme.

| Werkruimte | Inhoud | Kerninteractie |
|---|---|---|
| Vandaag | Persoonlijk dagoverzicht, relevante marktbewegingen, nieuwssamenvatting, portefeuille-alerts en financiële taken | Van gebeurtenis naar geraakt vermogen en concrete vervolgstap |
| Markten | Globale watchlists, screener, assetklassen, heatmaps, marktsessies en bronkwaliteit | Zoek een instrument en open een gekoppelde terminal |
| Terminal | Multi-chart, koersdetails, volumes, orderboek, time & sales, orderticket, paperposities | Van analyse naar Trade Impact Preview en paperorder |
| Intelligence | Nieuwsstroom, onderzoeksdossiers, bedrijf/assetprofielen, economische en bedrijfskalender | Bronmateriaal vergelijken en koppelen aan posities |
| Vermogen | Geconsolideerde balans, cashflow, rekeningen, exposure, performance en administratieve reconciliatie | Van totaal naar juridische eigenaar, rekening en boeking |
| Planning | Doelen, pensioen, scenario's, belastingen, nalatenschap en acties | Scenario's vergelijken met aannames en rekenverantwoording |
| Lab | Tutorials, paper trading, replay, backtests, strategieën en AI-evaluaties | Een beslissing oefenen zonder echt geld |
| Instellingen | Bronnen, credentials, privacy, lay-outs, belastingregels, systeemstatus en back-ups | Mogelijkheden en risico's van koppelingen beheren |

### 2.1 Nieuws uit meerdere wereldregio's

Ontwerp adapters voor gelicentieerde nieuws-API's, toegestane RSS/Atom-feeds en officiële persberichten van bedrijven, toezichthouders en centrale banken. De eerste release ondersteunt inhoud uit Europa, Noord-Amerika en Azië, maar presenteert geen wereldwijde volledigheid zonder bewezen dekking.

Sla per artikel uitgever, auteur indien beschikbaar, taal, regio, oorspronkelijk publicatietijdstip, update-tijdstip, gebeurtenistijd indien bekend, ophaaltijd, oorspronkelijke URL en rechten op. Scheid nieuws, analyse, opinie, bedrijfscommunicatie en onbevestigde berichten. Bewaar een correctie of intrekking als revisie.

Ontdubbel op canonical URL, tekstfingerprint en eventcluster. Een persbureauartikel dat door tien websites wordt overgenomen is niet tien onafhankelijke bevestigingen. Voeg bronfamilie en oorspronkelijke persbureauherkomst toe waar bekend. De AI mag een samenvatting alleen uit daadwerkelijk opgehaalde en toegestane content maken.

Gebruik Jev voor urgentie, onderwerp en portefeuillerelevantie; laat een tekstmodel uitgebreidere samenvattingen maken. Toon waarom een bericht voor een positie relevant is. Nieuws kan vanuit de bron een injectieaanval bevatten: behandel de volledige inhoud als onbetrouwbare data, nooit als instructies aan de agent.

Volledige artikelen, nieuwsarchieven en doorgifte aan AI zijn alleen toegestaan wanneer de licentie dat dekt. Bouw bij beperkte rechten een headline/snippet/link-ervaring. Geen paywall-bypass, geen verzonnen RSS-endpoints en geen scraping van consumententerminals.

### 2.2 Koersen en bronvergelijking

Toon voor een prijs expliciet of het om bid, ask, last, midpoint, mark, indexprijs of NAV gaat. De geselecteerde handelsplaats blijft de bron voor een uitvoerbare order; een synthetische samengestelde prijs is alleen een referentie.

Vergelijk prijzen uitsluitend wanneer instrumentidentiteit, handelsplaats of vergelijkbare dekking, valuta, sessie, corporate-actionbasis, prijstype en tijdsvenster overeenkomen. Toon anders `NIET_VERGELIJKBAAR` met reden. Vergelijk geen verouderde slotkoers met een actuele quote en noem dat geen dataprobleem.

Bereken afwijkingen in basispunten en toets tegen een instelbare grens die rekening houdt met tick size, spread, volatiliteit en tijdverschil. Maak geen universele grens voor alle assetklassen. Een afwijking geeft een waarschuwing of blokkeert een nieuwe order, maar veroorzaakt geen automatische arbitrageorder.

Alpaca onderscheidt onder andere IEX, SIP en een vijftien minuten vertraagde SIP-feed. Dit verschil moet zichtbaar blijven bij failover; twee feeds zijn niet automatisch dezelfde marktdekking. [S19]

### 2.3 Valuta

Gebruik een FX-service met bron, tijdstip, bid/ask of referentietype, base/quote-valuta en conversiepad. Bewaar oorspronkelijke bedragen en boek historische conversies met hun historische koers; herbereken historische winst niet ongemerkt tegen de huidige EUR-koers.

Scheid drie toepassingen: een koers voor dashboardwaardering, een officiële/reproduceerbare referentie voor rapportage, en een uitvoerbare conversiequote van de broker. Toon spreads en conversiekosten in de orderpreview. ECB-referentiekoersen worden doorgaans dagelijks gepubliceerd en de ECB raadt transactiegebruik af. Gebruik ze dus niet als realtime executiequote. [S23]

Stablecoins zijn afzonderlijke instrumenten met een eigen marktprijs. Neem niet aan dat één USDT of USDC exact één dollar waard is. Valuta-exposure van een ETF kan bovendien verschillen van zijn noteringsvaluta; onderliggende exposure is een aparte, brongebonden analyse.

### 2.4 Kalenders en events

Ondersteun marktsessies, feestdagen, afwijkende sluitingstijden, handelsstops, earnings, dividenddata, splits, economische publicaties, centrale-bankbesluiten en expiraties. Voeg persoonlijke financiële deadlines toe als aparte categorie.

Bewaar `scheduled_at`, `actual_at`, `published_at`, `updated_at`, oorspronkelijke tijdzone, bron en zekerheid van de planning. Voor macrodata bewaar eerste publicatie én latere revisies; backtests mogen geen herziene cijfers gebruiken vóórdat die bekend waren. Consensuscijfers moeten hun eigen bron en licentie behouden.

Toon impact op watchlists en bestaande exposure. Laat geplande waarschuwingen lokaal uitvoeren door de applicatiescheduler; meld in de UI wanneer de host offline was en een event niet op tijd kon worden gemonitord.

### 2.5 Charts, historische analyse en assetprofielen

Ondersteun candles, line/area, volume, vergelijking, logarithmische schaal, splits/dividendcorrectie, tekenobjecten en eerste indicatoren zoals SMA, EMA, RSI, MACD, ATR en VWAP. Definieer sessie- en ankerregels voor VWAP. Bereken indicatoren eerst in één canonieke backendimplementatie met fixtures; voeg worker-implementaties alleen toe met pariteitstests.

Bewaar raw en aangepaste reeksen gescheiden. Toon gaten als gaten; verzin geen verhandeld volume. Gebruik downsampling alleen voor weergave. Historische studies draaien op de vereiste oorspronkelijke resolutie en beschikbare gegevens, niet op de gerenderde grafiekpunten.

Bedrijfsprofielen bevatten identiteit, beursnoteringen, sector, bedrijfsomschrijving, rapportages, winst/cashflow/schuld, dividend en corporate actions voor zover beschikbaar. SEC EDGAR is een primaire bron voor Amerikaanse indieningen en XBRL-data, geen volledige wereldwijde bedrijfsdatabase. Internationale dekking komt van issuerfilings en afzonderlijk geteste leveranciers. [S24]

Maak asset-specifieke profieltabbladen: ETF-holdings en kosten met peildatum; crypto-netwerk, contractadres, supplydefinitie en exchangeparen; obligatiecoupon, looptijd en prijsconventie; derivaatunderlying, multiplier en settlement. Ontbrekende informatie blijft onbekend en wordt niet door AI 'aangevuld'.

### 2.6 Orderflow en koop-/verkoopdruk

Een transactie heeft een koper en een verkoper. Toon daarom geen ongedefinieerd 'percentage kopers'. Toon **agressief koop-/verkoopvolume**, orderboekdisbalans en datadekking, telkens voor een concrete handelsplaats en periode.

Voor bekende agressorzijde:

```text
buy_pressure = buy_initiated_volume / (buy_initiated_volume + sell_initiated_volume)
coverage = classified_volume / total_observed_volume
```

De noemer nul geeft `N/A`. Leg vast of volume in basisasset, contracten of quote-notional wordt gemeten. Bij onbekende agressorzijde toon `unknown`; een afgeleide classificatie krijgt een methodenaam en kwaliteitsstatus. Kraken documenteert bijvoorbeeld `side` als de kant van de takerorder; elke provider moet afzonderlijk op zulke semantiek worden getest. [S22]

Futures/options open interest, funding, liquidations, greeks en volatiliteit zijn optionele capabilitymodules. Toon afgeleide waarden met model, parameters en timestamp. Een FX-tickvolume mag niet als wereldwijd werkelijk handelsvolume worden gepresenteerd.

### 2.7 Tutorial, paper trading en replay

Maak vier expliciete omgevingen: `DEMO`, `PAPER`, `READ_ONLY_LIVE` en later `LIVE`. Bewaar hun data en orderrechten strikt gescheiden. Demo gebruikt herkenbare fictieve profielen; paper mag echte marktdata gebruiken maar altijd met een prominent simulatielabel. Paperposities en oefengeld mogen nooit in de werkelijke balans of fiscale feiten belanden. De planimpact van een paperorder wordt uitsluitend in een afzonderlijk gemarkeerd scenario berekend.

De tutorial leert instrument zoeken, bronstatus lezen, chart gebruiken, risico bepalen, paperorder uitvoeren, resultaat verklaren en impact op het vermogensplan beoordelen. Voeg opdrachten toe voor spread, slippage, FX-kosten, overconcentratie en verouderde data. Beloon begrip, niet zoveel mogelijk trades.

Het papermodel houdt rekening met bid/ask, kosten, latentie, gedeeltelijke fills, beperkte liquiditeit en handelsuren. Een limietorder vult niet automatisch omdat een candle de prijs raakte. Orderboekwachtrijpositie is een expliciete aanname, geen waargenomen feit. Een marketorder vult niet tegen de middenkoers zonder spread.

Replay gebruikt dezelfde eventcontracten en gesimuleerde klok als live. Een backtest krijgt vaste datasetversies, een point-in-time universum, oorspronkelijke nieuws/macrocijfers en een embargo op toekomstige informatie. Toon overfitting, gevoeligheid voor kosten, walk-forward-resultaten en drawdowns. Paperresultaten zijn geen garantie voor live-uitvoering.

## 3. Visueel productcontract

Het afzonderlijke `docs/DESIGN_SYSTEM.md` is verplicht. De hoofdrichting is **premium instrumentenpaneel, rustig en precies**: diepe grafiettinten, goede typografie, gedoseerde kleur, hoge informatiewaarde en betekenisvolle animatie. Geen marketinghero, generieke kaartjeswand, overdadige glow of decoratieve 3D die charts vertraagt.

Kernfuncties voor personalisatie zijn dockable panels, opslaan en herstellen van werkruimtes, gekoppelde instrumentselectie tussen charts/nieuws/ticket, multi-monitorvriendelijke pop-outs, instelbare dichtheid, light/dark, toegankelijke kleuren, Nederlandse/getoonde beursnotatie en een toetsenbordgerichte command palette.

De drie kenmerkende visuals zijn een **vermogenspad met scenario-bandbreedtes**, een **herleidbare exposurekaart** en een **Trade Impact Preview** waarin vóór/na naast elkaar staat. Een grafiek moet ook via een toegankelijke tabel te begrijpen zijn. Gebruik kwalitatieve badges met concrete betekenis, geen neppe 'AI intelligence score'.

Lever vóór de brede implementatie referenties voor Terminal, Vermogen, Planning en Source Health op, plus de belangrijkste fout- en mobiele staten. De developer kan hiervoor een image-generationtool gebruiken; de uiteindelijke UI blijft echte code en data. Vergelijk later browserbeelden met deze referenties.

## 4. Technische architectuur

### 4.1 Gekozen stack

| Laag | Voorkeur | Rol en begrenzing |
|---|---|---|
| Frontend | React 19.3 of nieuwere bewezen compatibele stabiele versie, TypeScript, Vite | Interactieve lokale SPA; geen SSR op het tickpad |
| Styling | Tailwind CSS, eigen designtokens, toegankelijke headless primitives | Eigen visuele identiteit; niet een ongewijzigd componenttemplate |
| Serverstate | TanStack Query | Verzoeken, snapshots, mutations en cache; niet iedere tick in querycache schrijven |
| UI-state | Kleine externe stores, bijvoorbeeld Zustand | Lay-outs, selectie en voorkeuren; subscriptions per instrument/paneel |
| Workspace | Dockview achter eigen layoutadapter | Docking, bewaren/herstellen; licentie en compatibiliteit vastleggen |
| Tradingcharts | TradingView Lightweight Charts | Zelf aangeleverde data, eigen overlays/indicatorlogica |
| Overige visuals | Een consistente chartlaag, bijvoorbeeld ECharts; SVG voor eenvoudige figuren | Scenario's, heatmaps, cashflows; alleen laden waar nodig |
| Datagrids | AG Grid Community, met eigen adapters/renderers | Betaalde mogelijkheden uitsluitend na expliciete licentiekeuze |
| Marktgateway | Rust + Tokio | WebSocketverbindingen, parsing, normalisatie, orderboekopbouw, snelle distributie |
| Domein-API | Python + FastAPI + Pydantic | Portfolio, planning, risk, configuratie, permissies en OpenAPI |
| Jobs/rekenwerk | Python-workerprocessen, Polars/NumPy waar passend | Historische analyse, import, Monte Carlo, nieuws en fiscale updates |
| Canonieke opslag | PostgreSQL | Ledger, identiteit, events, rulesets, scenario's, configuratie en audit |
| Marktarchief | Parquet + DuckDB in workers | Compacte historische datasets en scans; geen tweede authoritative geldboekhouding |
| Eventtransport | NATS + JetStream voor gekozen duurzame streams | Ontkoppeling en replay; duplicates en reconnects expliciet afhandelen |
| AI-bridge | Afgesloten Node/TypeScript-proces voor Codex | Codex App Server via stdio, toolpolicy en sessiebeheer |
| Jev | Python/HTTP-adapter in aparte jobpool | Alleen kleine begrensde classificaties buiten de koers-hot-path |
| Operations | Compose, structured logging, OpenTelemetry; observabilityprofiel optioneel | Lokale diagnose zonder externe telemetryplicht |

React publiceert momenteel 19.3; Vite levert een moderne React/TypeScript-toolchain. De keuze voor een SPA is hier een ontwerpbesluit: de terminal is vooral een lokale interactieve werkruimte, geen SEO-site. Bestaande Next.js-projecten hoeven niet herbouwd te worden, maar start niet tegelijk een Vite- én Next-app voor dezelfde terminal. [S08, S09, S10, S11]

Lightweight Charts is een andere bibliotheek dan TradingView Advanced Charts/Trading Platform. Volgens de huidige TradingView-pagina worden die laatste licenties niet aangeboden voor persoonlijke/hobbyprojecten; baseer deze lokale persoonlijke app dus niet op veronderstelde toegang. Lightweight Charts is wel open source, met toepasselijke licentie-/attributievoorwaarden. [S13, S14]

AG Grid Community en Enterprise hebben verschillende mogelijkheden. Ontwerp de eerste scope op Community en bouw bijvoorbeeld geen ongedocumenteerde afhankelijkheid van betaalde pivoting of ingebouwde exports. [S15]

### 4.2 Modulaire kern, geen overmatige microservices

De Python-codebase blijft een modulaire monoliet met domeinmodules. Splits processen op omdat hun belasting of bevoegdheden verschillen, niet om elke feature een service te geven. Rust bezit feednormalisatie en orderboeken; Python bezit geld, fiscale logica, portfolio en orderbeleid. Eén begrip krijgt niet twee tegenstrijdige authoritative implementaties.

Eerste Compose-topologie:

```text
browser
  └─ web / reverse proxy (alleen gepubliceerde lokale ingang)
       ├─ api (domein, auth, orderpreview, planning)
       ├─ market-gateway (streaming, quote snapshots)
       └─ ai-stream via geauthenticeerde api

market-gateway ── NATS/JetStream ── api / workers
api / workers ── PostgreSQL
workers ── Parquet-archief / DuckDB
api ── beperkte toolgateway ── codex-bridge ── externe Codex-service
workers ── Jev-adapter ── TypeSafe API

optionele profielen: observability / broker-gateway / zwaardere analytics
```

De zeven kerncontainers zijn `web`, `api`, `market-gateway`, `worker`, `postgres`, `nats` en `codex-bridge`. Containers voor broker-gateways of observability zijn optioneel. Geen Redis, Kafka, ClickHouse, Kubernetes of vector-database toevoegen zolang een concrete benchmark of functie dat niet rechtvaardigt. PostgreSQL full-text search is een goede eerste zoeklaag; embeddings zijn optioneel en privacygebonden.

### 4.3 Scheid drie paden

**Koerspad:** upstream WebSocket → parser → validatie → canoniek event → lokale snapshot/orderboek/indicatorupdates → geautoriseerde subscribers → browser. Geen AI-call, nieuwsophaling, rapport of complexe SQL in dit pad.

**Beslispad:** vastgelegde snapshot/nieuwsevent → deterministische filters → eventuele Jev-beoordeling → scenario of alert → optionele Codex-uitleg → policycheck → handmatige bevestiging wanneer geld geraakt wordt.

**Administratiepad:** broker/import events → validatie en deduplicatie → ledgertransactie → portfolioherberekening → fiscale jaarfeiten → planningprojectie. Een koersweergave mag een boeking nooit creëren.

Tokio biedt het asynchrone Rust-runtimefundament; JetStream biedt persistente eventvoorzieningen. De uiteindelijke latency, correctheid en doorvoer moeten met deze concrete applicatie worden gemeten. [S16, S17]

## 5. Connectorplatform en datakwaliteit

### 5.1 Adaptersoorten

Definieer afzonderlijke interfaces voor `MarketDataProvider`, `ExecutionProvider`, `NewsProvider`, `FundamentalsProvider`, `CalendarProvider`, `FXProvider`, `AccountImportProvider`, `TaxSourceProvider` en `AIProvider`. Eén leverancier kan meerdere interfaces aanbieden, maar elke capability heeft eigen rechten, status en tests.

De gebruikersinterface spreekt nooit direct met de provider. Providerkeys staan uitsluitend aan de serverzijde. Een nieuwe bron vraagt een adapter, capabilitymanifest, mapping, tests en onboardingformulier, niet een aanpassing in alle schermen.

Voor een nieuw bronprotocol is implementatiecode nodig. 'No-code bron aansluiten' geldt alleen voor configuraties van reeds ondersteunde protocollen zoals een goedgekeurde RSS-feed of CSV-mapping; een willekeurige API wordt niet magisch compatibel.

### 5.2 Capabilitymanifest

Minimaal de volgende velden:

```text
provider_id, adapter_version, schema_version
asset_classes, regions, venues, origin_feed_ids
capabilities: metadata, history, quotes, trades, l2, news, fundamentals, calendar
history_depth, supported_intervals, adjustment_modes
is_realtime, declared_delay_ms, snapshot_or_stream
supports_sequence, supports_replay, supports_orderbook_checksum
max_subscriptions, requests_per_window, connection_limits
license: display, non_display, storage, derived_data, redistribution, ai_processing
retention_policy, entitlement_expiry, professional_status_requirement
health, last_success_at, last_error, last_verified_at
execution_capabilities: order_types, time_in_force, precision, reconciliation
```

`supports_sequence` betekent provider-specifieke sequence-semantiek, niet dat elke oplopende trade-ID zonder gaten moet zijn. Reconnect, replay en gap detection moeten gebaseerd zijn op de documentatie van het concrete kanaal.

### 5.3 Eerste bronvolgorde

| Categorie | Eerste integratiepad | Kanttekening |
|---|---|---|
| Crypto marketdata | Kraken spot WebSocket; tweede adapter Coinbase Advanced Trade | Venue-specifieke prijzen; geen globale geconsolideerde waarheid [S21, S22] |
| Amerikaanse aandelen | Alpaca data-adapter | Feed en abonnement bepalen actualiteit/dekking [S19] |
| Breder beursuniversum | IBKR-adapter, aanvankelijk read-only | Contractidentificatie, abonnementen, sessies en gatewaywerking verifiëren [S20] |
| Referentie-FX | ECB | Rapportage/controle, niet executie [S23] |
| Uitvoerbare FX | Gekozen brokerconnector | Quote, spread, hoeveelheid en geldigheid horen bij dezelfde ordercontext |
| Company fundamentals | SEC EDGAR voor US; internationale provider achter hetzelfde contract | Geen EDGAR-werelddekking claimen [S24] |
| Nieuws | Toegestane RSS/Atom, officiële publicaties, gelicentieerde API | Eerst endpoints en gebruiksrechten controleren, pas dan activeren |
| Kalenders | Officiële beurs/centrale-bankkalenders plus provider voor earnings/macro | Scheid geplande, bevestigde en herziene tijden |
| Persoonlijke financiën | CSV, CAMT.053 en brokerexports, daarna ondersteunde read-only API's | Geen bank- of DigiD-wachtwoorden scrapen |
| Fiscaliteit | Belastingdienst, officiële publicaties, wetgeving en parlementaire dossiers | Per regelversie bron, status en menselijke goedkeuring |

Deze leverancierskeuzes zijn een startvolgorde, geen verplicht abonnement en geen bevestiging van accountgeschiktheid van de gebruiker. Leg actuele dekking, tarieven, licenties en Nederlandse beschikbaarheid vast voordat een betaalde/live koppeling wordt gekozen. Bestaande TradingView/n8n-workflows kunnen later via ondertekende, replaybestendige webhooks alerts aanleveren; niet rechtstreeks orders doorgeven.

### 5.4 Instrumentidentiteit

Gebruik een interne stabiele `instrument_id`. Voeg waar toepasselijk ISIN, FIGI, exchange-MIC, broker-contract-ID, listing, handelsvaluta, base/quote, chain-ID en contractadres toe. Een ticker is geen unieke identiteit. Bewaar symbol mappings met geldigheidsperioden; splits, fusies, tickerwijzigingen, delistings en tokenmigraties blijven reproduceerbaar.

Contractspecifiek zijn tick size, lot size, minimum notional, multiplier, expiry, strike, option right, settlementvaluta en settlementmethode vereist. Een listing en de economische onderliggende asset zijn verschillende entiteiten.

### 5.5 Canonieke eventenvelop

```text
id, event_type, schema_version, provider_id, adapter_version
instrument_id, venue_id, origin_feed_id, source_event_id
source_time_utc_ns (optioneel indien bron geen timestamp geeft)
received_at_utc, received_monotonic_ns, published_at_utc
sequence (met namespace), session_id, revision_of
quality_flags, delay_class, entitlement_id, trace_id
payload
```

Gebruik decimal strings/fixed-point voor financiële hoeveelheden. Nanosecondes en andere 64-bit integers gaan als strings over JSON om JavaScript-precisieverlies te voorkomen. Elk event wordt tegen zijn schema gevalideerd; foutieve events gaan naar een quarantine met reden en teller.

Naast marktgebeurtenistijd bewaart de researchlaag `first_available_at`: het eerste moment waarop de applicatie de informatie kon kennen. Dit is noodzakelijk voor eerlijke replay en causale analyses. Een gecorrigeerd artikel of financieel statement overschrijft de oorspronkelijke versie niet.

### 5.6 Herverbindingen, overbelasting en dataretentie

Gebruik persistente verbindingen, connection pooling, parallelle onafhankelijke requests, requestdeduplicatie, bounded queues, backoff met jitter, providerquota en circuit breakers. Prioriteer actieve instrumenten, open risico en zichtbare schermen; subscribe niet op het gehele mondiale universum.

Quoteweergave mag tussentijdse updates per instrument samenvoegen vóór rendering. Trades die volumes bepalen, orderboekdeltas, fills, boekingen en risico-events mogen niet stilzwijgend worden weggegooid. Gebruik bij een bookgap een nieuwe snapshot en provider-specifieke resync. Toon tot die tijd `BOOK_UNTRUSTED`.

JetStream en reconnects kunnen herlevering opleveren. Ontwerp voor at-least-once verwerking met idempotente consumers en duurzame checkpoints. Maak geen universele exactly-once-belofte over provider, bus, database en broker. Gebruik een transactional outbox waar domeinmutaties en eventpublicatie bij elkaar horen.

Start met configureerbare retentie van geselecteerde ticks/orderboeken, geaggregeerde candles en noodzakelijke fiscale/ledgerdata. Bepaal bewaartermijnen pas na schijfbudget- en licentiecontrole. Bij schijfdruk wordt een dataopname zichtbaar begrensd; order- en ledgeraudit gaan nooit stilzwijgend verloren. Exporteer waar toegestaan naar gecomprimeerde Parquetpartities met manifest, checksum en dataversie.

## 6. AI-architectuur: Codex, Jev en deterministische logica

### 6.1 Verdeel taken expliciet

| Component | Wel | Niet |
|---|---|---|
| Deterministische kern | Prijsvalidatie, exposure, orderlimieten, boekhouding, belastingberekening, scenarioformules | Vrije interpretatie van ontbrekende feiten |
| Jev | Nieuws classificeren, urgentie, relevantie, documenttype, atomair bewijsoordeel, routering naar review | Definitieve fiscale conclusies, kans-op-winst claimen, risk limits negeren, rechtstreeks handelen |
| Codex | Onderzoek, uitleg, vergelijking, plannen, toegestane tools gebruiken, analyseartefacten voorbereiden | Uit geheugen koersen/tarieven verzinnen, productiecode wijzigen, bankgeheimen lezen, orders autonoom uitvoeren |
| Mens | Doelen/risicobeleid bevestigen, gevoelige data vrijgeven, regels goedkeuren, live-acties bevestigen | Iedere koersupdate handmatig hoeven verwerken |

De meeste operationele 'snelle beslissingen' horen niet bij een model: verouderde data blokkeren, een limiet toetsen of een percentage berekenen is code. Jev wordt ingeschakeld wanneer een klein inhoudelijk oordeel werkelijk nodig is.

### 6.2 Echte Codex-integratie

Er zijn twee gescheiden toepassingen: de **developer-Codex** bouwt de applicatie; de **runtime-Codex** ondersteunt de gebruiker binnen de applicatie. Die hebben aparte workspaces, toegangsrechten en credentials.

De officiële Codex SDK ondersteunt programmatische integratie. Voor een rijke ingebouwde assistent met sessies, geschiedenis, goedkeuringen en gestreamde events beschrijft OpenAI de App Server. De huidige documentatie markeert het WebSockettransport als experimenteel; gebruik voor deze lokale bridge standaard stdio en pin CLI/protocolversies. Genereer de protocoltypen vanuit dezelfde geïnstalleerde CLI-versie. [S06, S07]

De browser praat met de eigen geauthenticeerde API. De Node-bridge start een lokaal Codex-proces via stdio en vertaalt events naar een beperkte UI-stream. Publiceer de Codexpoort niet op het LAN. Geef ieder gesprek context over huidig instrument, geselecteerde entiteit, gekozen tijdstip en toegestane datacategorieën.

Implementeer een beperkte eigen toolgateway, bijvoorbeeld met MCP-tools die Codex mag aanroepen:

```text
market.get_snapshot(instrument_id, venue_id)
research.search_news(query, as_of, source_filters)
portfolio.get_exposure(entity_scope, as_of)
planning.run_scenario(scenario_id, approved_assumptions)
tax.explain_calculation(calculation_id)
calendar.get_relevant_events(scope, range)
orders.preview_intent(intent)          # alleen berekenen, geen order plaatsen
reports.prepare_report(report_spec)    # lokaal artefact, niet automatisch versturen
```

De bridge is geen algemene JSON-RPC-proxy: hanteer een expliciete allowlist voor sessie- en analysehandelingen. Blokkeer onder meer directe shell-/command-/process-aanroepen, configuratiewijzigingen en het toevoegen van plugins of connectors vanuit de runtime-UI. Schakel niet-benodigde ingebouwde uitvoertools uit en bewijs met integratietests dat ook het model zelf geen alternatieve executieroute heeft. Een read-only bestandsinstelling alleen vervangt deze controle niet. [S07]

De server valideert iedere toolaanroep en scope onafhankelijk van de tekst van de agent. Een toolclaim 'de gebruiker heeft toestemming gegeven' geldt niet als toestemming. Bied runtime-Codex geen `submit_order`, `withdraw`, algemene SQL-console of onbeperkte shell aan. Een normale analyse vraagt in de eerste release geen vrij gegenereerde code-uitvoering.

Gebruik ondersteunde authenticatie, een aparte Codex-configuratiemap en een healthcheck. Neem niet aan dat de bestaande ChatGPT-appsessie automatisch beschikbaar of voldoende gelicentieerd is in Docker. Toon accountstatus, rate limits, werkelijke verbruikskosten voor zover beschikbaar en een configureerbaar budget.

### 6.3 Jev-integratie zonder verzonnen SDK

De gecontroleerde TypeSafe-documentatie beschrijft een HTTP-endpoint `/v1/systemone`, een Python-SDK en de primitives `choice`, `score` en `noul`. Gebruik die gedocumenteerde interface; verzin geen TypeScript-pakket of API-aanroep. Een eigen Python-adapter mag HTTP gebruiken met pooling, deadlines en een schema-validator. [S01, S02]

Stel per vraag één klein afgebakend probleem. Bijvoorbeeld: 'Is dit een officiële earningspublicatie?', 'Welke van deze nieuwslabels past?', of 'Is dit bericht relevant voor deze assetklasse?' Geef de benodigde gecontroleerde context mee. Een samengesteld oordeel over een complete beleggingsstrategie wordt opgesplitst of gaat naar Codex/mens.

**Intern contract, niet de externe TypeSafe-respons:**

```text
FastAssessment:
  assessment_id
  task_id + task_version
  input_snapshot_id + input_hash
  provider + requested_model + returned_model
  source_event_ids
  answers[]: question_id, primitive, value, probabilities?, confidence?
  disposition: DISPLAY | PRIORITIZE | REVIEW | ABSTAIN
  validity_deadline
  received_at + duration_ms
  schema_validation_status
```

Bewaar de ruwe gestructureerde antwoorden en de eigen disposition afzonderlijk. Jev's `confidence` bij Choice/Score is afgeleid van de kansverdeling; Noul levert niet hetzelfde confidenceveld. Het is geen kans dat een trade winstgevend wordt. Evalueer domeinspecifieke classificatiekwaliteit en drempels op eigen gelabelde data. [S03]

Maak een evaluation-set met handmatig gelabelde echte/toegestane of synthetische voorbeelden, waaronder ambiguïteit, te weinig informatie, meertaligheid en promptinjectie. Meet confusion matrices, precision/recall voor kritieke klassen, kalibratie waar van toepassing, abstention rate en foutkosten. Laat modelwijzigingen eerst shadowdraaien. Een automatisch veranderende `latest`-alias mag niet stilzwijgend een gevalideerde beslisregel vervangen.

Bij timeout, ongeldige output of onvoldoende context is de uitkomst `ABSTAIN`. Bestaande prijsupdates en deterministische veiligheidsregels blijven werken. Laat een cloud-AI-storing niet de terminal stilzetten. Voor Jev stel je een deadline en inputlimiet per taak in, afgeleid van een gemeten pilot; vendorbenchmarks zijn geen SLA voor deze applicatie.

### 6.4 Explainability en provenance

Toon bij een AI-analyse vier delen: **waargenomen feiten**, **gebruikte berekeningen**, **interpretatie/aannames** en **ontbrekende informatie**. Koppel bedragen aan een calculation-ID en nieuwsclaims aan bronmateriaal. Toon gebruikte modelversie, datatijdstip en geldigheidsduur waar relevant.

Een uitleg kan nooit een willekeurig bedrag toevoegen dat niet uit een toolresultaat of gebruikersinput komt. Valideer relevante getallen en bron-ID's vóór weergave. Dit is een controleerbare uitleg van gebruikte data en berekeningen, geen verzoek om interne verborgen modelredenering te tonen.

### 6.5 Privacy en cloudgrens

Lokaal hosten betekent niet dat AI-inferentie lokaal plaatsvindt. Codex en TypeSafe kunnen informatie naar een externe dienst sturen. TypeSafe vermeldt in zijn privacybeleid onder meer Amerikaanse hosting en dat input niet wordt gebruikt voor training/fine-tuning; dat is nog geen garantie van nulretentie of dataverwerking uitsluitend in Nederland. [S04]

Maak drie beleidsstanden: `LOCAL_ONLY` (geen externe modelcalls), `PUBLIC_DATA_AI` (alleen toegestane publieke gegevens) en `APPROVED_PERSONAL_AI` (door de gebruiker toegestane geminimaliseerde persoonlijke context). Geef de gebruiker een preview van gevoelige velden vóór vrijgave. Standaard geen BSN, IBAN, geboortedata van derden, testamenten, volledige belastingaangiften, wachtwoorden of API-keys naar modellen.

Persoonlijke documenten worden eerst lokaal geparsed. Alleen expliciet geselecteerde gegevens komen in modelcontext. Houd embeddings, logs, foutmeldingen en traces onder hetzelfde databeleid; ook een embedding kan gevoelige informatie representeren.

## 7. De persoonlijke financiële administratie

### 7.1 Eén financiële waarheid, meerdere perspectieven

Maak een gestructureerd vermogensmodel met `Person`, `Household`, `LegalEntity`, `Ownership`, `Account`, `Asset`, `Liability`, `Transaction`, `JournalEntry`, `Position`, `Valuation`, `IncomeStream`, `Expense`, `Goal`, `PensionRight`, `TaxFact`, `Document` en `Scenario`.

Een rekening heeft één vastgelegde juridische eigenaar. Een huishoudweergave is een rapportageperspectief, geen automatische gezamenlijke eigendom. Elke asset heeft valuta, hoeveelheid, waarderingsmethode, waarderingstijdstip, liquiditeit en eventuele beperkingen. Pensioeninkomen en de geschatte kapitaalwaarde van hetzelfde pensioen mogen niet dubbel meetellen in de projectie.

Gebruik voor de geldadministratie een dubbel boekhoudkundig journaal met controleerbare balans. Bewaar brontransacties ongewijzigd en leg correcties vast met tegenboekingen/revisies. Leg de gekozen multi-currency-methode vast: oorspronkelijke valuta per posting plus consistente functionele waardering en expliciete FX-/waarderingsverschillen. Een effectentransactie heeft cash, hoeveelheid, kosten en eventuele vorderingen/verplichtingen, niet alleen een tekstlabel 'koop'.

Dagelijkse portefeuillekoersen leveren waarderingsmutaties op in het analytische model, niet automatisch fiscale realisatie. Houd kostprijs, gerealiseerd resultaat, ongerealiseerd resultaat, dividend/rente, kosten en fiscale rendementdefinities apart.

### 7.2 Import en reconciliatie

Begin met CSV, CAMT.053 en brokerexports via een preview met kolommapping, datum-/decimaalnotatie, duplicaatdetectie en menselijke bevestiging. Bewaar een hash van bronbestand en importregels. Een tweede import van hetzelfde bestand mag niets dubbel boeken.

Match interne transfers tussen eigen rekeningen zonder ze als inkomen of uitgave te tellen. Match crypto wallet/exchangetransfers met netwerkfees en optioneel transaction-ID; onbekende transacties blijven in een reviewlijst. Verifieer periodiek aantallen, saldi en open orders tegen broker/exchange.

Bied een afzonderlijk rapport met verschillen, ontbrekende corporate actions, nog niet gematchte transfers en onbekende transactietypen. Voer geen eindjaarsbelastingberekening als 'compleet' op wanneer de onderliggende aansluiting onvolledig is.

### 7.3 Privé, holding en werk-BV

Maak drie standaard entiteittypen, met aparte rekeningen, resultaten, verplichtingen en fiscale perspectieven. Onderlinge leningen, dividenden, rekening-courant en managementvergoedingen worden getypeerde transacties; juridische en fiscale kwalificatie wordt niet uit vrije tekst afgeleid zonder review.

Consolideer met eigendomspercentages en elimineer onderlinge vorderingen/schulden wanneer het gekozen perspectief dat vereist. Tel niet tegelijk de waarde van een holdingaandeel in privé en alle onderliggende holdingactiva als extra vermogen. Toon 'economisch vermogen' en 'privé beschikbaar na veronderstelde belastingen/uitkeringen' als verschillende grootheden.

Voeg een workflow toe voor BV-status en relevante fiscale aandachtspunten, maar maak van 'slapend' geen automatische fiscale vrijstelling. Situatie-afhankelijke onderwerpen zoals gebruikelijk loon, deelnemingsvrijstelling, excessief lenen of bedrijfsopvolging krijgen `REQUIRES_REVIEW` totdat ze binnen een afgebakende geteste scope vallen.

### 7.4 Performance en risico

Toon zowel time-weighted als money-weighted rendement met duidelijke definitie. Houd externe stortingen/onttrekkingen, valuta-effect, kosten, income en waardebewegingen uit elkaar. Behandel randgevallen van IRR met meerdere/geen oplossingen expliciet.

Visualiseer exposure per economische asset, sector, regio, valuta, handelsplaats, broker en juridische entiteit. Toon overlap tussen ETF's en individuele aandelen alleen op basis van holdings met peildatum; onbekende look-through-dekking blijft zichtbaar. Risicomaten zoals volatiliteit, correlatie, drawdown, VaR/CVaR krijgen model, venster en beperkingen; schattingen zijn geen harde verliesgrenzen.

## 8. Nederlandse belasting- en pensioenengine

### 8.1 Een rules engine, geen chatbot met belastingkennis

Implementeer fiscale rekenlogica als pure, geteste functies met expliciete inputs, gevalideerde parameters en een versie-ID. De AI helpt bronnen lezen en verschillen uitleggen, maar activeert geen nieuwe fiscale formules.

Ondersteun in afzonderlijke modules: Box 1, Box 2, Box 3, vennootschapsbelasting waar relevant, pensioen/lijfrente en jaar-/reserveringsruimte, schenken/erven, eigen woning en schulden. Baken eerst de daadwerkelijke ondersteunde situaties af. Grensoverschrijdende fiscaliteit, bijzondere ondernemingsregelingen en onduidelijke juridische situaties mogen niet ongemerkt door een standaardcalculator lopen.

### 8.2 Regelregistratie

Gebruik voor elke regel of parameter de volgende metadata:

```text
rule_id, rule_version, jurisdiction, tax_type, tax_year
legislative_status: PROPOSED | ADOPTED | PROMULGATED | REPEALED
valid_from, valid_to, known_from, known_to
implementation_status: DRAFT | TESTED | APPROVED | RETIRED
source_documents[]: official_url, publication_date, retrieved_at, content_hash
legal_reference, official_section_or_article
parameter_status: PROVISIONAL | FINAL
parameter_values + units + rounding_policy
scope + eligibility_conditions + exclusions
reviewed_by, reviewed_at, approved_at
regression_test_ids, supersedes_rule_version
```

Een aangenomen maar nog niet ingegane regel is geen huidige regel. Een wetsvoorstel is een scenario-input, geen baseline. Een parameter kan voorlopig zijn terwijl de onderliggende wet al geldt. `known_from` en `valid_from` onderscheiden wat op een moment bekend was van de periode waarop de regel betrekking heeft.

Historische rapporten pinnen de ruleset én bronfeiten; een update overschrijft oude rapportages niet. Maak een nieuwe calculation-versie met een delta-uitleg.

### 8.3 Updatepipeline

De applicatiescheduler controleert periodiek een allowlist van officiële bronnen. Downloaden, tekstextractie, contenthash en brondiff leveren een kandidaatwijziging. AI kan deze samenvatten en mappen naar vermoedelijk geraakte regels. Nieuwe code/parameters gaan vervolgens naar een reviewqueue.

Voer vaste regressietests, grenswaardetests, officiële voorbeeldberekeningen en scenario-diff-tests uit. Toon de financiële impact van de kandidaat op bestaande scenario's zonder hem te activeren. Alleen een bevoegde menselijke review promoveert de versie. Een moeilijke juridische interpretatie vraagt inhoudelijke review door een deskundige; een groen technisch testsignaal is daarvoor niet voldoende.

Een mislukte crawl wordt `SOURCE_CHECK_FAILED`, niet 'geen verandering'. Rapporteer de laatste succesvolle broncontrole. Bij onvoldoende actualiteit markeer de berekening verouderd of concept. Deel relevante persoonlijke gevolgen mee, bijvoorbeeld welke reserveringsruimte mogelijk vervalt, maar voer geen storting of aangifte uit.

### 8.4 Box 3 als expliciete testcase

De Belastingdienst beschrijft momenteel een forfaitaire berekening en de mogelijkheid om een lager werkelijk rendement door te geven. De definities, vrijstellingen en kostenbehandeling verschillen; gebruik dus niet eenvoudig de fiscale belastingschijf over de gerealiseerde tradingwinst. De voorlopige aanslag 2026 gebruikt bovendien voorlopige forfaitaire uitgangspunten en niet alvast een definitief werkelijk jaarrendement. [S25, S26]

Bouw daarom afzonderlijke calculators voor de toepasselijke forfaitaire methode en de tegenbewijs-/werkelijk-rendementmethode, met eigen inputvereisten. Verzamel jaarbegin-/eindwaarden, inkomsten, relevante stortingen/onttrekkingen, schulden en assetclassificatie. Scheid koerswinst, fiscale rendementdefinitie en handels-P&L.

Bewaar de toekomstige stelselwijziging als voorstel-/scenariofamilie zolang deze niet definitief en van toepassing is. Op 24 september 2026 toont het Eerste Kamerdossier nog behandeling van het wetsvoorstel; de commissie besprak op 22 september de voortgang. De app mag een toekomstig 2028-regime dus niet als vaststaand in alle plannen invullen. [S27]

Vastgoed eigen gebruik, fiscale partners, overgangsjaren en bijzondere situaties krijgen aparte scopechecks. Toon bij ontbrekende gegevens `ONVOLLEDIG`, niet een geruststellend exact nettobedrag.

### 8.5 Pensioen en lijfrente

Ondersteun AOW, werkgeverspensioen, lijfrente/pensioenbeleggen, eigen vrije beleggingen en hun verschillende beschikbaarheidsmomenten. Maak inputs voor inkomen, pensioenopbouw, opgegeven factor A of de volgens de regeling benodigde alternatieve informatie, betaalde premies en historische jaargegevens.

De Belastingdienst koppelt jaarruimte aan de voorafgaande situatie en vraagt voor reserveringsruimte om historische gegevens; ontbrekende pensioeninformatie kan daarom niet veilig door AI worden geschat. De officiële hulpmiddelen en jaargebonden regels leveren regressiereferenties. [S28, S29]

Laat scenario's netto maandinkomen, pensioengat, inleg, fiscale effecten, inflatie en beperkingen van pensioenvermogen vergelijken. Een verwachte pensioenuitkering en vrij opneembaar beleggingskapitaal horen in verschillende categorieën. Geen advies 'stort maximaal' op basis van alleen inkomen zonder complete eligibility- en liquiditeitscheck.

### 8.6 Nalatenschap en schenken

Maak een overzicht van juridische eigendom, erfgenamen/begunstigden, gewenste verdeling, bestaande schenkingen, vorderingen/schulden, testamentmetadata, verzekeringen en benodigde liquide middelen bij overlijden. Bewaar gevoelige documenten versleuteld; een notariële tekst is niet automatisch machine-interpretabel recht.

Bereken uitsluitend scenario's met expliciete aannames over relaties en toepasbare vrijstellingen/tarieven. Jaarbedragen en voorwaarden komen uit gecontroleerde officiële versies. [S30, S31]

Voor complexe clausules, eerder ontstane kindervorderingen, bewind, uitsluitingsclausules, ondernemingsvermogen of internationale aspecten wordt een reviewactie aangemaakt. Presenteer geen automatisch rechtsgeldig testament en laat de AI geen erfgenaam of executeur 'instellen'. Een legacy-/noodmap geeft de eigenaar controle over toegang en export; geen automatische vrijgave van documenten op grond van een onbevestigd overlijden.

## 9. Scenario's en persoonlijk financieel plan

### 9.1 Samenhangende scenario-engine

Laat de gebruiker doelen vastleggen zoals pensioenleeftijd, netto uitgaven, buffer, huis, ondersteuning van kinderen, vermogensoverdracht en maximale risicoblootstelling. Modelleer cashflows per maand en belastingen volgens het juiste jaar. Bewaar rente, inflatie, rendementen, kosten, tax regime, tijdshorizon en wijzigingen als expliciete aannames.

Een scenario heeft een basispad, conservatief pad en gunstig pad, plus later Monte Carlo en historische stressscenario's. Monte Carlo gebruikt opgeslagen seed, aantal paden, parameters, correlaties en datasetversie. Toon percentielen en gevoeligheid, niet alleen een gladde exponentiële groeicurve. Kanspercentages zijn conditioneel op het model en geen garantie.

Beschrijf inflatie in nominaal én reëel perspectief, en verwerk belastingen, kosten, uitkeringen en volgorde van rendementen. Pas scenario-uitkomsten nooit rechtstreeks toe op live orders. Een toekomstig belastingvoorstel krijgt een apart zichtbaar scenario naast de goedgekeurde baseline.

### 9.2 Trade Impact Preview

Vóór een order toont de app dezelfde `TradeIntent` tegen een gecontroleerde snapshot:

| Dimensie | Voor/na |
|---|---|
| Liquiditeit | Beschikbare cash, reserveringen, settlement en verwachte kosten |
| Risico | Positiegrootte, concentratie, tegenpartij- en valuta-exposure |
| Plan | Effect op expliciet gekozen tradingbudget en beschikbare doelbuffers |
| Fiscaliteit | Alleen toepasselijke doorgerekende effecten; anders aandachtspunt met reden |
| Kwaliteit | Quoteleeftijd, bron, marktdekking, spreiding en ontbrekende gegevens |
| Actie | Paper uitvoeren; live alleen in latere vrijgegeven modus met bevestiging |

Bereken niet bij elke tick het volledige pensioenplan opnieuw. Gebruik een vers scenario-snapshot, actualiseer de relevante inputs en voer zware projecties asynchroon binnen de app uit. De UI noemt tijdstip en status van de berekening. Voor onmiddellijke risicocontrole zijn alleen deterministische actuele limieten leidend.

## 10. Orderveiligheid en latere live-uitvoering

### 10.1 Order lifecycle

Gebruik een expliciete toestandsmachine:

```text
DRAFT → VALIDATED → PREVIEWED → APPROVAL_REQUIRED → APPROVED
      → SUBMITTING → ACKNOWLEDGED → PARTIALLY_FILLED → FILLED

alternatieve staten: REJECTED, CANCEL_REQUESTED, CANCELED,
EXPIRED, UNKNOWN_REQUIRES_RECONCILIATION
```

Een time-out na verzenden kan betekenen dat de order is aangenomen. Geef daarom de onzekere toestand een eigen plek; zoek eerst bij de broker op client-order-ID/orderevents voordat opnieuw verzonden wordt. Een cancelrequest is niet meteen een bevestigde annulering.

Gebruik duurzame intent-ID's, idempotencykeys waar ondersteund, unieke broker-client-ID's, atomic risk reservations en reconciliatie. Bevestiging is gebonden aan exacte orderinhoud, account, entiteit, prijs-/hoeveelheidsgrens en vervaltijd; wijzigingen vereisen een nieuwe preview en toestemming.

### 10.2 Pre-trade checks

Controleer bevoegdheid, modus, instrumentcapabilities, tick/lot/minimum notional, koopkracht, settlement, marktstatus, quoteleeftijd, spread, maximale order/positie, totale exposure inclusief open orders en dagverliesbudget. Een ontbrekende of verouderde bron blokkeert nieuwe risicoverhogende orders. Annuleren en risicoreductie krijgen een afzonderlijk zorgvuldig beleid, geen onbedoelde blokkade door dezelfde regel.

Hanteer beperkte API-permissies, IP-allowlisting waar ondersteund, geen withdrawalrechten en een permanente killswitch. Onderscheid `HALT_NEW_ORDERS` van `CANCEL_OPEN_ORDERS`; automatisch alle posities liquideren is geen veilige standaard. Beschermende orders bij de broker vereisen een capabilitycheck; een lokale stop bestaat niet wanneer de computer slaapt.

Live start met één expliciet gekozen account en connector, bescheiden door de gebruiker vastgestelde grenzen en handmatige bevestiging. Autonome handel is een aparte latere scope met vooraf gedefinieerd beleid, tests, operatorbevoegdheid en duidelijke monitoring. Het bouwen van de app is op zichzelf geen toestemming om te handelen.

## 11. Veiligheid en lokale deployment

### 11.1 Compose en hostgrens

Publiceer standaard alleen de webingang op `127.0.0.1`; databases, NATS en Codex blijven intern. LAN-toegang is een expliciete instelling met authenticatie en TLS. Gebruik ook op localhost sessie-authenticatie, Origin/Host-validatie, CSRF-bescherming voor mutaties en bescherming tegen DNS-rebinding. Een lokale webapp is niet automatisch beschermd tegen andere websites in de browser.

Gebruik non-root images, read-only filesystems waar mogelijk, begrensde CPU/RAM, healthchecks, restartbeleid, netwerksegmentatie en gecontroleerde egress. Geen Docker-socket of gehele home-directory in de AI-container. Mount alleen de noodzakelijke scopes. Controleer amd64/arm64 op de werkelijk gekozen images en broker-gateway; emulatie en authenticatiebeperkingen zijn een zichtbare onboardingcheck.

Secrets worden alleen toegekend aan containers die ze nodig hebben. Compose ondersteunt hiervoor secrets; bescherm ook de bronbestanden op de host. Voor versleuteling op schijf en back-ups is aanvullend sleutelbeheer nodig. Log geen secretwaarden. [S18]

### 11.2 Documenten en plugins

Uploads krijgen MIME-/groottelimieten, veilige parsers, padvalidatie en bescherming tegen zipbombs en actieve content. Importeer CSV veilig en voorkom spreadsheetformule-injectie bij exports. Beperk URL-fetching tot gecontroleerde bestemmingen om SSRF naar lokale/cloudmetadata-endpoints te voorkomen.

Alleen expliciet vertrouwde, versiegebonden adapters mogen uitvoeren. Een manifest alleen vormt geen sandbox; onbetrouwbare plugincode draait niet in het proces met brokercredentials. Plugins krijgen afzonderlijke netwerk-/bestandstoegang en secretscopes.

### 11.3 Herstel en audit

Dagelijkse of door de gebruiker ingestelde lokale back-ups bevatten de authoritative database, persoonlijke documenten, regels, configuratie en auditmetadata. Versleutel exports, bewaar checksums en een restore-instructie. Test herstel op een lege installatie. Rotatie van sleutels mag oude back-ups niet onherstelbaar maken.

Append-only audit registreert logins, rechtenwijzigingen, imports, AI-data-uitgifte, rulesetpromotie, orderpreviews, bevestigingen, brokerantwoorden en reconciliatie. Een lokaal hashchain-log is tamper-evident onder aannames, niet absoluut onvervalsbaar voor de hostbeheerder.

Wanneer de host slaapt, worden geen gegevens opgehaald en geen alerts gegenereerd. Na hervatten: klok/sessie controleren, feeds herstellen, gaten/backfill markeren, accounts en orders reconciliëren en pas daarna livebevoegdheid opnieuw vrijgeven. Toon gemiste monitoringintervallen aan de gebruiker.

## 12. Prestatiebudget en meetplan

Alle onderstaande cijfers zijn **te bewijzen acceptatiedoelen**, geen reeds behaalde prestaties of garantie voor externe providers. Meet op een vastgelegde referentiemachine; startvoorstel is een recente 8-core host met 32 GB RAM, waarvan maximaal 8 vCPU en 12 GB aan het kernprofiel worden toegekend. Ondersteuning voor een kleinere host krijgt een compact profiel.

| Onderdeel | Doel onder afgesproken fixturebelasting |
|---|---|
| Warme app-shell | Binnen 1,5 seconde bruikbaar vanaf lokale origin |
| Initiële eigen JS-shell | Richtbudget 350 KB gzip; charts/grids/AI-schermen lazy loaded |
| Koersevent ontvangst → bruikbare lokale update | p95 onder 50 ms; p99 onder 100 ms |
| Lokale ontvangst → zichtbare chartupdate | p95 onder 150 ms inclusief batching; meet met trace/klokcorrectie |
| Snapshot-API warm | p95 onder 100 ms, exclusief nieuwe upstreamrequest |
| Command palette lokale zoekactie | p95 onder 100 ms |
| Chartinteractie | Richting 60 fps; geen structurele main-thread-stalls boven 50 ms |
| Worker/scenariowerk | Geen merkbare tick-/interactievertraging tijdens berekening |
| Jev | Eerst p50/p95/p99 meten per taak/inputgrootte; deadlines op basis daarvan |
| Herstel | Geen dubbele financiële boekingen/orders bij herlevering; gaps aantoonbaar zichtbaar |

Referentietest: 200 gesubscribede instrumenten, vier zichtbare charts, 20 geselecteerde orderboeken, 5.000 genormaliseerde events/seconde gedurende 60 seconden en een korte 20.000 events/seconde piek gedurende 10 seconden. Leg eventmix en berichtgroottes vast. Dit is een synthetische ingenieurstest, geen claim dat providers dit pakket leveren.

Meet afzonderlijk bronvertraging, netwerkvertraging, lokale verwerking, queue-age en rendervertraging. Exchange-timestamps zijn niet altijd gesynchroniseerd met de host; toon klokonzekerheid. Gebruik monotone tijd voor interne durations. Wijzig prestatiedoelen uitsluitend met een gemotiveerde ADR en gemeten bewijs, niet door een trage test te verwijderen.

Voor frontendperformance: subscribe per instrument, stuur patches, virtualiseer lange lijsten, batch UI-verversing, pauzeer niet-zichtbare rendering en verplaats zware parsing/rekenwerk naar workers. Bewaar kritieke backendmonitoring ook wanneer de browsertab niet actief is. WebGPU/OffscreenCanvas/WASM zijn optionele optimalisaties met capabilitydetectie en fallback, geen toegangsvoorwaarde voor de terminal.

## 13. Repository en contracten

```text
modern-trade-terminal/
  AGENTS.md
  README.md
  apps/web/                         # React UI
  services/api/                     # FastAPI + domeinmodules
    domains/identity/
    domains/portfolio/
    domains/ledger/
    domains/risk/
    domains/orders/
    domains/planning/
    domains/tax/
  services/market-gateway/           # Rust/Tokio
  services/worker/                   # Python jobs; gedeelde domeinbibliotheek
  services/codex-bridge/             # Node; stdio-supervisor en policy
  packages/contracts/               # JSON Schema/OpenAPI → gegenereerde typen
  packages/ui/                      # tokens, primitives, componenten
  packages/analytics/               # canonieke indicator-/analysefuncties
  adapters/                         # manifesten, mappings, fixtures, implementaties
  rules/nl/                         # jaar- en versiegebonden approved/candidate regels
  fixtures/                         # expliciet synthetisch of rechtmatig opgeslagen
  tests/unit/ tests/contracts/ tests/e2e/ tests/load/ tests/chaos/
  infra/compose/
  docs/adr/ docs/runbooks/ docs/design/ docs/providers/
```

Publieke interne APIgroepen zijn `/instruments`, `/quotes`, `/history`, `/news`, `/calendar`, `/accounts`, `/ledger`, `/portfolio`, `/scenarios`, `/tax`, `/sources`, `/ai` en `/orders/preview`. Een latere `/orders/submit` is een aparte capability met strikte autorisatie, niet hetzelfde endpoint met een boolletje.

Marktstreams hebben topics per capability/instrument/venue en alleen de toegestane scope. Slow consumers krijgen resync-protocol, niet een onbeperkt groeiende buffer. API's ondersteunen paginatie, begrensde time ranges en duidelijke foutcodes zoals `ENTITLEMENT_REQUIRED`, `STALE_DATA`, `INCOMPLETE_LEDGER` en `UNAPPROVED_RULESET`.

## 14. Uitrol met kwaliteitspoorten

De volledige backlog staat in `docs/BACKLOG.md`. Implementeer in deze volgorde, zonder de verplichte financefunctionaliteit tot een ongedefinieerde 'later' te reduceren.

| Mijlpaal | Oplevering | Releasepoort |
|---|---|---|
| M0 | Bestaand project inventariseren, architectuur, contracten, licentiecheck, visuele referenties | Besluiten vastgelegd; geen live rechten |
| M1 | Werkende terminalslice: Kraken, chart, bronstatus, papermodel, lokale ledger, eenvoudige wealth-impact | Reproduceerbare Compose-start en volledige gebruikersflow |
| M2 | Tweede cryptobron, aandelenadapter, nieuws, kalender, assetprofielen, bronvergelijking | Werkelijke versus fixturetests zichtbaar; alle verplichte terminalfuncties aanwezig |
| M3 | Financiële imports, cashflow, eigendomsstructuur, doelen, pensioen- en fiscale basis | Geen dubbel vermogen; complete versus onvolledige berekeningen herkenbaar |
| M4 | Codex, Jev, uitleg, evaluaties, privacy- en budgetbeleid | AI kan geen geld/rechten/regeldatabase wijzigen |
| M5 | Rules-updater, scenariovergelijking, estateworkflow, replay en performancehardening | Einde-tot-einde betrouwbaarheid, restore, chaos- en toegankelijkheidstests |
| M6 | Eén live connector, uitsluitend na afzonderlijke toestemming | Bewezen orderstate/reconciliatie; alle safetychecks groen |
| M7 | Marktuitbreiding: opties/futures/obligaties en geavanceerde analytics | Asset-specifieke risico's en lifecycle volledig ondersteund |

M1 is geen volwaardige eindoplevering. M2 t/m M5 leveren de gevraagde persoonlijke trade- en finance-assistent op binnen de gedocumenteerde markt- en fiscale scope. Niet beschikbare feeds of bijzondere fiscaliteit blijven herkenbaar beperkt, niet stilzwijgend zogenaamd ondersteund.

## 15. Acceptatietests die niet mogen ontbreken

### 15.1 Data en marktsemantiek

Een providerdisconnect veroorzaakt een stale-label en geen verzonnen realtimeprijs. Een failover naar delayed data verandert het label en blokkadebeleid. Verschillende quotevaluta's/prijstypen worden niet onterecht vergeleken. Dubbele trades veranderen volume niet dubbel. Een orderboekgap vraagt resync. Markt- en timezonewissels, late trades, revisies, splits en symbolmigraties hebben vaste fixtures.

### 15.2 Financiële juistheid

Importeer hetzelfde bestand twee keer zonder dubbele boeking. Bewijs dat een eigen rekeningtransfer geen rendement is. Toets multivaluta-kosten en waardering, partial fills, dividend, splits, terugboekingen, ontbrekende FX en entiteitsconsolidatie. Gebruik propertytests voor journaalbalans, quantityconservation en decimale precisie. Controleer exact op de toepasselijke afrondingsregel, niet op een toevallige float-tolerantie.

### 15.3 Fiscaliteit en plannen

Reproduceer officiële voorbeeldberekeningen voor de ondersteunde situaties. Test grensbedragen, jaargrenzen, ingangsdata, voorlopige parameters, ontbrekende data en partner-/entityscope. Een aangekondigde wet wijzigt de baseline niet. Een goedgekeurde nieuwe versie levert een nieuw rapport en verklaarde delta. Een broncontrolefout wordt geen succesvolle actualiteitscheck.

### 15.4 AI en bevoegdheden

Een kwaadaardig artikel dat om een trade, secret of regelwijziging vraagt krijgt geen bevoegdheid. Een hallucinerende modeloutput met niet-bestaande bron-ID wordt afgekeurd. Jev-timeout geeft abstention, niet 'koop'. Een runtime-agent kan de productieworkspace niet wijzigen. Privacy-modus wordt voor iedere tool/modelcall afgedwongen, ook in retries en logs.

### 15.5 Executie en herstel

Simuleer timeout nadat een broker een order heeft aangenomen: er ontstaat maximaal één bedoelde order en de toestand wordt gereconcilieerd. Test concurrente previews, kapitaalreservering, vervallen bevestiging, partial fills tijdens cancel, crash tussen outboxstappen en host-slaapstand. Toon onzekerheid zolang de brokerstatus niet bewezen is.

### 15.6 Visueel en bruikbaar

Lever screenshots van Terminal, Vermogen, Planning, Source Health, AI-review, lege staat en storing. Test toetsenbord, focus, contrast, screenreaderlabels, reduced motion en kleine schermen. Alle verplichte controls werken. Dezelfde positie en bedragen moeten in terminal, ledger, portefeuille en planning consistent zijn of een expliciete peildatumverklaring hebben.

## 16. Definition of Done

Een mijlpaal is pas klaar wanneer code, migrations, fixtures, documentatie, testresultaten en visuele controle zijn opgeleverd. Een live-integratie vereist bewijs van een echte connectie binnen de juiste rechten; anders heet de status 'adapter gebouwd, live verificatie ontbreekt'. Performance krijgt een benchmarkrapport met machineprofiel. Fiscale modules krijgen scope en brongebonden rekenbewijs, geen algemene claim van fiscale certificering.

De eindoplevering bevat een installatierunbook, source/entitlementmatrix, privacy- en secretmodel, ADR's, versiegebonden API-contracten, backup/restore-runbook, kostenoverzicht op basis van gekozen abonnementen en een overzicht van alle resterende beperkingen.

**Eindcriterium:** de gebruiker kan een marktgebeurtenis vinden, bronnen controleren, een positie analyseren, een realistische papertransactie uitvoeren, die in de administratie terugzien en het effect op zijn financiële plan begrijpen — zonder onzichtbare aannames, onjuiste realtimeclaims of ongeautoriseerde financiële acties.
