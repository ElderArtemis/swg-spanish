"""Retraduce las cadenas que fallaron en traducir.py (líneas FALLO del log).

Los textos con varias líneas se traducen línea a línea y se vuelven a montar con los saltos
originales: así el modelo no puede comerse ni añadir líneas (mensajes de combate con «~»,
descripciones largas). Lo que siga sin pasar la validación se lista para hacerlo a mano.
Uso: python3 -I rematar.py --host http://IP:11434 [--diag]
"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from traducir import BASE, ORIG, ES, TOK, llamar, valido, cargar_json, guardar_json
from treutil import parse_stf


def fallidas():
    vistas = {}
    for linea in open(os.path.join(BASE, "traducir.log"), encoding="utf-8"):
        if linea.startswith("FALLO "):
            rel, k = linea.split()[1].split(":", 1)
            vistas[(rel, k)] = None
    return list(vistas)


def traducible(t):
    return bool(re.search(r"[A-Za-z]{2}", TOK.sub("", t)))


def traducir_lineas(host, modelo, texto):
    lineas = texto.split("\n")
    idx = [i for i, l in enumerate(lineas) if traducible(l)]
    pend = {str(i): lineas[i] for i in idx}
    for _ in range(3):
        if not pend:
            break
        res, lote, car = {}, {}, 0
        for k in list(pend) + [None]:
            if lote and (k is None or len(lote) >= 25 or car + len(pend[k]) > 2500):
                try:
                    res.update(llamar(host, modelo, lote))
                except Exception:
                    pass
                lote, car = {}, 0
            if k is not None:
                lote[k] = pend[k]
                car += len(pend[k])
        for k in list(pend):
            r = res.get(k)
            if isinstance(r, str) and "\n" not in r.strip() and valido(pend[k], r):
                lineas[int(k)] = r.strip("\n")
                del pend[k]
        if pend and len(pend) > 1:
            for k in list(pend):
                try:
                    r = llamar(host, modelo, {k: pend[k]}).get(k)
                except Exception:
                    r = None
                if isinstance(r, str) and "\n" not in r.strip() and valido(pend[k], r):
                    lineas[int(k)] = r.strip("\n")
                    del pend[k]
    return ("\n".join(lineas), []) if not pend else (None, [lineas[int(k)] for k in pend])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--modelo", default="gpt-oss:20b")
    ap.add_argument("--diag", action="store_true")
    a = ap.parse_args()
    lista = fallidas()
    ok, quedan = 0, []
    cache = {}
    for rel, k in lista:
        if rel not in cache:
            cache[rel] = dict(parse_stf(open(os.path.join(ORIG, rel + ".stf"), "rb").read()))
        en = cache[rel][k]
        pes = os.path.join(ES, rel.replace("/", "__") + ".json")
        es = cargar_json(pes)
        if k in es:
            continue
        if a.diag:
            print(f"{rel}:{k} lineas={en.count(chr(10))+1} car={len(en)} tokens={TOK.findall(en)[:6]}")
            continue
        if "\n" in en:
            t, malas = traducir_lineas(a.host, a.modelo, en)
        else:
            t, malas = None, [en]
            for _ in range(3):
                try:
                    r = llamar(a.host, a.modelo, {k: en}).get(k)
                except Exception:
                    r = None
                if valido(en, r):
                    t, malas = r, []
                    break
        if t is not None and valido(en, t):
            es[k] = t
            guardar_json(pes, es)
            ok += 1
            print(f"OK    {rel}:{k}")
        else:
            quedan.append((rel, k))
            print(f"QUEDA {rel}:{k} -> {[m[:70] for m in malas][:3]}")
        sys.stdout.flush()
    print(f"\nTotal {len(lista)}: {ok} traducidas, {len(quedan)} quedan")


if __name__ == "__main__":
    main()
