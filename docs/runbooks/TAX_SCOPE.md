# Fiscale scope · NL 2025

De app heeft één expliciete ruleset `nl-2025-scope-1.0.0`. Andere jaren worden afgewezen. Bedragen worden met Decimal berekend en als strings verzonden. De actuele formulehash omvat code en parameters; bronversies zijn afzonderlijk gebonden aan review.

| Calculator | Ondersteund | Niet inbegrepen |
|---|---|---|
| Box 1 | Schijventarief over opgegeven belastbaar inkomen; volledig jaar onder AOW of volledig jaar AOW, inclusief oudere cohortgrens | Heffingskortingen, aftrekpostbepaling, premiedeeljaar, netto loon/uitkering, volledige aangifte |
| Box 2 | Positief regulier inkomen met opgegeven dividendvoorheffing | Verliesverrekening, grensoverschrijdende situaties en bijzondere structuren |
| Box 3 | Gewone banktegoeden/beleggingen/schulden, peildatum, partneraandeel, forfait en volledig opgegeven werkelijk rendement | Onvolledige opbrengsten/waardemutaties, bijzondere vrijstellingen, automatische waardering van vastgoed/crypto of juridische keuze bij uitzonderingen |
| Lijfrente | Inkomen vorig jaar, leeftijdsbevestiging, Factor A/overgangsregime of volledige WTP-aftrek uit UPO, betaalde inleg; tien jaar resterende ruimte met bewijs | Automatisch invullen ontbrekende historische ruimte, volledige actuarieel berekende pensioenuitkering/AOW |
| Schenking/erfenis | Gewone geldverkrijging voor kind, kleinkind of overige ontvanger | Partner-erfvrijstelling/imputatie, BOR, vruchtgebruik, eenmalige vrijstellingen, vrij-van-recht en juridische documentgeneratie |

Bronnen en officiële rekenvoorbeelden staan in de app onder Regels & bronnen en in `services/api/app/tax.py`. De officiële Box 3-voorbeelden worden als regressietests gebruikt; overige grenzen en tegenvoorbeelden staan in de domeintests. Een testsucces is geen individuele fiscale goedkeuring.

Een concept is bruikbaar voor een afgebakende berekening maar blijft CONCEPT_UNREVIEWED. Definitieve scoped output vereist complete passende invoer én expliciete menselijke review van de exacte formule/bronbinding. Alle vereiste bronnen moeten recent succesvol zijn gecontroleerd; downloads die falen zijn geen 'ongewijzigd'. Review is dertig dagen gebonden, vervalt bij gewijzigde code/parameters/bronnen en omvat geen toekomstige wetgeving. Wetgevingsvoorstellen worden niet automatisch tot actuele rekenregels gepromoveerd.

De bronmonitor haalt publieke allowlisted pagina's op bij een handmatige controle. Er is geen dagelijkse cloudtaak of automatische fiscale code-update. De broncontrole slaat hashes/metadata op; het is geen volledig digitaal archief van officiële webpagina's. De applicatie is opgeleverd met NEEDS_HUMAN_REVIEW.
