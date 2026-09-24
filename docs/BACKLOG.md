# Uitvoerbare backlog en releasepoorten

Gebruik deze volgorde. Maak per taak kleine commits, tests en een controleerbare
STATUS-update. `DONE` betekent werkend én getest; `BLOCKED_ACCESS` is geen `DONE`.
De mijlpalen zijn scopefasen, geen toegezegde kalenderplanning.

## M0 — Basisbesluiten en ontwerp

| ID | Taak | Acceptatie |
|---|---|---|
| M0.1 | Inventariseer bestaande code, host, Docker en beschikbare toegang | Geen bestaande code vernietigd; hardware-/versiematrix vastgelegd |
| M0.2 | Maak ADR's voor SPA, gateway, ledger, bus, AI-isolatie en tax engine | Alternatieven, kosten en grenzen beschreven |
| M0.3 | Definieer schema's voor identiteit, quote, trade, order, boeking en tax rule | Runtimevalidatie plus genereerbare TS/Python/Rust-typen |
| M0.4 | Verifieer huidige provider-/bibliotheekvoorwaarden | Capability-/entitlementmatrix; geen aangenomen abonnement |
| M0.5 | Ontwerp vier primaire schermen en componenten | Visuele referenties, tokens, foutstaten en responsive gedrag |
| M0.6 | Richt testfixtures en modusisolatie in | Fixtures herkenbaar fictief; live standaard niet beschikbaar |

**Poort:** het team weet welke data echt beschikbaar is, wat gesimuleerd wordt en
welke financiële acties verboden zijn. Geen live credentials nodig.

## M1 — Eerste complete verticale doorsnede

| ID | Taak | Acceptatie |
|---|---|---|
| M1.1 | Maak Compose-kernprofiel en lokale auth | Herhaalbare start, interne databases, healthchecks |
| M1.2 | Implementeer instrument registry en Kraken marketdata-adapter | Quotes/trades met herkomst; echte connectorstatus apart van fixtures |
| M1.3 | Bouw watchlist, chart, bronindicator en opgeslagen workspace | Keyboardbediening; correcte data-/foutstaten |
| M1.4 | Maak eenvoudig maar realistisch spot-papermodel | Bid/ask, fees, partial fills en limieten in tests |
| M1.5 | Voeg ledger en portfolio-snapshot toe | Eén paperfill levert één consistente positie en cashmutatie |
| M1.6 | Bouw minimale Trade Impact Preview en eenvoudige vermogensdoelbuffer | Voor/na consistent met ledger; nog geen onbewezen fiscale claims |
| M1.7 | Voeg eerste tutorial toe | Volledige flow uitvoerbaar zonder API-key via gemarkeerde demo |

**Poort:** instrument → chart → paperpreview → order → journaal → vermogensimpact
werkt in Docker. Live-integratietest zonder toegang staat expliciet als niet
uitgevoerd geregistreerd.

## M2 — Multi-source terminal en verplichte marktfuncties

| ID | Taak | Acceptatie |
|---|---|---|
| M2.1 | Coinbase tweede cryptoadapter | Nieuwe bron zonder nieuwe frontendbranches; contracttests |
| M2.2 | Alpaca aandelenadapter met feedselectie | IEX/SIP/delay/rechten zichtbaar; geen onterechte failover |
| M2.3 | Prijsvergelijker en FX-service | Niet-vergelijkbare prijzen geweigerd; ECB niet voor executie |
| M2.4 | RSS/Atom en nieuws-API contract, clustering en brondrawer | Meerdere toegestane uitgevers; publicatie/revisie/herkomst behouden |
| M2.5 | Kalender met sessies, macro en bedrijfsevents | Tijdzones, DST, closed sessions en herzieningen getest |
| M2.6 | Bedrijfs-/assetprofielen en corporate actions | Primary-sourcevelden; ontbrekende gegevens blijven onbekend |
| M2.7 | L2, time & sales en agressorvolume | Sequence-/bookresync, onbekende side en coverage correct |
| M2.8 | Source Health en configureerbare bronprioriteit | Disconnect, rate limit, entitlementfout en dataachterstand zichtbaar |

**Poort:** alle expliciet gevraagde terminalfuncties zijn aanwezig binnen de
beschikbare marktdekking. Eén leverancier weghalen breekt niet de hele terminal.

## M3 — Nederlandse persoonlijke financiële kern

| ID | Taak | Acceptatie |
|---|---|---|
| M3.1 | Privé/holding/werk-BV en eigendomsrelaties | Geen dubbele consolidering; duidelijke eigenaar van iedere rekening |
| M3.2 | CSV/CAMT.053/brokerimport met preview | Idempotent; eigen transfers geen inkomen; conflicts naar review |
| M3.3 | Cashflow, waarderingen en performance | Stortingen, FX, kosten, dividend en winst gescheiden |
| M3.4 | Doelen, maandcashflow en scenario-snapshots | Aannames expliciet; reproduceerbare basis-/stressscenario's |
| M3.5 | Rulesetregistry en calculators voor afgebakende Box 1/2/3-scope | Officiële tests; incomplete data blokkeert definitieve uitkomst |
| M3.6 | Pensioeninputs, jaar-/reserveringsruimte en projectie | Ontbrekende historische opbouw niet door AI ingevuld |
| M3.7 | Uitbreiding Trade Impact Preview naar entity-/plancontext | Handelspotje, belastingreserve en langetermijnbuffer onderscheiden |

**Poort:** vermogensdashboard en plan zijn financieel intern consistent; fiscale
ondersteuning is expliciet afgebakend en niet afhankelijk van een LLM-antwoord.

## M4 — Codex en Jev als gecontroleerde assistenten

| ID | Taak | Acceptatie |
|---|---|---|
| M4.1 | Codex stdio-bridge met sessies, auth en streaming | Geen publiek app-serverendpoint; gepinde protocoltypen |
| M4.2 | Beperkte read/analyse-toolgateway | Geen submit/withdraw/shell; server controleert iedere scope |
| M4.3 | Jev HTTP/Python-adapter en FastAssessment | Gedocumenteerde API, schemavalidatie, timeout → ABSTAIN |
| M4.4 | Gelabelde evaluatieset en shadowevaluatie | Kwaliteit per taak; modelwijziging zonder stilzwijgende promotie |
| M4.5 | AI-evidencepaneel en numerieke/sourcevalidatie | Feiten, berekeningen, interpretatie en onbekend gescheiden |
| M4.6 | Privacystanden en kosten-/ratebudgetten | Persoonlijke data standaard niet naar cloud; retries respecteren beleid |
| M4.7 | Promptinjectie- en bevoegdheidstests | Artikel kan geen order/rechtenwijziging/secretlezing veroorzaken |

**Poort:** het systeem blijft bruikbaar zonder AI. Een model kan adviseren en
verklaren, maar niet zelf zijn bevoegdheid vergroten of financieel handelen.

## M5 — Volledige finance-assistent en hardening

| ID | Taak | Acceptatie |
|---|---|---|
| M5.1 | Officiële bronmonitor en rule-reviewworkflow | Crawl failure ≠ geen wijziging; voorstellen blijven scenario |
| M5.2 | Pensioen-, belasting- en vermogensscenariovergelijking | Gecontroleerde rulesets, modelversies en delta-uitleg |
| M5.3 | Estate-/schenkworkflow en lokale documentvault | Review voor juridische complexiteit; geen automatische rechtsdocumenten |
| M5.4 | Replay, backtest en tutorialuitbreiding | Geen look-ahead; oorspronkelijke data/revisies/timeframes correct |
| M5.5 | Prestatie-/chaostests en frontendoptimalisatie | Gerapporteerde p50/p95/p99; geen stil dataverlies |
| M5.6 | Back-up, restore en sleep/wake-herstel | Restore op lege installatie; gemiste monitoring zichtbaar |
| M5.7 | Accessibility, browsers en visual fidelity | Kritieke flows in Chromium/WebKit; afgesproken viewports |
| M5.8 | Installatie-, gebruiks- en beperkingenhandleiding | Nieuwe installatie uitvoerbaar; kosten/rechten helder |

**Poort:** gevraagde trade- en finance-assistent gereed voor persoonlijk
read-only/papergebruik binnen de ondersteunde scope. Geen algemene claim van
wereldwijde realtimefeeds, fiscale certificering of gegarandeerde rendementen.

## M6 — Live, alleen na afzonderlijke toestemming

| ID | Taak | Acceptatie |
|---|---|---|
| M6.1 | Kies één toegestane broker/accountscope | Actuele NL-beschikbaarheid, voorwaarden en rechten gecontroleerd |
| M6.2 | Bouw complete execution-adapter | Types/precision/fees/session/reconciliation aangetoond |
| M6.3 | Atomic risk reservations en confirmation binding | Concurrency en verouderde previews kunnen limieten niet omzeilen |
| M6.4 | Timeout/retry/cancel/partial-fill/failure tests | Geen blinde resubmits; onbekende status blokkeert passend |
| M6.5 | Operatorcontrols en killswitch | Halt/cancel onderscheiden; geen automatische liquidatie |
| M6.6 | Beperkte gecontroleerde activatie | Gebruiker stelt limieten en bevestigt elke order |

**Poort:** geen live feature wordt door de development-agent zelfstandig
geactiveerd. Autonome trading blijft een volgende afzonderlijke productbeslissing.

## M7 — Markt- en analysemogelijkheden uitbreiden

Voeg pas na passende tests opties, futures en meer obligaties toe. Verplicht zijn
contractmultipliers, settlement, expiry, assignment/exercise waar toepasselijk,
marginmodel, corporate actions, providerrechten en accountgeschiktheid. Voeg
geavanceerde greeks, volatility surfaces en alternatieve data capabilitygewijs toe.
Een onbekend derivaat krijgt geen generieke spot-orderticket.

## Rapportage per taak

Leg `IMPLEMENTED`, `TESTED_WITH_FIXTURES`, `LIVE_VERIFIED`, `BLOCKED_ACCESS` en
`NOT_IN_SCOPE` apart vast. Geef commit-ID, testcommando, bewijsbestand, resterende
beperkingen en eerstvolgende concrete stap. Verander acceptatienormen niet om
mislukte tests groen te laten lijken.
