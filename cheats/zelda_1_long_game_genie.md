# The Legend of Zelda (NES) Rev 0 — long Game Genie codes

Cheats here need more codes than a real Game Genie can hold (it takes 3 at
most). Use them in an emulator that takes any number of codes, such as
Mesen. Cheats with 3 codes or fewer are in `zelda_1_game_genie.md`.

These codes are tested only on Rev 0, the original release. If your game
includes a message to "hold in reset button as you turn power off" on the
continue screen, it is Rev 1 (a re-release) and these codes may not work.

## Have the Magical Rod in your inventory

**Code(s):** `GGPZIVSE` + `EPPZTVGT` + `NZPZYTTE` + `OXPZENNN` +
`PEPZONNY` + `SEPZXNNN` + `YSPZUNNN` + `TEPZKNNY` + `GKPZSNNN` +
`AOPZVNNN` + `VXPZNNNY`

Tags: `play-start`

**Effect:** Every time a save file is entered (a brand-new file or an
existing one), the Magical Rod's ownership flag is forced on, so it's a
real, selectable, ownable item in the subscreen inventory — not just a
bypassed usability check.

**How it works:**

The Magical Rod's ownership is a single boolean at `Items+8` (CPU
`$065F`, unnamed in `Variables.inc`, between `Potion` at `$65E` and
`InvRaft` at `$660`). Unlike the sword, nothing in `WieldRod` itself
gates on ownership — the actual gate is upstream, in the generic
item-cursor logic (`FindAndSelectOccupiedItemSlot`) that skips any slot
where `Items, Y` is 0, so an unowned Rod slot can never be cycled to or
selected. Patching that shared cursor logic would risk affecting every
other item's selectability, so instead this patches the one place that
sets the byte: the save-file-load routine.

`UpdateMode1Menu_Sub1`'s `@ChoseSlot`/`@CopyItems` (bank 2, CPU
`$A5DF`+) copies the whole 40-byte `Items` block from SRAM into live RAM
every time a file is chosen, then resets three unrelated bytes:

```
@CopyItems:
    LDA ($00), Y
    STA Items, Y
    DEY
    BPL @CopyItems
    LDA #$00
    STA SwordBlocked
    STA ObjState                ; Reset player state.
    STA InvClock                ; Reset clock item.
```

The final `STA InvClock` (CPU `$A615`, opcode/operand bytes `8D 6C 06`)
is overwritten with `JMP $AF90` (`4C 90 AF` — codes `GGPZIVSE` /
`EPPZTVGT` / `NZPZYTTE`), redirecting into 8 bytes of previously-unused
`$FF` padding at the tail of bank 2 (`$AF90`-`$BF4F`, well clear of the
`BANK_02_ISR`/`BANK_02_VEC` segments that start at `$BF50`). That
injected code (codes `OXPZENNN` / `PEPZONNY` / `SEPZXNNN` / `YSPZUNNN` /
`TEPZKNNY` / `GKPZSNNN` / `AOPZVNNN` / `VXPZNNNY`) assembles to:

```
LDA #$01
STA Items+8      ; $065F — force the Magical Rod owned
JMP $A618        ; TAY — resume right after the original reset block
```

`SwordBlocked` and `ObjState` still get reset to 0 exactly as before
(their instructions are untouched); only the `InvClock` reset is
dropped, since a freshly-loaded profile's `InvClock` byte was already
copied from the save file by the `@CopyItems` loop itself two
instructions earlier (`InvClock` is `Items+21`, well within the copied
40-byte block) — skipping the extra forced zero just means a file saved
mid-Clock-effect would resume that way, an edge case that's not worth
another code to close.

Bank-uniqueness: the 3 redirect bytes at `$A615`-`$A617` (originally
`$8D`/`$6C`/`$06`) don't recur at those addresses in any other bank. The
8 trampoline bytes at `$AF90`-`$AF97` are written into space that reads
`$FF` in bank 2 — banks 0, 3, and 6 are `$FF` across that *entire*
4032-byte padding region too, and bank 5 has a wide local `$FF` run
covering the same 8 bytes, so the `$FF`-compare patch harmlessly touches
unused padding there as well when those banks happen to be active; banks
1, 4, and 7 hold non-`$FF` data at every one of those offsets, so the
patch never fires for them. Since the jump *into* this trampoline only
ever happens from the bank-2-only code at `$A615`, what any other bank
holds at `$AF90` is moot regardless — it's only ever executed while bank
2 is paged in.

**Not live-verified:** derived from reading `UpdateMode1Menu_Sub1`,
`FindAndSelectOccupiedItemSlot`, and `WieldRod`, not from observing it
in-game.

## Have the Recorder in your inventory

**Code(s):** `EPLZTTOX` + `NZLZYVUV` + `OXPXENNN` + `PEPXONNY` +
`SEPXXNNN` + `GSPXUNNN` + `TEPXKNNY` + `GKPXSNNN` + `OXPXVNNY` +
`UVPXNNNN`

Tags: `play-start`

**Effect:** Every time a save file is entered, the Recorder's ownership
flag is forced on, the same way the Magical Rod cheat above does —
by making `Items, Y` genuinely nonzero for its slot, rather than
bypassing the cursor-selection check that guards it.

**How it works:**

Like the Rod, the Recorder has no dedicated ownership variable in
`Variables.inc` — it's `Items+5` (CPU `$065C`, the unnamed gap between
`InvCandle` at `$65B` and `InvFood` at `$65D`), matched against slot 5
in `WieldItem_JumpTable` (`WieldFlute`) and against the same generic
`FindAndSelectOccupiedItemSlot` cursor gate used for every item.

Rather than reuse (and conflict with) the trampoline built for the
Magical Rod cheat above — two GG codes both trying to redirect the same
bytes would only let one of the two effects actually run if both cheats
were enabled together — this uses a second, independent redirect point
in the same `UpdateMode1Menu_Sub1` file-load routine (bank 2): the
unconditional jump at the very end of the `@CopyWorldFlags` copy loop,
right after the `Items` block has already been copied in:

```
    LDA $0F
    CMP #$07
    BNE @CopyWorldFlags         ; If not done (destination address < $07FF), then copy more.
    JMP GoToNextMode
```

`JMP GoToNextMode` (CPU `$A635`, bytes `4C A1 EB`) is retargeted by
changing only its two address-operand bytes at `$A636`/`$A637` (`A1
EB` &rarr; `98 AF` — codes `EPLZTTOX` / `NZLZYVUV`) to point at 8 more
bytes of the same unused `$FF` padding used for the Rod cheat, placed
immediately after that cheat's trampoline (`$AF98`-`$AF9F`, still well
clear of `BANK_02_ISR` at `$BF50`). The injected code (codes
`OXPXENNN` / `PEPXONNY` / `SEPXXNNN` / `GSPXUNNN` / `TEPXKNNY` /
`GKPXSNNN` / `OXPXVNNY` / `UVPXNNNN`) assembles to:

```
LDA #$01
STA Items+5      ; $065C — force the Recorder owned
JMP GoToNextMode  ; $EBA1 — the original jump target
```

Nothing here is sacrificed or skipped — the `JMP` opcode byte itself is
untouched, so unlike the Rod cheat there's no reset to give up; this
patch only ever changes where an already-unconditional jump lands, then
lands it back in the same place afterward.

Bank-uniqueness: `$A636`/`$A637` hold `$A1`/`$EB` only in bank 2 (no
other bank matches either byte at those addresses). The 8 trampoline
bytes at `$AF98`-`$AF9F` land in the same padding region validated for
the Rod cheat above — banks 0, 3, and 6 are `$FF` there across the whole
4032-byte span, and bank 5's local `$FF` run covers these offsets too,
so the compare-locked patch is harmless padding-to-padding noise on
those banks; banks 1, 4, and 7 hold unrelated non-`$FF` bytes there, so
the patch never fires for them. As with the Rod cheat, the jump *into*
this trampoline only ever happens from bank-2-only code, so it's
irrelevant what any other bank holds at that address.

**Not live-verified:** derived from reading `UpdateMode1Menu_Sub1` and
`WieldFlute`/`WieldItem_JumpTable`, not from observing it in-game.

## Recorder will take you to dungeons you haven't beaten

**Code(s):** `GKLXGESX` `ANLXIAPY` `NULXTATA` `SZYLANNN` `PYYLPNNY`
`TAYLZNNY` `PGYLLNNN` `EIYLINNY` `LAYLTNNY` `GGYLYNNN` `GAYUANNY`
`OZYUPNNY` `GGYUZNNN` `OGYULNNY` `EZYUGNNY`

**Effect:** Playing the Recorder in the overworld (outside a flute-secret
room) now summons the whirlwind to a dungeon whose Triforce piece you
*haven't* collected yet, instead of one you have.

**How it works:** `SummonWhirlwind` (`src/Z_01.asm`) walks around the 8
dungeon "level mask" bits (rotating a single-bit mask in `[00]` left or
right depending on which way Link is facing) looking for one that
satisfies a condition, then teleports to it:

```
@LoopTriforcePiece:
    ; If there are no triforce pieces, then return.
    LDA InvTriforce
    BEQ L6104_Exit

    ; If we have gotten this triforce piece, then go try to make a
    ; whirlwind.
    BIT $00
    BNE @MakeWhirlwind

    ; We have not gotten this piece.
    ; First, advance the teleporting index again.
    JSR AdvanceTeleportingLevelIndex
    ...
```

Vanilla logic stops rotating and teleports as soon as it finds a dungeon
bit that's *set* in `InvTriforce` (a beaten dungeon). The natural inverse
— stop on a bit that's *clear* instead — can't just flip the `BNE` to a
`BEQ` in place, though: the early guard above it (`LDA InvTriforce / BEQ
L6104_Exit`, which exists to stop the rotation from spinning forever when
no dungeon qualifies) only checks for `InvTriforce == 0`. That's the one
case where vanilla's "find a set bit" search could never terminate; for
an inverted "find a clear bit" search, the one case that could spin
forever is the opposite: `InvTriforce == $FF` (all 8 pieces already
collected, so no clear bit exists to find). Complementing the accumulator
right after loading it solves both problems in one move: `~InvTriforce`
is zero exactly when `InvTriforce == $FF` (so the *existing* `BEQ
L6104_Exit` now guards the right case), and `BIT $00` against the
complemented value is nonzero exactly when the target dungeon's bit is
*clear* in the real `InvTriforce` (so the *existing* `BNE @MakeWhirlwind`
now selects unbeaten dungeons) — without needing to touch either branch
at all.

Since this can't be done as an in-place edit (there's no spare byte to
fit an `EOR #$FF` into the existing instruction stream), it's a
redirect-to-trampoline patch, using the same technique as the "Have the
Magical Rod" cheat above. The 3-byte `LDA InvTriforce` at the top of the
loop (CPU `$A0BC`, bytes `AD 71 06`) is overwritten with `JMP $B770` (`4C
70 B7`); the 2 bytes right after it (the now-unreached `BEQ
L6104_Exit`) are left alone, since they're never executed again. `$B770`
is the start of a large (2016-byte) unused `$FF` padding run in bank 1,
just past the end of the RAM-relocated `BANK_01_CODE` segment and before
`BANK_01_ISR`. The trampoline there assembles to:

```
LDA InvTriforce      ; AD 71 06
EOR #$FF              ; 49 FF        (byte at $B774 is already $FF in unmodified ROM — no code needed for it)
BNE @Continue          ; D0 03
JMP L6104_Exit          ; 4C 04 A1    ; InvTriforce was $FF (all pieces owned) — bail out to avoid spinning forever
@Continue:
JMP $A0C1               ; 4C C1 A0    ; back into SummonWhirlwind, at the original "BIT $00" instruction
```

15 bytes changed across 14 addresses (one byte, `$B774`, already reads
`$FF` in the unpatched ROM and needs no code).

Bank-uniqueness: the 3-byte redirect at `$A0BC`-`$A0BE` matches its
original bytes (`AD`/`71`/`06`) in bank 1 only. The 12 trampoline bytes
at `$B770`-`$B77C` all use compare `$FF`; banks 0, 2, 3, 4, and 6 also
happen to be `$FF`-padded at this same offset (their own equivalent dead
space), so this cheat harmlessly rewrites unused padding in those banks
too — nothing in any of them ever reads or jumps into that offset, since
the only thing that ever jumps there is the redirect at `$A0BC`, which is
itself locked to bank 1. Banks 5 and 7 hold real, different bytes there
and are unaffected.

**Not live-verified:** derived from reading `SummonWhirlwind` and
`AdvanceTeleportingLevelIndex`, not from observing it in-game. The human
should specifically check the edge case of already having collected all
8 Triforce pieces (the code is designed not to hang in that case, but
this hasn't been tested).

## More overworld enemies spawn per screen

**Code(s):** `LAZPGLPA` `TAZPILGA` `YAZPTLIA` `AAZPYLTE`

**Effect:** Overworld rooms that spawn enemies now spawn more of them:
the four possible per-room enemy counts go from 1/4/5/6 to 3/6/7/8.

**How it works:** When an overworld room's monsters are set up
(`src/Z_05.asm`), the room's attribute byte packs a monster list ID
(which enemies) in its low bits and, in its top 2 bits, an index (0-3)
into a small "how many" table:

```
    ; Get index of monster count from high 2 bits of attribute byte C.
    AND #$C0
    CLC
    ROL
    ROL
    ROL
    TAY

    ; Get the object count from level info.
    LDA LevelInfo_FoeCounts, Y
```

`LevelInfo_FoeCounts` (`$6BA2`) is RAM, freshly copied from the current
level's info block on every level load; for the overworld, that source
data is `LevelInfoOW` (`src/Z_06.asm`, built from `dat/LevelInfoOW.dat`)
at CPU `$9300` in bank 6, with the 4-byte `FoeCounts` field sitting at
offset `$24` into that struct (CPU `$9324`-`$9327`), holding `$01 $04
$05 $06`. Patching those 4 bytes directly to `$03 $06 $07 $08` raises
every room's possible enemy count. This doesn't touch the maximum of 11
concurrent object slots a room can hold, and boss/unique object lists
(list ID `$32`-`$61`) are still forced back down to a count of 1 by the
same routine regardless of this table, so it can't cause slot exhaustion
or duplicate a boss.

Bank-uniqueness: all 4 addresses (`$9324`-`$9327`, bank 6) were checked
against all 8 banks; none of the other banks holds a matching byte at
any of these offsets.

**Not live-verified:** derived from reading the object-count setup code
in `src/Z_05.asm` and `dat/LevelInfoOW.dat`, not from observing it
in-game.

## Replace overworld enemies with dungeon enemies

**Code(s):** `GGAAUOSX` `ZIAAKPAI` `UPAASPLA` `SZIPZUNY` `APIPLUNY`
`EIIPGUNY` `APIPIUNY` `XZIPTUNY` `AAIPYUNY` `KTIOAUNN` `TGIOPUNN`
`LAIOZUNY` `ELIOLUNY` `PAIOGUNN` `OZIOIUNN` `GAIOTUNN` `SPIOYUNN`
`AITPAUNY` `LATPPUNY` `ETTPZUNN` `GGTPLUNN` `AITPGUNN` `UPTPIUNY`
`SZTPTUNN` `AITPYUNY` `LATOAUNY` `GGTOPUNN` `TATOZUNY` `OATOLUNN`

**Effect:** Every overworld room that would normally spawn ordinary
overworld enemies (Octoroks, Tektites, Leevers, etc.) now spawns Blue
Darknuts — a dungeon-only enemy — instead, in the same numbers the room
would have used. Dungeon rooms are unaffected.

**How it works:** After a room's monster-placement code (`src/Z_05.asm`)
fills in `ObjType+1` through `ObjType+RoomObjCount` with whichever
enemy type(s) the room's data specifies (either one repeated type, or a
list of different types via `ObjListAddrs`), every path funnels into a
shared instruction:

```
@StoreObjTemplate:
    ; Remember the object template type.
    LDA ObjType+1
    STA RoomObjTemplateType
```

This is a single, reliable choke point after the enemy types are
decided but before anything uses them. Redirecting its first instruction
(`LDA ObjType+1`, CPU `$8903`-`$8905`, bank 5, bytes `AD 50 03`) with
`JMP $9352` to a trampoline in unused bank-5 padding overwrites the
whole freshly-filled `ObjType` array with Blue Darknut (object type
`$0C`) whenever the current level is the overworld (`CurLevel == 0`),
then falls through to the original two instructions before rejoining at
`$8906`:

```
    LDA CurLevel
    BNE @Skip                   ; dungeons ($8bit CurLevel <> 0): leave enemies alone

    LDX #$00
@Loop:
    CPX RoomObjCount
    BCS @Skip
    LDA #$0C                    ; Blue Darknut
    STA ObjType+1, X
    INX
    JMP @Loop

@Skip:
    LDA ObjType+1                ; original instruction
    JMP $8906                     ; back into @StoreObjTemplate, right after the LDA
```

Blue Darknut was picked because it's a normal, fully-implemented enemy
type that never otherwise appears on the overworld, so there's no risk
of colliding with overworld-specific spawn/animation assumptions the
way reusing a boss or cave-only object type might.

Bank-uniqueness: the 3-byte redirect at `$8903`-`$8905` matches its
original bytes (`AD`/`50`/`03`) in bank 5 only. The 26 trampoline bytes
at `$9352`-`$936B` all use compare `$FF`; some other banks happen to
have unused `$FF` padding at some of these same offsets too, which is
harmless — nothing in those banks ever jumps into this address, since
the only thing that does is the redirect at `$8903`, which is itself
locked to bank 5.

**Not live-verified:** derived from reading the object-placement code in
`src/Z_05.asm`, not from observing it in-game. The human should check
that a full room of Blue Darknuts (rather than the original 1-3
enemies) doesn't cause slowdown or sprite flicker beyond what's already
normal for the game.

## Load dungeon enemy sprites in the overworld (companion to "Replace overworld enemies with dungeon enemies")

**Code(s):** `GGIAYESX` `UIIEAEIO` `UZIEPAIE` `SXIXUUNN` `IOIXKUNN`
`IEIXSUNY` `OKIXVUNN` `ZEIXNUNY` `ENTZEUNY` `LETZOUNY` `GKTZXUNN`
`PSTZUUNY` `EETZKUNY` `OXTZSUNN` `LNTZVUNN` `SETZNUNY` `AETXEUNY`
`OXTXOUNN` `EOTXXUNN` `SETXUUNY` `PETXKUNY` `OXTXSUNN` `ZETXVUNY`
`SETXNUNY` `ZEYZEUNY` `OXYZOUNN` `AXYZXUNY` `SEYZUUNY` `LEYZKUNY`
`AXYZSUNY` `KSYZVUNN` `EEYZNUNY` `GKYXEUNN` `TSYXOUNN` `EEYXXUNY`

**Effect:** A companion to the "Replace overworld enemies with dungeon
enemies" cheat above. That cheat turns every overworld enemy into a Blue
Darknut, but leaves the overworld's own sprite graphics loaded, so the
Darknuts are drawn with garbled, wrong-looking tiles. This cheat changes
*only* the sprite graphics the overworld loads, so Darknuts (and nothing
else visible under normal play) render correctly. It has no effect unless
combined with a cheat that actually spawns dungeon-only enemies on the
overworld.

**How it works:** Monster sprite tiles are uploaded to CHR-RAM by
`TransferLevelPatternBlocks` (`src/Z_03.asm`) every time a room loads.
Dungeon levels fill the $08E0-$1000 VRAM range from three source blocks
picked by `CurLevel` — a 256-byte "common" block, a 544-byte "extra"
block, and a 1024-byte "boss" block. The overworld instead fills that
entire range in one shot from a single 1824-byte block,
`PatternBlockOWSP`. Blue Darknut's animation frames (tiles `$AC`, `$B0`,
`$B4`, `$B8`, `$BC`, each a 2x2 sprite so `+1`/`+2`/`+3` are used too)
land inside the "extra" block's tile range ($9E-$C0), so whichever
overworld tiles currently sit there are what's drawn — and the
overworld's own graphics were never meant to be interpreted as Darknut
tiles.

Level 3 is one of the levels whose "extra" block (`PatternBlockUWSP358`)
is Darknut's; comparing its tiles at the relevant offsets against the
other two "extra" blocks used by other levels (`PatternBlockUWSP127`,
`PatternBlockUWSP469`) confirms it's the one with the armored
knight/shield artwork.

The patch has two parts:

1. A 3-byte redirect at the overworld sprite-loading loop's exit point
   (CPU `$8057`-`$8059`, bank 3, originally `LDA $051D` = `AD 1D 05`) is
   replaced with `JMP $ABDB` (`4C DB AB`), sending control into a
   trampoline in unused bank-3 padding instead of falling straight
   through to `ResetPatternBlockIndex`.
2. The 32-byte trampoline at `$ABDB`-`$ABFA` reproduces the original
   `LDA $051D` / `CMP #$02` check (so the normal two-block OW loop still
   runs to completion), then — once that loop is done — copies
   `PatternBlockUWSP358`'s 544 bytes on top of VRAM `$09E0` (the same
   "extra" range a dungeon room would fill) by setting up
   `TransferPatternBlock_Bank3`'s source/size and calling it directly,
   before jumping back to `ResetPatternBlockIndex` to finish normally:

   ```
   $ABDB: LDA $051D
   $ABDE: CMP #$02
   $ABE0: BEQ $ABE5
   $ABE2: JMP $8051          ; loop not done yet: continue it normally
   $ABE5: LDA #<PatternBlockUWSP358
   $ABE7: STA $00
   $ABE9: LDA #>PatternBlockUWSP358
   $ABEB: STA $01
   $ABED: LDA #$02            ; size hi byte of $0220 (544 bytes)
   $ABEF: STA $02
   $ABF1: LDA #$20            ; size lo byte
   $ABF3: STA $03
   $ABF5: JSR TransferPatternBlock_Bank3   ; $80DC
   $ABF8: JMP $805E                         ; ResetPatternBlockIndex
   ```

   `TransferPatternBlock_Bank3` picks its destination PPU address by
   table lookup, indexed by `PatternBlockIndex` — which is still `2` at
   this point, the same index a real dungeon room would use for its
   "extra" block — so this naturally lands the transfer at VRAM `$09E0`
   without needing to patch the destination separately.

Only the "extra" tile range ($09E0-$0C00) is overwritten; the common and
boss ranges keep whatever the overworld's own block already put there,
which is harmless since normal overworld enemies (and Blue Darknut) don't
use tiles outside the extra range for their sprites. The overworld
background tiles are completely untouched.

Bank-uniqueness: the 3-byte redirect at `$8057`-`$8059` matches its
original bytes (`AD`/`1D`/`05`) in bank 3 only — the other six banks
mapped into $8000-$BFFF hold unrelated code or, in bank 0's case, `$FF`
padding, none of which happens to start with those exact three bytes.
The 32 trampoline bytes at `$ABDB`-`$ABFA` all use compare `$FF`; bank 0
happens to have unused `$FF` padding across that entire range too, so the
same bytes get harmlessly written there as well — nothing in bank 0 (or
any bank but 3) ever jumps to `$ABDB`, since the only thing that does is
the redirect at `$8057`, which is itself locked to bank 3. Banks 1, 2, 4,
5, and 6 all hold live code across `$ABDB`-`$ABFA` that doesn't match
`$FF`, so they're unaffected.

**Not live-verified:** derived from reading `TransferLevelPatternBlocks`
and its helper routines in `src/Z_03.asm`, and from a static, offline
comparison of the three dungeon "extra" pattern blocks' tile graphics —
not from observing the patch in-game.

## Able to use the sword again almost immediately after touching a Bubble

**Code(s):** `PATELGAP` `XTYAZKSE` `XTYALKTX` `XTYAGGIE`

**Effect:** Touching a Bubble enemy no longer keeps Link's sword unusable
for any meaningful length of time. Touching the flashing (multicolor)
Bubble clears up within about a sixth of a second instead of roughly 2.7
seconds; touching a solid-color Bubble no longer disables the sword at
all (previously that variant disabled it *permanently*, until Link
touched a Fairy).

**How it works:** `UpdateBubble` (`src/Z_04.asm`) handles what happens
when Link collides with a Bubble, based on `ObjType`:

```
    ; If not type $2B (flashing), then go block or unblock the sword
    ; depending on the bubble type.
    LDA ObjType, X
    CMP #$2B
    BNE @BlockOrUnblock

    ; Else the flashing bubble blocks the sword temporarily.
    ; Set a long timer to $10 ($A0 frames) for this purpose.
    LDA #$10
    STA SwordBlockedLongTimer

@Exit:
    RTS

@BlockOrUnblock:
    ; Subtract $2C from the type to get the value for blocking: 0 or 1
    SEC
    SBC #$2C
    STA SwordBlocked
    RTS
```

Two separate variables gate sword use, checked together in
`Link_HandleInput` (`src/Z_05.asm`): `LDA SwordBlockedLongTimer / ORA
SwordBlocked / BNE :+` skips wielding the sword if either is nonzero.
`SwordBlockedLongTimer` is a "long timer" — one of a handful of zero-page
timers (`$4A`-`$4E`) that only tick down once every ~10 frames instead of
every frame (see the shared decrement loop in `src/Z_07.asm`), which is
why setting it to `$10` (16) produces a roughly 160-frame, 2.7-second
delay. `SwordBlocked`, on the other hand, is a plain flag: once
`@BlockOrUnblock` sets it to `1` (for one of the two solid-color Bubble
variants), nothing clears it again except touching a Fairy
(`World_FillHearts` in `src/Z_05.asm`, which resets it to `0` alongside
refilling hearts) — that's what makes the solid-color Bubble's curse
*permanent* rather than temporary.

The patch has two independent one-purpose parts:

1. The flashing Bubble's long-timer value: the immediate operand of `LDA
   #$10` at CPU `$846B` (bank 4) is changed from `$10` to `$01`, so the
   long timer clears on its very next tick (at most ~10 frames later)
   instead of after 160 frames.
2. The solid-color Bubble's permanent block: the 3-byte `STA
   $052E` (`SwordBlocked`) at CPU `$8472`-`$8474` (bank 4, originally
   `8D 2E 05`) is replaced with three `NOP`s. `@BlockOrUnblock` still runs
   (computing 0 or 1 into `A`) but the result is simply discarded, so
   `SwordBlocked` is never set and this Bubble variant no longer affects
   sword use at all. `SwordBlocked` is still reset to `0` elsewhere
   (character creation, touching a Fairy), so the variable itself stays
   well-defined — it just never gets written to `1` anymore.

Four one-byte patches. Bank-uniqueness: none of the other six banks
mapped into `$8000`-`$BFFF` has `$10` at `$846B`, or `$8D`/`$2E`/`$05` at
`$8472`/`$8473`/`$8474` respectively — each bank holds unrelated code or
data there, so the compare bytes pin all four patches to bank 4.

**Not live-verified:** derived from reading `UpdateBubble`,
`Link_HandleInput`, `World_FillHearts`, and the shared long-timer
decrement loop in `src/Z_07.asm`, not from observing it in-game.

## Automatically collect items anywhere onscreen

**Code(s):** `XVGZULEU` `XVGZKLLV` `XVGXNLEU` `XVIZELYS`

**Effect:** Any item sitting out in the current room — Rupees, Hearts, weapons,
even Triforce pieces — is automatically collected as soon as it's able to be
picked up at all, no matter where Link (or an active arrow, sword shot, or
boomerang) actually is relative to it on screen. Enemy collision is untouched;
this only affects the separate code path that decides whether an item is close
enough to pick up.

**How it works:** `TryTakeItem` (`src/Z_01.asm`) is called once per
frame for every dropped item, from `UpdateItem` (`src/Z_04.asm`) — once
for Link's own position, and again with Link's position temporarily
swapped out for an active arrow's, sword shot's, or boomerang's, so any
of the four can "carry" a pickup. Before actually taking the item, it
gates on proximity:

```
    ; If Y distance between Link and the item >= 9, return.
    LDA ObjY
    CLC
    ADC #$03
    SEC
    SBC ObjY, X
    JSR Abs
    CMP #$09
    BCS L6C28_Exit

    ; If X distance between Link and the item >= 9, return.
    LDA ObjX
    SEC
    SBC ObjX, X
    JSR Abs
    CMP #$09
    BCS L6C28_Exit
```

Each check computes the absolute distance on one axis and bails out to
`L6C28_Exit` (skip taking the item this frame) if it's 9 pixels or more.
This patches both `BCS L6C28_Exit` instructions — CPU `$ABC3`-`$ABC4`
(originally `$B0 $63`) and `$ABCF`-`$ABD0` (originally `$B0 $57`), both
in bank 1 — to `$EA $EA` (`NOP` `NOP`) each. With neither branch able to
fire, execution always falls through both distance checks no matter how
far apart the item and the taking object actually are, so the only
remaining gate is the item's own spawn-grace timer (`Item_ObjItemLifetime
>= $F0` skips taking it, unchanged by this patch) and whatever else
`TakeItem` normally requires (e.g. a full inventory slot for capacity
items). This routine is part of the same relocated bank-1 code block as
`CheckMonsterSwordShotOrMagicShotCollision` (see "Sword beam continues
flying after hitting an enemy" above): it's stored here in ROM but
actually executes from a RAM copy made at startup, so like that fix, the
patched behavior is in effect as soon as the game boots.

Four one-byte patches. None of the other six banks holds `$B0` at either
`$ABC3` or `$ABCF`, or `$63`/`$57` at `$ABC4`/`$ABD0` respectively (bank
0 is `$FF` padding at all four; the other banks hold unrelated code or
data), so the compare bytes pin every patch to bank 1.

**Not live-verified:** derived from reading `TryTakeItem`, `TakeItem`
(`src/Z_01.asm`), and `UpdateItem` (`src/Z_04.asm`), plus the bank-1
disassembly at `$ABBC`-`$ABF9` and the same four addresses across banks
0 and 2-6, not from observing it in-game.

## Have the Red Ring in your inventory

**Code(s):** `GGPZAVSE` + `EZPZPVTZ` + `NZPZZTIE` + `SEZZENNN` +
`TXZZONNN` + `IEZZXNNY` + `OXZZUNNN` + `ZEZZKNNY` + `SEZZSNNN` +
`ZVZZVNNY` + `TEZZNNNY` + `OXZXENNN` + `AEZXONNY` + `GKZXXNNN` +
`LOZXUNNY` + `VXZXKNNY`

Tags: `play-start`

**Effect:** Every time a save file is entered, the ring inventory byte
is forced to grade 2, so Link owns the Red Ring (the stronger of the
two damage-halving rings) — not merely the color/effect, but a real,
selectable inventory value.

**How it works:**

Rings are a class-2, grade-ordered item like the sword (see "Have the
Magical Sword in your inventory" above): `InvRing` (`Items+$0B`, CPU
`$0662`) holds 0 (none), 1 (Blue Ring), or 2 (Red Ring). `Link_BeHarmed`
(`src/Z_01.asm`) reads it directly to halve incoming damage once per
ring grade, so simply forcing this byte to 2 on file load is enough —
no separate gate needs patching, unlike the sword's `WieldSword`.

As with the Rod and Recorder cheats above, the target is
`UpdateMode1Menu_Sub1`'s file-load routine (bank 2, CPU `$A5DF`+),
which resets three bytes right after copying the `Items` block in from
SRAM:

```
    LDA #$00
    STA SwordBlocked             ; CPU $A60E-$A610
    STA ObjState                 ; CPU $A613
    STA InvClock                 ; CPU $A615, already claimed by the Rod cheat
```

The Rod cheat already claims the `InvClock` reset as its redirect
point, and the Recorder cheat claims the `JMP GoToNextMode` a few
instructions later, so this uses a third, independent redirect: `STA
SwordBlocked` (CPU `$A610`, bytes `8D 2E 05`) is overwritten with `JMP
$AFA0` (`4C A0 AF` — codes `GGPZAVSE` / `EZPZPVTZ` / `NZPZZTIE`),
pointing at 13 bytes of the same previously-unused `$FF` padding at the
tail of bank 2 (`$AF90`-`$BF4F`), placed right after the Recorder
cheat's trampoline (`$AFA0`-`$AFAC`, still clear of `BANK_02_ISR` at
`$BF50`). Unlike the Rod cheat, nothing is dropped: the trampoline
redoes the `SwordBlocked` reset itself before setting the ring, so
`SwordBlocked` still ends up 0 exactly as before. The injected code
(codes `SEZZENNN` / `TXZZONNN` / `IEZZXNNY` / `OXZZUNNN` / `ZEZZKNNY` /
`SEZZSNNN` / `ZVZZVNNY` / `TEZZNNNY` / `OXZXENNN` / `AEZXONNY` /
`GKZXXNNN` / `LOZXUNNY` / `VXZXKNNY`) assembles to:

```
STA SwordBlocked  ; $052E — redo the reset this redirect skipped
LDA #$02
STA InvRing        ; $0662 — force the Red Ring (grade 2)
LDA #$00           ; restore A so the resumed code's STA ObjState still writes 0
JMP $A613          ; STA ObjState — resume right where the redirect left off
```

Bank-uniqueness: the 3 redirect bytes at `$A610`-`$A612` (originally
`$8D`/`$2E`/`$05`) don't recur together at those addresses in any other
bank — bank 0 is `$FF` filler there, bank 1 holds `$F2`/`$20`/`$CB`,
bank 3 holds `$00`/`$00`/`$00`, bank 4 holds `$4C`/`$1D`/`$A6`, bank 5
holds `$A0`/`$30`/`$84`, and bank 6 holds `$E2`/`$24`/`$11` — none match
`$8D` at `$A610`, so each redirect byte's own compare pins it to bank
2. The 13 trampoline bytes at `$AFA0`-`$AFAC` are written into space
that reads `$FF` in bank 2 — banks 0, 3, 5, and 6 are `$FF` across that
entire padding region too, so the compare-locked patches harmlessly
touch unused padding there as well when those banks happen to be
active; banks 1 and 4 hold unrelated non-`$FF` data at every one of
those offsets, so the patch never fires for them. As with the Rod and
Recorder cheats, the jump into this trampoline only ever happens from
bank-2-only code, so what any other bank holds at `$AFA0` is moot
regardless.

**Not live-verified:** derived from reading `UpdateMode1Menu_Sub1`
(bank 2), `Link_BeHarmed` and `HandleClass2` (bank 1), and the "Blue
Ring costs 1 Rupee" cheat's item-ID/descriptor decoding above, not from
observing it in-game.

## Have the Magical Shield in your inventory

**Code(s):** `GKTXASSE` + `SXTXPITS` + `NXTXZITE` + `SEZXSNNN` +
`TSZXVNNY` + `TEZXNNNY` + `OXLZENNN` + `PELZONNY` + `SELZXNNN` +
`TNLZUNNY` + `TELZKNNY` + `OXLZSNNN` + `AELZVNNY` + `GKLZNNNN` +
`UVLXENNN` + `SXLXONNY`

Tags: `play-start`

**Effect:** Every time a save file is entered, the Magical Shield's
ownership flag is forced on, so Link can parry the shots (fireballs,
etc.) that only the Magical Shield blocks — a real, earned-looking
inventory value, not a bypassed check.

**How it works:**

`InvMagicShield` (`Items+$1F`, CPU `$0676`, item ID `$1C` in
`ItemIdToSlot`/`ItemIdToDescriptor`, descriptor `$01` — a plain
boolean, unlike the ring/sword's grade-based descriptors) gates the
"parry" branch in `Link_BeHarmed` (`src/Z_01.asm`, part of the
RAM-relocated `BANK_01_CODE` block, already documented by the shield
cheats above):

```
    ; If the magic shield is missing, then the rest of the shots do damage.
    ; So, go harm Link.
    LDA InvMagicShield
    BEQ HarmLink
```

Like the Rod, Recorder, and Red Ring cheats above, this forces the byte
by patching `UpdateMode1Menu_Sub1`'s file-load routine (bank 2, CPU
`$A5DF`+), which resets `Tune1`, `CurLevel`/`SelectedItemSlot`, and (via
`@ChoseSlot`) `SwordBlocked`/`ObjState`/`InvClock` right after copying
the file's `Items` block into RAM:

```
    LDA #$00
    STA Tune1
    LDA #$00
    STA CurLevel
    STA SelectedItemSlot         ; CPU $A5E8, this cheat's redirect point
    JSR TurnOffAllVideo
```

The `SwordBlocked`, `ObjState`, and `InvClock` resets are already
claimed by the Red Ring and Rod cheats above, and the trailing `JMP
GoToNextMode` is claimed by the Recorder cheat, so this uses a fourth,
independent redirect: `STA SelectedItemSlot` (CPU `$A5E8`, bytes `8D 56
06`) is overwritten with `JMP $AFAD` (`4C AD AF` — codes `GKTXASSE` /
`SXTXPITS` / `NXTXZITE`), pointing at 13 more bytes of the same
previously-unused `$FF` padding at the tail of bank 2 (`$AF90`-`$BF4F`),
placed right after the Red Ring cheat's trampoline (`$AFAD`-`$AFB9`,
still clear of `BANK_02_ISR` at `$BF50`). As with the Red Ring cheat,
nothing is dropped: the trampoline redoes the `SelectedItemSlot` reset
itself before setting the shield flag. The injected code (codes
`SEZXSNNN` / `TSZXVNNY` / `TEZXNNNY` / `OXLZENNN` / `PELZONNY` /
`SELZXNNN` / `TNLZUNNY` / `TELZKNNY` / `OXLZSNNN` / `AELZVNNY` /
`GKLZNNNN` / `UVLXENNN` / `SXLXONNY`) assembles to:

```
STA SelectedItemSlot  ; $0656 — redo the reset this redirect skipped
LDA #$01
STA InvMagicShield     ; $0676 — force the Magical Shield owned
LDA #$00                ; restore A for consistency with the resumed code
JMP $A5EB                ; JSR TurnOffAllVideo — resume right where the redirect left off
```

Bank-uniqueness: the 3 redirect bytes at `$A5E8`-`$A5EA` (originally
`$8D`/`$56`/`$06`) don't recur together at those addresses in any other
bank — bank 0 is `$FF` filler there, bank 1 holds `$24`/`$85`/`$03`,
bank 3 holds `$00`/`$00`/`$03`, bank 4 holds `$02`/`$8A`/`$A8`, bank 5
holds `$22`/`$23`/`$21`, and bank 6 holds `$21`/`$C0`/`$20` — none match
`$8D` at `$A5E8`, so each redirect byte's own compare pins it to bank
2. The 13 trampoline bytes at `$AFAD`-`$AFB9` are written into space
that reads `$FF` in bank 2 — banks 0, 3, 5, and 6 are `$FF` across that
entire padding region too, so the compare-locked patches harmlessly
touch unused padding there as well when those banks happen to be
active; banks 1 and 4 hold unrelated non-`$FF` data at every one of
those offsets, so the patch never fires for them. As with the other
`UpdateMode1Menu_Sub1` cheats, the jump into this trampoline only ever
happens from bank-2-only code, so what any other bank holds at `$AFAD`
is moot regardless.

**Not live-verified:** derived from reading `UpdateMode1Menu_Sub1`
(bank 2), `Link_BeHarmed` (bank 1), and `ItemIdToSlot`/
`ItemIdToDescriptor` (`src/Z_01.asm`), not from observing it in-game.

## Bomb and Candle secret entrances always revealed

**Code:** `AENAVTLP` + `AAEANYIA` (bombable walls) and `AAOEOYZZ` +
`AAUAONGA` (burnable trees)

**Effect:** Walk onto an overworld screen that hides a bombable staircase or a
burnable staircase and it opens by itself, complete with the "secret found"
jingle — no bomb, no candle, no hunting for the right spot.

**How it works:** Four one-byte patches in bank 4 (`src/Z_04.asm`), two per
secret type. The two routines are near-identical:

```
UpdateRockWall:
    ; If the secret in this room does not apply to the current quest,
    ; then return.
    JSR IsQuestSecretMismatch
    BCS @Exit

    ; If there is no detonating bomb (state $13) in slots $10 and $11,
    ; then return.
    LDY #$10
    LDA a:ObjState, Y
    CMP #$13
    BEQ @FoundBomb
    ...
@FoundBomb:
    STY $00
    ; If the tile object and weapon collide, then reveal the secret.
    JSR CheckTileObjWeaponCollision
    BEQ @Exit
    LDA #$24                    ; Black tile
    JSR RevealAndFlagSecretTileObj
```

`UpdateTree` is the same shape with `CMP #$22` (a standing fire) instead of
`CMP #$13`, and it reveals stair tiles (`$70`) via
`RevealAndFlagSecretStairsObj`. Both run every frame for as long as the tile
object exists in the room, and both end at `RevealSecretTileObj`, which swaps
the tiles, plays the secret-found tune, and sets the room's `$80` "secret
found" flag.

Each pair of patches removes the two things that normally have to be true:

- `AENAVTLP` changes `UpdateRockWall`'s `CMP #$13` operand at CPU `$8EF6`
  (originally `$13`) to `$00`, and `AAOEOYZZ` changes `UpdateTree`'s
  `CMP #$22` operand at CPU `$8F19` (originally `$22`) to `$00`. Weapon slot
  `$10` normally sits at state `$00` when it's empty, so the "is there a bomb
  / a flame here?" test now passes on an *empty* slot and the routine goes
  straight to `@FoundBomb` / `@FoundFire` with `Y = $10`.
- `AAEANYIA` changes the offset byte of `UpdateRockWall`'s
  `BEQ @Exit` after `JSR CheckTileObjWeaponCollision` at CPU `$8F07`
  (originally `$05`) to `$00`, and `AAUAONGA` does the same for
  `UpdateTree`'s at CPU `$8F31` (originally `$0C`). With offset `$00` the
  branch lands on the next instruction, so a failed collision test no longer
  aborts the reveal — which matters because the "weapon" is now an empty slot
  whose coordinates are meaningless.

Each compare byte pins its patch to that bank/offset; no other PRG bank holds
the same byte at any of the four addresses.

**Caveat — that's four codes.** Real Game Genie hardware only takes three at
once. The two pairs are independent: `AENAVTLP` + `AAEANYIA` alone gives you
the bomb secrets, `AAOEOYZZ` + `AAUAONGA` alone gives you the burn secrets.

**Caveat — quest gating still applies.** Neither patch touches
`IsQuestSecretMismatch`, so a secret that belongs to the other quest stays
hidden.

**Caveat — the tree patch also depends on an idle timer.** `UpdateTree` still
runs `LDA a:ObjTimer, Y / CMP #$02 / BCS` before the collision test. With
`Y = $10` pointing at an empty weapon slot that timer is normally `$00`, but
if something has left a value of 2 or more there the reveal waits until it
drains.

**Caveat — using a real bomb or candle can un-help you.** Once slot `$10`
actually holds something, its state is no longer `$00` and the patched test
falls through to the slot `$11` check, which is unpatched and still wants the
real state value.

**Not live-verified:** derived from reading `UpdateRockWall`, `UpdateTree`,
`RevealSecretTileObj`, and `CheckTileObjWeaponCollision` (`src/Z_04.asm`), not
from observing it in-game.

## Time moves only while a button is held

**Codes:** `XYUTNKEN` + `NYUVOGAX` + `ZAUVUKIA` + `OZUVKGSX` + `PAUVSGET`

Tags: `play-start`

**Effect:** When no button is held, the room freezes: Link, monsters and
weapons stop, and the music stops. Hold any button (a direction, A, B, Start
or Select) and the game runs at normal speed. Select no longer pauses.

The NES Game Genie holds only three codes, so this needs a patched ROM or two
stacked Game Genies.

**How it works:** The Select check in `UpdateMode5Play` (`src/Z_07.asm:1811`,
bank 7 CPU `$EC36`) toggles `Paused` when Select is pressed:

```asm
    LDA ButtonsPressed          ; A5 F8
    AND #$20                    ; 29 20
    BEQ @CheckPaused            ; F0 0D
    LDA Paused                  ; A5 E0
    EOR #$01                    ; 49 01
    STA Paused                  ; 85 E0
    BNE @CheckPaused            ; D0 05
    LDA #$0F
    STA ApuStatus_4015
```

Below it, `@CheckPaused` skips the whole world update when `Paused` is set.
The five codes change the first five instructions so that `Paused` is set from
the held buttons on every frame:

```asm
    LDA ButtonsDown             ; A5 FA   XYUTNKEN  $EC37:FA:F8
    AND #$FF                    ; 29 FF   NYUVOGAX  $EC39:FF:20
    BEQ $EC3E                   ; F0 02   ZAUVUKIA  $EC3B:02:0D
    LDA #$01                    ; A9 01   OZUVKGSX  $EC3C:A9:A5
                                ;         PAUVSGET  $EC3D:01:E0
$EC3E:
    EOR #$01                    ; 49 01
    STA Paused                  ; 85 E0
```

- No button held: `A` is 0, so the branch jumps into the `EOR` with `A` = 0.
  `Paused` becomes 1, and the frame is skipped.
- Any button held: the branch is not taken. `LDA #$01` then `EOR #$01` gives
  0. `Paused` becomes 0, and the world updates.

**Caveat — the music stops while time is stopped.** `DriveAudio`
(`src/Z_00.asm:105`) silences the channels and skips `DriveSong` while
`Paused` is set. The music starts again when you press a button.

**Caveat — the sound status register is written every moving frame.** When
`Paused` is 0, the old unpause path runs `LDA #$0F / STA ApuStatus_4015` on
every frame.

**Caveat — Start still opens the item menu.** Start is a button, so the world
runs on the frame Start goes down, and `@NotInMenu` opens the menu as usual.
The menu is checked before this code, so it is not frozen.

**Caveat — the involuntary pause still works normally.** `Paused = $02`, set
while hearts refill (`src/Z_05.asm:3027`), is tested before this check and is
unaffected.

**Caveat — compare bytes.** `$EC37`-`$EC3D` are in the `$C000`-`$FFFF` window,
which always maps bank 7 on this cart, so no other bank can match the compare
bytes.

**Live-verified** in fceumm, in a Level 9 room with monsters: with no buttons
for 120 frames, `Paused` stayed 1 and the monster positions (`$71`-`$73`,
`$85`-`$87`) did not change. From the same state with A held for 120 frames,
`Paused` was 0 and the monsters moved.

## Music and sound effects play a semitone higher, and rests play a low D

**Codes:** `LAEONGPA` + `ZAOOOGAA` + `LAXOSGPA` + `ZAUPNGAA` + `LAKPOGPA` +
`ZAKOKGAA`

Tags: `play-start` `interesting`

**Effect:** Almost every note of the music and the short tunes plays one
semitone higher. Rests are no longer silent: they play a low D. A few notes
come out silent or at a strange pitch instead. This needs 6 codes, which is
more than one Game Genie holds.

**How it works:** This is the Zelda version of the SMB1 code "Music and sound
effects play about a semitone higher, and rests play a low E". The notes in
`NotePeriodTable` (bank 0 CPU `$9F00`) are 2 bytes each and mostly go up a
semitone at a time, starting with the rest (`$00 $00`) at offset 8 and D3 at
offset `$0A`. Each of the three note routines reads the table twice
(`src/Z_00.asm`):

```
EmitSquareNote0:
    TAY
    LDA NotePeriodTable+1, Y
    BEQ Exit
    ...
    LDA NotePeriodTable, Y
```

`EmitSquareNote1` and `EmitTriangleNote` are the same. These codes add 2 to all
six table operands, so every note reads the next entry:

- `EmitSquareNote0`: `$9C0F:03:01` and `$9C19:02:00`.
- `EmitSquareNote1`: `$9C2D:03:01` and `$9C37:02:00`.
- `EmitTriangleNote`: `$9C41:03:01` and `$9C4C:02:00`.

The `BEQ Exit` test, which skips a rest, now sees the low byte of D3, so rests
play D3 instead.

**Evidence:** `ext/original.nes` has `B9 01 9F` at `$9C0E`, `$9C2C` and
`$9C40`, and `B9 00 9F` at `$9C18`, `$9C36` and `$9C4B`. `nes_gg.py` finds no
other bank with these bytes at these addresses, except `ZAKOKGAA`: bank 1 also
has `$00` at `$9C4C`. There it is a byte of `DemoBackgroundPatterns`, the
title-screen tiles that `TransferDemoPatterns` copies to CHR RAM. With this
code active, one row of one of those tiles gets a stray pixel.

**Caveat — the table is not fully in order.** Offsets `$00`-`$06` and
`$42`-`$4E` are not in pitch order, so notes there (for example F#5, offset
`$06`, which now reads the rest and plays nothing) move by more than a
semitone. Notes near the end of the table read the next routine's code bytes.

**Caveat — 3-code version not possible.** All six operands must move together.
Moving only the low-byte reads mixes each note's high byte with the next
note's low byte, which scrambles the pitch instead of shifting it.

**Not tested:** derived from reading `NotePeriodTable` and the three
`Emit...Note` routines, not from hearing it in-game.

## Monsters shoot magic rod shots and hurt each other

**Codes:** `AEOATOGI` + `EUOEGPEY` + `SUKAGPSP` + `EXOUGPKZ` + `TEOUIOPS` + `EESAGPAP` + `SOXLLOOO` + `ENXLGOKZ` + `GEXLIPAA` (use all nine)

Tags: `demo-ready` `long` `video-ready` `play-start`

**Effect:** The same monsters as "Most walking monsters shoot arrows" shoot
the magic wave from Link's Magic Rod, each time they turn to face Link. It
hurts monsters, not Link. Moblins and Lynels make only a brief ghost shot.
There is only
one shot at a time; Link's sword beam must wait for
it.

**How it works:** This is "Monsters shoot Link's arrows without hurting themselves" with slot `$0E`
(sword shot or magic shot) instead of `$12`:
`LDY #$0E` (`$B19C:A0:A4`, `$B19D:0E:59`). `UpdateSwordShotOrMagicShot` (`src/Z_07.asm`) tells the two
apart by the state's high bit; the rod sets state `$80`:

```
@MakeMagicShot:
    ...
    ; Activate the shot object (state $80).
    LDA #$80
```

The hook sets the shot's state with `LDA #$10` / `STA a:ObjState, Y`, so
`EESAGPAP` makes it `LDA #$80` (`$81D4:80:10`). The hook's q-speed `$A0` is
the same as the rod's. The last three codes are the fix from "Monsters shoot
Link's arrows without hurting themselves": `Shoot` gives the shooter 32
frames of invincibility instead of setting the shot's state
(`$B1A3:9D:99` + `$B1A4:F0:AC` + `$B1A5:04:00`), so the shooter can't hit
itself.

**Evidence:** `ext/original.nes` bank 4 has `A9 10 99 AC 00` at CPU `$81D3`.
`nes_gg.py` finds no other bank with the same bytes at any of the nine
addresses. A headless Mesen2 run of the nine codes, on the screen above the
start, showed Octoroks shooting magic waves that killed other Octoroks.

**Caveat — the caveats of "Monsters shoot Link's arrows without hurting themselves" apply.** Zols and
Vires may split oddly, and Moblins, Lynels, Octorok rocks and Wizzrobes only
make a brief ghost of their own shot (see "Monsters shoot Link's arrows
without hurting themselves").

**Caveat — the book.** With the book, a magic shot that hits a wall leaves
fire, as Link's does.

**Not tested:** derived from reading `Shoot`, `UpdateSwordShotOrMagicShot`
and the rod's shot code, not from observing it in-game.

## Monsters shoot magic rod shots from Link's position

**Codes:** `AEOATOGI` + `EUOEGPEY` + `SUKAGPSP` + `EXOUGPKZ` + `TEOUIOPS` + `EESAGPAP` + `SXULAPSL` + `SXULIPSL` (use all eight)

Tags: `interesting` `demo-ready` `video-ready` `play-start`

**Effect:** Like "Monsters shoot magic rod shots and hurt each other", but the shot starts where
Link is and flies the way the shooting monster faces.

**How it works:** "Monsters shoot magic rod shots and hurt each other"
without its three invincibility codes, plus two codes that make `Shoot` take the shot's position from Link (slot 0)
instead of the shooter:

```
    LDA ObjX, X                 ; B5 70 -> A5 70 (LDA ObjX, Link's X)
    STA a:ObjX, Y
    LDA ObjY, X                 ; B5 84 -> A5 84 (LDA ObjY, Link's Y)
    STA a:ObjY, Y
```

`SXULAPSL` + `SXULIPSL` (`$B1B0:A5:B5`, `$B1B5:A5:B5`). The zero-page form
reads slot 0, which is Link. The invincibility codes are left out, since the
shot doesn't start on the shooter.

**Evidence:** The same bytes as "Monsters shoot magic rod shots and hurt
each other". `ext/original.nes` bank 4 has `B5 70 99 70 00 B5 84 99 84 00`
at CPU `$B1B0`. `nes_gg.py` finds no other bank with `$B5` at `$B1B0` or
`$B1B5`. A headless Mesen2 run showed the shots start at Link.

**Caveat — the caveats of "Monsters shoot magic rod shots and hurt each other" apply.**

**Not tested:** derived from reading `Shoot`, not from observing it in-game.

## Monsters throw candle fire

**Codes:** `AEOATOGI` + `EUOEGPEY` + `SUKAGPSP` + `EXOUGPKZ` + `POOUIOPI` + `PXSAGPAP` + `SOXLLOOO` + `ENXLGOKZ` + `GEXLIPAA` (use all nine)

Tags: `play-start` `demo-ready` `video-ready`

**Effect:** The same monsters as "Most walking monsters shoot arrows" throw
candle fire each time they turn to face Link. The fire moves a tile ahead,
then burns in place for about a second. It hurts monsters, and it hurts Link
too, as Link's own fire does. In dark dungeon rooms it lights the room.

**How it works:** This is "Monsters shoot Link's arrows without hurting themselves" with slot `$11`
(Link's second bomb or fire slot) instead of `$12`: `LDY #$11` (`$B19C:A0:A4`,
`$B19D:11:59`). `UpdateBombOrFire` treats state `$2x` as fire, and
`UpdateFire` moves state `$21` (walking fire) `$10` pixels, then stands it
for `$3F` frames:

```
UpdateFire:
    ; If this is not a walking fire (state $21), skip moving it.
    LDA ObjState, X
    CMP #$21
```

`PXSAGPAP` makes the hook's shot state `$21` (`$81D4:21:10`). The last
three codes give the shooter 32 frames of invincibility from `Shoot`, as in
"Monsters shoot Link's arrows without hurting themselves".

**Evidence:** The same bytes as "Monsters shoot Link's arrows without hurting themselves" and
"Monsters shoot magic rod shots and hurt each other". `nes_gg.py` finds no other bank with the
same bytes at any of the nine addresses. A headless Mesen2 run of the nine codes, on
the screen above the start, showed the fire walk and then stand.

**Caveat — the shooter can still walk into its own fire** after its 32
frames are up, since the fire stands for about a second.

**Caveat — Link can't use a second fire or bomb while a monster's fire
burns.**

**Caveat — the caveats of "Monsters shoot Link's arrows without hurting
themselves" apply.** Zols and Vires may split oddly, and Moblins, Lynels,
Octorok rocks and Wizzrobes only make a brief ghost of their own shot.

**Not tested:** derived from reading `Shoot`, `UpdateBombOrFire` and
`UpdateFire`, not from observing it in-game.

## Monsters throw candle fire from Link's position

**Codes:** `AEOATOGI` + `EUOEGPEY` + `SUKAGPSP` + `EXOUGPKZ` + `POOUIOPI` + `PXSAGPAP` + `SXULAPSL` + `SXULIPSL` (use all eight)

Tags: `interesting` `play-start`

**Effect:** Like "Monsters throw candle fire", but the fire starts where Link
is and moves the way the throwing monster faces. The fire hurts Link, so
this is mostly a way to get Link burned.

**How it works:** "Monsters throw candle fire" without its three
invincibility codes, plus the two position codes from "Monsters shoot magic
rod shots from Link's position" (`SXULAPSL` + `SXULIPSL`, `$B1B0:A5:B5`,
`$B1B5:A5:B5`).

**Evidence:** The same bytes as those two entries. A headless Mesen2 run of
the eight codes burned Link until the game was over.

**Caveat — the caveats of "Monsters throw candle fire" apply.**

**Not tested:** derived from reading `Shoot` and `UpdateFire`, not from
observing it in-game.

## Monsters shoot Link's arrows without hurting themselves

**Codes:** `AEOATOGI` + `EUOEGPEY` + `SUKAGPSP` + `EXOUGPKZ` + `ZOOUIOPI` + `SOXLLOOO` + `ENXLGOKZ` + `GEXLIPAA` (use all eight)

**Effect:** The same monsters as "Most walking monsters shoot arrows" shoot
Link's own arrow instead of a Moblin arrow, each time they turn to face Link.
Link's arrow hurts monsters, so monsters can shoot each other. It doesn't
hurt Link. The shooter can't be hurt for about half a second after each
shot, so its own arrow flies away without hitting it. There is only one Link
arrow at a time, so a new shot takes the arrow away from wherever it was,
Link's own arrow too. Moblins, Lynels and Octorok rocks no longer shoot
anything (see the caveats).

**How it works:** Link's weapons each have a fixed object slot: `$12` is the
arrow (or rod), `$0E` the sword shot or magic shot, and `$10`/`$11` the bombs
or fire. `CheckMonsterCollisions` (`src/Z_01.asm`) checks every monster
against these slots:

```
    LDY #$10
    JSR CheckMonsterBombOrFireCollision
    LDY #$11
    JSR CheckMonsterBombOrFireCollision
    LDY #$0D
    JSR CheckMonsterSwordCollision
    LDY #$12
    JSR CheckMonsterArrowOrRodCollision
```

and `UpdateRodOrArrow` (`src/Z_07.asm`) moves slot `$12` as an arrow when its
state is `$1x`. So the codes make `Shoot` (`src/Z_04.asm`, used for every
monster shot) put the shot's direction and position in slot `$12` instead of
a free monster slot:

- `AEOATOGI` + `EUOEGPEY` + `SUKAGPSP`: the hook from "Most walking monsters
  shoot arrows", with shot type `$00` instead of `$5B` (`$8196:00:5C`,
  `$819C:B0:F0`, `$81C4:B5:95`). Type `$00` is below `$53`, so `ShootLimited`
  doesn't count it as a monster shot. (The count only goes down when a
  monster shot object is destroyed, and this one never is.) `Shoot` still
  calls `SetTypeAndClearObject` on the free monster slot, but with type
  `$00`, so that slot stays empty. The end of the hook sets the shot's state
  to `$10` (arrow flying) and q-speed `$A0` (2.5 pixels a frame), which the
  arrow needs to move.
- `EXOUGPKZ` + `ZOOUIOPI`: `LDY EmptyMonsterSlot` becomes `LDY #$12`
  (`$B19C:A0:A4`, `$B19D:12:59`).
- `SOXLLOOO` + `ENXLGOKZ` + `GEXLIPAA`: the shooter's invincibility, below.

The arrow starts on top of the shooter, and Link's arrow hurts any monster
it touches, so the shooter needs to be invincible for a moment. Making only
the walking-monster hook do this isn't enough. Octoroks also shoot
through their own `_TryShooting`, which runs right after
`Wanderer_TargetPlayer`. When the hook can't fire (the Octorok's `ObjTimer`
isn't 0), the "wants to shoot" flag stays set. `_TryShooting` then counts its
shoot timer down and calls `Shoot` while the Octorok stands still. That arrow
gets no invincibility, so it hits the Octorok at once.

So the invincibility goes into `Shoot`, and every shot gives it:

```
Shoot:
    ...
    LDY EmptyMonsterSlot        ; now LDY #$12
    LDX CurObjIndex
    LDA #$10
    STA a:ObjState, Y           ; 99 AC 00 -> 9D F0 04 (STA ObjInvincibilityTimer, X)
    LDA #$00
    STA a:ObjTimer, Y
```

The shooter gets invincibility `$10`, which `DecrementInvincibilityTimer`
counts down every other frame, so 32 frames. `Shoot` no longer sets the
shot's state. The walking-monster hook sets it to `$10` (arrow flying) itself
afterward (`LDA #$10` / `STA a:ObjState, Y` at `$81D3`), so its arrows still
fly. Shots from `_TryShooting` (Octoroks when the hook can't fire, Moblins,
Lynels) and from Wizzrobes don't change slot `$12`'s state, so they make no
arrow. Their own shot type goes into a free monster slot in state 0, which
runs `BounceShot`: a brief ghost that bounces and disappears.

Raw form of the invincibility codes: `$B1A3:9D:99` + `$B1A4:F0:AC` +
`$B1A5:04:00`.

**Evidence:** `ext/original.nes` bank 4 has `A6 59 A5 00 20 B3 FE A4 59 AE 40
03 A9 10 99 AC 00 A9 00 99 28 00` at CPU `$B195` (`Shoot`). `nes_gg.py` finds no other bank with the same bytes at
any of the eight addresses. A headless Mesen2 run of the eight codes, on the
screen above the start, showed Octoroks shooting arrows that killed other
Octoroks.

**Caveat — Moblins and Lynels don't shoot.** They are below type `$05`, so the
hook skips them, and their own shots now make no arrow, only a brief ghost (see above). They still become
invincible for 32 frames each time they try.

**Caveat — Octorok rocks are gone.** Octoroks shoot only through the hook.

**Caveat — Zols and Vires.** `CreateChildGel` and Vire's split also use
`Shoot`. The Gel or Keese goes into a free monster slot, but its position and
direction go to Link's weapon slot, so it may appear where an old object was.
Not checked in-game.

**Caveat — the shooter is safe for 32 frames after each shot.** Link can't
hurt it then, and it can't hurt Link by touching him.

**Caveat — the hook's other caveats apply.** Throwers' timers are reset and
Goriyas don't pause after throwing (see "Most walking monsters shoot
arrows"). Goriyas lose track of their boomerang.

**Caveat — arrow damage and color come from Link's arrow item.** With no
arrow item, the arrow does silver-arrow damage and may use an odd palette.

**Caveat — same bytes as the other walking-monster codes.** Use only one of
them.

**Not tested:** derived from reading `Shoot`, `_TryShooting`,
`UpdateOctorock` and `CheckMonsterCollisions`, not from observing it in-game.

## Monsters shoot magic rod shots, injuring themselves

**Codes:** `AEOATOGI` + `EUOEGPEY` + `SUKAGPSP` + `EXOUGPKZ` + `TEOUIOPS` + `EESAGPAP` (use all six)

**Effect:** The same monsters as "Most walking monsters shoot arrows" shoot
the magic wave from Link's Magic Rod each time they turn to face Link. The
wave starts on top of the shooter, so it nearly always hits the monster that
shot it. It hurts other monsters it reaches, and it doesn't hurt Link.

**How it works:** This is "Monsters shoot magic rod shots and hurt each other" with three codes
left out:

- The three `Shoot` invincibility codes, so the shooter is hit by its own
  shot.

The rest is the same: `AEOATOGI` + `EUOEGPEY` + `SUKAGPSP` are the
walking-monster hook with shot type `$00`, and `EESAGPAP` makes the hook set
the shot's state to `$80` (magic shot, `$81D4:80:10`).
`CheckMonsterCollisions` checks every monster against slot `$0E`, so the
shot hurts monsters.

Moblins and Lynels need no codes of their own. They shoot through `Shoot`
too, so the same change sends their shots to slot `$0E` with state `$10`,
which is Link's sword beam.

**Evidence:** The same bytes as "Monsters shoot magic rod shots and hurt each other".
`nes_gg.py` finds no other bank with the same bytes at any of the six
addresses. A headless Mesen2 run of the six codes, on the screen above the
start, showed all four Octoroks die where they stood while Link was far
away.

**Caveat — Moblin and Lynel shots.** Without the `LDX` codes, their shot type
(`$5B` arrow, `$57` sword) still goes into a free monster slot, cleared to
state 0. A monster shot in state 0 runs `BounceShot`, so it may show briefly
at an old position, bounce, and disappear. Their real shot is Link's sword
beam in slot `$0E`. Not checked in-game.

**Caveat — the other caveats of "Monsters shoot Link's arrows without
hurting themselves" apply.** Zols and Vires may split oddly, and only one shot can be
out at a time.

**Caveat — same bytes as the other walking-monster codes.** Use only one of
them.

**Not tested by the user.**
