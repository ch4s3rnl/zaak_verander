#       zaak_verander

Dit script is bedoeld om geautomatiseerde taken te verrichten op meer dan 50 items.
In de webinterface is dit niet mogelijk, maar wel kan een export worden gemaakt van meerdere items.

Voor het gebruik van dit script is weinig technische kennis nodig, 
wel is het belangrijk om te realiseren dat verkeerd gebruik grote gevolgen kan hebben.

Tijdens het maken van het script zijn de volgende uitgangspunten gebruikt:

- Aanpassingen in bulk worden alleen gedaan op collecties van zaken die aan zelfde criteria voldoen.
- Er is geen foutcorrectie.

####    Voorbereiding voor gebruik:

#####   1. Zaken klaarzetten
Maak een export van de zaken waarop je een handeling wil verrichten. Deze kan je het beste als Excel-bestand maken.
Kopieer de kolom met het zaaknummer naar een txt-bestand en sla deze op.

#####   2. Sessie-gegevens ophalen
Ga naar jouw Zaaksysteem pagina (prod, accept, ontwikkel of test) en open de ontwikkel-tab van jouw browser. Ga op de ontwikkel-tab naar het tabblad **netwerk** en kopieer van een willekeurige actie de cURL.

Deze gegevens moeten na het starten van het script geplakt worden in de terminal.

####    Gebruik:

Voer het volgende commando uit in een terminal. Zorg ervoor dat het bestand met de zaken in dezelfde map staat als het script of geef het volledige pad op.

```python3 zaak_verander.py --zaken bestand_waarin_zaken_staan.txt```

Het bestand waarin de zaken staan moet per regel een zaaknummer hebben en verder niets:

####    Bijvoorbeeld:
```103356
321547
354987```
#   De functies
Hieronder alle functies die ik in het script heb gezet en eventuele aandachtspunten.

###     Sessie informatie 

Om het script bruikbaar te maken voor meerdere Zaaksysteem-gebruikers zijn de gegevens voor het maken van de verbinding niet in het script opgeslagen.
Na het starten van het script zal gevraagd worden om een cURL te plakken. Deze is op te halen uit het development gedeelte van elke webbrowser.
De benodigde gegevens zullen door het script uit deze cURL worden gehaald en opgeslagen in een sessie-bestand. 
Als het sessie-bestand ouder is dan 1 uur zal een nieuwe sessie gevraagd worden.

Ik heb niet getest hoe lang een sessie actief blijft en hoe een sessie verbroken kan raken. 
Tijdens het uitvoeren van het script is het daarom belangrijk om de ingelogde sessie in de webbrowser open te houden.

Er is **GEEN** rekening gehouden met de mogelijke gevolgen als een sessie verloopt.
Op basis van de log zou dan achterhaald moeten worden welke aanpassingen mislukt zijn.

In een eventuele volgende versie is hier nog ruimte voor verbetering. Maar ik zie daar momenteel geen toegevoegde waarde voor.

###     Fase aanpassen

Deze functie is gemaakt voor correctie van zaken bij overgang naar een koppeling. 
Fases naar voren zetten werkt niet. Het enige doel - en dat doet het script nu - is het terug kunnen zetten naar fase 2.
Als om welke reden dan ook in bulk zaken naar een andere fase terug gezet moeten worden kan dat ook.

###     Heropenen 

Het is met het script mogelijk om zaken in bulk te heropenen.

###     Updaten

##   LET OP: 
> Alleen bij het eerste zaaknummer uit het bronbestand wordt het zaaktype opgehaald!
> Deze wordt vervolgens toegepast op alle zaaknummers uit het bestand zonder verdere bevestiging te vragen!

Met de updaten functie wordt eerst het huidige zaaktype opgehaald. 
Deze wordt daarna nogmaals toegepast waardoor de laatste versie van het zaaktype actief wordt.
Ter verificatie toont het script eerst het huidige zaaktype, op die manier is vast te stellen dat je de juiste hebt.

###     Gegevens ophalen
Met deze functie kan gecontroleerd worden of een kenmerk in een zaak aanwezig is. Ook kan er gecontroleerd worden of een specifieke waarde in het kenmerk aanwezig is.

De toepassing waarvoor ik deze functie in het script heb gezet is om te kunnen controleren of er in het kenmerk `ztc_zkn_status` gegevens stonden. Als daarin niets staat, en de waarde dus `null` is dat de zaak nog nooit via een koppeling een update heeft gehad. Na migratie betekende dit dat vanuit de vakapplicatie een update naar de zaak moest worden gestuurd.

De optie om specifieke waardes op te zoeken hebben wij nog niet nodig gehad en verdere aanpassing hiervan zal misschien nog nodig zijn. Mijn vermoeden is dat dit voor MDTO nog wel eens handig kan worden.

####    Log-bestanden 

Na het aanpassen van de zaken zal een log-bestand worden gegenereerd waarin de uitgevoerde acties gelogd zijn.
Het formaat van het log-bestand is Excel vriendelijk met een tab-gescheiden indeling.

