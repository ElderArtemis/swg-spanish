"""Corrige de forma determinista términos que el modelo no respetó del glosario."""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from traducir import ES, ORIG, guardar_json, valido
from treutil import parse_stf

def cap(src, dst):
    return dst[0].upper() + dst[1:] if src[0].isupper() else dst

REGLAS = [
    (r"\b([Cc])omputadora ([Tt])áctica\b", lambda m: cap(m.group(0), "ordenador táctico")),
    (r"\b([Ll])as ([Cc])omputadoras\b", lambda m: cap(m.group(0), "los ordenadores")),
    (r"\b([Ll])a ([Cc])omputadora\b", lambda m: cap(m.group(0), "el ordenador")),
    (r"\b([Uu])na ([Cc])omputadora\b", lambda m: cap(m.group(0), "un ordenador")),
    (r"\b([Cc])omputadoras\b", lambda m: cap(m.group(0), "ordenadores")),
    (r"\b([Cc])omputadora\b", lambda m: cap(m.group(0), "ordenador")),
    (r"\bordenador (robad|destruid|dañad|nuev|vieja|antigu|encriptad|cifrad)a\b", lambda m: "ordenador " + m.group(1).replace("viej", "viej") + "o"),
    (r"\bOrdenador de Vuelo\b", lambda m: "Ordenador de vuelo"),
    (r"\bDroids\b", lambda m: "droides"), (r"\bdroids\b", lambda m: "droides"),
    (r"\bDroid\b", lambda m: "Droide"), (r"\bdroid\b", lambda m: "droide"),
    (r"\bBlasters\b", lambda m: "Blásteres"), (r"\bblasters\b", lambda m: "blásteres"),
    (r"\bBlaster\b", lambda m: "Bláster"), (r"\bblaster\b", lambda m: "bláster"),
    (r"\bWookie(s?)\b", lambda m: "Wookiee" + m.group(1)),
]
COMMANDO = [(r"\bcomandantes\b", "comandos"), (r"\bComandantes\b", "Comandos"),
            (r"\bcomandante\b", "comando"), (r"\bComandante\b", "Comando")]

cont = collections.Counter(); malos = 0
for fn in sorted(os.listdir(ES)):
    rel = fn[:-5].replace("__", "/"); p = os.path.join(ES, fn); es = json.load(open(p)); o = None; cambio = False
    for k, v in es.items():
        n = v
        for pat, f in REGLAS:
            n2 = re.sub(pat, f, n)
            if n2 != n: cont[pat[:30]] += 1; n = n2
        if re.search(r"[Cc]omandante", n):
            if o is None: o = dict(parse_stf(open(os.path.join(ORIG, rel + ".stf"), "rb").read()))
            if re.search(r"\bcommandos?\b", o[k], re.I) and not re.search(r"\bcommanders?\b", o[k], re.I):
                for a, b in COMMANDO: n = re.sub(a, b, n)
                cont["commando"] += 1
        if n != v:
            if o is None: o = dict(parse_stf(open(os.path.join(ORIG, rel + ".stf"), "rb").read()))
            if valido(o[k], n): es[k] = n; cambio = True
            else: malos += 1
    if cambio: guardar_json(p, es)
for k, n in cont.most_common(): print(n, k)
print("rechazados por validación:", malos)
