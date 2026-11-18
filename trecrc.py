import struct, sys, zlib

TABLE = []
for i in range(256):
    c = i << 24
    for _ in range(8):
        c = ((c << 1) ^ 0x04C11DB7) if c & 0x80000000 else (c << 1)
        c &= 0xFFFFFFFF
    TABLE.append(c)


def swgcrc(name):
    c = 0xFFFFFFFF
    for b in name.lower().encode("latin-1"):
        c = ((c << 8) & 0xFFFFFFFF) ^ TABLE[((c >> 24) ^ b) & 0xFF]
    return c ^ 0xFFFFFFFF


if __name__ == "__main__":
    f = open(sys.argv[1], "rb")
    tok, ver, n, toc_off, toc_c, toc_sz, blk_c, blk_sz, blk_usz = struct.unpack("<4s4s7I", f.read(36))
    print(tok, ver, n, toc_off, toc_c, toc_sz, blk_c, blk_sz, blk_usz)
    f.seek(toc_off)
    toc = f.read(toc_sz)
    toc = zlib.decompress(toc) if toc_c else toc
    names = f.read(blk_sz)
    names = zlib.decompress(names) if blk_c else names
    rest = f.read()
    print("bytes tras nombres:", len(rest), "=", len(rest) / max(n, 1), "por fichero")
    ok = bad = 0
    prev = -1
    sorted_ok = True
    for i in range(n):
        crc, length, off, comp, clen, noff = struct.unpack_from("<6I", toc, i * 24)
        nm = names[noff:names.index(b"\0", noff)].decode("latin-1")
        if crc < prev:
            sorted_ok = False
        prev = crc
        if swgcrc(nm) == crc:
            ok += 1
        else:
            bad += 1
            if bad < 3:
                print("mal", nm, hex(crc), hex(swgcrc(nm)))
    print("crc ok", ok, "mal", bad, "ordenado por crc", sorted_ok)
