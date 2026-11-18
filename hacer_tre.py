import hashlib, json, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from treutil import parse_stf
from trecrc import swgcrc


def build_stf(pairs):
    head = struct.pack("<IBII", 0xABCD, 1, len(pairs) + 1, len(pairs))
    vals, names = [], []
    for i, (k, v) in enumerate(pairs, 1):
        u = v.encode("utf-16-le")
        vals.append(struct.pack("<III", i, 0xFFFFFFFF, len(u) // 2) + u)
        kb = k.encode("latin-1")
        names.append(struct.pack("<II", i, len(kb)) + kb)
    return head + b"".join(vals) + b"".join(names)


def build_tre(files, out):
    items = sorted(files.items(), key=lambda kv: swgcrc(kv[0]))
    data, toc, names, md5s = bytearray(), bytearray(), bytearray(), bytearray()
    off = 36
    for name, blob in items:
        toc += struct.pack("<6I", swgcrc(name), len(blob), off + len(data), 0, 0, len(names))
        names += name.encode("latin-1") + b"\0"
        md5s += hashlib.md5(blob).digest()
        data += blob
    toc_off = 36 + len(data)
    head = struct.pack("<4s4s7I", b"EERT", b"5000", len(items), toc_off, 0, len(toc), 0, len(names), len(names))
    with open(out, "wb") as f:
        f.write(head + data + toc + names + md5s)


if __name__ == "__main__":
    orig, trad, out = sys.argv[1], sys.argv[2], sys.argv[3]
    files, total, hechas = {}, 0, 0
    for fn in sorted(os.listdir(trad)):
        if not fn.endswith(".json"):
            continue
        rel = fn[:-5].replace("__", "/")
        es = json.load(open(os.path.join(trad, fn), encoding="utf-8"))
        en = parse_stf(open(os.path.join(orig, "string/en", rel + ".stf"), "rb").read())
        pairs = []
        for k, v in en:
            total += 1
            if k in es:
                hechas += 1
            pairs.append((k, es.get(k, v)))
        files[f"string/en/{rel}.stf"] = build_stf(pairs)
    build_tre(files, out)
    print(f"{len(files)} ficheros, {hechas}/{total} cadenas traducidas -> {out}")
