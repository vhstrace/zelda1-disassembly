#!/usr/bin/env python3
"""Zelda 1 wrapper for nes_gg.py.

  python3 -I cheats/tools/zgg.py BANK:ADDR:NEWBYTE ...

Runs nes_gg.py with Zelda's bank layout (MMC1, 16 KB banks; banks 0-6
load at $8000, bank 7 is fixed at $C000) on bin/Z.nes, or on --rom.
With a placeholder build (bin/placeholder_ranges.txt from
cheats/cloud_build.sh), it also warns when a patched byte, or the same
address in another bank, is placeholder data. A placeholder byte is 0,
not the real byte, so its compare byte or the other-bank check can't be
trusted.
"""
import os, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(here))
args = sys.argv[1:]
rom = os.path.join(root, 'bin', 'Z.nes')
if '--rom' in args:
    i = args.index('--rom'); rom = args[i + 1]; del args[i:i + 2]
out = subprocess.run([sys.executable, '-I', os.path.join(here, 'nes_gg.py'), '--rom', rom,
                      '--bank-size', '4000', '--default-org', '8000', '--org', '7:C000',
                      '--fixed', '7'] + args, capture_output=True, text=True)
sys.stdout.write(out.stdout); sys.stderr.write(out.stderr)
rp = os.path.join(root, 'bin', 'placeholder_ranges.txt')
if out.returncode or not os.path.exists(rp) or rom != os.path.join(root, 'bin', 'Z.nes'):
    sys.exit(out.returncode)
ranges = []
for line in open(rp):
    off, ln, name = line.split()
    ranges.append((int(off), int(off) + int(ln), name))
def hit(off):
    return next((n for a, b, n in ranges if a <= off < b), None)
bad = 0
for p in args:
    if p.startswith('-'): continue
    bank, addr = int(p.split(':')[0]), int(p.split(':')[1], 16)
    org = 0xC000 if bank == 7 else 0x8000
    n = hit(16 + bank * 0x4000 + addr - org)
    if n:
        bad = 1; print(f'WARNING {bank}:{addr:04X} is placeholder data ({n}); its compare byte is not real.')
    if bank != 7:
        for b in range(7):
            if b == bank: continue
            n = hit(16 + b * 0x4000 + addr - 0x8000)
            if n:
                bad = 1; print(f'WARNING {bank}:{addr:04X}: bank {b} has placeholder data there ({n}); the other-bank check for it is not real.')
if bad:
    print('Recheck these on the Mac with the real ROM before shipping the code.')
