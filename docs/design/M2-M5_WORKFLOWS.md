# M2–M5 schermcontract

Bouw voort op de vier goedgekeurde referenties in `references/`. Donkere en lichte tokens, compacte navigatierail, duidelijk hoofdwerkvlak met één contextkolom. Standaard 1440×900; op mobiel één kolom en horizontaal toegankelijke tabellen. De persoonlijke omgeving begint leeg.

- **Markten**: links doorzoekbare instrumentlijst; centraal geselecteerd profiel en gekoppeld orderboek/tape; rechts herkomst/vergelijkbaarheid. Onder tab Nieuws & kalender staan clusters met publicatie én beschikbaarheid. Selectie leidt naar hetzelfde instrument in Terminal; metadata-only instrumenten krijgen geen spotticket.
- **Administratie**: scope en eigenaar bovenaan, saldo/waarderingskwaliteit als samenvattende regel. Tabs Rekeningen, Importeren, Journaal en Bezittingen. Import is een vaste volgorde: bestand/mapping → preview → classificatie/conflicten → bevestigen → reconciliatie. Bronkenmerk, valuta en fouten blijven naast de rij.
- **Vermogen**: bestaande paperbalans blijft intact. Nieuwe Administratie toont privé/BV-geconsolideerde feiten en expliciete eliminaties; geen vermenging met paper.
- **Planning**: lijst opgeslagen scenario's naast invoer/resultaat. Resultaat toont basis en stress, beschermd geld, pensioen dat vaststaat, doeltekorten en aannames. Vergelijking gebruikt onveranderlijke snapshots. Fiscale en pensioenformulieren gebruiken dezelfde veldcomponenten en de schema's van de server. Iedere uitkomst toont versie, scope, conceptstatus en bronnen.
- **Nalatenschap & documenten**: begeleide verdeling met juridische reviewvragen, documentenlijst met categorie/versie/download. Geen juridische tekstgenerator. Persoonlijke documenten zijn lokaal versleuteld.
- **Bronnen**: provider-capabilities en ontbrekende toegang, configureerbare prioriteit, officiële bronnencontrole en expliciete menselijke goedkeuring van formule+bronversie.
- **Lab**: reproduceerbare replay/backtest met tijdschuif, datasetversie, volgende-baruitvoering en kosten; modelbeoordeling in aparte tab. Bestaande tutorial blijft bereikbaar.

Gedeelde componenten: WorkspaceTabs, ScopeBar, SchemaForm, ImportPreview, EvidenceResult, JobProgress, ScenarioCompare, DocumentList. Formulieren houden geld als strings. Foutmeldingen blijven in het werkvlak, focus en native controls werken met toetsenbord. Lang werk toont status/annuleren; een ontbrekende koppeling krijgt een concrete status. Geen succesclaim voordat server bevestigt.
