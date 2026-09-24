# M0 implementatiecontract · 24 september 2026

De vier bestaande gegenereerde beelden in references zijn vooraf geïnspecteerde visuele richting. Dit contract beperkt de inhoud tot de M1-scope. De beelden bevatten geen echte saldi, rechten of belastingresultaten.

## Schermen en primaire flow
Terminal: 64px rail, 52px contextbalk, 248px watchlist, dominante chart, 336px orderinspector. Eén gekoppelde instrumentselectie stuurt chart, bron, ticket en analyse. Onder de chart: Orders, Posities, Trades en Journaal. Drie synthetische EUR-spotparen. Werkende 15m/1u/4u/1d historie en SMA; geen uitgeschakelde nep-chartcontrols.
Vermogen: open samenvattingsband voor oefencash, gemarkeerde posities en oefenvermogen, één rekeningentabel, journaal en herkomst. Geen echte vermogenssom of gefingeerde BV-bezittingen.
Planning: bewerkbare oefenreserve, effect van de laatste paperorder, deterministisch cashpad met expliciete maandinleg/uitgaven. Geen belastingen of rendementsvoorspelling.
Bronnen: capabilitytabel en inspecteerbaar manifest. Fixture pauzeren/hervatten, mapping bekijken en lokale contractdiagnose. Geen groene live-status zonder echte proef.

## Componenten
AppShell, NavigationRail, ContextBar, StatusBar, DataTable, SourceBadge, Money, InstrumentSelector, MarketChart, OrderTicket, ImpactDialog, EvidencePanel, EmptyState, ErrorNotice, CommandPalette, TutorialStepper.
ImpactDialog: instrument, venue, account, simulatiemodus, exacte intent, voor/na-cash, positie, kosten, buffer, quoteherkomst, vervaltijd, IOC-restant. Bevestiging vervalt bij edit, bronpauze of wijziging van de rekening.
EvidencePanel: Feiten / Berekeningen / Interpretatie / Onbekend. Lokale deterministische uitleg duidelijk onderscheiden van Codex of Jev. Externe AI blijft uit.

## Tokens en bediening
Kleuren exact uit DESIGN_SYSTEM.md; sans lokaal systeemfont met licentie van host, cijfers monospace/tabular. UI 13–14px, metadata minimaal12px, prijs32px, kop28px. Spacing4px, radius6px, dunne scheidingen, geen widgetwand.
1440px compacte inspector; tablet inspector als drawer; mobiel leesmodus met orderactie geblokkeerd en uitleg. Command palette Ctrl/Cmd+K; Escape sluit dialog; focus trap en herstel; licht/donker en reduced motion.

## Foutstaten
Bron gepauzeerd → oude fixture zichtbaar met STALE, nieuwe orders geblokkeerd. Preview verlopen → herberekenen. Cash/revisie gewijzigd → nieuwe preview. Geen posities → uitleg + open terminal. AI niet aangesloten → ABSTAIN en lokale uitleg. Fiscaliteit → ONVOLLEDIG, geen bedrag.

## Opzettelijke verschillen met oude conceptbeelden
Nederlandse labels en actuele fixture-datum, geen gefingeerde persoon. Rail en kleuren volgen DESIGN_SYSTEM. Alleen drie ondersteunde paren. Geen verbonden bank-/pensioensaldi, verwachte rendementen of AI-advies. Open tabellen vervangen kaarten met niet-ondersteunde metrics. Dit is de vóór implementatie vastgelegde, afgebakende M1-referentie.
