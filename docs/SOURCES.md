# Primaire bronnen en verificatiepunten

**Onderzoeksdatum:** 24 september 2026. De onderstaande documentatie is gebruikt voor dit bouwplan. Productdocumentatie en wettelijke status kunnen veranderen. Controleer toegang, voorwaarden, versies en juridische status opnieuw bij implementatie en bij elke relevante release.

Dit register is een technische bronverantwoording, geen juridisch advies of certificering van providers. De architectuurkeuzes, UI-specificaties en prestatiedoelen in het bouwplan zijn eigen ontwerpvoorstellen. Een leverancierbenchmark is geen bewezen prestatie van deze applicatie.

## Jev / TypeSafe

| ID | Primaire bron | Betekenis voor de implementatie |
|---|---|---|
| S01 | [TypeSafe — Introduction](https://docs.typesafe.ai/introduction) | Jev ondersteunt getypeerde vragen en uitkomsten, waaronder Choice, Score en Noul. Controleer de responsevorm per vraagtype; veronderstel geen uniforme confidencevelden. |
| S02 | [TypeSafe — Quickstart](https://docs.typesafe.ai/introduction/quickstart) | Documenteert `POST https://api.typesafe.ai/v1/systemone`, bearer-authenticatie en de Python-package `typesafe-sdk`. Voor andere runtimes kan een eigen getypeerde HTTP-adapter nodig zijn. Voorbeelden met `jev-latest` zijn geen garantie op onveranderlijk modelgedrag. |
| S03 | [TypeSafe — Confidence](https://docs.typesafe.ai/confidence) | Confidence heeft een specifieke modelbetekenis. Behandel die niet als kans op winst of als vervanging van externe validatie, kalibratie en abstentionbeleid. |
| S04 | [TypeSafe — Privacy Policy](https://typesafe.ai/legal/privacy-policy) | Beschrijft onder meer verwerking/hosting in de Verenigde Staten en het beleid om input niet voor training of fine-tuning te gebruiken. Dat betekent niet automatisch EU-hosting, lokale verwerking of zero retention. |
| S05 | [TypeSafe — Acceptable Use Policy](https://typesafe.ai/legal/acceptable-use-policy) | Controleer voorwaarden en toegestaan gebruik voordat de integratie wordt geactiveerd; geef geen data door waarvoor geen toestemming of recht bestaat. |

Marketingclaims over absolute snelheid of het volledig ontbreken van hallucinaties worden niet als acceptatiebewijs overgenomen. Meet Jev met de werkelijke eigen payloads en beoordeelde testgevallen. Leg prompt-, schema-, model- en evaluatieversies vast.

## Codex / OpenAI

| ID | Primaire bron | Betekenis voor de implementatie |
|---|---|---|
| S06 | [OpenAI — Codex SDK](https://developers.openai.com/codex/sdk/) | Officiële programmatische integratie; documentatie kan doorverwijzen naar de actuele documentatiehost. Gebruik de passende SDK en ondersteunde authenticatie, niet schermscraping van een consumenteninterface. |
| S07 | [OpenAI — Codex App Server](https://developers.openai.com/codex/app-server/) | Voor integratie van sessies, streaming, approvals en clientinterfaces. Stdio is het uitgangspunt; de gedocumenteerde WebSocket-transportoptie is experimenteel. Houd de bridge intern en pin client-/protocolversies. |

Een Codex-sandbox of tool approval is niet hetzelfde als goedkeuring van een financiële transactie. De applicatie houdt orderautorisatie, risicobudgetten en toegang tot financiële credentials zelf in beheer. Neem niet aan dat een desktoplogin, abonnement of bestaande connector automatisch API-toegang binnen Docker verschaft.

## Frontend, realtime runtime en deployment

| ID | Primaire bron | Betekenis voor de implementatie |
|---|---|---|
| S08 | [React — Blog en releases](https://react.dev/blog) | Tijdens dit onderzoek vermeldt de officiële site React 19.3, gepubliceerd op 9 september 2026. Los bij M0 de daadwerkelijk compatibele stabiele versies op; gebruik geen zwevende `latest`-dependencies. |
| S09 | [Vite — Getting Started](https://vite.dev/guide/) | Bouwbasis voor de lokale React/TypeScript SPA. Controleer actuele Node-vereisten en plugincompatibiliteit. |
| S10 | [Tailwind CSS — Using Vite](https://tailwindcss.com/docs/installation/using-vite) | Officiële integratiebasis; implementeer het eigen design system in plaats van een generiek componentthema. |
| S11 | [TanStack Query — React overview](https://tanstack.com/query/latest/docs/framework/react/overview) | Serverstate, caching en querylifecycles. Het tickpad wordt afzonderlijk ontworpen en mag niet elk bericht als een volledige query-invalidation behandelen. |
| S12 | [Dockview — Official documentation](https://dockview.dev/) | Kandidaat voor dockbare panelen en werkruimtes; test layoutpersistency, herstel, toegankelijkheid en licentie voordat het contract wordt vastgezet. |
| S13 | [TradingView — Lightweight Charts](https://www.tradingview.com/lightweight-charts/) | Open-source chartbasis voor eigen data. Controleer LICENSE/NOTICE en attributievereisten van de daadwerkelijk gepinde versie. |
| S14 | [TradingView — Charting libraries and FAQ](https://www.tradingview.com/free-charting-libraries/) | De FAQ sluit beschikbaarstelling van Advanced Charts en Trading Platform voor persoonlijk/hobby-/studie-/testgebruik uit. Bouw dit persoonlijke project daarom niet op de aanname van gratis toegang tot die bibliotheken. |
| S15 | [AG Grid — Licensing and pricing](https://www.ag-grid.com/license-pricing/) | Maak onderscheid tussen Community en betaalde Enterprise-functionaliteit. Gebruik geen Enterprise-pivot, export of andere betaalde features zonder benodigde licentie. |
| S16 | [NATS — JetStream](https://docs.nats.io/concepts/jetstream) | Persistente messaging waar nodig. Brokers, databases en externe executie vereisen daarnaast eigen deduplicatie, idempotency en reconciliatie; geen onbewezen end-to-end exactly-once-belofte. |
| S17 | [Tokio — Official project](https://tokio.rs/) | Kandidaatruntime voor de Rust-marktdatalaag. De snelheidsdoelen van dit plan zijn nog te benchmarken, niet door het gebruik van Rust of Tokio gegarandeerd. |
| S18 | [Docker — Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/) | Geheimen per service beschikbaar stellen in plaats van ze in frontendbundles of images te plaatsen. Dit vervangt geen beveiligde host, minimale rechten en versleutelde back-ups. |

Voor overige genoemde bouwblokken, zoals FastAPI, Pydantic, PostgreSQL, DuckDB, Polars, ECharts en testtools, legt M0 exacte versies, licenties, platformondersteuning en integratietests vast. Het plan doet geen claim dat een specifieke ongecontroleerde patchversie de nieuwste of veiligste is.

## Marktdata, assetinformatie en valuta

| ID | Primaire bron | Betekenis voor de implementatie |
|---|---|---|
| S19 | [Alpaca — Real-time stock pricing data](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data) | IEX, SIP en delayed SIP verschillen in dekking, toegang en vertraging. De UI en failover mogen dit onderscheid niet verbergen. |
| S20 | [Interactive Brokers — Market data subscriptions](https://www.interactivebrokers.com/docs/general/market-data-subscriptions/introduction) | Veel effectenfeeds vereisen geschikte abonnementen. Verifieer API-, gebruikers-, markt- en non-display-rechten afzonderlijk van het bestaan van een rekening. |
| S21 | [Coinbase — Advanced Trade WebSocket endpoints](https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-endpoints) | Officiële streamingbasis. Test kanaalinhoud, heartbeats, reconnect, sequencegedrag en account-/regiodekking vóór ingebruikname. |
| S22 | [Kraken — WebSocket v2 trades](https://docs.kraken.com/exchange/api-reference/spot-websocket-v2/trade) | Documenteert `side` als de kant van de takerorder. Koop-/verkoopdruk moet bij iedere andere provider opnieuw op diens eigen semantiek worden afgestemd. |
| S23 | [ECB — Euro reference exchange rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html) | Referentiekoersen worden gewoonlijk op werkdagen rond 16:00 gepubliceerd en zijn informatief. De ECB raadt gebruik voor transacties af; dit is geen realtime uitvoerbare FX-feed. |
| S24 | [SEC — EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | Primaire bron voor Amerikaanse filings en XBRL-bedrijfsinformatie; geen wereldwijde instrument- of fundamentalsdekking. Houd rekening met publicatie-/amendmenttijd en toegangsbeleid. |

Geen enkele bron in deze tabel verleent automatisch rechten om alle gegevens op te slaan, door te geven aan AI of te herdistribueren. Leg bronlicenties en entitlementbeslissingen expliciet vast. Een index is een marktmaatstaf, geen zelfstandige dataprovider. Ook twee verschillende leveranciers kunnen dezelfde onderliggende datastroom gebruiken.

## Nederlandse belasting, pensioen en nalatenschap

| ID | Primaire bron | Betekenis voor de implementatie |
|---|---|---|
| S25 | [Belastingdienst — Werkelijk rendement](https://www.belastingdienst.nl/wps/wcm/connect/nl/box-3/content/wat-is-mijn-werkelijk-rendement) | Actueel kader voor werkelijk rendement/tegenbewijs. Modelleer dit afzonderlijk van forfaitaire Box 3-berekeningen; een simpele heffing op gerealiseerde tradingwinst is geen correcte algemene vervanging. |
| S26 | [Belastingdienst — Berekening Box 3-inkomen 2026](https://www.belastingdienst.nl/wps/wcm/connect/nl/box-3/content/berekening-box-3-inkomen-2026) | Jaargebonden rekenkader. Maak onderscheid tussen voorlopige en definitieve parameters en tussen forfaitaire voorlopige berekening en later vaststelbare jaarinformatie. |
| S27 | [Eerste Kamer — Wet werkelijk rendement Box 3, 36.748](https://www.eerstekamer.nl/wetsvoorstel/36748_wet_werkelijk_rendement_box) | Op 24 september 2026 is de wetgevingsbehandeling nog niet afgerond. Een beoogde invoering in 2028 mag dus niet als onvoorwaardelijk vaststaande regelgeving in de basisscenario's worden verwerkt. |
| S28 | [Belastingdienst — Lijfrentepremies aftrekken](https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/prive/werk_en_inkomen/lijfrente/aftrekken-lijfrentepremies/aftrekken-lijfrentepremies) | Jaarruimte/reserveringsruimte vereist relevante inkomens- en pensioeninformatie uit eerdere jaren en toepasselijke jaarregels. Ontbrekende gegevens leiden tot onvolledigheid, niet tot verzonnen aftrekruimte. |
| S29 | [Belastingdienst — Hulpmiddel lijfrentepremie](https://www.belastingdienst.nl/wps/wcm/connect/nl/aftrek-en-kortingen/content/hulpmiddel-lijfrentepremie-2016-en-daarna) | Primaire referentie voor invoergegevens en controle van pensioenberekeningen. Gebruik geverifieerde fixtures; automatiseer geen ongeautoriseerde persoonlijke login. |
| S30 | [Belastingdienst — Belastingvrij schenken](https://www.belastingdienst.nl/wps/wcm/connect/nl/schenken/content/tot-welk-bedrag-belastingvrij-schenken) | Vrijstellingen hangen af van jaar, relatie en voorwaarden. Geef niet één generiek bedrag dat in alle situaties zou gelden. |
| S31 | [Belastingdienst — Vrijstellingen erfbelasting](https://www.belastingdienst.nl/wps/wcm/connect/nl/erfbelasting/content/vrijstelling-erfbelasting) | Relatie- en jaarafhankelijke berekening, met relevante voorwaarden. Testament, partnerbegrip en eigendomsverhoudingen vragen afzonderlijke beoordeling. |

### Bronbeleid van de toekomstige fiscale monitor

Begin met Belastingdienst, Rijksoverheid, Officiële Bekendmakingen, wetten.overheid.nl en de relevante parlementaire dossiers. Sla bron, inhoudshash, ophaaltijd, geldigheidsperiode, ingangsdatum, juridische status en kennisdatum op. Een persbericht, politieke aankondiging, wetsvoorstel en in werking getreden regeling zijn niet hetzelfde.

Laat automatische detectie een wijzigingsvoorstel aanmaken, nooit zelfstandig productiebelastingregels activeren. Vereis rekenfixtures, regressietests, een impactvergelijking en een expliciete review. De persoon die goedkeurt moet bij materiële fiscale/juridische keuzes kunnen terugvallen op een bevoegde adviseur. Bij conflicten of ontbrekende wetstekst blijft de status onbevestigd.
