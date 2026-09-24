# Provider-, capability- en licentiematrix

Gecontroleerd 2026-09-24 op primaire documentatie. Documentatie lezen bewijst geen accounttoegang, live feed, abonnement of datalicentie. Buildtooling haalt publieke pakketten op; runtime heeft LOCAL_ONLY-beleid.

| Bron/library | Gebouwd/gebruikt | Rechten/status | Primaire bron |
|---|---|---|---|
| Eigen fixtures | Quotes, trades, candles, volume, SMA | Synthetisch, lokaal; geen beursdata of handelsrecht | services/api/app/market.py |
| Kraken Spot v2 | Ticker/trade-normalisatie; eenmalige opt-in probe | Publieke data vereist geen key; live niet uitgevoerd, verdere hergebruik/AI-rechten onbekend | [Ticker](https://docs.kraken.com/exchange/api-reference/spot-websocket-v2/ticker), [Trades](https://docs.kraken.com/exchange/api-reference/spot-websocket-v2/trade) |
| Codex | Alleen read/preview-bevoegdheidsgrens | Runtimebridge ontbreekt; accountautorisatie nodig, LOCAL_ONLY | [Bouwplanbronnen S01–S05](../SOURCES.md) |
| Jev/TypeSafe | Begrensde ABSTAIN-response | HTTP-runtime ontbreekt; credentials en data-uitgiftebeleid nodig | [Quickstart](https://docs.typesafe.ai/introduction/quickstart) |
| React / React DOM | 19.3.0 | MIT; publieke npm-installatie, geen provideraccount | [React-blog](https://react.dev/blog) |
| Vite | 8.3.1 | MIT | [Vite](https://vite.dev/guide/) |
| Lightweight Charts | 5.2.1 | Apache-2.0; NOTICE/licentie bewaard; logo en TradingView-link zichtbaar | [Docs](https://tradingview.github.io/lightweight-charts/docs), [NOTICE](https://github.com/tradingview/lightweight-charts/blob/master/NOTICE) |
| Docker Compose | Lokale deployment/secrets | Bronfiles zelf beschermen; geen versleutelde vault | [Compose-secrets](https://docs.docker.com/compose/how-tos/use-secrets/) |
| cryptography | 46.0.5, alleen lokale backuphelper | Fernet authenticated encryption; sleutel lokaal buiten iCloud | [Fernet](https://cryptography.io/en/46.0.5/fernet/) |

Exacte frontendversies en transitieve integriteit: package-lock.json. Pythonversies: services/api/requirements.lock. Back-uphelper: scripts/requirements-backup.lock. Rust: Cargo.lock. Baseimages: infra/images.lock. Installatie compatibel gebleken door build en tests op arm64; geen algemene kwetsbaarheidsvrijverklaring of amd64-claim.

AG Grid, Dockview, NATS en een permanente Rust-gateway zijn in M1 niet geïnstalleerd. Advanced Charts/Trading Platform wordt niet gebruikt. Coinbase, Alpaca, IBKR, nieuws en financiële imports zijn M2/M3; hun dekking/toegang wordt niet verondersteld. Zie oorspronkelijke SOURCES.md voor het bredere onderzoeksregister, niet als activatiebewijs.
