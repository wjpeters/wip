# ADR 0003 · M2–M5 lokale productuitbreiding

Opdracht 2026-09-24: voltooi de read-only/paperapplicatie. Bestaande gebruikersrekening en M1-ledger blijven behouden. Verder ontwikkelen in dezelfde goedgekeurde lokale map, QA op eigen volume.

De modulaire API wordt uitgebreid met marktadapters, research, financiële imports/entiteiten, scenario's/tax, AI-policy en documentvault. Domeinen krijgen afzonderlijke opslag en deterministische functies; AI draait in een eigen opt-in bridgeproces. Financiële administratie heeft afzonderlijke DEMO en PERSONAL-scopes. Paperboekhouding wordt nooit samengevoegd met persoonlijke feiten.

Primaire UI-routes: Markten → instrument/research → Terminal/preview; Administratie → importpreview → reconciliatie → geconsolideerd vermogen; Planning → doel/scenario → pensioen/fiscaliteit → bron/review; Lab → replay/backtest → evaluatie. Geen verzameling losstaande KPI-widgets. Bestaande primaire referenties, tokens, rail en table/detailpatroon blijven leidend. Nieuwe componenten: WorkspaceTabs, EntityScope, ImportPreview, SourceEvidence, ScenarioCompare, RulesReview, DocumentList, AssistantConversation en ReplayControls.

Externe bronadapters zijn opt-in en server-side. Geen providerkeys in browser. Missing credentials geven NOT_RUN_MISSING_CREDENTIALS, publieke feeds zonder verificatie NOT_RUN_EXTERNAL_NETWORK. Synthetische fixturemodus is permanent zichtbaar. Persoonlijke gegevens gaan standaard niet naar AI. Docker-default heeft geen modelcredentials en geen actieve cloudcalls.

Fiscale startscope: NL 2025, afgebakende individuele calculators en voorwaardelijke scenario's. Parameters uit officiële bronnen met peildatum en reviewstatus. Menselijke review blijft nodig voor promotie; geen aannames over Willems huishouden/BV. Ontbrekende input blokkeert definitieve output. Afwijkende jaren/situaties geven concrete reviewredenen, geen stilzwijgende extrapolatie.

Testpoort per fase: contract-, domein-, integratie- en browserproeven; definitieve acceptatiematrix per oorspronkelijke backlog-ID. Bewezen fixtures en echte providerverificatie blijven afzonderlijke kolommen. M6/M7/live, betaalde diensten en vertrouwelijke cloudcalls blijven buiten de release.
