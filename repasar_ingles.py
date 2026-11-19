"""Repasa las cadenas que quedaron idénticas al inglés (el modelo a veces devuelve la tanda sin traducir).
Uso: python3 -I repasar_ingles.py --host http://IP:11434 lista.json   (lista = {"fichero:clave": texto})"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import traducir
from traducir import ES, llamar, valido, cargar_json, guardar_json

traducir.SISTEMA += """- Si el texto es un nombre propio (personaje, nave, lugar, empresa), una ruta de fichero, un identificador interno o una lista de emoticonos, devuélvelo EXACTAMENTE igual. Todo lo demás (objetos genéricos, descripciones, instrucciones, títulos) tradúcelo siempre: nunca devuelvas en inglés una frase normal.
"""
SALTAR = re.compile(r"^(mood_types|socials|cbt_spam|emoticon_|chat_emoticon|chat_bubble|space/ship_names|npc_name|.*region_names|.*_lookat|building_detail|encoded_disk|loading/)")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--host", required=True); ap.add_argument("lista"); ap.add_argument("--tam", type=int, default=30)
    a = ap.parse_args()
    lista = json.load(open(a.lista)); porf = {}
    for fk, v in lista.items():
        f, k = fk.split(":", 1)
        if SALTAR.match(f) or ".iff" in v or "\\" in v or "filename_of_object" in v or k == "do_not_edit" or k.startswith("return_waypoint_name"):
            continue
        porf.setdefault(f, {})[k] = v
    hechas = iguales = malas = 0
    for f, d in porf.items():
        p = os.path.join(ES, f.replace("/", "__") + ".json"); es = cargar_json(p)
        items = list(d.items())
        for i in range(0, len(items), a.tam):
            lote = dict(items[i:i + a.tam])
            try:
                res = llamar(a.host, "gpt-oss:20b", lote)
            except Exception:
                res = {}
            for k, v in lote.items():
                r = res.get(k)
                if valido(v, r):
                    if r != v: es[k] = r; hechas += 1
                    else: iguales += 1
                else: malas += 1
            guardar_json(p, es)
        print(f"{f}: total {hechas} traducidas, {iguales} iguales, {malas} sin respuesta válida", flush=True)
    print(f"FIN {hechas} traducidas, {iguales} iguales, {malas} sin respuesta válida")

if __name__ == "__main__":
    main()
