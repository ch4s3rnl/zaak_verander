# zaak_verander
=
Versie 1 van het script kan worden gebruikt door beheerders van Zaaksysteem.nl

Voor het gebruik van dit script is weinig technische kennis nodig, 
wel is het belangrijk om te realiseren dat verkeerd gebruik grote gevolgen kan hebben.

Tijdens het maken van het script zijn de volgende uitgangspunten gebruikt:

- Aanpassingen in bulk worden alleen gedaan op collecties van zaken die aan zelfde criteria voldoen.
- Er is geen foutcorrectie.

####    Gebruik:

$python3 zaak_verander.py --zaken bestand_waarin_zaken_staan.txt

Het bestand waarin de zaken staan moet per regel een zaaknummer hebben en verder niets:

####    Bijvoorbeeld:

103356

321547

354987

#   De functies
Hieronder alle functies die ik in het script heb gezet en eventuele aandachtspunten.

###   Sessie informatie 

Om het script bruikbaar te maken voor meerdere Zaaksysteem-gebruikers zijn de gegevens voor het maken van de verbinding niet in het script opgeslagen.
Na het starten van het script zal gevraagd worden om een cURL te plakken. Deze is op te halen uit het development gedeelte van elke webbrowser.
De benodigde gegevens zullen door het script uit deze cURL worden gehaald en opgeslagen in een sessie-bestand. 
Als het sessie-bestand ouder is dan 1 uur zal een nieuwe sessie gevraagd worden.

Ik heb niet getest hoe lang een sessie actief blijft en hoe een sessie verbroken kan raken. 
Tijdens het uitvoeren van het script is het daarom belangrijk om de ingelogde sessie in de webbrowser open te houden.

Er is GEEN rekening gehouden met de mogelijke gevolgen als een sessie verloopt.
Op basis van de log zou dan achterhaald moeten worden welke aanpassingen mislukt zijn.

In een eventuele volgende versie is hier nog ruimte voor verbetering. Maar ik zie daar momenteel geen toegevoegde waarde voor.

###   Fase aanpassen

Deze functie is gemaakt voor correctie van zaken bij overgang naar een koppeling. 
Fases naar voren zetten werkt niet. Het enige doel - en dat doet het script nu - is het terug kunnen zetten naar fase 2.
Als om welke reden dan ook in bulk zaken naar een andere fase terug gezet moeten worden kan dat ook.

###   Heropenen 

Het is met het script mogelijk om zaken in bulk te heropenen.

###   Updaten

##LET OP: 
> Alleen bij het eerste zaaknummer uit het bronbestand wordt het zaaktype opgehaald!
> Deze wordt vervolgens toegepast op alle zaaknummers uit het bestand zonder verdere bevestiging te vragen!

Met de updaten functie wordt eerst het huidige zaaktype opgehaald. 
Deze wordt daarna nogmaals toegepast waardoor de laatste versie van het zaaktype actief wordt.
Ter verificatie toont het script eerst het huidige zaaktype, op die manier is vast te stellen dat je de juiste hebt.

###   Log-bestanden 

Na het aanpassen van de zaken zal een log-bestand worden gegenereerd waarin de uitgevoerde acties gelogd zijn.
Het formaat van het log-bestand is Excel vriendelijk met een tab-gescheiden indeling.

