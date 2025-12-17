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
        BASE_URL = re.search(r"(https://[^/'\s]+)", curl).group(1)
        XSRF_TOKEN, SESSION_COOKIE = extract_from_curl(curl)
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

def log(zaak, actie, resultaat):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()}\t{zaak}\t{actie}\t{resultaat}\n")

# =========================
# Actiekeuze
# =========================
actie = ""
while actie not in ("f", "u", "h"):
    actie = input("(f)ase aanpassen, (u)pdate zaaktype, (h)eropenen: ").lower()

# =========================
# Zaken inlezen
# =========================
zaken = [z.strip() for z in Path(args.zaken).read_text().splitlines() if z.strip()]
eerste_zaak = zaken[0]

# =========================
# Alleen bij FASE: huidige fase ophalen & tonen
# =========================
def haal_fase_info(zaak):
    req = urllib.request.Request(
        f"{BASE_URL}/api/v0/case/{zaak}",
        headers={
            "Accept": "application/json",
            "X-XSRF-TOKEN": XSRF_TOKEN,
            "Cookie": f"zaaksysteem_session={SESSION_COOKIE}; XSRF-TOKEN={XSRF_TOKEN}"
        }
    )
    with urllib.request.urlopen(req) as r:
        values = json.loads(r.read())["result"][0]["values"]
        return {
            "progress": int(values.get("case.progress_status", 0)),
            "name": values.get("case.phase", "Onbekend")
        }

if actie == "f":
    info = haal_fase_info(eerste_zaak)
    print("\nHUIDIGE FASE (voorbeeldzaak):")
    print(f"  Fase: {info['name']}")
    print(f"  Voortgang: {info['progress']}%")

    while True:
        try:
            doel_fase = int(input("\nNaar welke fase aanpassen?: "))
            if doel_fase < 1:
                raise ValueError
            break
        except ValueError:
            print("Voer een geldig positief getal in.")

    fase_payload = doel_fase - 1

# =========================
# Verwerken
# =========================
for i, zaak in enumerate(zaken, 1):
    try:
        if actie == "f":
            payload = {
                "selected_case_ids": int(zaak),
                "no_redirect": 1,
                "selection": "one_case",
                "commit": 1,
                "milestone": fase_payload
            }
            url = f"{BASE_URL}/zaak/{zaak}/update/set_settings"
            actie_omschrijving = f"Fase aangepast naar {doel_fase}"

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
        urllib.request.urlopen(req)
        log(zaak, actie_omschrijving, "OK")

    except Exception as e:
        log(zaak, actie_omschrijving, f"FOUT: {e}")

    bar = int(i / len(zaken) * 40)
    print(f"[{'#'*bar}{'-'*(40-bar)}] {i}/{len(zaken)}", end="\r")
    time.sleep(0.05)

print("\nKlaar. Logbestand:", log_file)
