# AGENTS.md — Modern Trade Terminal

## Opdracht

Bouw een hoogwaardige lokale webapplicatie voor marktanalyse, paper trading,
portfolio-administratie en Nederlandse belasting-, pensioen- en vermogensplanning.
De gebruiker wil snelle uitbreidbare bronintegraties, Codex voor diepgaand
AI-werk en Jev van TypeSafe voor kleine snelle gestructureerde beoordelingen.

De volledige productspecificatie staat in `MODERN_TRADE_TERMINAL_BUILD_PLAN.md`.
Gebruik `docs/DESIGN_SYSTEM.md`, `docs/BACKLOG.md` en `docs/SOURCES.md` erbij.

## Niet-onderhandelbare regels

1. **Geen fictieve werkelijkheid.** Label ieder gegeven als echt, vertraagd,
   indicatief, geschat, gesimuleerd of ontbrekend. Een placeholder is geen
   providerintegratie. Een geslaagde mocktest is geen live integratietest.
2. **Geen orders zonder bevoegdheid.** Start met demo/paper en read-only accounts.
   De omschakeling naar live is een aparte expliciet toegestane release. AI krijgt
   geen broker- of exchangegeheimen en mag de executiegateway niet rechtstreeks
   benaderen. Withdrawals, transfers en leverage zijn standaard uitgeschakeld.
3. **Geen schijnzekerheid.** Een AI-confidence is geen kans op winst. Een typed
   antwoord is niet noodzakelijk waar. Toon onzekerheid en ondersteun `ABSTAIN`.
4. **Geld is exact.** Gebruik Decimal/fixed-point voor prijzen, aantallen,
   boekingen, kosten en belastingen. Serialiseer bedragen als strings met
   valuta/eenheid. Floating point mag voor expliciet benaderende statistiek en
   rendering, niet voor authoritative financiële rekenlogica.
5. **Bronnen zijn onderdeel van het datamodel.** Bewaar provider, oorspronkelijke
   feed/venue, tijdstip, licentie, revisie en kwaliteitsstatus. Een onafhankelijke
   vergelijking vereist meer dan twee leveranciersnamen met dezelfde bronfeed.
6. **Regels zijn versiegebonden.** Fiscale uitkomsten komen uit geteste code en
   een goedgekeurde ruleset, niet uit vrije AI-tekst. Scheid wetsvoorstellen,
   aangenomen wetgeving, ingangsdatum en menselijke reviewstatus.
7. **Geen dubbele vermogenswaarde.** Consolideer privé/holding/werk-BV met
   eigendomspercentages en eliminaties. Tel BV-aandelen en dezelfde onderliggende
   BV-activa niet tegelijkertijd mee. Pensioenaanspraken zijn geen vrij cashsaldo.
8. **Herstart is een risicosituatie.** Na slaapstand, disconnect, timeout of
   herstart eerst synchroniseren en reconciliëren. Herhaal nooit blind een
   order die mogelijk al door de broker is aangenomen.
9. **Data blijft lokaal tenzij toegestaan.** Externe modellen zijn cloudcalls.
   Verstuur geen BSN, credentials, volledige fiscale dossiers of andere
   vertrouwelijke gegevens zonder passende toestemming en databeleid. Logs
   bevatten geen secrets. Docker Compose-secrets zijn geen volledige encrypted vault.
10. **Niet zelf de eigen veiligheidsgrenzen veranderen.** Runtime-Codex mag geen
    productiecode, belastingregels, risk limits of systeemrechten aanpassen.
    De development-agent gebruikt aparte workspaces en credentials.
11. **Geen ongeautoriseerde externe acties.** Geen abonnement afsluiten, API-key
    aanmaken, credentials uit andere apps overnemen, order plaatsen, document
    versturen of rechten verruimen zonder expliciete bevoegdheid.
12. **Visueel én functioneel opleveren.** Geen dashboard als screenshot. Alle
    kerncontrols zijn werkende UI. Niet-gebouwde functies zijn disabled met uitleg,
    niet misleidend klikbaar.

## Technische discipline

Gebruik actuele stabiele onderling compatibele versies, controleer officiële
documentatie en leg exacte versies en container-digests vast. Gebruik geen
zwevende `latest`-versies voor productie. Inventariseer eerst het bestaande
project; vernietig geen aanwezige implementatie. Architectuurwijzigingen vragen
een ADR met consequenties voor snelheid, betrouwbaarheid en onderhoud.

Definieer wire contracts één keer in JSON Schema/OpenAPI; genereer TypeScript,
Python en Rust typen en valideer ook tijdens runtime. Bewaar oude events met hun
schema-versie. Scheid UI-layoutstate, serverstate en realtime tickstate.

Maak kleine complete verticale slices. Houd de hot path vrij van AI, webscraping,
zware SQL, rapportgeneratie en Monte Carlo. Doe geen kunstmatige vertragingen en
geen canvas/webgl/worker-optimalisaties zonder zinvolle use case of meting.

## Zelfstandig verder werken

Ontbreekt een secret of providerrecht, bouw dan adaptercontract, fixtures,
contracttests en een heldere onboardingstatus. Markeer de echte connectortest als
`NOT_RUN_MISSING_CREDENTIALS`. Ga door met onafhankelijke onderdelen. Meld een
werkelijke blocker concreet; verberg hem niet met generieke mockdata.

Vraag geen herhaalde toestemming voor lokale niet-destructieve codewijzigingen
binnen het project. Vraag wél expliciete toestemming voor financiële acties,
betaalde externe diensten, vertrouwelijke clouduploads en live-activering.

## Verificatie per mijlpaal

Voer lint/typechecks, unit-/propertytests, adaptertests en relevante e2e-tests uit.
Test minimaal Chromium en Safari/WebKit voor kritieke flows. Controleer de
interface op 1440×900, 1920×1080, 3440×1440, tablet en mobiele leesmodus, op
licht/donker, met toetsenbord en reduced motion. Vergelijk daadwerkelijke
browserbeelden met het designcontract; repareer afsnijding en visuele afwijkingen.

Publiceer `STATUS.md` met gebouwde functies, testcommando's, testresultaten,
ontbrekende rechten, bekende beperkingen en volgende concrete taak. Neem geen
claim als 'production ready', 'realtime wereldwijd' of 'fiscaal correct' op zonder
het bijbehorende bewijs en afgebakende scope.
