# Privacy en veiligheidsgrenzen · 0.5.0

- Het project, lokale secretbestanden, Docker-volumes, documenten en back-ups staan buiten iCloud. Alleen een niet-geheime projectverwijzing staat in WPOS. Er is geen cloudopslag of telemetry.
- Lokale auth: zelfgekozen wachtwoord, salted PBKDF2, acht uur server-side sessie, HttpOnly/SameSite=Strict, Host/Origin- en CSRF-controle. Geen verborgen resetendpoint. Alleen loopbackpoort 4186 wordt gepubliceerd.
- Web/API/worker en optionele services: non-root waar het image dat ondersteunt, read-only filesystem, tmpfs, resourcegrenzen, dropped capabilities, geen Docker-socket of home-mount. PostgreSQL draait in het officiële image op een intern netwerk.
- Domeinen zijn gescheiden: paperrekening, DEMO/PERSONAL-administratie, marktservice, analyseworker, fiscale code en optionele AI-container. De marktservice kent geen financiële database. De AI-container krijgt geen documenten, persoonlijke financiële records of brokersecrets.
- Alleen bronmonitor-worker en expliciet optionele providercontainers hebben egress. De gewone API heeft geen publieke internetroute. De bronmonitor leest vaste officiële publieke URLs; documenten kunnen geen URL of toolopdracht afdwingen.
- AI standaard uit, limieten nul. Lokale uitleg is geen modelantwoord. Na provideractivatie blijven gegevenspreview, publieke/synthetische scope en expliciete bevestiging verplicht. Geheim-/persoonsnummerpatronen worden geweigerd; dit is geen garantie dat iedere vertrouwelijke vrije tekst automatisch herkenbaar is. Vertrouwelijke cloudverwerking is niet ondersteund.
- Modeloutput scheidt bronfeiten, gecontroleerde berekeningsreferenties, interpretatie en onbekend. Numerieke/sourcevalidatie is geen semantische waarheidscontrole. ABSTAIN en menselijke beoordeling blijven noodzakelijk.
- Geen liveorderroute, withdrawal, leverage, automatische rechtenwijziging of automatische rule-promotie. Paperpreview is sessie-/versiegebonden, zestig seconden geldig en transactioneel/idempotent. Geld gebruikt Decimal.
- Documentinhoud en bestandsmetadata zijn lokaal met Fernet versleuteld. Sleutel staat buiten iCloud, apart van de database. Back-ups bundelen de vaultsleutel binnen een afzonderlijke versleutelde envelop. Compose-secrets zijn gewone hostbestanden, geen encrypted vault.
- Logs bevatten geen credentials. Browsertraces en echte imports kunnen persoonlijke data bevatten en zijn Git-ignored. API-audit is append-only via applicatieroutes; een hostbeheerder blijft vertrouwd.

Lokale HTTP-opstelling: geen LAN/TLS- of multi-user product. Geen onafhankelijke penetratietest/certificering. Er is geen externe back-up ingesteld. Zie BACKUP_RESTORE voor bescherming tegen hostverlies.
