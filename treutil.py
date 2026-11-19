import os, re, struct, sys, zlib


def read_tre(path):
    f = open(path, "rb")
    h = f.read(36)
    tok, ver, n, toc_off, toc_c, toc_sz, blk_c, blk_sz, blk_usz = struct.unpack("<4s4s7I", h)
    f.seek(toc_off)
    toc = f.read(toc_sz)
    if toc_c:
        toc = zlib.decompress(toc)
    names = f.read(blk_sz)
    if blk_c:
        names = zlib.decompress(names)
    out = {}
    for i in range(n):
        crc, length, off, comp, clen, noff = struct.unpack_from("<6I", toc, i * 24)
        name = names[noff:names.index(b"\0", noff)].decode("latin-1")
        out[name] = (path, length, off, comp, clen)
    return out


def read_entry(e):
    path, length, off, comp, clen = e
    with open(path, "rb") as f:
        f.seek(off)
        if comp:
            return zlib.decompress(f.read(clen))
        return f.read(length)


def search_order(cfgdir):
    pri = []
    for line in open(os.path.join(cfgdir, "swgemu_live.cfg"), encoding="latin-1"):
        m = re.match(r"\s*searchTree_\d+_(\d+)=(\S+)", line)
        if m:
            pri.append((int(m.group(1)), m.group(2)))
    pri.sort()
    return [n for _, n in pri]


def merged_index(cfgdir):
    idx = {}
    for tre in search_order(cfgdir):
        p = os.path.join(cfgdir, tre)
        if os.path.exists(p):
            idx.update(read_tre(p))
    for root, _, files in os.walk(cfgdir):
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, cfgdir)
            if "/" in rel:
                idx[rel] = (full, os.path.getsize(full), 0, 0, 0)
    return idx


def parse_stf(data):
    if len(data) < 13:
        return []
    magic, flag, nxt, count = struct.unpack_from("<IBII", data, 0)
    pos = 13
    vals = {}
    for _ in range(count):
        sid, crc, nchar = struct.unpack_from("<III", data, pos)
        pos += 12
        vals[sid] = data[pos:pos + nchar * 2].decode("utf-16-le", "replace")
        pos += nchar * 2
    out = []
    for _ in range(count):
        sid, ln = struct.unpack_from("<II", data, pos)
        pos += 8
        out.append((data[pos:pos + ln].decode("latin-1"), vals.get(sid, "")))
        pos += ln
    return out


if __name__ == "__main__":
    cmd, cfgdir = sys.argv[1], sys.argv[2]
    idx = merged_index(cfgdir)
    if cmd == "stats":
        stf = sorted(k for k in idx if k.startswith("string/en/") and k.endswith(".stf"))
        tot_e = tot_c = 0
        sizes = []
        for k in stf:
            ent = parse_stf(read_entry(idx[k]))
            c = sum(len(v) for _, v in ent)
            tot_e += len(ent)
            tot_c += c
            sizes.append((c, len(ent), k))
        print(f"ficheros stf: {len(stf)}  cadenas: {tot_e}  caracteres: {tot_c}")
        for c, e, k in sorted(sizes, reverse=True)[:int(sys.argv[3]) if len(sys.argv) > 3 else 25]:
            print(f"{c:>9} car {e:>6} cad  {k}")
    elif cmd == "dump":
        for k, v in parse_stf(read_entry(idx[sys.argv[3]])):
            print(f"{k}\t{v!r}")
    elif cmd == "extract":
        out = sys.argv[3]
        n = 0
        for k in sorted(idx):
            if k.startswith("string/en/") and k.endswith(".stf"):
                dest = os.path.join(out, k)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(read_entry(idx[k]))
                n += 1
        print(f"{n} ficheros extraidos en {out}")
    elif cmd == "find":
        pat = sys.argv[3]
        for k in sorted(idx):
            if re.search(pat, k):
                print(k, idx[k][1], os.path.basename(idx[k][0]))
