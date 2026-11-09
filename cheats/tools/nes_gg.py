#!/usr/bin/env python3
"""NES Game Genie helper: encode codes and check compare bytes across banks.

  nes_gg.py --rom ROM [--bank-size 2000] [--default-org A000]
            [--org 0:C000,30:8000,31:E000] [--fixed 30,31] BANK:ADDR:NEWBYTE ...

ADDR, NEWBYTE, sizes and orgs are hex; BANK is decimal. For each patch it prints
the 8-letter code, the raw form (address:new-byte:compare-byte), the file
offset, and any OTHER bank that loads at the same CPU window and has the same
compare byte there (a code with such a match also changes that bank). It ends
with a ggpatch argument string (CODE@bank+...; fixed-bank codes have no @).
Banks not in --org load at --default-org. An NROM game is one bank:
--bank-size 8000 --default-org 8000.
"""
import argparse

L = "APZLGITYEOXUKSVN"

def enc(a, v, c):
    n = [(v&7)|((v>>4)&8), ((v>>4)&7)|((a>>4)&8), ((a>>4)&7)|8, ((a>>12)&7)|(a&8),
         (a&7)|((a>>8)&8), ((a>>8)&7)|(c&8), (c&7)|((c>>4)&8), ((c>>4)&7)|(v&8)]
    return "".join(L[x] for x in n)

assert enc(0x81A1,0xFF,0x10)=="NNXAPPAO" and enc(0x8E5E,0x17,0xE7)=="YPSEVTNT"

p = argparse.ArgumentParser()
p.add_argument('--rom', required=True)
p.add_argument('--bank-size', default='2000')
p.add_argument('--default-org', default='A000')
p.add_argument('--org', default='')
p.add_argument('--fixed', default='')
p.add_argument('patch', nargs='+')
a = p.parse_args()
rom = open(a.rom, 'rb').read()
hdr = 16 if rom[:4] == b'NES\x1a' else 0
size = int(a.bank_size, 16); dflt = int(a.default_org, 16)
orgs = {int(b): int(o, 16) for b, o in (x.split(':') for x in a.org.split(',') if x)}
fixed = {int(x) for x in a.fixed.split(',') if x}
nbanks = (len(rom) - hdr) // size if hdr else len(rom) // size
if hdr: nbanks = rom[4] * 0x4000 // size
org = lambda b: orgs.get(b, dflt)
off = lambda b, ad: hdr + b*size + (ad - org(b))
args, codes = [], []
for spec in a.patch:
    b, ad, v = spec.split(':'); b = int(b); ad = int(ad, 16); v = int(v, 16)
    assert org(b) <= ad < org(b) + size, f"{ad:04X} is not in bank {b}'s window at {org(b):04X}"
    c = rom[off(b, ad)]
    same = [x for x in range(nbanks) if x != b and org(x) == org(b) and org(x) <= ad < org(x)+size
            and rom[off(x, ad)] == c] if b not in fixed else []
    code = enc(ad, v, c); codes.append(code)
    print(f"{code}  {ad:04X}:{v:02X}:{c:02X}  bank {b} (@{org(b):04X})  file 0x{off(b, ad):X}"
          + (f"   ALSO MATCHES banks {same}" if same else ""))
    args.append(code if b in fixed or nbanks == 1 else code + "@" + "/".join(map(str, [b] + same)))
print("codes:", " + ".join(f"`{c}`" for c in codes))
print("ggpatch:", "+".join(args))
