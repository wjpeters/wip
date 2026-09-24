# Synthetische fixtures

`market/m1-quotes.json` bevat uitsluitend zelfgekozen fictieve bedragen. Runtimegenerator in `services/api/app/market.py` produceert versie `mtt-synthetic-v1` met peildatum 2026-09-24T12:00:00Z, vaste seed, drie EUR-spotparen, 120 candles per interval, synthetisch volume en takertrades. Geen historische beursdataset. Back-endtests borgen determinisme, SMA en quote-semantiek.

Kraken-voorbeelden in test_domain.py en de contractdiagnose zijn synthetische protocolberichten, geen opgeslagen livefeed. Hun parserstatus heet TESTED_WITH_FIXTURES. Grote trade-ID, malformed input, venue, bid/ask, onbekende symbolen en decimal strings worden getest. QA-screenshots bevatten alleen oefengeld.
