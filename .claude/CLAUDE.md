# Cloud sessions (Claude Code on the web and mobile)

This part applies only when `ext/original.nes` is missing, which is the
case in a cloud session. On the Mac, ignore it and follow `AGENTS.md`.

Work on the `cheat-hunt` branch. The Game Genie entries are in `cheats/`:

- `cheats/zelda_1_game_genie.md`: cheats with 1 to 3 codes.
- `cheats/zelda_1_long_game_genie.md`: cheats with more than 3 codes.

The Mac copies them back into its own `game_genie/` folder later, and
builds ROMs, syncs Mesen2, Batocera and MinUI there. None of those exist
here, so don't try them, and don't write to `~/Downloads`.

## The ROM

The real ROM is not in git. A SessionStart hook runs
`cheats/cloud_build.sh`, which builds `bin/Z.nes` with its 48 data files
(graphics, music, level data; 44420 bytes, listed in `src/bins.xml`)
filled with zero bytes. All code bytes are real. If `bin/Z.nes` is
missing, run `cheats/cloud_build.sh` yourself.

## Making a code

1. Find the code to change in `src/Z_00.asm` to `src/Z_07.asm` (one file
   per 16 KB bank). Don't change the disassembly to make a code.
2. Encode it with the wrapper, which knows Zelda's layout (MMC1; banks 0-6
   load at `$8000`, bank 7 is fixed at `$C000`) and reads the original
   byte from `bin/Z.nes`:

       python3 -I cheats/tools/zgg.py 4:B19C:A0 4:B1A2:11

   It prints the 8-letter codes, the raw form and the ggpatch string. If it
   says `ALSO MATCHES banks [...]`, the code would also change another
   bank. Pick a different byte with the same effect (another byte of the
   same instruction, a branch offset of `$00`, `JSR` to `BIT` with
   `$20` to `$2C`, and so on), or say in the entry that no clean code
   exists.
3. If it prints `WARNING ... placeholder data`, the compare byte or the
   other-bank check is not real. Keep the code, but add this caveat:
   "Made from a placeholder build: recheck the compare byte and other
   banks with the real ROM." Codes in data tables (not in code) always
   get this warning.
4. Write the entry at the bottom of the right file in `cheats/`.

## Entry format

Copy the newest entries. The shape is:

```
## Short title that says what the player sees

**Codes:** `AAAAAAAA` + `BBBBBBBB` (use both)
**Raw form:** `$B19C:A0:A4` + `$B1A2:11:10` (address:new:compare, bank 4)
**Recorded:** YYYY-MM-DD HH:MM:SS

**Mechanism:** what the original code does (quote it, with labels and
the source file), and what the patched code does.

**Evidence:** the bytes read from `bin/Z.nes` and the other-bank check.

**Caveats:**

- Not tested.
- Side effects, limits, and things that still work as before.
```

- Newest entry last, in **Recorded:** order. Use simple technical
  English.
- No `Tags:` line unless the user asks for tags. Add or remove tags only
  when asked.
- Optional extra codes go on their own line, such as
  `**Optional, for Wizzrobes too:** ...`.
- When porting a cheat from another game, say which one in the Mechanism.
  Other games' cheat files are not in this repo; the user can paste one.

## Commits

Commit each change on `cheat-hunt` and push it. Messages: `Add: <title>`
for a new entry, `Remove: <title>` for a deleted one, otherwise a short
plain sentence. No attribution lines. Never commit `bin/`, `ext/` or
any ROM.
