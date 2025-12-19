#!/usr/bin/env python3
import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import urllib.request
import re

# =========================
# Sessie management
# =========================
def zoek_recente_sessie(max_leeftijd_uren=1):
    patroon = "sessie-*.json"
    for sessie_file in sorted(Path(".").glob(patroon), reverse=True):
        try:
            parts = sessie_file.stem.split("-")
            if len(parts) >= 4:
                datum = f"{parts[2]}-{parts[3]}"
                sessie_tijd = datetime.strptime(datum, "%Y%m%d-%H%M%S")
                if datetime.now() - sessie_tijd < timedelta(hours=max_leeftijd_uren):
                    return json.loads(sessie_file.read_text()), int(
                        (datetime.now() - sessie_tijd).total_seconds() / 60
                    )
        except Exception:
            continue
    return None, None


def sla_sessie_op(base_url, xsrf, session):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    env = "acceptatie" if "accept" in base_url else "productie"
    f = Path(f"sessie-{env}-{ts}.json")
    f.write_text(json.dumps({
        "base_url": base_url,
        "xsrf_token": xsrf,
        "session_cookie": session
    }, indent=2))
    print(f"✓ Sessie opgeslagen in {f}\n")


def extract_from_curl(curl):
    xsrf = ""
    session = ""
    if m := re.search(r"X-XSRF-TOKEN:\s*([^'\"]+)", curl):
        xsrf = m.group(1)
    if m := re.search(r"Cookie:\s*([^'\"]+)", curl):
        c = m.group(1)
        if s := re.search(r"zaaksysteem_session=([^;]+)", c):
            session = s.group(1)
        if not xsrf and (x := re.search(r"XSRF-TOKEN=([^;]+)", c)):
            xsrf = x.group(1)
    return xsrf, session


# =========================
# Argumenten
# =========================
parser = argparse.ArgumentParser()
parser.add_argument("--zaken", required=True)
args = parser.parse_args()

# =========================
# Sessie kiezen
# =========================
sessie, minuten = zoek_recente_sessie()

if sessie:
    print(f"✓ Recente sessie gevonden ({minuten} min oud)")
    print(f"  URL: {sessie['base_url']}")
    if input("\nBestaande sessie gebruiken? (j/n): ").lower() in ("j", "ja"):
        BASE_URL = sessie["base_url"]
        XSRF_TOKEN = sessie["xsrf_token"]
        SESSION_COOKIE = sessie["session_cookie"]
        print("✓ Sessie geladen\n")
    else:
        sessie = None

if not sessie:
    print("\nPlak cURL (lege regel stopt):")
    lines = []
    while True:
        l = input()
        if not l.strip():
            break
        lines.append(l)
    curl = " ".join(lines)

    if curl:
        if m := re.search(r"(https://[^/'\s]+)", curl):
            BASE_URL = m.group(1)
            print(f"✓ URL gedetecteerd: {BASE_URL}")
        else:
            print("✗ Kon URL niet vinden")
            BASE_URL = input("BASE_URL: ").strip()
        
        XSRF_TOKEN, SESSION_COOKIE = extract_from_curl(curl)
        if XSRF_TOKEN and SESSION_COOKIE:
            print("✓ Token en cookie geëxtraheerd")
        else:
            print("✗ Kon token/cookie niet vinden")
            XSRF_TOKEN = input("X-XSRF-TOKEN: ").strip()
            SESSION_COOKIE = input("SESSION_COOKIE: ").strip()
    else:
        BASE_URL = input("BASE_URL: ").strip()
        XSRF_TOKEN = input("X-XSRF-TOKEN: ").strip()
        SESSION_COOKIE = input("SESSION_COOKIE: ").strip()

    sla_sessie_op(BASE_URL, XSRF_TOKEN, SESSION_COOKIE)

# =========================
# Logging
# =========================
log_file = Path(f"zaak-update-{datetime.now():%Y%m%d-%H%M%S}.log")
log_file.write_text("Datum\tZaak\tActie\tResultaat\n")

def log_actie(zaak, actie, resultaat):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}\t{zaak}\t{actie}\t{resultaat}\n")

# =========================
# Actiekeuze
# =========================
actie = ""
while actie not in ("f", "u", "h", "c"):
    actie = input("Wat wil je doen? (f)ase, (u)pdate zaaktype, (h)eropenen, (c)ontroleer kenmerk: ").lower()

# =========================
# Zaken inlezen
# =========================
zaken = [z.strip() for z in Path(args.zaken).read_text().splitlines() if z.strip()]
eerste_zaak = zaken[0]

# =========================
# Hulpfuncties voor zaakinfo ophalen
# =========================
def haal_zaak_info(zaak):
    req = urllib.request.Request(
        f"{BASE_URL}/api/v0/case/{zaak}",
        headers={
            "Accept": "application/json",
            "X-XSRF-TOKEN": XSRF_TOKEN,
            "Cookie": f"zaaksysteem_session={SESSION_COOKIE}; XSRF-TOKEN={XSRF_TOKEN}"
        }
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["result"][0]["values"]


def controleer_kenmerk(zaak, kenmerk, verwachte_waarde=None, check_niet_null=False):
    """
    Controleert of een zaak een bepaald kenmerk heeft (en optioneel een specifieke waarde).
    
    Parameters:
    - zaak: zaaknummer
    - kenmerk: naam van het kenmerk (bijv. "attribute.magicstring" of "case.status")
    - verwachte_waarde: optioneel - de waarde die het kenmerk moet hebben
    - check_niet_null: als True, check alleen of kenmerk niet null is
    
    Returns:
    - (True, waarde) als kenmerk bestaat en aan criteria voldoet
    - (False, None) of (False, waarde) als kenmerk niet bestaat of niet voldoet
    """
    try:
        values = haal_zaak_info(zaak)
        
        # Check of kenmerk bestaat in de response
        if kenmerk not in values:
            return False, None
        
        huidige_waarde = values[kenmerk]
        
        # Check of kenmerk null is
        if huidige_waarde is None:
            return False, None
        
        # Als alleen check of kenmerk niet null is
        if check_niet_null:
            return True, huidige_waarde
        
        # Als geen specifieke waarde verwacht, return True met de huidige waarde
        if verwachte_waarde is None:
            return True, huidige_waarde
        
        # Check of waarde overeenkomt
        if str(huidige_waarde) == str(verwachte_waarde):
            return True, huidige_waarde
        else:
            return False, huidige_waarde
            
    except Exception as e:
        print(f"✗ Fout bij ophalen kenmerk voor zaak {zaak}: {e}")
        return False, None

# =========================
# Actie-specifieke input
# =========================
if actie == "f":
    # Huidige fase ophalen
    values = haal_zaak_info(eerste_zaak)
    huidige_fase = values.get("case.phase", "Onbekend")
    voortgang = int(values.get("case.progress_status", 0))
    
    print(f"\nHUIDIGE FASE (zaak {eerste_zaak}):")
    print(f"  Fase: {huidige_fase}")
    print(f"  Voortgang: {voortgang}%")
    
    while True:
        try:
            doel_fase = int(input("\nNaar welke fase zetten? (bijv. 2, 3, 4, ...): "))
            if doel_fase < 1:
                print("✗ Fase moet minimaal 1 zijn")
                continue
            break
        except ValueError:
            print("✗ Ongeldig fase nummer")
    
    fase_payload = doel_fase - 1
    print(f"✓ Fase {doel_fase} geselecteerd (API waarde: {fase_payload})")

elif actie == "u":
    # Zaaktype ophalen en bevestigen
    values = haal_zaak_info(eerste_zaak)
    casetype_id = values.get("case.casetype.id")
    casetype_name = values.get("case.casetype.name")
    
    if casetype_id and casetype_name:
        print(f"\nGevonden zaaktype voor zaak {eerste_zaak}:")
        print(f"  ID: {casetype_id}")
        print(f"  Naam: {casetype_name}")
        
        bevestiging = input("\nIs dit het juiste zaaktype? (j/n): ").lower()
        if bevestiging in ["j", "ja"]:
            zaaktype_id = casetype_id
            print(f"✓ Zaaktype ID {zaaktype_id} wordt gebruikt")
        else:
            zaaktype_id = input("Geef het gewenste zaaktype ID op: ").strip()
    else:
        print("✗ Kan zaaktype niet ophalen")
        zaaktype_id = input("Geef het zaaktype ID op: ").strip()

elif actie == "c":
    # Controleer kenmerk
    print("\nCONTROLEER KENMERK")
    print("Voer de magicstring in van het kenmerk dat je wilt controleren.")
    print("Een magicstring is de technische naam van een kenmerk in het zaaktype,")
    print("bijvoorbeeld: 'ztc_contactpersoon', 'ztc_zkn_status', 'ztc_zkn_resultaat', etc.")
    
    magicstring = input("\nMagicstring van het kenmerk: ").strip()
    kenmerk_naam = f"attribute.{magicstring}"
    
    print("\nWil je controleren op:")
    print("  1. Of het kenmerk een waarde heeft (niet leeg/null)")
    print("  2. Of het kenmerk een specifieke waarde heeft")
    
    keuze = ""
    while keuze not in ("1", "2"):
        keuze = input("Keuze (1 of 2): ").strip()
    
    if keuze == "1":
        verwachte_waarde = None
        check_niet_null = True
        controle_beschrijving = f"Kenmerk '{magicstring}' heeft waarde"
    else:
        verwachte_waarde = input("Welke waarde verwacht je?: ").strip()
        check_niet_null = False
        controle_beschrijving = f"Kenmerk '{magicstring}' = '{verwachte_waarde}'"
    
    print(f"\n✓ Controle: {controle_beschrijving}")

# Voor heropenen is geen extra input nodig

# =========================
# Verwerken
# =========================
print(f"\nStart verwerking van {len(zaken)} zaken...")

for i, zaak in enumerate(zaken, 1):
    try:
        if actie == "c":
            # Controleer kenmerk
            if keuze == "1":
                voldoet, waarde = controleer_kenmerk(zaak, kenmerk_naam, check_niet_null=True)
            else:
                voldoet, waarde = controleer_kenmerk(zaak, kenmerk_naam, verwachte_waarde)
            
            if voldoet:
                log_actie(zaak, controle_beschrijving, f"✓ Waarde: {waarde}")
            else:
                if waarde is None:
                    log_actie(zaak, controle_beschrijving, "✗ Leeg/Null")
                else:
                    log_actie(zaak, controle_beschrijving, f"✗ Waarde: {waarde}")
            
            # Voor controle doen we geen POST, alleen loggen
            continue
        
        if actie == "f":
            payload = {
                "selected_case_ids": int(zaak),
                "no_redirect": 1,
                "selection": "one_case",
                "commit": 1,
                "milestone": fase_payload
            }
            url = f"{BASE_URL}/zaak/{zaak}/update/set_settings"
            actie_omschrijving = f"Fase aangepast naar fase {doel_fase}"

        elif actie == "u":
            payload = {
                "selected_case_ids": int(zaak),
                "no_redirect": 1,
                "selection": "one_case",
                "commit": 1,
                "zaaktype_id": int(zaaktype_id)
            }
            url = f"{BASE_URL}/zaak/{zaak}/update/set_settings"
            actie_omschrijving = f"Zaaktype geupdated naar {zaaktype_id}"

        elif actie == "h":
            payload = {"status": "open"}
            url = f"{BASE_URL}/api/v0/case/{zaak}/update"
            actie_omschrijving = "Zaak heropend"

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-XSRF-TOKEN": XSRF_TOKEN,
                "Cookie": f"zaaksysteem_session={SESSION_COOKIE}; XSRF-TOKEN={XSRF_TOKEN}"
            }
        )
        
        with urllib.request.urlopen(req) as response:
            resp_text = response.read().decode()
            try:
                resp_json = json.loads(resp_text)
                messages = resp_json.get("json", {}).get("messages", [])
                if messages:
                    result_msg = messages[0].get("message", "OK")
                else:
                    result_msg = "OK"
            except:
                result_msg = "OK"
            
            log_actie(zaak, actie_omschrijving, result_msg)

    except Exception as e:
        if actie == "c":
            log_actie(zaak, controle_beschrijving, f"FOUT: {e}")
        else:
            log_actie(zaak, actie_omschrijving, f"FOUT: {e}")

    # Voortgangsbalk
    bar = int(i / len(zaken) * 40)
    print(f"[{'#'*bar}{'-'*(40-bar)}] {i}/{len(zaken)}", end="\r")
    time.sleep(0.05)

print(f"\n\nKlaar! Logbestand: {log_file}")