# Visuele vergelijking · M1

Vier concepten zijn vóór implementatie geïnspecteerd. Laatste QA: originele terminalreferentie en daadwerkelijke Chromium-terminal/preview opnieuw in dezelfde controle bekeken. Vermogen, Planning, Bronnen, lichtthema en mobiel eveneens visueel geïnspecteerd. De verse lege terminal is daarnaast op het native conceptcanvas 1672×940 naast de originele referentie bekeken. Rail, watchlist, dominante chart, inspector en onderste contextstrook volgen het scoped contract. Reguliere browserbewijzen staan op de vijf overeengekomen viewports; geen pixelidentieke claim voor bewust afwijkende M1-inhoud.

| Aspect | Bevinding |
|---|---|
| Compositie | Smalle rail, rustige header, watchlist links, dominante chart, order/risico/uitleg rechts en gekoppelde transactietabel onderaan |
| Typografie | Systeemfont, tabelcijfers monospace/tabular; UI 13–14px, metadata 12px; expliciete Nederlandse valutaformattering |
| Kleur/materialen | Grafiet, dunne scheidingen, gedoseerd blauw; amber PAPER/SIMULATED en rode/groene marktsemantiek; geen decoratieve glow |
| Maat/ritme | 64px rail, 52px header, 248px watchlist, 336px inspector; tabellen dragen informatie zonder losse KPI-kaartenwand |
| Interactie | Gekoppelde selectie, werkende timeframe/SMA, chartzoom/crosshair, source drawer, previewdialoog, journaal en plan |
| Responsief | Geen pagina-brede horizontale overflow op vijf viewports; interne tabellen mogen scrollen. Tablet orderpaneel uitklapbaar; mobiel leesmodus |
| Finance | Vermogen en Planning volgen een rustiger ritme met open samenvatting, één hoofdvisual, rekeningen/assumpties en herkomst |

Bewuste afwijkingen, vóór implementatie vastgelegd: drie synthetische instrumenten in plaats van een fictieve wereldmarkt-watchlist; geen AI-orderadvies of niet-aangesloten bank-/BV-balansen; een expliciete previewdialoog; IOC in plaats van onbewezen dagorders; lokale tokenkleuren uit DESIGN_SYSTEM in plaats van exacte kleuren van het gegenereerde beeld. M1 gebruikt vaste responsieve layout, geen docking.

Gevonden en hersteld: chartattributie zat onder een `img`-rol met interactieve link (axe-fout); vervangen door een gelabelde region. Tabel- en bronlabels gecontroleerd op afsnijding. Chartprijzen naar nl-NL-formattering. Testbediening aangepast voor herhaald opslaan van gewijzigde planreserve, niet door asserts te verwijderen. Geen console-pageerrors in beide kritieke browserflows.

Resterende grenzen: geen afzonderlijke handmatige screenreadertest, native Safari of native browserzoom; automatische axe-check van terminal, niet volledige certificering van alle schermen. Scope/inhoudverschillen met het brede productconcept staan expliciet in STATUS.


## M2–M5 visuele controle · 24 september 2026

De echte `chromium-expanded-scenario.png` is naast `references/planning.png` bekeken. Behouden: donkere grafietbasis, smalle rail, blauwe focus/acties, scenarioselectie links, groot vermogenspad en aansluitende gegevenscontrole. Bewuste aanpassing: invoer en opgeslagen resultaat hebben elk een volledig werkvlak; geen permanent smalle invoerkolom bij tientallen fiscale velden. De oudere reference bevat fictieve pensioen-/netto-inkomenscurves die niet als bestaande rekencapability zijn gekopieerd. Geblokkeerd pensioen en cashreserves staan expliciet apart.

Administratie en Markten gebruiken dezelfde rij-/detailstructuur, componenten, tokens en scopebalk. Geteste beelden: 1440, 1920, 3440, 1024 en 390 breed, Chromium en WebKit. Mobiele tabellen scrollen binnen hun vlak; vaste navigatie blijft bereikbaar. Full-page mobiele screenshots bevatten de vaste balk op de viewportpositie, geen onbereikbare inhoud: de daadwerkelijke pagina blijft scrollbaar. Geen horizontale paginauitloop in de assertions.

Reparaties uit browserproeven: eenduidige namen voor chartselecties, expliciete toegankelijkheidsnaam voor de omgeving en gegenereerde formuliervelden, bovenaan beginnen bij scenario-screenshots, ontbrekende tweekolomsopmaak Assistent. Lazy geladen werkruimtes houden de hoofdroute compact. Axe-controles op de primaire routes en licht/donker-terminal gaven geen overtredingen binnen de geteste regels. Geen volledige handmatige screenreader- of native Safari-certificering.
