# Lokale grens en veiligheidscontroles

- Auth met zelfgekozen wachtwoord, salted PBKDF2, willekeurige server-side sessie van acht uur, HttpOnly/SameSite=Strict-cookie. Geen standaard-PIN. Foutieve login begrensd tot vijf per minuut per proces/clientadres.
- Alleen localhost/127.0.0.1 en de gekozen poort toegestaan als Host en Origin. CSRF verplicht voor mutaties; controle vóór requestbody-validatie.
- UI/web en API draaien non-root met read-only filesystem, tmpfs, beperkte resources, capability drop en no-new-privileges. PostgreSQL gebruikt het officiële image en een privé datavolume.
- Alleen web heeft een gepubliceerde loopbackpoort. API/database zijn op interne Docker-netwerken. Geen Docker-socket, home-directorymount, betaalde provider of telemetry.
- Geen liveorderroute. AI kan geen order indienen, geld overboeken, rulesets wijzigen of shell uitvoeren. LOCAL_ONLY is actief. De runtime verstuurt geen financiële appgegevens naar externe modellen.
- Previews horen bij sessie, exacte intent, bron- en rekeningversie; vervallen na 60 seconden. Bevestiging is transactioneel en idempotent. Geldberekeningen uitsluitend Decimal, bedragen als strings.
- Paper heeft een aparte rekening en kwaliteitslabels. Werkelijk vermogen blijft onbekend. Geen fiscale uitvoer zonder goedgekeurde regels, geen geclaimde pensioen-/BV-ondersteuning.
- Geheimen blijven lokaal buiten iCloud en Git. Docker Compose-secrets zijn geen encrypted vault. Versleutelde back-ups hebben een afzonderlijke lokale sleutel; de hostbeheerder blijft een vertrouwde partij.

De browser gebruikt lokaal HTTP. Extern/LAN delen is niet ondersteund; voeg pas na een afzonderlijk ontwerp TLS en toegangsbeleid toe. Dit bewijs is functionele beveiligingstest, geen volledige onafhankelijke penetratietest.
