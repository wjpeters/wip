# ADR 0002 · Lokale M1-kern

Keuze: voortbouwen op aangetroffen eerdere code, uitsluitend in nieuwe WPOS-local projectmap. Oude Downloads-installatie en Docker-volumes blijven ongemoeid. Composeproject wpos-mtt, poort 4186.

SPA: React/TypeScript/Vite volgens plan. Zelfstandige native tabellen voor drie instrumenten; AG Grid en Dockview pas bij uitgebreide workspace. Geen betaalde licentie. Voordeel: kleine bundel/toegankelijke HTML; nadeel: nog geen docking. Eigen chartlaag vervangen door Lightweight Charts als basis voor correcte interactie en schaal; lokale historie wordt door backend geleverd.
Gateway/bus: M1 scheidt marktmodule en financiële domeinen in code. Drie containers web/api/postgres. Rust/NATS/worker worden niet als lege services toegevoegd. Geen 5000-events/s claim. Uitbreiding met processen volgt zodra streaming wordt geactiveerd en gemeten. Nadelen: geen procesisolatie van marktparser; M1 gebruikt begrensde lokale fixtures. Publieke Kraken-adapter is opt-in en alleen read-only; geen live start door deze release.
Ledger: PostgreSQL, atomische rekeninglock, duurzame previews en unieke preview-orderrelatie. Decimal, cents ROUND_HALF_UP, gemiddelde kostprijs en apart resultaat. IOC limit: direct uitvoerbaar deel; restant expliciet geannuleerd. Geen rustende orders of wachtrijclaim.
AI: providercontracten buiten rekenkern. LOCAL_ONLY; geen cloudcall, geen runtime-shell, geen geheime context. Codex voor onderzoek/uitleg; Jev voor begrensde beoordelingen met ABSTAIN bij ontbrekende toegang. Runtimeuitvoering M4, afzonderlijk bewijs nodig.
Tax: eigen rulesetcontract, geen actieve ruleset of calculator M1. Definitieve berekening geblokkeerd met UNAPPROVED_RULESET. Geen fiscaal getal in de paperimpact.
Kosten: uitsluitend bestaande lokale Docker-runtime en open-source libraries; geen abonnement of betaalde provider geactiveerd.
