import json, os, re, sys

TOK = re.compile(r"%[A-Z]{2}|\\#[0-9a-zA-Z]*|\\>[0-9]+|@[a-z_/0-9]+:[a-z_0-9]+")

en_all = json.load(open(sys.argv[1], encoding="utf-8"))
es_all = json.load(open(sys.argv[2], encoding="utf-8"))
outdir = sys.argv[3]
problemas = 0
for fichero, en in en_all.items():
    es = es_all.get(fichero, {})
    for k, v in en.items():
        if k not in es:
            print(f"FALTA {fichero}:{k}")
            problemas += 1
            continue
        if sorted(TOK.findall(v)) != sorted(TOK.findall(es[k])):
            print(f"TOKENS {fichero}:{k}  en={TOK.findall(v)} es={TOK.findall(es[k])}")
            problemas += 1
    for k in es:
        if k not in en:
            print(f"SOBRA {fichero}:{k}")
            problemas += 1
if problemas:
    print(f"{problemas} problemas: no se escribe nada")
    sys.exit(1)
for fichero, es in es_all.items():
    p = os.path.join(outdir, fichero.replace("/", "__") + ".json")
    previo = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    previo.update(es)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(previo, f, ensure_ascii=False, indent=0)
print(f"ok: {len(es_all)} ficheros, {sum(len(v) for v in es_all.values())} cadenas")
