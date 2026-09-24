# Design system en visueel implementatiecontract

**Product:** Modern Trade Terminal  
**Versie:** 1.0, 24 september 2026  
**Status:** ontwerpbrief voor de developer; nog geen gegenereerde mockups of gebouwde UI

## 1. Visuele richting

Ontwerp een premium financieel instrumentenpaneel: precies, rustig, tactiel en
informatierijk. Trading is compact en snel; vermogensplanning is ruimer en
verklarend. Beide voelen als hetzelfde product, niet als twee gekochte templates.

Het scherm draait om data en beslissingen. Vermijd een marketinghero,
welkomstillustraties boven de werkruimte, generieke bento-kaarten, extreem ronde
panelen, overdadige gradients, permanente bewegende achtergronden en decoratieve
3D. Een prijs hoeft niet in een grote afgeronde kaart om belangrijk te zijn.

De kwaliteitslat is: iedere pixel ondersteunt leesbaarheid, herleidbaarheid of
bediening. Een professionele uitstraling is een ontwerpdoel, geen te claimen
gewonnen award.

## 2. Kleur en typografie

Begin met deze tokens en toets contrast in de daadwerkelijke implementatie.
Semantische kleuren zijn onafhankelijk van gebruikersaccenten.

```css
:root[data-theme="dark"] {
  --canvas: #0b0f16;
  --surface: #111722;
  --surface-raised: #182130;
  --surface-hover: #202c3f;
  --border-subtle: #283449;
  --text-primary: #edf2fa;
  --text-secondary: #b3bed0;
  --text-muted: #939fb3;
  --accent: #78a9ff;
  --positive: #62d4ad;
  --negative: #ff8c99;
  --warning: #f1c16e;
  --focus: #accbff;
}
:root[data-theme="light"] {
  --canvas: #f5f7fb;
  --surface: #ffffff;
  --surface-raised: #edf1f7;
  --surface-hover: #e4eaf4;
  --border-subtle: #cbd3e0;
  --text-primary: #152033;
  --text-secondary: #3d4f68;
  --text-muted: #53647a;
  --accent: #2457b3;
  --positive: #17674e;
  --negative: #ae2942;
  --warning: #825708;
  --focus: #164dba;
}
```

Gebruik een lokaal gehoste goed leesbare sans-serif, bijvoorbeeld Inter/Geist met
passende licentie, en een monospacefamilie voor prijzen en technische identifiers.
Gebruik tabular numerals. De belangrijkste prijs is 28–36 px; paginakoppen
24–30 px; paneelkoppen 14–16 px; reguliere UI 13–14 px; ondersteunende metadata
minimaal 12 px. Lange uitleg en onboarding 15–16 px. Laat cruciale orderinformatie
niet kleiner worden om meer data op één scherm te persen.

Gebruik een 4 px spacing-grid, hoofdmarges 16/24 px en panelradii circa 6–10 px.
Tradingpanelen scheiden met dunne lijnen, niet met zware shadows of meerdere
niveaus van geneste kaders. In lichtmodus mag de achtergrond licht zijn maar de
content blijft contrastvast; laat grafieklijnen niet verbleken.

Winst/verlies krijgt altijd ook teken, label of richting. Een waarschuwing heeft
tekst, niet alleen een geel puntje. Focus is duidelijk zichtbaar. Contrast en
bediening moeten op WCAG-AA-niveau worden getest; de tokens alleen bewijzen dat
niet.

## 3. App-shell en navigatie

Een navigatierail van 64 px blijft stabiel. Hoofdonderdelen: Vandaag, Markten,
Terminal, Intelligence, Vermogen, Planning, Lab en Instellingen. Tooltips bij
iconen, leesbare labels in uitgevouwen stand en actieve-staatmarkering.

Bovenin de werkruimte staat een contextbalk van ongeveer 52 px met werkruimtetabs,
command palette, geselecteerde entiteit/account en een zeer zichtbare modus.
Een financiële mode-switch is geen onschuldige thematoggle: LIVE activeren opent
een expliciet proces, niet één klik.

De onderbalk van circa 26 px toont verbindingen, verwerking/achterstand,
peildatum en een systeemstatusdrawer. Toon alleen relevante technische details;
maak de header niet tot een onleesbaar instrumentenpaneel met twintig badges.

`Ctrl/Cmd+K` opent zoeken/acties. Instrumentselectie heeft expliciete linkgroepen
zodat gekoppelde charts, nieuws en orderticket meewisselen. Panelen kunnen ook
worden vastgepind. Toon zichtbaar wanneer een ticket op een ander instrument of
account staat dan de centrale chart.

## 4. Primaire schermen

### 4.1 Terminal — referentie 1920×1080

Na de 64 px rail bevat het werkvlak een watchlist van circa 248 px, een flexibel
middenvlak en een rechtercontextpaneel van circa 336 px. De chart krijgt het
meeste oppervlak, ongeveer 65–72% van de beschikbare hoogte. Onder de chart staan
contextuele tabs voor Orders, Posities, Time & Sales, Nieuws en Journaal.

De watchlist is een echte tabel met symbool, venue/valuta, laatste prijs,
verandering, sparkline en kwaliteitsindicator. Groepeer op door gebruiker gekozen
categorie; geen willekeurige marktmetrieken als vulling.

Het midden bevat de instrumentheader, timeframe/indicatorcontrols, hoofdchart,
volume en hoogstens enkele gekozen subpanes. De rechterzijde heeft tabs
Assistent, Risico en Order. Door een order te openen verschijnt een duidelijke
preview, niet een koopknop boven een generiek AI-antwoord.

Een chartheader toont actuele bron en quotetype naast de prijs. Een vertraagde
feed, gesimuleerde reeks, handelsstop of ontbrekende data is direct zichtbaar.
Laat referentiekoers, uitvoerbare ask/bid en laatste transactie naast elkaar zien
wanneer dat voor de order relevant is.

Op 1440 px wordt de AI-context standaard inklapbaar. Op tablet transformeert het
rechterpaneel naar een drawer. Op mobiel is de app eerst een lees- en
reviewomgeving; verberg complexe orderflow niet in een onbruikbare miniatuur.
Live orderbevestiging op mobiel is pas actief na een afzonderlijk geteste flow.

### 4.2 Vermogen — referentie 1920×1080

Bovenaan staan totaal economisch vermogen, vrij beschikbare liquiditeit en
vermogen met beperkingen, met consistente peildatum. Geen som die privévermogen,
BV-activa en pensioenrechten ongecontroleerd optelt.

De centrale visual is het vermogenspad, met schakelaar historisch/geprojecteerd,
nominaal/reëel en expliciete scenario's. Daaronder komt een volwaardige
rekening-/bezittingentabel. De tweede analysezone toont exposure of cashflow;
geen identieke kaarten met telkens een donut.

De entiteitsselector geeft Privé, Holding, Werk-BV of een geconsolideerd
perspectief. Een ownership/exposurevisual geeft doorklikbare relaties weer en
legt eliminaties uit. Een zijpaneel toont herkomst, waarderingsmethode en
ontbrekende administratie. Bouw hier geen decoratief rondzwevende galaxy.

### 4.3 Planning — referentie 1920×1080

Links staan doelen en scenario's. Middenin een toekomstpad met leeftijd/jaar,
inkomen, uitgaven, belasting en beschikbare buffers. Rechts een inspector met
expliciete aannames en een tab Rekenverantwoording.

Een wijziging in pensioenleeftijd of inleg maakt een conceptscenario. Toon
verschillen ten opzichte van de baseline en de gevolgen voor liquiditeit.
Monte-Carlo-bandbreedtes krijgen een legenda, seed/modelversie in details en een
tekstuele interpretatie zonder schijnprecisie.

De belastingschakelaar toont de gekozen ruleset en het relevante jaar. Voorstellen
staan visueel en functioneel apart van geldende/goedgekeurde regels. Onvolledige
input geeft een concrete lijst ontbrekende gegevens, geen exact ogende prognose.

### 4.4 Source Health — referentie 1440×900

Een tabel met bron, capabilities, bereik, latency, laatste bericht,
abonnementsstatus, queue-age en foutstatus. Klikken opent een drawer met
feedherkomst, rechten, laatste succesvolle controle en diagnose.

Bied acties Verbinding testen, Tijdelijk pauzeren, Prioriteit wijzigen en Mapping
bekijken. Pauzeren geeft aan welke alerts of posities dit raakt. Een provider
uitschakelen mag niet stilzwijgend alle benodigde controles voor live orders
omzeilen.

De bronvergelijker toont tijd/prijs/venue naast elkaar en verklaart waarom data
vergelijkbaar of niet vergelijkbaar is. Maak van providerstatus geen nietszeggende
score op honderd punten.

## 5. Kenmerkende interacties

### Trade Impact Preview

Gebruik een ruime drawer of modal met instrument, venue, account, entiteit, modus,
ordertype, hoeveelheid en prijsbereik. Daaronder een voor/na-tabel met cash,
reserveringen, exposure en planbuffer. Toon kosten en FX apart. Ondersteun
waarschuwingen en blokkerende redenen zonder verscholen tooltips.

De primaire actie heet bijvoorbeeld `Paperorder plaatsen`, niet het misleidende
`Bevestigen` zonder context. Liveacties krijgen een andere duidelijke tekst.
Bij een verlopen quote of veranderde hoeveelheid ververst de preview en vervalt
een eerdere toestemming.

### AI-evidencepaneel

Gebruik vier leesbare secties: Feiten, Berekeningen, Interpretatie en Onbekend.
Bronverwijzingen openen het toegestane bronfragment of de officiële pagina.
Rekenverwijzingen openen calculation details. De gebruiker kan context en
gegevens die naar cloud-AI gaan bekijken.

Geen decoratieve typmachineanimatie die lezen vertraagt. Stream tekst rustig,
maar toon een berekend bedrag pas nadat de relevante gestructureerde tooluitkomst
beschikbaar en gevalideerd is.

### Layout personalisatie

Bied presets Daghandel, Onderzoek, Vermogen en Rustige modus. De gebruiker kan
panelen verslepen, formaat aanpassen, pinnen en lay-outs benoemen. Bewaar
lay-outschema's met versie en migratie. Een ongeldige layout krijgt een herstelactie,
geen wit scherm.

Multi-window/pop-out vensters delen de backendverbindingen en juiste accountcontext.
Open niet per venster opnieuw alle upstream subscriptions. Geef bij verlies van
context of sessie geen handelsbevoegdheid terug zonder controle.

## 6. Motion en prestaties

Beperk gewone overgangen tot circa 120–180 ms; drawers circa 180–220 ms. Gebruik
animatie voor focus, ordening en context, niet als voortdurende aandachtstrekker.
Koersverandering kan een korte subtiele highlight krijgen; voorkom flitsen en
springende kolombreedtes. Respecteer reduced motion en bied een volledig rustige
modus.

Chart- en tabelweergave gebruikt afgesproken batching. Animatie stopt voor
verborgen panelen, terwijl backendmonitoring blijft draaien. Zware visuals zijn
lazy loaded. Vermijd een WebGL- of WebGPU-vereiste voor standaardgebruik.

## 7. Foutstaten zijn productontwerp

Ontwerp afzonderlijk: geen bron aangesloten, ontbrekend abonnement, geen marktdata,
markt gesloten, vertraagde feed, verouderde feed, boekgap, reconnect, onbekende
orderstatus, onvolledige import, onbeoordeelde belastingregel, AI-timeout en
privacyblokkade. Een lege grafiek met spinner is geen uitleg.

Demo heeft overal een zichtbaar label en fictieve voorbeeldgegevens. Een datafout
mag geen mooie maar foutieve grafiek opleveren. Beschikbare oude data mag zichtbaar
blijven met duidelijk tijdstip en beperkingen.

## 8. Oplevering en visuele acceptatie

Maak eerst vier referentiebeelden voor de primaire schermen, plus details voor
orderticket, AI-evidence en foutstaten. Leg tokens, componentanatomie, iconen,
spacing en gedrag vast. Vertaal referenties naar herbruikbare codecomponenten;
gebruik geen screenshot als interface.

Controleer daadwerkelijke browserbeelden op 1440×900, 1920×1080, 3440×1440,
tablet en mobiele leesmodus. Test ook 200% zoom, toetsenbordfocus, light/dark en
reduced motion. Vergelijk minimaal layout, typografie, kleuren, tabeldichtheid,
chartleesbaarheid en foutweergave met de referenties.

Lever een fidelity-log met concrete afwijkingen en fixes, plus bewijs van deze
flow: instrument kiezen → bron inspecteren → chart analyseren → paperpreview →
order → journaal → vermogensimpact. Functionele tests vervangen deze visuele
controle niet, en mooie screenshots vervangen functionele tests evenmin.
