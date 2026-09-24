# Gebruik · 0.5.0

## 1. Oefen de volledige tradeflow

Open Terminal en kies BTC, ETH of SOL. Bron inspecteren toont SIMULATED. Kies interval, charttype en indicator; onder grafiekinstellingen staan vier tijdvensters, log-schaal, paneelzijde, dichtheid en een horizontaal prijsniveau. Een apart venster toont alleen gekoppelde grafieken.

Vul een kooplimiet en aantal in, bekijk de preview en bevestig binnen zestig seconden. Alleen het direct beschikbare deel wordt uitgevoerd; de rest vervalt. Cash, kosten en positie worden atomair geboekt. Bekijk Orders/Journaal en Vermogen. Pauzeer de fixture in Bronnen om te zien dat nieuwe orders blokkeren. Planning → Paperplan gebruikt uitsluitend deze oefenrekening.

## 2. Richt je administratie in

Kies Administratie → Omgeving. DEMO bevat pas na 'Laad fictieve voorbeeldadministratie' oefengegevens; PERSONAL begint leeg. Maak een juridische eigenaar en rekening aan. Gebruik het getoonde eigenaar-/rekeningkenmerk in invoer die hierom vraagt. Leg een eigendomsketen vast met percentages. Een holdingbelang en dezelfde onderliggende activa worden niet dubbel geteld. Pensioenaanspraken zijn geen vrije cash.

Importeren accepteert CSV met kolommapping of CAMT.053. Gebruik het voorbeeld als contract voor broker-CSV. Datums en decimaalteken worden expliciet gekozen. Een import verloopt altijd via preview; onbekende categorieën vereisen beoordeling. Classificeer beide benen van eigen overboekingen als transfer en leg intercompanyleningen met tegenrekening vast. Bevestig pas wanneer de preview geen conflicten heeft. Herimport is idempotent. Een gewijzigd bedrag onder dezelfde referentie is een conflict.

Journaal blijft bewaard. Corrigeer via een tegenboeking met reden; afhankelijke transacties moeten eerst worden gecorrigeerd. Een CSV-export ontsmet spreadsheetformules. Posities gebruiken gemiddelde kostprijs. Bij een niet-EUR-transactie voer je EUR per eenheid vreemde valuta in. Waardeer vreemde cash via Rekeningen → Valutakoers waarderen. Het oorspronkelijke vreemde-valutasaldo blijft behouden.

Bezittingen ondersteunt handmatige activa, negatieve schulden, deelnemingen en pensioen. Een nieuwe waardering bewaart de eerdere versie. Positiewaarderingen en splits worden expliciet ingevoerd. Ontbrekende marktwaardering blijft kostprijsfallback met label. Onder Rendement voer je begin/eindwaarden en externe kasstromen in: TWR gebruikt kasstromen aan het einde van iedere deelperiode; IRR gebruikt datums, stortingen negatief en eindwaarde positief. De app verzint geen historische waarderingen.

## 3. Maak een plan

Kies dezelfde omgeving en een eigenaar. Vul eigen aannames in of gebruik uitsluitend in DEMO het voorbeeld. Het plan bewaart de actuele administratieversie; cash en beleggingen zijn expliciete scenario-inputs, geen stilzwijgende synchronisatie. Controleer ze vóór berekening. De lokale worker berekent maandcashflow, doelen, basis en stress. Monte Carlo is een begrensd synthetisch model, geen marktvoorspelling.

Iedere berekening wordt een onveranderlijke snapshot. Vergelijken toont invoerverschillen en resultaten bij gelijke scope/horizon; fiscale vergelijkingen vereisen hetzelfde rekentype. Handelsimpact gebruikt een afgerond scenario, dezelfde eigenaar, een EUR-rekening en ongewijzigde administratieversie. Belastingreserve, langetermijnbuffer en handelspotje worden afzonderlijk getoetst. Dit autoriseert geen order.

Fiscaliteit en Pensioen ondersteunen alleen de afgebakende 2025-regels; lees TAX_SCOPE. Bijzondere of onvolledige gevallen worden geblokkeerd. Regels & bronnen haalt alleen vaste publieke officiële bronnen op. Een mislukte download is FETCH_FAILED. Review bindt een formulehash aan de gecontroleerde bronversies en vervalt bij wijzigingen/ouderdom. De applicatie beoordeelt zichzelf niet juridisch.

## 4. Documenten en nalatenschap

De kluis bewaart PDF, tekst en ondersteunde afbeeldingen lokaal versleuteld, maximaal 5 MB per document en 500 documenten. Categoriseer, koppel desgewenst een entiteit en voeg een opvolgende versie toe. Download wordt als bijlage aangeboden. Documentinhoud en bestandsnamen gaan niet naar een model.

Nalatenschap is een eenvoudig scenario, geen testament. Complexe rechtsverhoudingen vragen review. Voor erf-/schenkberekeningen gelden dezelfde jaar- en scopegrenzen als bij fiscaliteit.

## 5. Bronnen en assistentie

Markten bevat het bronprofiel, kwaliteit, vergelijkbaarheid, L2 en tape. Unknown aggressor-side telt niet als koop/verkoop; coverage blijft zichtbaar. Coinbase/Alpaca fixturetests bewijzen parsing, geen verbinding. ECB-demo is een referentiekoers, nooit executieprijs. Nieuwsimport vereist bevestigde weergaverechten; RSS/Atom en het gedocumenteerde JSON-contract bewaren herkomst en revisies. Nieuws is bronmateriaal, geen opdracht aan AI.

Lokale kalenderherinneringen werken wanneer Docker draait. Na slaap/herstart is gemiste monitoring zichtbaar. Er wordt geen e-mail, agenda-item of push verstuurd. Externe beursagenda's zijn niet aangesloten.

Assistent → Lokale uitleg werkt zonder provider. Onderzoek toont eerst precies de openbare/synthetische broncontext en je prompt. Alleen na bevestiging kan een afzonderlijk geactiveerde provider worden gebruikt. Gebruik geen vertrouwelijke prompt. De gateway geeft geen toegang tot persoonlijke administratie, kluis, brokercredentials of shell. Evaluatie toont een synthetische testset; dat is geen gemeten modelkwaliteit.

## 6. Bewaren en herstellen

Maak regelmatig een versleutelde back-up volgens BACKUP_RESTORE. Bewaar de back-upsleutel afzonderlijk veilig buiten iCloud. De actieve datavolumes zijn lokaal in Docker. Alleen Git gebruiken beschermt de administratie en documenten niet.
