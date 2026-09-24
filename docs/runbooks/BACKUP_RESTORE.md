# Versleutelde back-up en herstel

M1 ondersteunt handmatige lokale databaseback-ups. Het PostgreSQL-dump bevat ledger, orders, previews, accountinstellingen, auth-hashes en audit. Alleen versleutelde bytes worden naar schijf geschreven. Fernet via cryptography 46.0.5 verifieert authenticiteit vóór herstel. De sleutel staat in `.secrets/backup_key` met modus 600, buiten iCloud. Bewaar de oorspronkelijke sleutel afzonderlijk veilig als je back-ups naar een eigen off-device locatie kopieert. Zonder deze sleutel is herstel onmogelijk. Er is geen externe back-up ingesteld.

Installeer zo nodig `scripts/requirements-backup.lock` in de lokale .venv; zie INSTALLATION.

```sh
rtk proxy .venv/bin/python scripts/backup.py create
```

Dit meldt alleen het versleutelde bestandspad en de grootte. Vervang FILE hieronder door dat pad:

```sh
rtk proxy .venv/bin/python scripts/backup.py verify --file FILE
```

`verify` maakt een nieuwe tijdelijke database, herstelt het archief, controleert journaalbalans/cash en vergelijkt hashes van account/orders/ledger met de huidige database. Daarna wordt uitsluitend die tijdelijke database verwijderd. Een oude back-up mag afwijken van een intussen gewijzigde rekening; `matches_current_source=false` is dan geen bewijs van een kapotte back-up. De inhoud moet altijd intern reconciliëren.

```sh
rtk proxy .venv/bin/python scripts/backup.py recover --file FILE
```

`recover` maakt een nieuwe `recovered_mtt_<random>` database en verwijdert herstelde actieve sessies. De huidige `mtt`-database wordt nooit overschreven en de app wordt niet automatisch omgeschakeld. Voor daadwerkelijke ingebruikname: stop de API/web, laat de oorspronkelijke database behouden, kies de herstelde database in een lokale configuratie, start de API met de passende lokale secret en controleer startup-reconciliatie. Deze laatste omschakeling is niet uitgevoerd op de gebruikersomgeving. De gebruiker moet opnieuw inloggen met het wachtwoord van de back-up.

Herhaalbare QA-proef: voeg `--project wpos-mtt-qa` toe aan create en verify. [Bewijs](../evidence/backup-restore.json): restore op een nieuwe database, alle drie de hashes identiek, geldsaldo in balans, vervalste ciphertext geweigerd. De probe-database is verwijderd. De eerste test vond plaats vóór de laatste browserrun; latere QA-orders wijzigen logischerwijs de bronhash.

Grenzen: geen dagelijkse scheduler, rotatie of off-device controle; geen backup van documenten (M1 kent geen uploads). Grote dumps worden in geheugen verwerkt. Broncode/lockfiles staan in Git; Git vervangt deze databaseback-up niet. Back-ups zijn lokaal op dezelfde host, dus op zichzelf geen bescherming tegen verlies van die host.
