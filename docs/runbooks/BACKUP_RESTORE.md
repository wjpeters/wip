# Versleutelde back-up en herstel

Release 0.5.0 ondersteunt handmatige lokale databaseback-ups. Het PostgreSQL-dump bevat ledger, orders, previews, accountinstellingen, auth-hashes, audit, administratie, scenario’s, rule-reviews, kalender en versleutelde documenten. Alleen versleutelde bytes worden naar schijf geschreven. Fernet via cryptography 46.0.5 verifieert authenticiteit vóór herstel. De sleutel staat in `.secrets/backup_key` met modus 600, buiten iCloud. Bewaar de oorspronkelijke sleutel afzonderlijk veilig als je back-ups naar een eigen off-device locatie kopieert. Zonder deze sleutel is herstel onmogelijk. Er is geen externe back-up ingesteld.

Installeer zo nodig `scripts/requirements-backup.lock` in de lokale .venv; zie INSTALLATION.

```sh
rtk proxy .venv/bin/python scripts/backup.py create
```

Dit meldt alleen het versleutelde bestandspad en de grootte. Vervang FILE hieronder door dat pad:

```sh
rtk proxy .venv/bin/python scripts/backup.py verify --file FILE
```

`verify` maakt een nieuwe tijdelijke database, herstelt het archief, controleert journaalbalans/cash en vergelijkt hashes van alle publieke tabellen met de huidige database. Daarna wordt uitsluitend die tijdelijke database verwijderd. Een oude back-up mag afwijken van een intussen gewijzigde rekening; `matches_current_source=false` is dan geen bewijs van een kapotte back-up. De inhoud moet altijd intern reconciliëren.

```sh
rtk proxy .venv/bin/python scripts/backup.py recover --file FILE
```

`recover` maakt een nieuwe `recovered_mtt_<random>` database en verwijdert herstelde actieve sessies. De huidige `mtt`-database wordt nooit overschreven en de app wordt niet automatisch omgeschakeld. Voor daadwerkelijke ingebruikname: stop de API/web, laat de oorspronkelijke database behouden, kies de herstelde database in een lokale configuratie, start de API met de passende lokale secret en controleer startup-reconciliatie. Deze laatste omschakeling is niet uitgevoerd op de gebruikersomgeving. De gebruiker moet opnieuw inloggen met het wachtwoord van de back-up.

Herhaalbare QA-proef: voeg `--project wpos-mtt-qa` toe aan create en verify. [Bewijs M5](../evidence/backup-restore-m5.json): restore op een nieuwe database, alle tabelhashes identiek, geldsaldo in balans, vervalste ciphertext geweigerd. De probe-database is verwijderd. De eerste test vond plaats vóór de laatste browserrun; latere QA-orders wijzigen logischerwijs de bronhash.

Grenzen: geen dagelijkse scheduler, rotatie of off-device controle; documenten en de vaultsleutel worden meegenomen in de versleutelde envelop; providerconfiguraties en AI-conversatievolume niet. Grote dumps worden in geheugen verwerkt. Broncode/lockfiles staan in Git; Git vervangt deze databaseback-up niet. Back-ups zijn lokaal op dezelfde host, dus op zichzelf geen bescherming tegen verlies van die host.

## Documentherstel en monitoring

Backupformaat MTT_BACKUP_2 bewaart de database plus vaultsleutel in één versleutelde envelop. Verify ontsleutelt iedere documentinhoud en metadata, controleert contenthashes en sluit af zonder de actieve database te wijzigen. Recover schrijft de herstelde vaultsleutel als nieuw lokaal 600-bestand; bestaande sleutels worden niet overschreven. Oudere M1-dumps blijven leesbaar. Bij ingebruikname van herstel moeten database én bijbehorende vaultsleutel samen worden geselecteerd.

De kalenderworker schrijft iedere vijf seconden een heartbeat. Daardoor kan vergelijking met een draaiende actuele database afwijken terwijl het archief correct is. Voor een exacte tabelvergelijking: stop alleen de QA-worker tijdens create+verify en voer geen UI-mutaties uit. De app toont gemiste monitoring na hervatten.
