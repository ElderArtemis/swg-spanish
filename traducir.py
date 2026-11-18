import argparse, json, os, re, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from treutil import parse_stf

BASE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(BASE, "orig", "string", "en")
ES = os.path.join(BASE, "es")
TOK = re.compile(r"%[A-Z]{2}|\\#[0-9a-zA-Z]*|\\>[0-9]+|\\@[0-9]+|@[a-z_/0-9]+:[a-z_0-9]+")

SISTEMA = """Eres un traductor profesional de videojuegos. Traduces al español de España los textos del MMORPG Star Wars Galaxies (2003).
Reglas obligatorias:
- Devuelve SOLO un objeto JSON con exactamente las mismas claves que recibes y el texto traducido como valor.
- Conserva EXACTAMENTE y sin traducir estas marcas: %TU %TT %TO %DI %DF y cualquier %XX, \\#codigo, \\#. , \\>NN, \\@NN y referencias tipo @fichero:clave. También los saltos de línea (\\n) en el mismo número y posición aproximada.
- No traduzcas nombres propios de personajes, planetas, ciudades, especies ni marcas del universo Star Wars (Tatooine, Mos Eisley, Coronet, Jabba, Wookiee, Twi'lek, Bothan, Rodian, Zabrak, Ithorian, Sullustan, Trandoshan, Mon Calamari, Jedi, Sith, Teras Kasi, Hutt, Ewok, AT-ST...).
- Tono: natural y conciso, como un juego comercial traducido en España. Tutea al jugador. Sin explicaciones ni notas.
- Glosario fijo: Force=la Fuerza; Force Sensitive=sensible a la Fuerza; lightsaber=sable de luz; blaster=bláster; credits=créditos; waypoint=punto de ruta; datapad=datapad; draft schematic=esquema de diseño; manufacturing schematic=esquema de fabricación; crafting=fabricación; survey=prospección; harvester=recolector; hopper=tolva; bounty hunter=cazarrecompensas; Brawler=Luchador; Marksman=Tirador; Entertainer=Animador; Scout=Explorador; Medic=Médico; Artisan=Artesano; Novice=novato; Master=maestro; Imperial=imperial; Rebel=rebelde; stormtrooper=soldado de asalto; droid=droide; speeder=deslizador; vibroblade=vibrocuchilla; buff=mejora; mission terminal=terminal de misiones; cantina=cantina; health/action/mind=Salud/Acción/Mente; wounds=heridas; battle fatigue=fatiga de combate; NPC=PNJ.
- Profesiones (siempre así, también en plural y en minúscula dentro de frase): Pistoleer=Pistolero; Rifleman=Fusilero; Carbineer=Carabinero; Commando=Comando (NUNCA «comandante»); Smuggler=Contrabandista; Fencer=Esgrimista; Swordsman=Espadachín; Pikeman=Piquero; Teras Kasi Artist=Artista de Teras Kasi; Combat Medic=Médico de combate; Doctor=Doctor; Architect=Arquitecto; Armorsmith=Armero; Weaponsmith=Fabricante de armas; Tailor=Sastre; Chef=Chef; Merchant=Mercader; Droid Engineer=Ingeniero de droides; Bio-Engineer=Bioingeniero; Creature Handler=Domador de criaturas; Ranger=Guardabosques; Image Designer=Diseñador de imagen; Dancer=Bailarín; Musician=Músico; Politician=Político; Squad Leader=Jefe de escuadra; Shipwright=Constructor de naves; Padawan=Padawan; Jedi Knight=Caballero Jedi; Apprentice=Aprendiz; commoner=ciudadano.
- Usa siempre los signos de apertura ¡ y ¿ cuando haya ! o ?.
"""


def cargar_json(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}


def guardar_json(p, d):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=0)
    os.replace(tmp, p)


def prioridad(rel):
    orden = [("skl_", 0), ("cmd_", 1), ("att", 1), ("stat_", 1), ("obj_attr", 1), ("jedi", 1), ("force", 1),
             ("item", 2), ("_n", 3), ("kb/", 4), ("loc", 5), ("mob/", 5), ("conversation/", 7),
             ("mission/", 8), ("cbt_spam", 9)]
    for pat, p in orden:
        if pat in rel:
            return p
    return 6


def llamar(host, modelo, lote, timeout=600):
    cuerpo = {
        "model": modelo, "stream": False, "format": "json", "keep_alive": "30m",
        "think": "low" if "gpt-oss" in modelo else False,
        "options": {"temperature": 0.2, "num_ctx": 8192},
        "messages": [{"role": "system", "content": SISTEMA},
                     {"role": "user", "content": json.dumps(lote, ensure_ascii=False)}],
    }
    req = urllib.request.Request(host.rstrip("/") + "/api/chat", data=json.dumps(cuerpo).encode(),
                                 headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    return json.loads(r["message"]["content"])


def valido(en, es):
    if not isinstance(es, str) or not es.strip() and en.strip():
        return False
    if sorted(TOK.findall(en)) != sorted(TOK.findall(es)):
        return False
    if abs(en.count("\n") - es.count("\n")) > 1:
        return False
    return len(es) < len(en) * 3 + 40


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--modelo", default="gpt-oss:20b")
    ap.add_argument("--max-cadenas", type=int, default=30)
    ap.add_argument("--max-car", type=int, default=2500)
    ap.add_argument("--solo", default="")
    a = ap.parse_args()

    ficheros = []
    for root, _, files in os.walk(ORIG):
        for fn in files:
            if fn.endswith(".stf"):
                rel = os.path.relpath(os.path.join(root, fn), ORIG)[:-4]
                if a.solo and not re.search(a.solo, rel):
                    continue
                ficheros.append(rel)
    ficheros.sort(key=lambda r: (prioridad(r), r))
    log = open(os.path.join(BASE, "traducir.log"), "a", encoding="utf-8")
    inicio, hechas, fallos = time.time(), 0, 0
    for rel in ficheros:
        en = dict(parse_stf(open(os.path.join(ORIG, rel + ".stf"), "rb").read()))
        pes = os.path.join(ES, rel.replace("/", "__") + ".json")
        es = cargar_json(pes)
        pend = []
        for k, v in en.items():
            if k in es:
                continue
            if not re.search(r"[A-Za-z]{2}", TOK.sub("", v)):
                es[k] = v
                continue
            pend.append((k, v))
        if not pend:
            guardar_json(pes, es) if es else None
            continue
        i = 0
        while i < len(pend):
            lote, car = {}, 0
            while i < len(pend) and len(lote) < a.max_cadenas and (car + len(pend[i][1]) < a.max_car or not lote):
                lote[pend[i][0]] = pend[i][1]
                car += len(pend[i][1])
                i += 1
            for intento in range(3):
                try:
                    res = llamar(a.host, a.modelo, lote)
                    break
                except Exception as e:
                    log.write(f"{time.strftime('%H:%M:%S')} error {rel}: {e}\n"); log.flush()
                    res = {}
                    time.sleep(10 * (intento + 1))
            malos = {}
            for k, v in lote.items():
                if valido(v, res.get(k)):
                    es[k] = res[k]
                    hechas += 1
                else:
                    malos[k] = v
            for k, v in malos.items():
                try:
                    r1 = llamar(a.host, a.modelo, {k: v}).get(k)
                except Exception:
                    r1 = None
                if valido(v, r1):
                    es[k] = r1
                    hechas += 1
                else:
                    fallos += 1
                    log.write(f"FALLO {rel}:{k} {v[:80]!r} -> {str(r1)[:80]!r}\n")
            guardar_json(pes, es)
            ritmo = hechas / max(time.time() - inicio, 1) * 3600
            log.write(f"{time.strftime('%H:%M:%S')} {rel} {i}/{len(pend)} | total {hechas} ok, {fallos} fallos, {ritmo:.0f}/h\n")
            log.flush()
    log.write(f"FIN {hechas} ok, {fallos} fallos\n")


if __name__ == "__main__":
    main()
