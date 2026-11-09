# The Legend of Zelda (NES) Rev 0 — Game Genie Codes

These codes are tested only on Rev 0, the original release. If your game
includes a message to "hold in reset button as you turn power off" on the
continue screen, it is Rev 1 (a re-release) and these codes may not work.

## Start a new game without entering a name

**Code:** `AEUXISET`

**Effect:** On the file-select screen, the cursor can stop on an empty save
slot instead of auto-skipping it. Move the cursor to any blank slot and press
Start — the game begins immediately with a blank name, no trip through
"REGISTER YOUR NAME" required.

**How it works:** Vanilla code (`src/Z_02.asm`, in `UpdateMode1Menu_Sub0`)
skips inactive slots whenever the cursor moves:

```
LDA IsSaveSlotActive, Y
BEQ @ChangeSelection   ; if slot isn't active, keep advancing past it
```

This patches the branch's offset byte at CPU address `$A5BD` (originally
`$E8`) to `$00`, which makes the branch always land on the very next
instruction — i.e. it never actually skips a slot anymore, active or not.
One-byte patch; the code's compare byte (`E8`) targets that specific
bank/offset so it doesn't misfire against unrelated code sharing the same
switchable ROM window.

## Fastest possible NPC text

**Code:** `AAOESATA`

Tags: `demo-ready` `utility` `play-start` `curated`

**Effect:** Dialogue from overworld/cave NPCs (old men, shopkeepers, etc.)
prints as fast as the engine can draw it — one character per frame instead
of one every 6 frames.

**How it works:** Vanilla code (`src/Z_01.asm`, in `UpdatePersonState_Textbox`)
waits 6 frames between characters:

```
LDA #$06
STA ObjTimer+1   ; wait 6 frames after the next character is shown
```

This patches the immediate operand at CPU address `$881D` (originally `$06`)
to `$00`, so the wait timer is already expired by the time the next frame's
check runs, and a new character is emitted every frame. One-byte patch;
the code's compare byte (`06`) targets that specific bank/offset so it
doesn't misfire against unrelated code sharing the same switchable ROM
window.

## Slow Octoroks (and Ghinis) spawn moving much faster

**Code:** `EASATYAZ`

**Effect:** Regular (non-flying) Ghinis charge around the overworld at 4x
normal speed, permanently. The slower AI variant of both Red and Blue
Octoroks only gets the fast speed for an instant right as it finishes
spawning — for the rest of its life it moves at its normal, unpatched
speed. See the caveat below for why Octoroks don't stay fast.

**How it works:** Vanilla code (`src/Z_04.asm`) sets each monster's
per-frame movement speed (`ObjQSpeedFrac`) once, when the object spawns:

```
InitSlowOctorockOrGhini:
    ; Assign QSpeed $20 (0.5 pixels a frame).
    LDA #$20
    BNE :+
```

`InitSlowOctorockOrGhini` is used by the slower AI variant of both Red and
Blue Octoroks (object types `$07`/`$09`) — and also by regular ground Ghinis
(type `$1F`), which is why they speed up too.

This patches the immediate operand at CPU address `$8756` (originally
`$20`) to `$80`, bumping that speed from 0.5 to 2.0 pixels/frame. One-byte
patch; the code's compare byte (`20`) targets that specific bank/offset so
it doesn't misfire against unrelated code sharing the same switchable ROM
window.

**Caveat — Octoroks only:** unlike Ghini, `UpdateOctorock` calls a shared
helper (`_TryShooting`, also in `src/Z_04.asm`) every single frame to manage
its rock-throwing cooldown, and that helper unconditionally overwrites the
same `ObjQSpeedFrac` field with either `0` (while winding up to shoot) or
the rock projectile's own speed constant (`$20` for this slow variant) —
not the value this patch set at spawn. Movement for the frame already
happened before `_TryShooting` runs, so the patched speed is visible for
one instant right after the spawn cloud clears, then the Octorok settles
back to its normal, unpatched pace for good. Ghini never calls
`_TryShooting` (it doesn't throw anything), so its speed boost has no such
override and lasts for its whole lifetime.

## Fast Octoroks spawn moving much faster

**Code:** `EGSEZYAL`

**Effect:** The faster AI variant of both Red and Blue Octoroks only gets
the fast speed for an instant right as it finishes spawning. For the rest
of its life it settles to a smaller, incidental speed bump (0.75 to 1.0
pixels/frame) rather than the patched value — see the caveat below.

**How it works:** Vanilla code (`src/Z_04.asm`) sets each monster's
per-frame movement speed (`ObjQSpeedFrac`) once, when the object spawns:

```
InitFastOctorock:
    ; Assign QSpeed $30 (0.75 pixels a frame).
    LDA #$30
:
    STA ObjQSpeedFrac, X
```

`InitFastOctorock` is used only by the faster AI variant of both colors
(object types `$08`/`$0A`) — no other monster type shares it.

This patches the immediate operand at CPU address `$875A` (originally
`$30`) to `$C0`, bumping that speed from 0.75 to 3.0 pixels/frame (matching
the speed already used elsewhere in the engine for monster-shot
projectiles, so it's a value the movement code is known to handle safely).
One-byte patch; the code's compare byte (`30`) targets that specific
bank/offset so it doesn't misfire against unrelated code sharing the same
switchable ROM window.

**Caveat:** `UpdateOctorock` calls a shared helper (`_TryShooting`, also in
`src/Z_04.asm`) every single frame to manage its rock-throwing cooldown,
and that helper unconditionally overwrites the same `ObjQSpeedFrac` field
with either `0` (while winding up to shoot) or the rock projectile's own
speed constant — `$40` for this fast variant (the shot speed doubles for
the fast AI) — not the value this patch set at spawn. Movement for the
frame already happened before `_TryShooting` runs, so the patched speed
($C0$) is visible for one instant right after the spawn cloud clears, then
the Octorok settles to `$40` (1.0 pixels/frame) for the rest of its life —
faster than its original `$30`, but nowhere near the patched value.

## Octoroks move much faster after shooting

**Code:** `ATOAOGAZ`

Tags: `play-start`

**Effect:** All Octoroks (red and blue, both slow and fast AI variants)
settle into a sustained ~3x-4x normal movement speed — usually within a
few seconds of spawning. Unlike the two codes above, this speed increase
doesn't fade: it works *with* the mechanism that was undoing them, instead
of getting undone by it.

**How it works:** As described in the caveats above, `UpdateOctorock`
(`src/Z_04.asm`) loads a "speed" value and hands it to `_TryShooting`,
which stores it into `ObjQSpeedFrac, X` once the Octorok finishes (or
skips) its shot-preparation cycle — this is the exact write that made the
previous two codes' spawn-time speed boosts fade:

```
; If the octorock is slow, then use q-speed $20.
; Else double it.
LDA #$20
LDY ObjType, X
CPY #$07
BEQ @Shoot
CPY #$09
BEQ @Shoot
ASL

@Shoot:
    ; Shoot a flying rock (object type $53).
    LDY #$53
    JSR _TryShooting
```

This patches the immediate operand at CPU address `$8C11` (originally
`$20`) to `$60`. The slower AI variant (which skips the `ASL`) now gets
1.5 pixels/frame instead of 0.5; the faster AI variant (which doubles it)
gets 3.0 pixels/frame instead of 0.75 — the same `$C0` value used by the
spawn-time fast-Octorok patch above, so it's a speed the movement code is
already known to handle safely. One-byte patch; the code's compare byte
(`20`) targets that specific bank/offset so it doesn't misfire against
unrelated code sharing the same switchable ROM window.

Blue Octoroks always attempt to shoot every frame (object types `$09`/
`$0A` are exempted from `_TryShooting`'s random chance-to-shoot check), so
they pick up the new speed almost immediately after spawning. Red
Octoroks only roll a small chance (about 3% per frame) to start a shot
cycle while idle, so they can take a few seconds to speed up — but once
they've fired their first shot, `_TryShooting` locks in the new speed and
it holds until their next shot cycle, during which movement briefly
pauses (same as in vanilla). Verified live: after ~5 seconds in a room of
four slow (red) Octoroks, all four had settled at the patched 1.5
pixels/frame and stayed there, pausing only during their periodic shot
windups.

This code can be combined with either of the two spawn-time codes above
for both an instant burst on spawn *and* a durable fast speed afterward.

## Shield blocks projectiles regardless of which way Link is facing

**Code:** `AEEUYUZP`

Tags: `demo-ready` `play-start` `shield-collection` `curated`

**Effect:** Normally, Link's shield only parries a monster's shot (flying
rock, arrow, boomerang, magic wand blast, etc.) if he's facing directly
opposite the shot's travel direction. This code removes that facing
requirement — any shot that would normally be parried when Link faces it
now gets parried no matter which way he's facing, as long as the other
parry conditions still hold (right shot type, or the magic shield for the
shots that require it).

**How it works:** `CheckLinkCollision` (`src/Z_01.asm`) is bank-1 code that
runs from a fixed RAM copy at `$6C90`-`$7EFF` (its `BANK_01_CODE` segment
is loaded from ROM but relocated to RAM at startup, so it can be called
from any bank regardless of which ROM bank is currently switched in).
After confirming a monster shot has hit Link's hitbox, it checks whether
Link and the shot are facing opposite directions before deciding whether
to parry:

```
    ; If Link and the shot are not facing opposite directions,
    ; then go harm Link.
    ;
    ; Note the bitwise AND in the test. It picks out one direction
    ; component of a monster that can move diagonally.
    LDA ObjDir
    ORA ObjDir, X
    AND #$0C
    CMP #$0C
    BEQ @FacingOpposite
    LDA ObjDir
    ORA ObjDir, X
    AND #$03
    CMP #$03
    BNE HarmLink

@FacingOpposite:
    ; Link and the shot are facing opposite directions.
    ; Link can parry certain weapons/shots.
```

This patches the branch offset byte of `BNE HarmLink` — at CPU address
`$B38F` in bank 1's ROM window (originally `$1A`, a +26 offset) — to `$00`,
the same "make the branch land on the very next instruction" trick used by
the very first code in this document. Whether or not the horizontal-facing
comparison sets the zero flag, the branch (taken or not) now lands on
`@FacingOpposite`, so the routine always treats Link as if he were facing
the shot. The vertical-facing check above it (`BEQ @FacingOpposite`) is
untouched and still short-circuits the same way; it's the second,
horizontal check that no longer has a path to `HarmLink`. One-byte patch;
the code's compare byte (`1A`) targets that specific bank/offset so it
doesn't misfire against unrelated code sharing the same switchable ROM
window. Note that because this routine executes from its RAM copy, the
patched byte only takes effect after the RAM copy is made (at startup),
which is when the game is normally already running — this isn't a
practical limitation, just a detail of how the patch propagates.

**Not live-verified:** confirmed via the emulator that the patched byte
($00) is present in the RAM copy of the routine that actually executes at
runtime, but the in-game parry behavior itself (getting hit by a shot from
an off-angle with the shield up) has not yet been observed.

## Shield blocks projectiles even while Link is striking

**Code:** `AANULUTZ`

Tags: `demo-ready` `play-start` `shield-collection` `curated`

**Effect:** Normally, the instant Link raises his sword, item, or anything
else that puts him in a non-idle "using something" state, his shield stops
being able to parry monster shots — even if he's otherwise facing the shot
correctly. This code removes that restriction, so the shield can parry a
shot at any time, including mid-swing.

**How it works:** `CheckLinkCollision` (`src/Z_01.asm`), the same bank-1
routine described in the code above (it runs from its RAM copy at
`$6C90`-`$7EFF`), gates the whole parry path behind Link's own state before
it ever checks facing direction:

```
    ; If object type = Fireball2 ($56) or $5A, or Link is not idle;
    ; then go harm Link.
    CMP #$56
    BEQ HarmLink
    CMP #$5A
    BEQ HarmLink
    LDA ObjState
    AND #$F0
    BNE HarmLink

    ; If Link and the shot are not facing opposite directions,
    ; then go harm Link.
```

`ObjState`'s high nibble is `$10` whenever Link is "wielding sword/item"
(set by `PlaceWeaponForPlayerState` in the same file, comment: "Set
player's state to $10 (wielding sword/item)") — i.e. mid-swing or mid-item
-use — and nonzero there means not idle. `AND #$F0` isolates that nibble,
and the `BNE HarmLink` sends any shot straight to damaging Link whenever
he's not idle, before facing or shield are ever considered.

This patches the branch offset byte of that `BNE HarmLink` — at CPU
address `$B37B` in bank 1's ROM window (originally `$2E`, a +46 offset) —
to `$00`, the same "make the branch land on the very next instruction"
trick used by the two codes above. Whether Link is idle or not, execution
now always falls through to the facing-direction check that follows,
instead of shortcutting straight to `HarmLink`. One-byte patch; the code's
compare byte (`2E`) targets that specific bank/offset so it doesn't
misfire against unrelated code sharing the same switchable ROM window.

This code is independent of the "blocked regardless of facing" code above
— facing still matters here unless that code is also applied. Combine both
for a shield that blocks any parryable shot, from any facing direction, at
any time.

**Not live-verified:** derived from reading the routine, not from
observing it in-game.

## Touching almost anything spawns a ghost

**Code:** `YAUXZZLA`

Tags: `play-start`

Based on a code from Zelda Xtreme.

**Effect:** Originally a 6-letter Zelda Xtreme code (`PPLXZZ`, "When touching
walls, a ghost will appear"). Walking into a tile while grid-aligned spawns
a Flying Ghini in the square Link is facing, fading in the way monsters
normally do. This reuses a real vanilla mechanic — some gravestone and
Armos tiles are secretly "passive tile objects" that spawn a monster when
Link pushes into them — and simply widens which tiles count as a trap,
rather than corrupting the routine's control flow.

**How it works:** `CheckPassiveTileObjects` (`src/Z_01.asm`) runs every
frame Link is grid-aligned and pressing a direction. It loops over 8 tile
IDs (`$BC`-`$C3`, the gravestone/Armos squares) looking for a match against
the tile Link just collided with, then computes a spawn square from Link's
position and facing, and spawns an Armos or a Flying Ghini depending on
which of the 8 tiles matched:

```
CheckPassiveTileObjects:
    ...
    LDA #$BB
    STA $02                     ; [02] holds the collided tile.
    LDX #$08
    LDA ObjCollidedTile

@NextTile:
    INC $02
    DEX
    BPL @TestTile

@ReturnX0:
    LDX #$00
    RTS

@TestTile:
    CMP $02
    BNE @NextTile

    ; We'll be computing the location of the square.
    ; Start with Link's location.
    LDA ObjX
    STA $00                     ; [00] holds X coordinate
    LDA ObjY
    STA $01                     ; [01] holds Y coordinate
    ...
@ChooseObjType:
    LDA #$1E                    ; Armos
    LDY $02                     ; [02] collided tile
    CPY #$C0
    BCS :+                      ; If tile >= $C0, then instantiate an armos.
    LDA #$22                    ; Flying Ghini
:
    STA ObjType, X
```

This patches the branch operand of `BPL @TestTile` at CPU address `$A23A`
(originally `$03`, a +3 offset) to `$07` (+7). The new target lands exactly
on `LDA ObjX` — the start of the legitimate "compute the spawn square" code
— skipping only the 4-byte tile-match check (`CMP $02` / `BNE @NextTile`).
Everything downstream still runs for real: the spawn coordinates are
computed from Link's actual position and facing direction, the routine
still checks for an already-fading duplicate at that spot, and it still
calls `FindEmptyMonsterSlot` to find a genuine free slot. Because `X`
starts at 8, the `BPL` branch is taken on the very first pass through the
loop — after exactly one `INC $02` — so `[02]` is always `$BC`, the first
tile in the gravestone/Armos range. `$BC` is below `$C0`, so
`@ChooseObjType` always falls through to `LDA #$22 ; Flying Ghini`. That's
the ghost. One-byte patch; the code's compare byte (`03`) targets that
specific bank/offset so it doesn't misfire against unrelated code sharing
the same switchable ROM window.

**Why not the more literal conversion of the 6-letter code:** patching
`BPL @TestTile`'s offset to `$11` (+17) instead — matching a more direct
translation of the "always take the branch on the first pass" idea — lands
mid-instruction, in the middle of the same coordinate-setup block, skipping
it entirely along with the tile-match check. The ghost then spawns using
whatever stale values happened to be left in `$00`/`$01` rather than a
position derived from Link. `$07` gets the same "any tile is a trap" effect
while leaving the rest of the routine's real logic intact.

**Why the original 6-letter code needed fixing:** Zelda Xtreme's `PPLXZZ`
has no compare byte, so it patches CPU address `$A23A` in *every* bank,
not just the one with `CheckPassiveTileObjects`. In this build, that same
address also falls inside unrelated code in other banks — for example
bank 4, where it lands on the opcode of `STA ObjInvincibilityTimer, X` in
the Manhandla boss fight, corrupting it into a different instruction
whenever that bank happens to be active. Pinning the patch to bank 1's
original byte (`$03`) via the compare byte fixes that.

**Not live-verified:** the Flying-Ghini effect above is derived from
reading the routine, not from observing it in-game.

## Walls turn into Armos enemies on contact

**Code:** `IZUZZXAA`

Tags: `play-start`

Based on a code from Zelda Xtreme.

**Effect:** Originally a 6-letter Zelda Xtreme code (`IZLZZZ`, "Walls turn
into Armos enemies upon contact"). Widens the same passive-tile-object trap
described above to cover many more tile IDs — mostly ones that resolve to
Armos rather than Flying Ghini — so walking into a much wider variety of
wall tiles triggers an Armos spawn. Unlike the ghost code above, this one
needs no branch trickery at all: it's a straight, legitimate extension of
the vanilla loop bound.

**How it works:** `CheckPassiveTileObjects` (`src/Z_01.asm`) sets up its
tile-match loop like this:

```
    LDA #$BB
    STA $02                     ; [02] holds the collided tile.
    LDX #$08
    LDA ObjCollidedTile

@NextTile:
    INC $02
    DEX
    BPL @TestTile
```

`X` is the loop's trip count: starting it at `$08` makes the loop test 8
tile IDs, `$BC` through `$C3`, against `ObjCollidedTile`. `@ChooseObjType`
later spawns an Armos for any matched tile `>= $C0` and a Flying Ghini
otherwise — so normally only 4 of those 8 tiles ($C0-$C3) yield an Armos.

This patches the immediate operand of `LDX #$08` at CPU address `$A232`
(originally `$08`) to `$25` (37), extending the loop to test 37 tile IDs,
`$BC` through `$E0`. Only the first 4 (`$BC`-`$BF`) are still below `$C0`
and yield a Ghini; the other 33 (`$C0`-`$E0`) yield an Armos. Every other
instruction in the routine — the compare, the coordinate setup, the
duplicate check, the empty-slot search — runs completely unmodified. This
is not a control-flow exploit like the ghost code above; it's the same
technique the game already uses to distinguish gravestone tiles from Armos
tiles, just pointed at a much bigger tile-ID range. One-byte patch; the
code's compare byte (`08`) targets that specific bank/offset so it doesn't
misfire against unrelated code sharing the same switchable ROM window —
for example, bank 2 has `LDA #$2F` at this address (part of an unrelated
wraparound calculation) and bank 4 has `STA ObjDir, X` (part of Manhandla's
boss fight), both of which the 6-letter code without a compare byte would
silently corrupt whenever that bank was active.

**Not live-verified:** whether this reliably reads as "walls" depends on
which tile IDs the game's various wall/obstacle graphics actually use
within `$C4`-`$E0` — derived from reading the routine and the ROM's tile
data, not from observing it in-game.

## Sword hits every enemy on the screen

**Codes:** `AAVLLGGY` + `AEKULSOG`

Tags: `demo-ready` `play-start` `curated`

**Effect:** Swinging the sword damages *every* monster currently on the
screen, no matter where they are — Link doesn't have to be anywhere near
them, or facing them. Each enemy is hit once per swing and gets knocked
back exactly as if the blade had actually connected. Also affects the
boomerang, arrows, the Magical Rod, and the sword beam, all of which hit
everything on screen while they're active.

**How it works:** Two one-byte patches, both in bank 1 (`src/Z_01.asm`).

`CheckMonsterCollisions` runs once per active monster slot per frame and
tries each of Link's weapons against that monster. Every slender weapon
(sword, boomerang, arrow, rod, sword/magic shot) funnels into
`CheckMonsterWeaponCollision`, which is where the range test lives:

```
CheckMonsterWeaponCollision:
    STA $05

    ; Reset [06] for no collision.
    LDA #$00
    STA $06

    ; If the weapon's not active (state = 0), then return.
    LDY $00
    LDA a:ObjState, Y
    BEQ L74D8_Exit

    ; If the objects do not collide, then return.
    JSR DoObjectsCollideWithThresholds
    BEQ L74D8_Exit

    ; If the weapon is a boomerang ...
    CPY #$0F
    BNE HandleMonsterWeaponCollision
```

**Code 1 (`AAVLLGGY`)** patches the offset byte of the second
`BEQ L74D8_Exit` at CPU address `$B463` (originally `$74`, a -$37 jump
back to the `RTS`) to `$00`. A branch offset of zero lands on the very
next instruction, so the "objects are too far apart" early-out never
fires and control always falls through to `HandleMonsterWeaponCollision`
→ `DealDamage`. Nothing else about the routine changes: the weapon must
still be active (`ObjState <> 0` — for the sword,
`CheckMonsterSwordCollision` has already required state `$02`, fully
extended), the monster's `ObjInvincibilityMask` is still consulted, Gohma
still only takes hits on its eye, Darknuts still parry from the front,
and the damage points in `[07]` are still the real ones for whichever
sword Link is carrying. Only the distance check is gone.

**Code 2 (`AEKULSOG`)** is what keeps this from being a one-frame screen
wipe. `DoObjectsCollideWithThresholds` still writes `0` into `[06]` when
the objects really are far apart, and the caller checks it:

```
CheckMonsterStabbingCollision:
    ...
    JSR CheckMonsterSlenderWeaponCollision2

    ; If no collision, then return.
    LDA $06
    BEQ L7595_Exit
    JMP ParryOrShove
```

With only code 1 applied, damage is dealt but `ParryOrShove` is skipped,
so `BeginShove` never runs and the monster never gets its post-hit
`ObjInvincibilityTimer`. `CheckMonsterCollisions` would then deal full
sword damage again on *every* frame the sword is extended, killing
everything the instant the swing starts. This patches that branch's
offset byte at CPU address `$B5CB` (originally `$C9`, a -$37 jump back to
the `RTS`) to `$00`, so `ParryOrShove` always runs. The monster gets
shoved and receives the usual `$10` frames of invincibility, which makes
the hit register exactly once per swing — the normal amount of damage,
just delivered at any range.

Both are one-byte patches, and each code's compare byte targets its
specific bank/offset so it doesn't misfire against unrelated code sharing
the same switchable ROM window. Both compare values are unique to bank 1
across the whole ROM: at `$B463` the other banks hold `$03` (bank 4, part
of a `STA $0380, X`), `$8F` (bank 5, the high byte of a `JMP $8F61`), and
`$08` (bank 7, a branch offset); at `$B5CB` they hold `$05` (bank 5, part
of a `STA $0305`) and `$BD` (bank 7, the opcode of an `LDA $034F, X`).
A 6-letter version of either code would silently corrupt those whenever
the bank was active.

**Not live-verified:** derived from reading the collision routines, not
from observing it in-game.

## Sword beam leaves behind flames, like the Magic Book does for the rod

**Codes:** `AESNAUIL` (+ optional `AESNILIL`)

Tags: `demo-ready` `play-start` `curated`

**Effect:** Link's sword beam bursts into a standing flame wherever it
stops — on hitting an enemy or on hitting a wall — exactly the way the
Magical Rod's beam does once you have the Book of Magic. The flame is a
real fire object: it lingers for `$4F` frames and damages whatever walks
into it. The trade-off is that the beam no longer plays its four-corner
"spread" animation, because in the engine the spread and the flame are
the two mutually exclusive outcomes of the same branch.

The second code is optional: with only `AESNAUIL` you need the Book of
Magic in your inventory for flames to appear, just like the rod does.
Adding `AESNILIL` drops that requirement so the flames work from the
start of the game.

**How it works:** Both patches are in bank 7 (`src/Z_07.asm`), which is
the fixed `$C000-$FFFF` bank under this game's MMC1 mapping.

When Link's shot stops moving, `UpdateSwordShotOrMagicShot` falls into
`HandleShotBlocked`; the same routine is also called from bank 1
(`CheckMonsterSwordShotOrMagicShotCollision`, `src/Z_01.asm`) the moment
the shot registers a hit on a monster. Both entry points use shot slot
`$0E`, so these patches only ever touch Link's own beam:

```
HandleShotBlocked:
    LDA ObjState, X
    ASL
    BCC SetShotSpreadingState

    ; This is a magic shot.
    ;
    ; If missing the magic book, go deactivate the shot object.
    LDA InvBook
    BEQ DeactivateShot

    ; Try to activate a fire object. Temporarily mark the candle
    ; unused, so it only has to depend on having an empty slot.
    ...
```

The high bit of `ObjState` is what separates the two shots — set for the
Magical Rod's magic shot, clear for the sword beam — so the `ASL` /
`BCC` pair is the entire "which kind of shot am I?" test.

**Code 1 (`AESNAUIL`)** patches that branch's offset byte at CPU address
`$F3D8` (originally `$3D`, a +$3D jump forward to
`SetShotSpreadingState`) to `$00`. A branch offset of zero lands on the
very next instruction, so the sword beam stops being routed to the
spread animation and falls through into the magic shot's flame path
instead. Everything downstream is the vanilla rod-plus-book code, run
unmodified: it saves and restores `ObjState` and `UsedCandle` around a
call to `WieldCandle`, checks that a fire object was actually created
(state `$21`), promotes it to a standing fire (`$22`), copies the shot's
own X, Y and direction onto the fire, gives it the usual `$4F`-frame
lifetime, and then deactivates slot `$0E`. If no object slot is free the
routine still bails out cleanly to `DeactivateLinkShot`, exactly as it
does for the rod.

**Code 2 (`AESNILIL`)** patches the offset byte of the `BEQ
DeactivateShot` that follows `LDA InvBook`, at CPU address `$F3DD`
(originally `$35`, a +$35 jump forward to `DeactivateShot`), to `$00`.
That makes the "do you own the Book of Magic?" check fall through
whichever way it goes, so the flame is created regardless. Being a check
on the shared magic-shot path, this one also lets the Magical Rod's beam
leave flames without the Book.

Both are one-byte patches. Bank 7 is fixed in the `$C000-$FFFF` window,
so unlike the switchable `$8000-$BFFF` codes elsewhere in this file there
is no other bank that could ever be mapped at these addresses; the
compare bytes (`3D` and `35`) are included per this project's convention
rather than out of necessity.

**Not live-verified:** derived from reading `HandleShotBlocked` and its
two callers, not from observing it in-game.

## Recorder reveals an entrance and makes water walkable on any overworld screen

**Codes:** `AEOTNYPZ` + `AEXTUYTP`

**Effect:** Playing the Recorder anywhere on the overworld runs the
Level 7 pond-draining sequence: the water palette cycles through its
twelve shades, the water becomes walkable, and a staircase appears at
screen position (`$60`, `$90`) with the room flagged as "secret found" —
the same thing that normally only happens at the lake in room `$42`.
The Recorder never summons the whirlwind on the overworld anymore, since
revealing the secret replaces it.

**How it works:** Both patches are in bank 7 (`src/Z_07.asm`), the fixed
`$C000-$FFFF` bank. `WieldFlute` has already returned early if Link is
underworld or not in game mode 5, so this stays an overworld-only effect.

```
    ; Look for the current room in this list of $A that have a flute secret.
    LDA RoomId
    LDY #$0A

@FindSecretRoom:
    CMP FluteRoomSecretsOW, Y
    BEQ @Found
    DEY
    BPL @FindSecretRoom
    BMI @FluteSecretNotFound

@Found:
    CPY #$00
    BNE @Normal
    PLA
    BNE @SummonWhirlwind
    BEQ @RevealSecret

@Normal:
    ; For other rooms in the list:
    ; In Q1, go summon the whirlwind.
    ; In Q2, continue to reveal the secret.
    PLA
    BEQ @SummonWhirlwind

@RevealSecret:
```

Vanilla, only 11 overworld rooms are in `FluteRoomSecretsOW`, and even
for those the quest number decides between revealing the secret and
summoning the whirlwind. Two branch offsets stand between "any screen"
and "reveal the secret".

**Code 1 (`AEOTNYPZ`)** patches the offset byte of `BMI
@FluteSecretNotFound` at CPU address `$EF97` (originally `$21`, a +$21
jump forward) to `$00`. A branch offset of zero lands on the very next
instruction, so when the room-search loop falls off the end of the table
it drops into `@Found` instead of into the not-found handler. `Y` is
`$FF` at that point, so `CPY #$00` / `BNE @Normal` sends it to `@Normal`.
This also keeps the stack balanced: `@FluteSecretNotFound` existed only
to `PLA` the pushed quest number before falling into `@SummonWhirlwind`,
and `@Normal` performs exactly the same `PLA`.

**Code 2 (`AEXTUYTP`)** patches the offset byte of `@Normal`'s `BEQ
@SummonWhirlwind` at CPU address `$EFA3` (originally `$16`, a +$16 jump
forward) to `$00`, so the quest-number test can no longer divert to the
whirlwind and control always falls through into `@RevealSecret`.

From there everything is the untouched vanilla reveal: it returns early
if `SecretColorCycle` is already running, searches object slots 9 down to
1 for a free one, and drops a type-`$5E` flute-secret object in it.
`InitFluteSecret` then sets `SecretColorCycle` to 1, and
`UpdateFluteSecret` steps the pond palette every 8 frames through
`PondCycleColors`, sets `ObjectFirstUnwalkableTile` to `$99` at step `$A`
so the water can be walked on, and at step `$B` calls `RevealPondStairs`
→ `RevealAndFlagSecretStairsObj`, which draws the stairs tiles and sets
the room's "secret found" flag.

Both are one-byte patches. Bank 7 is fixed in the `$C000-$FFFF` window,
so no other bank can ever be mapped at these addresses; the compare bytes
(`21` and `16`) are included per this project's convention rather than
out of necessity.

**Caveat — room `$42` in Quest 2:** that room is index 0 in the table, so
it takes the `CPY #$00` / `BNE @Normal` path that falls *through* rather
than the `@Normal` path, and its quest test (`PLA` / `BNE
@SummonWhirlwind` at `$EF9D`) is untouched by either code. Standing in
room `$42` in Q2 still summons the whirlwind. Every other room, in both
quests, reveals the secret.

**Not live-verified:** derived from reading `WieldFlute`,
`UpdateFluteSecret`, and `RevealAndFlagSecretStairsObj`, not from
observing it in-game.

## All enemies on a screen always spawn even if you've defeated some before

**Codes:** `AVXOTAEZ` + `AVOPLZEZ`

**Effect:** Every room, overworld or underworld, always spawns its full
complement of monsters, no matter how many were killed there earlier —
whether that's earlier in the same visit, on a recent lap through nearby
screens, or in a much older visit whose "all defeated" flag would normally
have kept it permanently empty (or, for one-time foes, made a monster
never reappear at all).

**How it works:** Both patches are in bank 5 (`src/Z_05.asm`). Before a
room's monsters are placed, the engine loads the room's *full* foe count
from level data into a scratch object count (`[03]`), then calls one of
two routines to reduce that count based on prior kills — one for the
overworld, one for underworld:

```
    ; Get the object count from level info.
    LDA LevelInfo_FoeCounts, Y
    ...
    STA $03                     ; Put the count in [03].

    ; Use the room history to modify the number of objects to make.
    LDA CurLevel
    BNE :+
    JSR ModifyObjCountByHistoryOW
    JMP @StoreObjCount
:
    JSR ModifyObjCountByHistoryUW
```

`ModifyObjCountByHistoryOW` checks the current room against a 6-entry
recent-room history and the room's saved kill-count flags, then subtracts
however many foes were already killed there from `[03]` (or zeroes it
entirely once the flags show every foe in the room was defeated).
`ModifyObjCountByHistoryUW` does the equivalent for dungeons using
`LevelKillCounts` and the level's world-flag byte — and additionally, for
object types that represent one-time (non-recurring) foes, zeroes the
object count/list ID for good once the flags show the room fully cleared,
so that kind of object never spawns there again.

**Code 1 (`AVXOTAEZ`)** patches the opcode byte of `ModifyObjCountByHistoryOW`'s
first instruction (`LDY #$05`) at CPU address `$90AE` (originally `$A0`) to
`$60` (`RTS`). The routine now returns immediately, before it ever looks at
history or kill flags, so `[03]` keeps the full foe count that was just
loaded from level data — overworld rooms always place every monster the
level data specifies for them.

**Code 2 (`AVOPLZEZ`)** does the same thing to `ModifyObjCountByHistoryUW`,
patching the opcode byte of its own first `LDY #$05` at CPU address `$9293`
(originally `$A0`) to `$60`. Dungeon rooms get the identical treatment,
including one-time foes, which can now respawn on repeat visits just like
regular monsters.

Both are one-byte patches. Bank 5 is the only bank with `$A0` (`LDY
#imm`) at either address — the other banks hold unrelated opcodes/operands
there (for example `$0E`/`$85` in bank 0, `$C2`/`$BD` in bank 4), so a
6-letter version of either code would silently corrupt those banks'
code whenever they were active. The compare bytes (`A0` at both addresses)
pin each patch to bank 5.

**Not live-verified:** derived from reading `ModifyObjCountByHistoryOW`,
`ModifyObjCountByHistoryUW`, and their shared caller, not from observing it
in-game.

## Collect any Rupies, get 255

**Code:** `SZSZISVK`

**Effect:** After collecting any rupee (even the smallest, single-rupee
pickup), Link's rupee count climbs steadily and locks in at 255 a few
seconds later, then stays there permanently — further rupee pickups or
spending no longer move it.

**How it works:** `World_ChangeRupees` (`src/Z_01.asm`) is bank-1 code
that runs from its RAM copy at `$6C90`-`$7EFF` (its `BANK_01_CODE`
segment, loaded from ROM but relocated to RAM at startup so it can run
regardless of which bank is currently switched in). It ticks
`InvRupees` toward whatever's pending in `RupeesToAdd`/`RupeesToSubtract`
by 1 every 2 frames, and — critically — it pre-clamps those pending
counters every time it runs, *before* doing any add/subtract, so the
count can never overshoot 0 or 255:

```
    ; Reset RupeesToAdd or RupeesToSubtract as appropriate,
    ; if reached 0 or max.
    LDY #$27                    ; Index of RupeesToSubtract item slot.
    LDA InvRupees
    BEQ @ResetSlot
    LDY #$26                    ; Index of RupeesToAdd item slot.
    CMP #$FF
    BNE :+                      ; If 0 < rupees < $FF, don't reset anything.

@ResetSlot:
    LDA #$00                    ; Reset the slot we chose.
    STA Items, Y
:
    LDA FrameCounter
    LSR
    BCS L6506_Exit              ; Every two frames, return.
    LDA RupeesToAdd
    BEQ @CheckSubtract          ; If RupeesToAdd <> 0,
    DEC RupeesToAdd             ; then add one rupee.
    INC InvRupees
```

(`Items, Y` with `Y` = `$26`/`$27` is the same RAM byte as
`RupeesToAdd`/`RupeesToSubtract` — `Items` starts at `$0657`, and
`$0657+$26` = `$067D` = `RupeesToAdd` — so that `STA Items, Y` really is
resetting the pending counter directly.)

This patches the opcode byte of `DEC RupeesToAdd` at CPU address `$A555`
(originally `$CE`, `DEC` absolute) to `$AD` (`LDA` absolute) — same
instruction length, so the following address operand (`RupeesToAdd`'s
own address) is reused unchanged and nothing downstream shifts out of
alignment. `RupeesToAdd` is now only ever *read*, never decremented, by
this instruction. So once any rupee pickup sets `RupeesToAdd` to a
nonzero value (via `TakeOneRupee`'s unpatched `INC RupeesToAdd`, or any
other source of rupees), it never depletes on its own, and the tick above
it (`INC InvRupees`) fires every 2 frames indefinitely — climbing
`InvRupees` all the way to `$FF`. At that point the pre-clamp at the top
of the routine (the code shown first above) starts recognizing
`InvRupees = $FF` on every call and force-resets `RupeesToAdd` to 0 via
the `Items, Y` alias before the (patched, now-inert) read instruction is
ever reached again — so the count settles exactly at 255 and holds
there, even across later pickups (each one re-arms `RupeesToAdd`, but the
pre-clamp immediately disarms it again on the very next call since
`InvRupees` is already maxed).

One-byte patch. Bank 1 is the only bank with `$CE` at this address — the
other banks hold unrelated opcodes there (for example `$A4`/`$99` in
banks 2/3, `$BD` in bank 4), so a 6-letter version of this code would
silently corrupt those banks' code whenever they were active. The compare
byte (`CE`) pins the patch to bank 1. Note that because this routine
executes from its RAM copy, the patched byte only takes effect after the
RAM copy is made (at startup), which is when the game is normally already
running — this isn't a practical limitation, just a detail of how the
patch propagates.

**Not live-verified:** derived from reading `World_ChangeRupees` and
`TakeOneRupee`, not from observing it in-game.

## Have the Magical Sword in your inventory

**Code(s):** `AAAAKVXY` + `AAZUYILA`

Tags: `play-start`

**Effect:** Link can swing the sword and fire full-strength sword beams
even on a file where `Items` (the sword grade, `$0657`) is still 0 — i.e.
before the Wood Sword has ever been picked up.

**How it works:**

`WieldSword` (bank 5) gates the entire sword action on owning any sword
at all:

```
WieldSword:
    ; If there's no sword, return.
    LDA Items
    BEQ L14DFF_Exit

    ; Switch to the sword slot.
    LDX #$0D
```

`AAAAKVXY` patches the operand byte of `BEQ L14DFF_Exit` (CPU `$8E04`,
originally `$FA`) to `$00`, so the branch always lands on the very next
instruction whether or not `Items` is 0. The sword slot is then always
activated, regardless of sword grade.

Separately, `CheckMonsterSwordShotOrMagicShotCollision` (bank 1, part of
the RAM-relocated `BANK_01_CODE` block) picks the sword beam's damage
points by grade:

```
    ; Determine the damage points for the kind of sword.
    ; - wood sword:   $10
    ; - white sword:  $20
    ; - master sword: $40
    LDY #$40
    LDA Items
    CMP #$03
    BEQ @CheckCollision
    LDY #$20
    CMP #$02
    BEQ @CheckCollision
    LDY #$10
```

With `Items = 0` this falls all the way through to the weakest ($10)
beam damage. `AAZUYILA` patches the operand byte of the first `CMP #$03`
(CPU `$B52F`, originally `$03`) to `$00`, so a grade of 0 now matches
this check instead of 3, and the beam keeps the full `$40` (Magical
Sword) damage from the initial `LDY #$40` load. (On a file that
legitimately owns the grade-3 sword already, this same check now *fails*
to match — `Items` is 3, not 0 — so a genuinely-earned Magical Sword's
beam falls through to $10 instead. That tradeoff only matters if this
code is applied on top of a file that already has the real Magical
Sword, which defeats the point of the cheat in the first place.)

Melee sword damage (`CheckMonsterSwordCollision`, same bank) is left
unpatched: it looks up `SwordDamagePoints-1, Y` with `Y = Items`, and
with `Items = 0` that reads the byte immediately before the
`SwordDamagePoints` table — which happens to be the `$60` opcode byte of
the preceding routine's trailing `RTS`. That's *more* than the real
Magical Sword's $40, so it was left alone rather than spending another
code to "fix" an already-favorable accident.

Both patched bytes are unique to bank 5/1 respectively — `$FA` at
`$8E04` only appears in bank 5 (other banks hold values like `$01`,
`$80`, `$02`, `$F8`, `$37`, `$DB`, `$F1`), and `$03` at `$B52F` only
appears in bank 1 (other banks hold `$FF`, `$5A`, or `$0E`) — so 6-letter
versions of either code would risk corrupting unrelated banks. The
compare bytes pin both patches to the correct bank. As with other
`BANK_01_CODE` patches in this document, the bank-1 patch only takes
effect once the RAM copy is made at startup.

**Not live-verified:** derived from reading `WieldSword`,
`CheckMonsterSwordShotOrMagicShotCollision`, and
`CheckMonsterSwordCollision`, not from observing it in-game.

## Descend stairs as rapidly as possible

**Code:** `AEOASLLA`

**Effect:** Walking onto a cave/dungeon-entrance stairs tile (e.g. the sword
cave) makes Link sink out of view and change modes 4x faster than normal.

**How it works:** Vanilla code (`src/Z_05.asm`, `UpdateMode10Stairs_Full`)
drives the "sinking into the stairs" animation by moving Link down 1 pixel
only once every 4 frames, then comparing his position against the target:

```
    LDA FrameCounter
    AND #$03
    BNE AnimateAndDrawLinkBehindBackground    ; If it's not time to change position, go draw.
    INC ObjY                    ; Move Link down 1 pixel.
    LDA ObjY
    CMP StairsTargetY
    BNE AnimateAndDrawLinkBehindBackground    ; If Link hasn't reached the end of the walk, go draw.
```

This patches the `AND #$03` immediate operand at CPU `$8B95` (originally
`$03`) to `$00`. ANDing `FrameCounter` with 0 always yields 0, so the
following `BNE` is never taken and Link's Y position advances by 1 pixel
every single frame instead of every 4th — a straight 4x speedup of the
descent, with the mode-change trigger (`ObjY == StairsTargetY`) firing that
much sooner too. One-byte patch, no bytes sacrificed.

Bank-uniqueness: `UpdateMode10Stairs_Full` lives in the switchable $8000
window loaded from `Z_05.asm` (bank 5). Checking the same offset
(`$8000+$B95`) across all 8 banks, only bank 5 holds `$03` there (bank 0
and 3 hold `$FF`, bank 1 holds `$A5`, bank 2 holds `$00`, bank 4 holds
`$85`, bank 6 holds `$14`, bank 7 holds `$E3`), so the compare byte locks
this patch to bank 5 and it can't misfire against unrelated code sharing
that address in another bank.

**Not live-verified:** derived from reading `UpdateMode10Stairs_Full`, not
from observing it in-game.

## Basic items (coins, hearts) get the same hold-up fanfare as major items

**Code:** `AENZUUIA`

Tags: `demo-ready` `play-start` `curated`

**Effect:** Picking up a rupee, heart, bomb refill, or any other everyday
drop during normal play makes Link stop, hold it overhead, and play the
"item get" jingle — the same presentation major items get when handed to
you in a cave (e.g. the wooden sword).

**How it works:** Every item pickup, whether a room/cave item, a grass
drop, or an enemy drop, funnels through the same routine (`src/Z_01.asm`,
`TryTakeItem`/`TakeItem`). Near the top of `TakeItem`, vanilla code decides
whether to show the "hold item overhead" presentation based on the current
game mode:

```
    ; If we're in a cave or cellar, then
    ; prepare to lift the item.
    LDX GameMode
    CPX #$05
    BEQ @SkipLift
    LDX #$80                    ; Lift for $80 frames.
    STX ItemLiftTimer
    LDX #$08                    ; Play the "item" song.
    STX SongRequest
    STA ItemTypeToLift          ; Set the item type for lifting.

@SkipLift:
```

`GameMode` 5 is `Mode5Play` — ordinary overworld/underworld gameplay (as
opposed to the separate cave/shop "give item" mode). So during regular
play, the `BEQ @SkipLift` always skips setting `ItemLiftTimer`, and every
pickup — rupees, hearts, keys, and dungeon room treasures alike — is
absorbed silently with no hold-up and no freeze. Only cave/shop item gifts
(where `GameMode != 5`) fall through and get the full `ItemLiftTimer`
treatment (Link freezes, raises the item, and the "item" song plays via
the shared `CheckLiftItem`/`SetUpAndDrawLinkLiftingItem` code in
`src/Z_07.asm`).

This patches the `BEQ @SkipLift` branch-offset byte at CPU `$ABF3`
(originally `$0D`, the LOAD-image copy of this RAM-relocated
`BANK_01_CODE` segment — see `__BANK_01_CODE_LOAD__`/`__BANK_01_CODE_RUN__`
in `bin/Z.map`) to `$00`. A `BEQ` with a zero offset always lands on the
very next instruction (the same place execution falls through to when the
branch isn't taken), so the skip becomes a no-op regardless of `GameMode`
— every pickup during normal play now sets up the lift exactly like a cave
gift does. One-byte patch, nothing sacrificed.

Bank-uniqueness: checking the same offset (`$8000+$2BF3`) across all 8
banks, only bank 1 holds `$0D` there (bank 0 and 3 hold `$FF`, bank 2 holds
`$2A`, bank 4 holds `$E0`, bank 5 holds `$90`, bank 6 holds `$DC`, bank 7
holds `$A1`), so the compare byte locks this patch to bank 1.

**Not live-verified:** derived from reading `TakeItem` and
`CheckLiftItem`, not from observing it in-game.

## Link can walk on water (overworld)

**Code:** `OPSUAEOE`

Tags: `demo-ready` `curated`

**Effect:** In the overworld, Link (and every other object, since the
check isn't Link-specific) can walk straight out onto lakes and ponds as
if they were ordinary ground — no ladder, no raft needed.

**How it works:** Object movement collision throughout `src/Z_04.asm` and
`src/Z_07.asm` compares the tile Link is about to step onto against a
single RAM threshold, `ObjectFirstUnwalkableTile` (`$34A`): any tile ID
`>= ObjectFirstUnwalkableTile` blocks movement. This is the same variable
the Recorder's Level 7 pond secret (`UpdateFluteSecret`,
`src/Z_07.asm`) temporarily bumps up to reveal a walkable path:

```
    CPY #$0A
    BNE L1FF28_Exit             ; If the index is $A,
    LDA #$99                    ; then make most water tiles (< $99) walkable.
    STA ObjectFirstUnwalkableTile
```

Its *default* value, though, gets reset on every room transition by
`SetupObjRoomBounds` (`src/Z_05.asm`), which copies 5 bytes (left/right/up/
down object bounds, then first-unwalkable-tile) from one of two fixed
tables depending on whether Link is in the overworld or underworld:

```
ObjectRoomBoundsOW:
    .BYTE $11, $E0, $4E, $CD, $89

ObjectRoomBoundsUW:
    .BYTE $21, $D0, $5E, $BD, $78
```

Water tiles occupy the range `$8D`-`$98` (see the Zora-spawn check in
`src/Z_04.asm`, which only spawns Zoras on tiles in that range). The OW
table's default threshold of `$89` already blocks everything from `$89`
up, water included; the flute secret's `$99` only lifts the block for
water specifically, leaving true obstacles (`$99`+) still solid.

This patches the OW table's 5th byte at CPU `$B058` (originally `$89`) to
`$99` — the same value the flute secret already uses. Every overworld
room load now installs the flute secret's "water is walkable" threshold
permanently, with no code path left that ever puts it back to `$89`. The
underworld table (`$78`) is untouched, so this doesn't affect dungeon
collision. One-byte patch, nothing sacrificed.

Bank-uniqueness: checking the same offset (`$8000+$3058`) across all 8
banks, only bank 5 holds `$89` there (banks 0, 2, 3, and 6 hold `$FF`,
bank 1 holds `$0D`, bank 4 holds `$18`, bank 7 holds `$09`), so the
compare byte locks this patch to bank 5.

**Not live-verified:** derived from reading `SetupObjRoomBounds` and
`UpdateFluteSecret`, not from observing it in-game.

## Recorder whirlwind takes you to a crossroads instead of the Level 1 entrance

**Code(s):** `AGPZAATU`

**Effect:** Playing the Recorder in the overworld, when it would
normally summon the whirlwind to Level 1's entrance, now takes Link to
the overworld room immediately south of a Fairy Spring (room `$49`)
instead — a crossroads screen with paths leading out in every
direction.

**How it works:** `WhirlwindPrevRoomIdList` (`src/Z_01.asm`) is an
8-byte table, indexed by the teleporting level index (see the "Recorder
will take you to dungeons you haven't beaten" cheat above for how that
index is picked):

```
WhirlwindPrevRoomIdList:
    .BYTE $36, $3B, $73, $44, $0A, $21, $41, $6C
```

Each entry isn't the destination room itself — it's the room *to the
left* of it. When the whirlwind picks Link up (`UpdateWhirlwind_Full`),
it looks up this table and stores the result in `WhirlwindPrevRoomId`.
Once the teleport scroll begins, `InitMode7_Sub0` (`src/Z_05.asm`)
copies `WhirlwindPrevRoomId` into the live `RoomId`, and the ordinary
rightward-scroll transition takes over from there — scrolling one room
to the right of it, which lands Link in the actual destination room.

This patches the first entry (level 1, CPU `$A010`, bank 1) from `$36`
to `$48` — the room to the left of crossroads room `$49` — so the
whirlwind lands Link there instead of at Level 1's entrance. `$48` and
`$49` are in the same map row, so the rightward scroll that follows
works exactly as it does for a normal dungeon-entrance teleport.

Bank-uniqueness: `$A010` is a plain bank-1 ROM-resident byte (part of
`WhirlwindPrevRoomIdList`, which sits before the `BANK_01_CODE`
RAM-relocated region and so is not itself relocated). Checked against
all 8 banks — none of the other banks holds `$36` at this offset, so the
compare byte is unique to bank 1.

**Not live-verified:** derived from reading `WhirlwindPrevRoomIdList`,
`UpdateWhirlwind_Full`, `InitMode7_Sub0`, and the overworld room
attribute data (`dat/LevelBlockOW.dat`) that places a Fairy Spring
object in room `$39`, one row north of the crossroads at `$49`, not
from observing it in-game.

## Overworld cave people are shuffled to the next cave "kind"

**Code(s):** `PVYETSZV`

**Effect:** Every overworld cave/shop person now behaves like the *next*
kind of cave person instead of their own — wrong dialogue, wrong item,
wrong price, wrong "pay"/"pick up" behavior, all shifted uniformly by
one slot. The very last kind (object type `$7D`) shifts one slot past
the end of the relevant tables and reads adjacent, unrelated bytes
instead.

**How it works:** `InitCaveContinue` (`src/Z_01.asm`) turns a cave
person's object type into a 0-19 index (there are 20 distinct kinds of
overworld cave/shop people, object types `$6A`-`$7D`) and uses that same
index three times: once into `OverworldPersonTextSelectors` (a 20-byte
table giving each kind's text ID and pay/pickup flags), and twice
(multiplied by 3) into `LevelBlockAttrsE` for that kind's three item IDs
and three prices:

```
InitCaveContinue:
    ; Get this cave's index (object type - $6A).
    LDA ObjType+1
    SEC
    SBC #$6A
    TAY

    ; Get the person text selector by looking up the text selector byte
    ; for this index, and masking it with $3F.
    LDA OverworldPersonTextSelectors, Y
    ...
```

Changing the `SBC #$6A` immediate to `SBC #$69` (CPU `$85FE`, bank 1)
makes the computed index one higher than the person's real kind, so
every subsequent read off of `Y` — text, item, and price — is uniformly
shifted to the next kind's data instead. Because all three reads use the
same shifted `Y`, each cave's new text still correctly matches whatever
new item/price it now hands out — it's a different, but still internally
consistent, "kind" of cave person.

The 20 valid kinds are indices 0-19. With the shift, the top kind
(object type `$7D`, which would normally be index 19) computes index 20
instead, one past the end of `OverworldPersonTextSelectors`'s declared
20 bytes and past the 0-59/60-119 ranges `InitCaveContinue` expects
inside `LevelBlockAttrsE`. In both cases, the "overflow" read lands on
other real, already-allocated data rather than crashing: index 20 into
`OverworldPersonTextSelectors` reads the first byte of the immediately
following `MoneyGameLossAmounts` table (`$0A`), and the item/price reads
at `Y`=60 land within `LevelBlockAttrsE`'s own 128-byte RAM block
(`$6A7E`-`$6AFD`, shared with `LevelBlockAttrsF` starting only at
`$6AFE`) — so the worst case is a cave showing bogus but harmless
text/item/price data, not a crash. This does **not** move any dungeon
entrances around: dungeon entrance placement comes from each room's own
object-layout data, which is entirely separate from this cave-person
kind table.

Bank-uniqueness: CPU `$85FE` is plain bank-1 ROM-resident code (well
before the `BANK_01_CODE` RAM-relocated region), and its original byte
`$6A` doesn't match any other bank's byte at that same file offset.

**Not live-verified:** derived from reading `InitCaveContinue`,
`OverworldPersonTextSelectors`, and the `LevelBlockAttrsE` layout, not
from observing it in-game. The human should specifically check the
highest-index cave kind (object type `$7D`) for anything unusual, since
its data now comes from just past the end of the intended tables.

## Don't lose a Rupee when firing an arrow

**Code(s):** `XVAEXVVV` `XVAEUVTN` `XVAEKTTE`

**Effect:** Firing an arrow with the Bow no longer costs a Rupee. You
still need at least 1 Rupee to fire at all (that check is untouched).

**How it works:** `WieldArrow` (`src/Z_05.asm`) is the routine that runs
when the bow's item slot is used:

```
WieldArrow:
    ; If there's no bow, return.
    LDA Bow
    BEQ WieldNothing
    ...
    ; If there are no rupees, return.
    LDA InvRupees
    BEQ WieldNothing
    LDA #$02                    ; Boomerang/arrow sound effect
    JSR PlayEffect

    ; Post a rupee to subtract.
    INC RupeesToSubtract
    ...
```

`INC RupeesToSubtract` (CPU `$8E8A`-`$8E8C`, bank 5, bytes `EE 7E 06`)
queues a Rupee deduction, which a separate status-bar routine drains one
at a time from `InvRupees` later. Overwriting the instruction with three
`NOP`s (`EA EA EA`) removes the deduction entirely, while leaving the
preceding `LDA InvRupees / BEQ WieldNothing` guard (which requires
owning at least one Rupee to fire) completely intact.

Bank-uniqueness: `$8E8A`-`$8E8C` are plain bank-5 ROM-resident bytes
(no `BANK_05_CODE` RAM-relocated segment exists in this build). Checked
against all 8 banks; none of the other banks holds a matching byte at
any of these offsets.

**Not live-verified:** derived from reading `WieldArrow`, not from
observing it in-game.

## Prevent Zoras from appearing

**Code(s):** `AETATVAA`

**Effect:** Zoras never pop up out of the water on the overworld.

**How it works:** `CheckZora` (`src/Z_04.asm`) is what decides whether
to spawn a Zora in the current room:

```
CheckZora:
    ; If the zora attribute of this room is off, return.
    LDY RoomId
    LDA LevelBlockAttrsA, Y
    AND #$08                    ; Zora attribute
    BEQ @Exit
    ...
```

Each room's attribute byte has a bit (`$08`) marking it as a
Zora-eligible water room; if that bit is clear, the routine exits
immediately without spawning one. Changing the `AND #$08` immediate
(CPU `$86E6`, bank 4) to `AND #$00` makes the test always evaluate to
zero, so every room is treated as if its Zora bit were off — the
`BEQ @Exit` always taken, and the rest of the routine (which finds an
empty monster slot and a water tile to place the Zora on) never runs.

Bank-uniqueness: `$86E6`'s original byte `$08` was checked against all
8 banks; only bank 4 holds that value at this offset.

**Not live-verified:** derived from reading `CheckZora`, not from
observing it in-game.

## Prevent falling rocks from appearing

**Code(s):** `AVAAVASL`

**Effect:** The falling-boulder hazard on Death Mountain (overworld)
never spawns any boulders.

**How it works:** In rooms with the boulder hazard, one object slot
holds a persistent "boulder set" controller object, updated by
`UpdateBoulderSet` (`src/Z_04.asm`) every frame:

```
UpdateBoulderSet:
    ; If the object timer has not expired, then return.
    LDA ObjTimer, X
    BNE @Exit

    ; If the maximum number (3) of boulders are active, then
    ; go set the timer to wait a random amount of time.
    LDA ActiveBoulders
    CMP #$03
    BEQ @RandomizeTimer
    ...
```

When its timer expires, it looks for an empty monster slot and, if
fewer than 3 boulders are already falling, spawns a new one. Changing
the routine's first byte (CPU `$8886`, bank 4) from `$B5` (the opcode
for `LDA $28,X`) to `$60` (`RTS`) makes the whole routine return
immediately every time it's called, before it ever checks the timer or
spawns anything. The now-unreached second byte (`$28`, the original
instruction's operand) is simply dead data that's never fetched as an
opcode. The controller object itself still exists and gets updated each
frame — it just does nothing.

Bank-uniqueness: `$8886`'s original byte `$B5` was checked against all
8 banks; only bank 4 holds that value at this offset.

**Not live-verified:** derived from reading `UpdateBoulderSet`, not
from observing it in-game.

## Scrolling: Vertical scroll runs every frame (byte 1 of 2)

**Code(s):** `XVTEPPES`

**Effect:** Part of a pair — **must be combined with "Scrolling:
Vertical scroll runs every frame (byte 2 of 2)"** below. Together,
the two codes make the screen-scroll animation's vertical step (used
when walking up or down between rooms) advance every frame instead of
being throttled to every 2nd (overworld) or 4th (dungeon) frame.
Applied alone, this code corrupts a branch instruction into garbage
and should not be used by itself.

**How it works:** In `ScrollWorld` (`src/Z_05.asm`, bank 5), the
routine that advances the scroll position once per call from
`UpdateMode7Scroll`:

```
ScrollWorld:
    LDA FrameCounter

    ; The purpose of this is to delay vertical scrolling.
    ; OW: once every two frames
    ; UW: once every four frames
    ; Horizontal scrolling happens every frame.
    AND #$03
    LDY CurLevel
    BNE :+
    AND #$01
:
    CMP VScrollStartFrame
    BNE ScrollWorldH
    ...
```

`BNE ScrollWorldH` (CPU `$81E9`-`$81EA`, bytes `$D0 $6A`) skips the
vertical-scroll step on frames that don't match `VScrollStartFrame`.
This code changes the first of those two bytes, `$81E9`: `$D0`
&rarr; `$EA` — turning the `BNE` into the first half of a two-byte
`NOP`. The second half is changed by the paired code below.

Bank-uniqueness: `$81E9`'s original byte `$D0` was checked against
all 8 banks; only bank 5 holds that value at this offset.

**Not live-verified:** derived from reading `ScrollWorld`, not from
observing it in-game.

## Scrolling: Vertical scroll runs every frame (byte 2 of 2)

**Code(s):** `XVTEZOZV`

**Effect:** Part of a pair — **must be combined with "Scrolling:
Vertical scroll runs every frame (byte 1 of 2)"** above. See that
entry for the combined effect. Applied alone, this code corrupts a
branch instruction into garbage and should not be used by itself.

**How it works:** Changes the second byte of the `BNE ScrollWorldH`
instruction described above, CPU `$81EA` (bank 5): `$6A` &rarr;
`$EA`. Combined with the first byte's change, the instruction becomes
two `NOP`s (`$EA $EA`), so the branch is never taken and the
vertical-scroll step always runs, regardless of `FrameCounter` or
`VScrollStartFrame`. The preceding `AND`/`CMP` instructions still
execute harmlessly; their result is just no longer used to gate
anything.

Bank-uniqueness: `$81EA`'s original byte `$6A` was checked against
all 8 banks; only bank 5 holds that value at this offset.

**Not live-verified:** derived from reading `ScrollWorld`, not from
observing it in-game.

## Scrolling: Horizontal scroll speed increased to 4/8 pixels per frame

**Code(s):** `GAIATZZA`

**Effect:** Increases the screen-scroll animation's horizontal speed
(used when walking left or right between rooms) from 2 to 4
pixels/frame in dungeons, and from 4 to 8 pixels/frame in the
overworld. **Should be combined with both "Scrolling: Nametable-switch
sync for faster horizontal scroll (dungeons)" and "...(overworld)"**
below — applied alone, the room transition will likely get stuck
partway through, since the nametable-switch check will no longer
match the new speed.

**How it works:** In `ScrollWorldH` (`src/Z_05.asm`, bank 5):

```
ScrollWorldH:
    LDA #$02                    ; Use the default scroll speed: 2 pixels a frame.
    LDX #$FE
    LDY CurLevel
    BNE :+
    ASL                         ; Scroll twice as fast if in the overworld.
    LDX #$FC
:
    STA $00                     ; [00] holds the speed.
    STX $01                     ; [01] holds the X position where we must start using NT 1.
```

This code changes CPU `$8256` (bank 5): `$02` &rarr; `$04` — the
speed loaded into `A`, which becomes the dungeon speed directly, and
the overworld speed after the `ASL` doubles it. This is a milder,
safer increase than doubling again to 8/16: with a comfortable margin
below this routine's edge-of-screen clamp (`CMP #$F0` / `BCS`, further
down in `ScrollWorldH`), which can tolerate up to 16 pixels/frame
before `ObjX` risks wrapping past 255.

Bank-uniqueness: `$8256`'s original byte `$02` was checked against
all 8 banks; only bank 5 holds that value at this offset.

**Not live-verified:** derived from reading `ScrollWorld`, not from
observing it in-game.

## Scrolling: Nametable-switch sync for faster horizontal scroll (dungeons)

**Code(s):** `KYIEAXVN`

**Effect:** Keeps the room-transition logic working correctly for the
*dungeon* path once horizontal scroll speed has been increased.
**Must be combined with "Scrolling: Horizontal scroll speed increased
to 4/8 pixels per frame"** above — applied alone (with the original
2 pixels/frame speed still in place), this code has no effect, since
scrolling would still complete before ever reaching the new reference
value.

**How it works:** In the `ScrollWorldH` listing above, `X` (stashed
in `$01`) is a reference scroll position used later to detect when to
switch the base nametable; it must always equal `256 - speed`. With
the dungeon speed raised from 2 to 4 by the paired code, this
reference has to move from `256-2=$FE` to `256-4=$FC` to match. This
code changes CPU `$8258` (bank 5): `$FE` &rarr; `$FC`.

Bank-uniqueness: `$8258`'s original byte `$FE` was checked against
all 8 banks; only bank 5 holds that value at this offset.

**Not live-verified:** derived from reading `ScrollWorld`, not from
observing it in-game.

## Scrolling: Nametable-switch sync for faster horizontal scroll (overworld)

**Code(s):** `EYIEYXKN`

**Effect:** Keeps the room-transition logic working correctly for the
*overworld* path once horizontal scroll speed has been increased.
**Must be combined with "Scrolling: Horizontal scroll speed increased
to 4/8 pixels per frame"** above — applied alone (with the original
4 pixels/frame overworld speed still in place), this code has no
effect, since scrolling would still complete before ever reaching the
new reference value.

**How it works:** Same mechanism as the dungeon-path sync code above,
but for the `LDX #$FC` on the overworld branch of `ScrollWorldH`. With
the overworld speed raised from 4 to 8 by the paired code, this
reference has to move from `256-4=$FC` to `256-8=$F8` to match. This
code changes CPU `$825F` (bank 5): `$FC` &rarr; `$F8`.

Bank-uniqueness: `$825F`'s original byte `$FC` was checked against
all 8 banks; only bank 5 holds that value at this offset.

**Not live-verified:** derived from reading `ScrollWorld`, not from
observing it in-game.

## Sword beam continues flying after hitting an enemy

**Codes:** `XTKLTIAX` + `XTKLYIKS` + `XTKUAIUN`

Tags: `play-start`

**Effect:** Link's sword beam no longer stops or spreads out when it hits a
monster — it keeps flying in a straight line through the monster and on
across the screen, still damaging every monster it passes through along
the way. It still stops normally when it hits a wall.

This is a cleaner version of the 6-letter code `ESSYGLSL`: same effect, but
with a compare byte so it only patches the bank that actually holds this
routine.

**How it works:** `CheckMonsterSwordShotOrMagicShotCollision`
(`src/Z_01.asm`) is bank-1 code that runs from its RAM copy at
`$6C90`-`$7EFF` (its `BANK_01_CODE` segment is loaded from ROM but
relocated to RAM at startup, so it can be called from any bank regardless
of which ROM bank is currently switched in). After a collision is detected
and damage has already been dealt (inside `CheckMonsterShotCollision`,
called just above), it calls `HandleShotBlocked` to stop the shot:

```
@CheckCollision:
    TYA
    JSR CheckMonsterShotCollision

    ; If no collision, then return.
    LDA $06
    BEQ @Exit

    ; Else handle blocking the shot.
    TXA
    PHA
    LDX #$0E                    ; Shot object slot
    JSR HandleShotBlocked
    PLA
    TAX

@Exit:
    RTS
```

`HandleShotBlocked` (`src/Z_07.asm`) is what makes the shot stop: for a
sword shot it sets the "spreading out" state (the four-corner flash
animation, followed by deactivation a few frames later); it's the same
routine called when the shot hits a wall.

This patches the 3-byte `JSR HandleShotBlocked` at CPU address `$B546`
(originally `$20 $D4 $F3`) to `$EA $EA $EA` (three `NOP`s) — one byte per
code, each with its own compare byte. The surrounding `TXA`/`PHA`/`LDX
#$0E`/`PLA`/`TAX` still run, but now just push and pop the monster slot in
`X` around three no-ops instead of around the call, so `X` comes out
exactly as it went in. Damage, invincibility, and shoving are untouched —
those all happened earlier, inside `CheckMonsterShotCollision` — only the
call that would have stopped/spread the shot is skipped. The shot's
`ObjState` is never touched, so `UpdateSwordShotOrMagicShot` keeps moving
it every frame exactly as if it hadn't hit anything, letting it collide
with (and damage) further monsters in its path. Hitting a wall still goes
through `HandleShotBlocked` normally, since that call (from
`UpdateSwordShotOrMagicShot` in `src/Z_07.asm`) is a separate, unpatched
call site.

Three one-byte patches. Bank 5 (`$12 $20 $A3`) and bank 7 (`$20 $27 $70`,
coincidentally also starting with a `JSR` opcode) both hold different,
unrelated code at this same address; the other banks hold `$FF` padding
there. The compare bytes (`20`, `D4`, `F3`) pin each patch to bank 1 so it
doesn't misfire against bank 5's or bank 7's code when either is active.
Note that because this routine executes from its RAM copy, the patched
bytes only take effect after the RAM copy is made (at startup), which is
when the game is normally already running — this isn't a practical
limitation, just a detail of how the patch propagates.

**Not live-verified:** derived from reading
`CheckMonsterSwordShotOrMagicShotCollision`, `HandleShotBlocked`, and
`UpdateSwordShotOrMagicShot`, not from observing it in-game.

## Disable music

**Code(s):** `XTGPUAAX` `XTGPKELV` `XTGPSEKO`

Tags: `utility` `play-start`

**Effect:** Background music (level themes, overworld/underworld themes,
etc.) never plays. Sound effects, the short item-fanfare tunes, and DMC
samples are unaffected.

**How it works:** `DriveAudio` (`src/Z_00.asm`) is the per-frame audio
driver, called once a frame (via a bank switch to bank 0) from
`src/Z_07.asm`. When the game isn't paused, it drives several
sub-systems in sequence:

```
        jsr     DriveTune1
        jsr     DriveEffect
        jsr     DriveSample
        jsr     DriveSong
@Play:  jsr     DriveTune0
```

`DriveSong` is the routine that advances the currently-playing
background music track (built from the `SongHeader*`/`SongScript*`
tables at the top of `Z_00.asm`), as distinct from `DriveTune0`/
`DriveTune1` (short one-shot fanfares like the item-get jingle),
`DriveEffect` (sound effects), and `DriveSample` (DMC samples).

The patch replaces the 3-byte `JSR DriveSong` call (CPU `$9843`-`$9845`
in bank 0, originally `20 6B 9C`) with three `NOP`s. `DriveSong` itself,
and the song-selection/song-request logic elsewhere in the game, are
untouched — the routine that steps the music forward simply never runs,
so whatever song is queued stays silently stuck instead of playing.

Three one-byte patches. Bank-uniqueness: none of the other six banks
mapped into `$8000`-`$BFFF` has `$20`/`$6B`/`$9C` at
`$9843`/`$9844`/`$9845` respectively — each bank holds unrelated code or
data there, so the compare bytes pin all three patches to bank 0.

**Not live-verified:** derived from reading `DriveAudio` in
`src/Z_00.asm` and the bank-0 disassembly at `$9843`, not from observing
it in-game.

## Start the game on the second quest

**Code(s):** `XTIOSYES` `XTIOVNYE`

**Effect:** Any newly-created save file (a previously-empty/inactive
slot given a name at the file-select screen) starts on the second quest
instead of the first, regardless of what name is entered.

**How it works:** `UpdateModeERegister` (`src/Z_02.asm`) is the routine
that commits a new name typed at the file-select screen into save file
B. For each inactive slot, after copying the typed name, it contains a
long-standing Zelda series trick: if the name typed exactly matches
"ZELDA", the new file starts on the second quest.

```
    LDX #$00                    ; Compare the name to "ZELDA".

@CompareToZelda:
    LDA Names, Y
    CMP ZeldaString, X
    BNE @FlagBReady             ; If there's any mismatch, then skip the rest.
    INY
    INX
    CPX #$05
    BCC @CompareToZelda         ; Go check the next character until the end of "ZELDA".
    PLA                         ; Pop and push the slot number, so we can get it into X.
    PHA
    TAX
    LDY #$00                    ; Set second quest in file B.
    LDA #$01
    STA ($CC), Y

@FlagBReady:
    ...
```

The `BNE @FlagBReady` (CPU `$9F5D`-`$9F5E` in bank 2, originally `D0
0F`) is what lets a mismatched character skip straight past the
"set second quest" code. The patch replaces it with two `NOP`s, so a
mismatch is simply ignored: the loop still runs all 5 iterations (`INY`/
`INX`/`CPX #$05`/`BCC`), then always falls through to `LDY #$00 / LDA
#$01 / STA ($CC), Y`, unconditionally setting the new file's quest
number to 1 (second quest) no matter what name was actually typed. The
rest of the routine (marking the file ready to save, copying the name,
computing the checksum) is untouched.

Two one-byte patches. Bank-uniqueness: none of the other six banks
mapped into `$8000`-`$BFFF` has `$D0`/`$0F` at `$9F5D`/`$9F5E`
respectively — each bank holds unrelated code or data there, so the
compare bytes pin both patches to bank 2.

**Not live-verified:** derived from reading `UpdateModeERegister` in
`src/Z_02.asm` and the bank-2 disassembly at `$9F5D`, not from observing
it in-game.

## Title screen switches to "demo" mode much more quickly

**Code(s):** `XVLOAIES` `XVLOPILE`

**Effect:** The initial title-screen logo card ("THE LEGEND OF ZELDA")
advances into the rest of the attract-mode sequence (the scrolling
story text, item showcase, etc. — internally called "the demo") almost
immediately, instead of sitting for about 512 frames (roughly 8.5
seconds) first.

**How it works:** `AnimateDemoPhase0Subphase0` (`src/Z_02.asm`) is the
routine that runs every frame while the title logo is shown. It counts
frames in `DemoTimer` (an 8-bit counter reused for several unrelated
delays throughout the demo sequence, guaranteed to start at 0 here
because the previous lap through the sequence resets it right before
looping back to phase 0), advancing to the next subphase only once the
counter wraps back around to 0 after 256 increments:

```
AnimateDemoPhase0Subphase0:
    ; Animate while we wait about 512 frames.
    LDA FrameCounter
    AND #$01                    ; The timer is incremented every other frame.
    BEQ @SkipTimer
    INC DemoTimer
    LDA DemoTimer
    BNE @SkipTimer
    JMP IncSubphase             ; Go advance the demo subphase and return.

@SkipTimer:
    JSR AnimateDemoPhase0Subphase0Artifacts
    RTS
```

The patch replaces the 2-byte `BNE @SkipTimer` (CPU `$95B8`-`$95B9` in
bank 2, originally `D0 03`) with two `NOP`s, so the branch is never
taken — execution always falls through to `JMP IncSubphase` regardless
of `DemoTimer`'s value. The outer `AND #$01`/`BEQ @SkipTimer` gate (which
only lets this code run on odd frames) is untouched, so the subphase
still advances on a frame boundary rather than mid-frame, but it now
happens on the very first odd frame reached instead of after 256 of
them — a couple of frames instead of roughly 512.

Two one-byte patches. Bank-uniqueness: none of the other six banks
mapped into `$8000`-`$BFFF` has `$D0`/`$03` at `$95B8`/`$95B9`
respectively — each bank holds unrelated code or data there, so the
compare bytes pin both patches to bank 2.

**Not live-verified:** derived from reading `AnimateDemoPhase0Subphase0`
in `src/Z_02.asm` and the bank-2 disassembly at `$95B8`, not from
observing it in-game.

## Monsters pursue their targets more persistently

**Code(s):** `XVLEAAEO` `XVLEPEZK`

**Effect:** Moblins, Goriyas, Octoroks, Vires, and Keese (the monster
types that already chase dropped Food) now beeline for it almost every
frame instead of only turning to follow it some of the time. This also
makes these same monster types chase Link far more relentlessly when no
Food is out, since they share the same targeting code.

**How it works:** When Food is active, `UpdateBoomerangOrFood`
(`src/Z_07.asm`) unconditionally overwrites the shared `ChaseTargetX`/
`ChaseTargetY` variables with the Food's position (for the eligible
monster types), and leaves them there for as long as the Food is out.
Every wandering monster's AI (`Wanderer_TargetPlayer`, `src/Z_04.asm`)
already steers toward whatever `ChaseTargetX`/`ChaseTargetY` currently
holds — but only some of the time:

```
    LDA ObjTurnRate, X
    CMP Random+1, X
    BCC @TurnIfTime             ; turn rate < random: wander/turn randomly instead
    LDA ObjState
    CMP #$FF
    BEQ @TurnIfTime
    ; ...falls through to actually turn toward ChaseTargetX/Y...
```

Each monster type has a fixed `ObjTurnRate`, and each decision point
this is compared against a random byte (`Random+1, X`) — if the random
byte wins, the monster ignores the chase target for this decision and
just wanders/turns on its own. This patch NOPs out the `BCC
@TurnIfTime` (CPU `$80B8`-`$80B9` in bank 4, originally `$90 $4A`), so
the random check can no longer skip the pursuit logic — every wanderer
now turns toward its current chase target (Food, if any is out and the
monster type is eligible; otherwise Link) at every decision point.

Two one-byte patches. Bank-uniqueness: checked `$80B8`-`$80B9` against
all 7 switchable banks. None of the other six banks has `$90`/`$4A` at
that address — each holds unrelated code or data there, so the compare
bytes pin both patches to bank 4.

**Not live-verified:** derived from reading `UpdateBoomerangOrFood`
(`src/Z_07.asm`) and `Wanderer_TargetPlayer` (`src/Z_04.asm`), plus the
bank-4 disassembly at `$80B8`, not from observing it in-game.

## Blue Ring costs 1 Rupee

**Code:** `PAVEIVXY`

**Effect:** The Blue Ring, sold in the overworld shop that normally
charges 250 Rupees for it, now costs only 1 Rupee.

**How it works:** Each overworld cave's wares are defined by two
parallel 3-entry arrays inside `LevelBlockOW.dat` (`.INCBIN`'d in
`src/Z_06.asm`, table E of that file, loaded at CPU `$8400` in bank 6):
one holding the 3 item IDs sold in that cave, the other holding the 3
matching prices. `InitCaveContinue` (`src/Z_01.asm`) picks out the
3-entry slice for the current cave and copies it into `CaveItemIds`/
`CavePrices`; `TakeItem` (`src/Z_01.asm`) later resolves an item ID to
an inventory slot via `ItemIdToSlot` and to an effect via
`ItemIdToDescriptor`. Item ID `$12` (18) maps to inventory slot `$0B`
(the ring slot) with descriptor `$21` (grade 1), confirming it's the
Blue Ring; item ID `$13` (19) is the Red Ring (grade 2) at the same
slot.

Scanning the decoded price table turns up cave index 16, ware slot 1
(0-indexed), selling item ID `$12` for price byte `$FA` (250) — the
Blue Ring's vanilla price. That price byte's file offset resolves to
CPU address `$866D` in bank 6. This patches that single byte from `$FA`
to `$01`.

One-byte patch. Bank-uniqueness: checked `$866D` against all 7
switchable banks. Bank 0 holds unused `$FF` filler there (harmless).
Banks 1-5 hold unrelated code bytes (`$1A`, `$20`, `$1C`, `$B0`, `$88`
respectively). Only bank 6 holds `$FA`, so the compare byte pins the
patch to bank 6.

**Not live-verified:** derived from reading `InitCaveContinue`,
`TakeItem`, `ItemIdToSlot`, and `ItemIdToDescriptor` in
`src/Z_01.asm`, decoding `bin/dat/LevelBlockOW.dat`'s cave price table,
and the bank-6 disassembly at `$866D`, not from observing it in-game.

## Dark dungeon rooms are always lit

**Code(s):** `AEYLZPEA` `AEPLITEA`

**Effect:** Dungeon rooms that are normally pitch black (except for a
small area you've lit with the Candle) now render fully lit from the
moment you enter them, with no fade-to-black and no need to use the
Candle.

**How it works:** Whether a dungeon room is dark is a single bit
(`$80`) in `LevelBlockAttrsE` — a per-room attribute byte loaded from
the dungeon's level data. Two identical copies of a helper routine,
`IsDarkRoom_Bank4` (`src/Z_04.asm`) and `IsDarkRoom_Bank5`
(`src/Z_05.asm`), read that bit for the current room:

```
    LDA CurLevel
    BEQ :+
    LDA LevelBlockAttrsE, Y
    AND #$80
:
    RTS
```

Room-scroll and room-entry code (`InitMode7_Sub5`/`@CheckDark`/
`@DarkenRoom` and `InitMode4` in `src/Z_05.asm`) call these to decide
whether to kick off a fade-to-black `FadeCycle`, and `UpdateCandle`
(`src/Z_04.asm`) calls them to decide whether swinging the Candle
should start a fade-to-light. Both copies are duplicated because
they're called from different overlay banks; if only one were patched,
rooms would still go dark whenever the other bank was switched in.

This patches the `AND #$80` immediate operand in both copies to `AND
#$00`, at CPU `$B1F2` (bank 4) and CPU `$B695` (bank 5). With the mask
always producing 0, both routines report every room as "not dark," so
the fade-to-black is never triggered and rooms simply stay at their
normal brightness. `AnimateWorldFading`, `CandleState`, and
`FadeCycle` are untouched — the Candle can still be swung and simply
has nothing to brighten.

Two one-byte patches. Bank-uniqueness: checked `$B1F2` and `$B695`
against all 7 switchable banks. At `$B1F2`, bank 1 holds `$05` and
bank 5 holds `$C9` (unrelated code); banks 0, 2, 3, and 6 hold unused
`$FF` filler there (harmless) — only bank 4 holds `$80`. At `$B695`,
bank 1 holds `$60` (an unrelated `RTS`); banks 0, 2, 3, 4, and 6 hold
unused `$FF` filler there (harmless) — only bank 5 holds `$80`. Each
compare byte pins its patch to the intended bank.

**Not live-verified:** derived from reading `IsDarkRoom_Bank4`
(`src/Z_04.asm`), `IsDarkRoom_Bank5` (`src/Z_05.asm`), the dark-room
handling in `InitMode7_Sub5`/`InitMode4`/`UpdateCandle`, and the
bank-4/bank-5 disassembly at `$B1F2`/`$B695`, not from observing it
in-game.

## Can't collide with flames from the Candle or Magic Book

**Code:** `AENYUETA`

**Effect:** The standing-fire object Link creates — by swinging the
Candle, or (with the Book of Magic) wherever the Magical Rod's beam
stops — no longer shoves or damages Link when he walks into it.
Everything else about the fire (its lifetime, its animation, its
ability to damage/kill monsters via `CheckMonsterBombOrFireCollision`)
is unaffected.

**How it works:** The Candle's and the Book-empowered Rod's flames are
the same object: `WieldCandle` (`src/Z_01.asm`) activates weapon slot
`$10` or `$11` in state `$21` (moving fire), which `UpdateFire`
(`src/Z_07.asm`, called every frame from the fixed-bank weapon-update
loop as `UpdateBombOrFire`) advances to state `$22` (standing fire)
once it has traveled $10 subpixels. Bank 7's `HandleShotBlocked`
routine (used by the sword-beam-leaves-flames cheat, and natively by
the Rod's beam when the Book of Magic is owned) calls the very same
`WieldCandle`, so both flame sources funnel into this one collision
check.

`UpdateFire`'s own bespoke player-collision code (distinct from the
generic `CheckLinkCollision` used by monsters) runs every frame a fire
is standing:

```
    LDA ObjInvincibilityTimer
    BNE L1F91D_Exit             ; Link invincible -- no collision
    ...
    LDY $00
    LDX #$00
    LDA #$0E                    ; collision threshold: 14px in X and Y
    JSR DoObjectsCollide
    BEQ L1F91D_Exit             ; too far apart -- no collision
    ...
    JMP Link_BeHarmed           ; shove + damage Link half a heart
```

`DoObjectsCollide`'s threshold argument (in `A`) is copied into both
`[$0D]` (horizontal) and `[$0E]` (vertical) and compared against the
actual pixel distance with `CMP` / `BCS`: the objects only register as
colliding if the distance is *less than* the threshold. This patches
the `LDA #$0E` at CPU `$F8F2` (bank 7) so its operand byte at `$F8F3`
becomes `$00` instead of `$0E`. With a threshold of 0, the unsigned
distance comparison (`CMP #$00`) always sets the carry flag — `BCS`
therefore always takes the "no collision" path, regardless of how
close Link actually is to the fire.

One-byte patch. CPU `$F8F3` falls in bank 7, the fixed bank permanently
mapped to `$C000`-`$FFFF` under this ROM's MMC1 setup — unlike the
switchable `$8000`-`$BFFF` window, this address is unambiguous on
hardware no matter which of the other banks is switched in, so no
cross-bank check applies here; the disassembler itself confirms the
bank argument is ignored above `$C000`. The compare byte (`$0E`) is
included only to satisfy this project's "codes must have a compare
byte" rule.

**Not live-verified:** derived from reading `WieldCandle`
(`src/Z_01.asm`), `UpdateFire`/`UpdateBombOrFire`
(`src/Z_07.asm`), and `DoObjectsCollide`/`DoObjectsCollideWithThresholds`
(`src/Z_01.asm`), plus the bank-7 disassembly at `$F8D9`-`$F902`, not
from observing it in-game.

## Link keeps spinning much longer when he dies

**Code:** `AXVAUGIE`

**Effect:** After Link's hearts run out, the four-direction spin he
does before the screen fades to grey now takes about 8 times as long,
so the spin is much more prominent before the "GAME OVER" sequence
continues.

**How it works:** The death sequence is game mode `$11`. Once its
setup finishes (`InitMode11_Sub1`, `src/Z_05.asm`), `DeathModeCounter`
is set to `$04` — the number of full rotations Link performs — and
`UpdateMode11Death_Sub7` (`src/Z_05.asm`) drives the spin every frame:

```
    LDA $E5                     ; DeathModeCounter
    BEQ L8CD7                   ; Once it's 0, move to the next submode.
    LDA $33                     ; ObjTimer+11
    BNE L8CF2                   ; If the timer hasn't expired, just redraw Link.
    LDA #$05                    ; Once it expires, arm it again...
    STA $33                     ; ...and turn Link to the next direction.
    ...
```

Link holds each of the four facing directions for however many frames
`ObjTimer+11` (zero page `$33`) is reloaded with — 5 frames per
direction in vanilla, so a full down→left→up→right rotation take 20
frames, and all `$04` rotations take about 80 frames (~1.3 seconds)
before `DeathModeCounter` reaches 0 and the sequence advances to the
grey fade-out.

This patches the `LDA #$05` reload at CPU `$8CE3` (bank 5) to `$28`
(40 decimal) — eight times the original delay. Link now holds each
direction for 40 frames, so a full rotation takes 160 frames and all
four rotations take about 640 frames (~10.7 seconds) before advancing.
`DeathModeCounter` itself (and the rest of the death sequence) is
untouched, so the number of rotations and everything after the spin
stays the same — only its pace changes.

One-byte patch. Bank-uniqueness: checked `$8CE3` against all 7
switchable banks. Bank 0 and bank 1 hold unused `$FF` filler there
(harmless); banks 2 and 6 hold `$00` (`BRK`, unrelated); bank 3 holds
`$FD`; bank 4 holds `$84`. Only bank 5 holds `$05`, so the compare byte
pins the patch to bank 5.

**Not live-verified:** derived from reading `InitMode11_Sub1` and
`UpdateMode11Death_Sub7` (`src/Z_05.asm`), plus the bank-5
disassembly at `$8A60`-`$8A96` and `$8CDA`-`$8D00`, not from observing
it in-game.

## Enemy destruction animation loops instead of completing

**Code(s):** `XVPYXGEU` `XVPYUGPE`

**Effect:** When a monster dies, the two-frame death-spark flicker it
normally shows for a moment now repeats indefinitely instead of
finishing — the monster never drops an item and never actually
disappears, since the code path that would end the animation is never
reached. Monsters spawning in from a puff of cloud are affected the
same way, since they share this same routine: instead of the cloud
resolving into a live monster, once the counter free-runs long enough
it will eventually cycle back through the whole cloud-spawn animation
again too.

**How it works:** Every object with a nonzero `ObjMetastate` — a
monster that's dying, or one still spawning from a cloud — is routed
away from its normal per-type update routine and into the shared
`UpdateMetaObject` (`src/Z_07.asm`), which calls
`AnimateAndDrawMetaObject` to draw the current animation frame and
advance the counter, then decides whether the animation is finished:

```
UpdateMetaObject:
    JSR AnimateAndDrawMetaObject

    ; Go handle end metastates (4 and $14) specially.
    LDA ObjMetastate, X
    AND #$0F
    CMP #$04
    BCS UpdateMetaObjectEnd

DoNothing:
    RTS
```

`ObjMetastate` counts up by one every 6 frames. Values `$00`-`$03`
draw the spawning-cloud frames; `$10` and above draw the death-spark
frames (alternating every step, based on bit 0). Once the low nibble
reaches `$04` — metastate `$04` (cloud finished) or `$14` (spark
finished) — `UpdateMetaObjectEnd` takes over: for `$04` it just resets
the metastate so the monster starts updating normally; for `$14` it
additionally converts the monster into a dropped item first
(`ObjType` becomes `$60`, `SetUpDroppedItem` runs) before doing the
same reset.

This NOPs out the `BCS UpdateMetaObjectEnd` at CPU `$FC92`-`$FC93`
(bank 7), replacing both the opcode (`$B0`) and its operand (`$01`)
with `$EA` (`NOP`). Execution now always falls through to `DoNothing`
(`RTS`) instead, so `UpdateMetaObjectEnd` — and therefore the item
drop and the metastate reset — is never reached. `ObjMetastate` just
keeps incrementing every 6 frames as a free-running 8-bit counter:
values `$10`-`$FF` all render as death-spark frames (the animation
code only looks at the low nibble and bit 0), so it flickers
continuously; once it wraps past `$FF` back to `$00`-`$0F`, it briefly
shows the spawning-cloud frames before climbing back past `$10` into
the spark frames again, endlessly repeating the whole cycle.

Two one-byte patches. Both CPU addresses fall in bank 7, the fixed
bank permanently mapped to `$C000`-`$FFFF` under this ROM's MMC1
setup, so no cross-bank check applies — the disassembler confirms the
bank argument is ignored above `$C000`. The compare bytes (`$B0`,
`$01`) are included only to satisfy this project's "codes must have a
compare byte" rule.

**Not live-verified:** derived from reading `UpdateMetaObject`,
`UpdateMetaObjectEnd`, and `AnimateAndDrawMetaObject`
(`src/Z_07.asm`), plus the bank-7 disassembly at `$FA0C`-`$FA30` and
`$FC88`-`$FCD7`, not from observing it in-game.

## Square 0 channel plays garbled notes

**Code:** `NGEOSKEZ`

Tags: `play-start`

This is a cleaner version of the 6-letter code `NGAOSG`: same effect, but
with a compare byte so it only patches the bank that actually holds this
routine.

**Effect:** Whenever a new note starts on the APU's Square 0 channel —
which covers both background music (the melody line) and the short
one-shot tunes like the item-get jingle and the "heart warning" beep —
the frequency and length values written to the sound hardware are wrong,
so the note comes out garbled instead of on-pitch. Square 1 notes and the
triangle/noise/DMC channels are unaffected.

**How it works:** `EmitSquareNote0` (`src/Z_00.asm`) is the shared
routine both `DriveSong` (background music) and `DriveTune0` (short
one-shot tunes) call to start a new note on Square 0:

```
; Params:
; A: offset of a note in period table
;
EmitSquareNote0:
    TAY
    LDA NotePeriodTable+1, Y
    BEQ Exit
    STA CurNoteLowPeriodSq0
    STA Sq0Timer_4002
    LDA NotePeriodTable, Y
    ORA #$08
    STA Sq0Length_4003

Exit:
    RTS
```

`TAY` copies the note ID from `A` into `Y` so the two `NotePeriodTable`
lookups can use it as an index.

This patches the `TAY` opcode (`$A8`) at CPU `$9C0D` (bank 0) to `$C7`,
which the 2A03 decodes as the undocumented opcode `DCP` (zero page) — a
two-byte instruction, unlike the one-byte `TAY` it replaces. Because it's
one byte longer, it swallows the next byte (`$B9`, the opcode of the
`LDA $9F01,Y` that used to follow) as its own operand, and every
instruction after that decodes shifted by one byte relative to the
original code, until the byte stream happens to re-align two instructions
later at the original `BEQ Exit`. In between, `DCP $B9` decrements
zero-page `$B9` and sets flags from comparing it to `A`, and `ORA
($9F,X)` replaces `A` with an unrelated value read through a zero-page
pointer — so `Exit` is reached (or not) based on the wrong condition, and
`Y` is never actually updated to the note ID. The two `STA`s that follow
still run, but they store this corrupted `A` and index `NotePeriodTable`
with whatever `Y` already held from unrelated code, instead of the
values `TAY`/the period-table lookups were supposed to produce — so the
channel's timer and length registers end up loaded with garbage instead
of the intended note.

One one-byte patch. Bank 1 (`$FF`), bank 2 (`$FF`), bank 3 (`$04`), bank
4 (`$03`), bank 5 (`$9B`), and bank 6 (`$7F`) all hold different,
unrelated bytes at `$9C0D` — bank 3's byte happens to be a data byte
inside an unrelated overworld column-heap table (`ColumnHeapOW1`) that
the original 6-letter code (with no compare byte) would have silently
corrupted too, along with whatever bank 1/2/4/5/6 keep there. The compare
byte (`$A8`) pins the patch to bank 0, so none of that collateral damage
happens.

**Not live-verified:** derived from reading `EmitSquareNote0`,
`DriveSong`, and `DriveTune0` (`src/Z_00.asm`), the bank-0 disassembly at
`$9C08`-`$9C20`, and the same address across banks 1-6, not from
observing it in-game.

## Buy shop items regardless of Rupee count

**Code(s):** `XVTESAEO` `XVTEVALK`

This is a cleaner version of the 8-letter code `ANVESAEP`: same effect,
but a deterministic patch instead of one that depends on incidental CPU
flag state.

**Effect:** Picking up an item in a shop cave always completes the
purchase, even with zero (or otherwise insufficient) Rupees. Rupees
still get spent (and can underflow to a very large count if you couldn't
really afford it) — only the check that would normally refuse the
purchase is disabled.

**How it works:** the shop-purchase branch of `@PickedUpWare`
(`src/Z_01.asm`, bank 1) gates the purchase on Rupee count:

```
    ; If rupees < price, then return.
    LDA InvRupees
    CMP CavePrices, X
    BCC Exit

    ; Pass the price to pay for the item.
    LDA CavePrices, X
    JSR PostDebit
```

`ANVESAEP` decodes to CPU `$88ED` (bank 1, compare `$90`) with new value
`$70`. `$90` is the opcode of the `BCC Exit` shown above; `$70` is the
opcode of `BVS` (branch if oVerflow set) — both are two-byte relative
branches, so swapping one for the other doesn't shift any following
code. But `CMP` doesn't touch the overflow flag, so this just makes the
purchase branch on whatever `V` happens to already hold left over from
earlier, unrelated instructions, rather than on anything to do with
Rupee count. In practice `V` is clear far more often than not (it takes
a signed-overflowing `ADC`/`SBC` to set it, and few nearby instructions
do that), so purchases usually go through — hence "always allows you to
buy anything" — but it's not guaranteed, and if something upstream
happens to leave `V` set, the original Rupee check re-asserts itself by
coincidence.

This patches the same 2-byte `BCC Exit` (CPU `$88ED`-`$88EE`, originally
`$90 $43`) to `$EA $EA` (`NOP` `NOP`) instead. With the branch itself
gone rather than retargeted to an unrelated flag, the purchase always
goes through unconditionally — no dependence on `V`'s incidental state.

Two one-byte patches. Bank 0 (`$FF`/`$FF`), bank 2 (`$00`/`$00`), bank 3
(`$00`/`$00`), bank 4 (`$60`/`$60`), bank 5 (`$3F`/`$87`), and bank 6
(`$03`/`$0D`) all hold different, unrelated bytes at `$88ED`/`$88EE`, so
the compare bytes (`$90`, `$43`) pin both patches to bank 1.

**Not live-verified:** derived from reading `@PickedUpWare`
(`src/Z_01.asm`), the bank-1 disassembly at `$88EA`-`$88F2`, and the
same two addresses across banks 0 and 2-6, not from observing it
in-game.

## Enemies take much longer to appear from clouds in the middle of a screen

**Code:** `ATXYEZTA`

**Effect:** When a monster spawns via a puff-of-smoke cloud in the
middle of a room or overworld screen (rather than walking in from a
screen edge), the cloud animation lasts about 16x longer — roughly 6.4
seconds instead of 0.4 seconds — before the monster becomes active.
Monsters that walk in from the edges of the screen are unaffected,
since they never go through this cloud animation.

**How it works:** `AnimateAndDrawMetaObject` (`src/Z_07.asm`, fixed
bank at `$C000`-`$FFFF`) drives the spawn-cloud animation via
`ObjMetastate`, which starts at 0 and advances through 4 stages before
the object is treated as fully spawned (`UpdateMetaObjectEnd`, once
`ObjMetastate` reaches 4). Each stage lasts until `ObjTimer` counts
down to 0, at which point it's reset and the next stage begins:

```
@CheckMetaObjTimer:
    LDA ObjTimer, X
    BNE @Exit

@IncMetastate:
    LDA #$06                    ; 6 frames per stage
    STA ObjTimer, X
    INC ObjMetastate, X
```

This patches the immediate operand of `LDA #$06` (CPU `$FA20`,
originally `$06`) to `$60` (96 frames per stage), stretching all 4
stages from a total of 24 frames to 384 frames.

One-byte patch. This address is in the fixed bank, always mapped at
`$C000`-`$FFFF` regardless of which switchable bank is selected, so
there's no cross-bank ambiguity to check.

**Not live-verified:** derived from reading `AnimateAndDrawMetaObject`
and `UpdateMetaObject`/`UpdateMetaObjectEnd` (`src/Z_07.asm`) and the
fixed-bank disassembly at `$FA0C`-`$FA26`, not from observing it
in-game.

## Enemies take much longer to come in from the edges of a screen

**Code:** `AGXNXIZA`

**Effect:** In dungeon rooms that spawn monsters from the screen edges
(rather than from a cloud in the middle), each monster takes roughly
13-16x longer to walk on screen after the previous one — about 10.7 to
11.2 seconds apart instead of 0.3 to 0.8 seconds. Monsters that spawn
via a cloud in the middle of the screen are unaffected, since they
don't use this timer.

**How it works:** the edge-spawn code (`src/Z_07.asm`, fixed bank at
`$C000`-`$FFFF`) uses `MonstersFromEdgesLongTimer` (zero page `$4B`) to
pace how often a new monster is allowed in from an edge. It's one of
several "long timer" variables (`ChaseLongTimer`, `SwordBlockedLongTimer`,
`RedLeeverLongTimer`, all in `src/Variables.inc`) that get decremented
once every 10 frames by shared timer-tick code, so each unit here is
10 frames:

```
    ; Set the monsters-from-edges long timer to a random value
    ; between 2 and 5. So, it will last 20 to 50 frames.
    LDA Random+1, X
    AND #$03
    CLC
    ADC #$02
    STA MonstersFromEdgesLongTimer
```

This patches the immediate operand of `ADC #$02` (CPU `$FD2A`,
originally `$02`) to `$40` (64), so the random range becomes
64-67 units (640-670 frames) instead of 2-5 units (20-50 frames).

One-byte patch. This address is in the fixed bank, always mapped at
`$C000`-`$FFFF` regardless of which switchable bank is selected, so
there's no cross-bank ambiguity to check.

**Not live-verified:** derived from reading the edge-spawn code and
`FindNextEdgeSpawnCell` (`src/Z_07.asm`, `src/Z_05.asm`), the
`MonstersFromEdgesLongTimer` definition (`src/Variables.inc`), and the
fixed-bank disassembly at `$FD26`-`$FD2C`, not from observing it
in-game.

## Play the "secret found" fanfare on every screen transition

**Code(s):** `GEIVVZIA` `OETTUXZL` `EOTTKXEL`

**Effect:** The "secret found" fanfare tune plays every time a new
room or screen is entered — every overworld scroll, every cave/dungeon
doorway, every stairway. As a side effect, room items stop being
created: dungeon room items (keys, compasses, maps, weapons, etc.),
the overworld heart container in room `$5F`, and push-block objects
never appear, because the same routine that would have created them is
what's been replaced to play the fanfare instead. Existing items
already placed as free-standing objects are unaffected.

**How it works:** in vanilla code, one specific overworld screen
(upper-right of the map) is home to a secret hidden under an Armos
statue; walking onto that screen and finding the correct Armos calls
`PlaySecretFoundTune` (`src/Z_04.asm`, bank 4) — a tiny routine that
just requests the tune:

```
PlaySecretFoundTune:
    LDA #$04
    STA Tune1Request
    RTS
```

Every room/screen entry — overworld or underworld, by scrolling, door,
cave, or stairway — runs `RunCrossRoomTasksAndBeginUpdateMode`
(`src/Z_07.asm`, fixed bank at `$C000`-`$FFFF`), which unconditionally
switches to bank 5 and calls `CreateRoomObjects` to set up that room's
item/push-block object:

```
    LDA #$05
    JSR SwitchBank
    JSR CreateRoomObjects
```

This patches all three of those bytes: the bank number `$05` (CPU
`$EADE`) to `$04`, and the `JSR CreateRoomObjects` target address
(CPU `$EAE3`-`$EAE4`, originally `$3A $B8` i.e. `$B83A`) to `$81 $90`
i.e. `$9081` — the address of `PlaySecretFoundTune`. Since
`PlaySecretFoundTune` only touches a RAM variable (no bank-5-specific
code or data), redirecting both the bank switch and the call target
together keeps everything self-consistent: the call now runs
`PlaySecretFoundTune` in bank 4 instead of `CreateRoomObjects` in
bank 5, on every single room transition.

Three one-byte patches, all in the fixed bank, so there's no
cross-bank ambiguity to check.

**Not live-verified:** derived from reading `RunCrossRoomTasksAndBeginUpdateMode`
(`src/Z_07.asm`), `PlaySecretFoundTune` and the Armos secret-reveal
code in `InitArmos`-family init code (`src/Z_04.asm`), `CreateRoomObjects`
(`src/Z_05.asm`), and the fixed-bank disassembly at `$EADD`-`$EAE5`,
not from observing it in-game.

## Enemy fireballs freeze in midair

**Codes:** `GKNEGLAX` `IENEILPY`

**Effect:** Fireballs (the Wizzrobes' and Aquamentus's projectile, and
similar enemy fireballs) no longer harm Link or bounce off his shield.
They fly straight through him as if he weren't there, and are never
destroyed by touching him. Fireballs are still destroyed normally by
hitting a wall or leaving the room, and their movement/animation is
unaffected. Collision for other monster shots (arrows, boomerangs,
"regular" monster shots) and for melee-touching monsters is unaffected,
since each shot type checks its own collision independently.

**How it works:** `UpdateFireball` (`src/Z_04.asm`, bank 4) ends every
frame by funneling into a shared collision check:

```
        jsr     CheckShotLinkCollision          ; 83FC 20 71 83
        lda     ShotCollidesWithLink             ; 83FF AD 4B 03
        bne     @DestroyMonster                  ; 8402 D0 D3
        jmp     L_DrawShot                        ; 8404 4C 05 83
```

`CheckShotLinkCollision` calls the generic `CheckLinkCollision`
(`src/Z_01.asm`), which is shared by every monster and monster-shot
type in the game (regular melee monsters, arrows, boomerangs, other
monster shots) — it's the routine that actually applies damage/shove
to Link via `HarmLink`. Patching inside it would remove collision for
everything, not just fireballs. Instead, this patches the `jsr
CheckShotLinkCollision` at CPU `$83FC` into `jmp L_DrawShot`: opcode
`$20` (JSR) becomes `$4C` (JMP), and the operand's low byte `$71`
(pointing at `CheckShotLinkCollision` = `$8371`) becomes `$05`
(pointing at `L_DrawShot` = `$8305`) at CPU `$83FD`. The operand's
high byte (`$83`) is identical for both targets, so only these two
bytes need to change. This skips `CheckShotLinkCollision` (and thus
`CheckLinkCollision`) entirely for fireballs, so Link is never even
checked for a collision with one — no damage, no shield bounce, and
the fireball is never destroyed by touching him.

Bank 4 (`Z_04.asm`) is a switchable bank. Checked CPU `$83FC`-`$83FD`
across the other six switchable banks (0, 1, 2, 3, 5, 6): none contain
byte `$20` at `$83FC` or `$71` at `$83FD`, so both codes only take
effect with bank 4 switched in.

**Not live-verified:** derived from reading `UpdateFireball` and
`CheckShotLinkCollision` (`src/Z_04.asm`), `CheckLinkCollision`
(`src/Z_01.asm`), and the bank-4 disassembly at `$83FC`-`$8404`, not
from observing it in-game.

## Replace the tile floor in dungeons with a different pattern

**Code:** `ATOXYYGX`

**Effect:** Every dungeon room's open floor tile is drawn using a
different tile than normal. The new tile is another value already used
elsewhere in the same lookup table for a walkable single-tile square, so
the floor remains fully walkable — only its appearance changes.

**How it works:** `LayoutUWFloor` (`src/Z_05.asm`) lays out each
underworld room's floor from an 8-entry table, `PrimarySquaresUW`:

```
PrimarySquaresUW:
    .BYTE $B0, $74, $94, $B4, $70, $68, $F4, $24
```

Each room's column data picks one of these 8 entries per square (a 3-bit
index, `AND #$07`) and hands it to `WriteSquareUW`, which either draws
four different consecutive tiles as a 2x2 block (values `$70`-`$F2`) or
repeats one tile across all four positions (everything else). Index 7
(`$24`, the last entry) is the plain open floor — the value every empty
square in a room resolves to. Index 5 (`$68`) is a different value in
the same "repeat one tile" category, already used elsewhere as a
walkable single-tile square.

This patches index 7's byte at CPU `$A71F` (bank 5) from `$24` to `$68`,
so floor squares render with index 5's tile instead of their own.
Walkability is governed separately by `ObjectFirstUnwalkableTile`
(`$34A`), which every underworld room load sets to `$78` (see
`SetupObjRoomBounds` / `ObjectRoomBoundsUW`, and the "Link can always
walk on water" entry above); both `$24` and `$68` are well under that
threshold, so the swap doesn't change what's walkable, only what it
looks like.

**Side effect:** CPU `$A71F` isn't uniquely bank 5's. Bank 6 holds the
opening story text (`StoryTileAttrTransferBuf`, an `INCBIN`'d data
block read by `Z_06.asm`) as a run of mostly blank-space tile bytes
(`$24`), and by coincidence one of those padding bytes lands at this
same address, in the blank padding before the "SHE WAS CAPTURED" line
(not inside any word). Because this is a data-value match, not a
bank-specific one, the code also fires when bank 6 is switched in,
turning that one padding space into whatever glyph tile `$68` is,
during the intro story sequence. Checked CPU `$A71F` across the other
five switchable banks (0, 1, 2, 3, 4): none hold `$24` there, so this
collision is limited to bank 6.

**Not live-verified:** derived from reading `LayoutUWFloor`,
`WriteSquareUW`, `PrimarySquaresUW` (`src/Z_05.asm`), the bank-5
disassembly at `$A718`-`$A71F`, and `StoryTileAttrTransferBuf`'s data
(`src/Z_06.asm`, `bin/dat/StoryTileAttrTransferBuf.dat`), not from
observing it in-game.

## Every overworld screen has a heart container waiting outside

**Code:** `ESOUUAEY`

Tags: `demo-ready` `play-start` `curated`

**Effect:** Walk onto any overworld screen and a Heart Container is sitting
there at pixel (`$C0`, `$90`) — right of centre, a little below the middle of
the play area. Touch it and it's yours, permanently raising your maximum
hearts. One per screen: once collected, that screen's flag is set and it
doesn't come back. The one screen that *loses* its heart container is screen
`$5F`, the one that normally has it (see the caveat).

**How it works:** `CreateRoomObjects` (`src/Z_05.asm`) is the routine that
decides what the "room item" object (slot `$13`) is when a room loads. In the
overworld it takes a dedicated branch, `@MakeHeartContainerOW`, which hard-
codes the single outdoor heart container:

```
@MakeHeartContainerOW:
    ; Try to make the heart container in OW.
    LDA #$1A                    ; Heart container
    STA RoomItemId

    ; Load the coordinates of the heart container in
    ; OW room $5F.
    LDA #$C0
    LDY #$90

    ; If in mode 5, and in room $5F, then go store the coordinates
    ; in the object slot.
    LDX GameMode
    CPX #$05
    BNE :+
    LDX RoomId
    CPX #$5F
    BEQ @StoreLocation
:
    ; Else deactivate the object.
    DEC ObjState+19
    RTS
```

The screen test is the single branch `BEQ @StoreLocation` at CPU `$B89B`
(bank 5, opcode byte `$F0`). This patches it to `$D0` — `BNE` — inverting the
test: every overworld screen *except* `$5F` now falls through to
`@StoreLocation`, which stores the already-loaded `$C0`/`$90` coordinates into
`ObjX+19`/`ObjY+19` and leaves the object active. `RoomItemId` was already set
to `$1A` two instructions earlier, and `ItemIdToSlot`/`ItemIdToDescriptor`
(`src/Z_01.asm`) map item ID `$1A` to slot `$18` with descriptor `$10`, which
`TakeItem`'s `@TakeHeartContainer` branch turns into "+1 container, +1 heart,
capped at 16". One-byte patch; the compare byte (`F0`) pins it to this
bank/offset — bank 7 also holds `$F0` at that offset, but bank 7 is the fixed
top bank at `$C000` and is never mapped into the `$8000` window, so it can't
collide.

**Caveat — screen `$5F` loses its heart container:** the branch is inverted,
not disabled, so the one screen that normally holds the outdoor heart
container is now the one screen that doesn't.

**Caveat — shares the "item taken" room flag with cave secrets:**
`TryTakeItem` (`src/Z_01.asm`) marks a collected room item by calling
`SetRoomFlagUWItemState`, which does `ORA #$10` on the current room's flag
byte — and the cave code in the same file calls that identical routine to
"mark this secret taken" for paying old men. `TryTakeRoomItem` also checks
that same flag before letting you pick anything up. So on any screen where you
have already settled a cave's business, the free heart container won't be
there; and grabbing the free heart container on a screen sets the flag that
that screen's cave uses, so expect caves on looted screens to act as though
their secret was already handled.

**Not live-verified:** derived from reading `CreateRoomObjects`
(`src/Z_05.asm`) and `TryTakeRoomItem`/`TakeItem`/`ItemIdToSlot`
(`src/Z_01.asm`), not from observing it in-game.

## Every overworld screen has a boomerang waiting outside

**Code:** `ESOUUAEY` + `IOEUXEZO`

Tags: `demo-ready` `play-start`

**Effect:** The same free item on every overworld screen as the cheat above,
but it's a Boomerang instead of a Heart Container. Pick it up and it lands in
the wooden-boomerang slot, ready to select and throw.

**How it works:** Same mechanism as the heart-container cheat above —
`ESOUUAEY` flips `@MakeHeartContainerOW`'s `BEQ @StoreLocation` (CPU `$B89B`,
bank 5) to `BNE`, so every overworld screen other than `$5F` leaves the room
item object active at (`$C0`, `$90`).

`IOEUXEZO` changes what that item *is*. `@MakeHeartContainerOW` opens with

```
    LDA #$1A                    ; Heart container
    STA RoomItemId
```

and this patches the immediate operand at CPU `$B88A` (bank 5, originally
`$1A`) to `$1D`. In `ItemIdToSlot` (`src/Z_01.asm`) item ID `$1D` maps to item
slot `$1D`, which is `InvBoomerang` (`$0674`); its `ItemIdToDescriptor` entry
is `$01` — class 0, a plain "you have it" boolean — so `TakeItem` falls all
the way through to `SetItemValue` and stores 1. Two one-byte patches, each
compare-pinned to its own bank/offset.

**Caveats:** identical to the heart-container cheat above — screen `$5F` gets
nothing, and the pickup shares the `$10` room-flag bit with cave secrets.

**Not live-verified:** derived from reading `CreateRoomObjects`
(`src/Z_05.asm`) and `ItemIdToSlot`/`ItemIdToDescriptor` (`src/Z_01.asm`), not
from observing it in-game.

## After being hit, stay immune to damage for much longer

**Code:** `NNVUGVAO`

**Effect:** Getting hit still costs hearts and still knocks Link back, but the
mercy-invincibility that follows lasts `$FF` frames (255, roughly 4¼ seconds)
instead of `$18` (24, about ⅖ of a second). Link flashes through the palette
cycle the whole time and walks through monsters, fireballs and everything else
without taking a second hit.

**How it works:** `BeginShove` (`src/Z_01.asm`, part of the `BANK_01_CODE`
block that gets copied into Save RAM and executed from `$6C90`) handles the
knockback when Link is the defender:

```
    ; Mark Link invincible $18 frames, and should move $20 pixels.
    LDA #$18
    STA ObjInvincibilityTimer
    LDA #$20
    STA ObjShoveDistance
```

`CheckLinkCollision` in the same file is what consumes that timer:

```
    ; If Link is invincible, or we have the magic clock,
    ; or Link is stunned, or the monster is stunned;
    ; then return no collision.
    LDA ObjInvincibilityTimer
    ORA InvClock
    ...
    BNE L73A9_Exit
```

This patches the immediate operand at CPU `$B6EC` (originally `$18`) to
`$FF`. Because bank 1's code runs from a RAM copy, the patch lands on the
*ROM* bytes at `$B6EC` in bank 1 — the Game Genie intercepts the read while
the copy loop is fetching them, so the relocated code at `$7E28` gets the
patched value. One-byte patch; the compare byte (`18`) pins it to that
bank/offset, and no other PRG bank holds `$18` at `$B6EC`.

**Caveat — Link flashes for the whole 255 frames.** `Anim_WriteSprite`
(`src/Z_01.asm`) substitutes `FrameCounter AND $03` for Link's sprite
attribute byte whenever `ObjInvincibilityTimer` is non-zero, so he cycles
through all four sprite palettes for the full duration.

**Caveat — this is the shove path only.** The same `LDA #$18` runs only when
`BeginShove` decides Link is the defender and he wasn't already invincible;
damage sources that don't shove aren't affected.

**Not live-verified:** derived from reading `BeginShove`,
`CheckLinkCollision`, and `Anim_WriteSprite` (`src/Z_01.asm`), not from
observing it in-game.

## Enemies always frozen as if you picked up a Clock

**Code:** `OZSTUZSE`

Tags: `play-start`

**Effect:** The magic-clock state is permanently on. Monsters stand still and
stop shooting, and Link is invincible — the full Clock effect, from the moment
you enter the first room, for the whole game.

**How it works:** The Clock is a single RAM flag, `InvClock` (`$066C`), and
roughly two dozen monster routines in `src/Z_04.asm` gate their behaviour on
it with the same idiom, e.g. in `UpdateCommonWanderer`:

```
    ; If we have the magic clock or the monster is stunned, then return.
    LDA InvClock
    ORA ObjStunTimer, X
    BNE Exit
```

and `CheckLinkCollision` (`src/Z_01.asm`) folds it into Link's invincibility
test (quoted in the mercy-invincibility cheat above). Nothing in the ROM ever
*decrements* `InvClock`; the only thing that clears it is
`ResetPlayerState` (`src/Z_07.asm`), which runs on every room transition:

```
ResetPlayerState:
    LDA #$00
    STA ObjState
    STA InvClock
    RTS
```

which assembles to `A9 00 / 85 AC / 8D 6C 06 / 60` at CPU `$EA51` (bank 7, the
fixed `$C000` bank). This patches the `STA ObjState` opcode at `$EA53` from
`$85` (`STA` zero page) to `$A9` (`LDA` immediate). The two bytes `85 AC`
become `A9 AC` — `LDA #$AC` — so the routine now reads

```
    LDA #$00        ; dead
    LDA #$AC
    STA InvClock    ; $AC is non-zero, so the clock reads as active
    RTS
```

Every room transition now *sets* the clock instead of clearing it. The value
doesn't matter: every reader only tests it for non-zero. One-byte patch; the
compare byte (`85`) pins it, and this address lives in the fixed top bank, so
no other bank can ever be mapped there.

**Caveat — Link's action state is no longer reset.** The patch consumes the
`STA ObjState` that `ResetPlayerState` used to perform, so Link's action state
now carries across room transitions, across the Continue/Save/Retry menu
(`src/Z_05.asm` calls `ResetPlayerState` there too) and into `InitMode6`. If
Link is mid-action when one of those happens, he keeps that state instead of
being returned to idle.

**Caveat — the clock doesn't show anywhere.** The inventory subscreen's draw
loop (`src/Z_05.asm`) stops at item slot `$12`, and the clock lives in slot
`$15`, so there's no on-screen indication that it's active.

**Not live-verified:** derived from reading `ResetPlayerState`
(`src/Z_07.asm`), the `InvClock` gates in `src/Z_04.asm`, and
`CheckLinkCollision` (`src/Z_01.asm`), not from observing it in-game.

## Map always active for the current dungeon

**Code:** `AAXLIAKY`

**Effect:** Every dungeon draws its level map as though you'd already found
the Map for it.

**How it works:** `InitMode3_Sub6` (`src/Z_05.asm`) is the submode that cues
the map graphic into the map area of the status bar when a level loads:

```
InitMode3_Sub6:
    LDA CurLevel
    BEQ :+                      ; If in OW, skip checking the level's map.
    JSR HasMap
    BEQ L1701A_Exit             ; If we don't have the map, go to the next submode.
:
    LDA #$44
    BNE SelectTransferBuf       ; Cue transfer of map in status bar, and go to next submode.
```

`HasMap` (`src/Z_05.asm`) returns `Items+$11 AND LevelMasks[level]` — zero
when this level's map bit isn't set. This patches the `BEQ`'s offset byte at
CPU `$B025` (bank 5, originally `$F4`) to `$00`, which makes the branch land
on the very next instruction — it no longer skips anything, so `LDA #$44` runs
and the map is cued regardless. One-byte patch; the compare byte (`F4`) pins
it to that bank/offset.

**Caveat — the Map icon still won't show in the subscreen.** The inventory
draw loop (`src/Z_05.asm`, `@LoopDrawItem`) calls `HasMap` separately when it
reaches item slot `$11` and skips the icon when it returns zero. That call is
untouched, so you get the map itself but not the little map icon beside it.

**Not live-verified:** derived from reading `InitMode3_Sub6` and `HasMap`
(`src/Z_05.asm`), not from observing it in-game.

## Compass always active for the current dungeon

**Code:** `AEETTTTG` + `AAKAYOPA`

**Effect:** Every dungeon shows the blinking Triforce-room marker on the map
as though you'd already found the Compass for it.

**How it works:** Two one-byte patches, both neutering a `BEQ` that guards a
`HasCompass` result. `HasCompass` (`src/Z_05.asm`) returns
`Items+$10 AND LevelMasks[level]`, i.e. zero when this level's compass bit
isn't set.

`AEETTTTG` handles the marker itself. `UpdateTriforcePositionMarker`
(`src/Z_07.asm`) is what places it:

```
UpdateTriforcePositionMarker:
    LDA CurLevel
    BEQ Exit                    ; If in OW, then return.
    LDA #$05
    JSR SwitchBank
    JSR HasCompass
    BEQ Exit                    ; If player hasn't gotten the compass, then return.
    LDA LevelInfo_TriforceRoomId
    LDX #$04
    JMP UpdatePositionMarker
```

This patches that branch's offset byte at CPU `$E686` (bank 7, the fixed
`$C000` bank; originally `$46`) to `$00`, so it falls through to
`LDA LevelInfo_TriforceRoomId` every time.

`AAKAYOPA` handles the marker's animation. `MovePositionMarkers`
(`src/Z_05.asm`) nudges the marker sprites each frame:

```
    ; If in UW and have the compass, then move the triforce position marker.
    LDA CurLevel
    BEQ Exit
    JSR HasCompass
    BEQ Exit
    LDA Sprites+88
    CLC
    ADC $00
    STA Sprites+88
```

This patches that branch's offset byte at CPU `$8147` (bank 5, originally
`$09`) to `$00`. Both compare bytes pin their patches to their own
bank/offset.

**Caveat — the Compass icon still won't show in the subscreen.** As with the
map cheat above, the inventory draw loop calls `HasCompass` separately for
item slot `$10` and that call is untouched.

**Not live-verified:** derived from reading `UpdateTriforcePositionMarker`
(`src/Z_07.asm`) and `MovePositionMarkers`/`HasCompass` (`src/Z_05.asm`), not
from observing it in-game.

## Zora can also appear on land

**Code:** `AAOEYNSA`

Tags: `demo-ready` `play-start`

**Effect:** On overworld screens flagged for Zoras, the Zora no longer has to
rise out of water — it can surface anywhere on the screen, including dry
ground, and spits its fireball from there.

**How it works:** `CheckZora` (`src/Z_04.asm`) picks a Zora spawn point by
trying up to 13 pseudo-random `$10`-pixel-aligned positions and testing the
tile under each one:

```
    ; Get the tile at that location.
    ; If it's not a water tile, then go loop again.
    JSR GetCollidableTileStill
    CMP #$8D
    BCC @NextLoopTileCandidate
    CMP #$99
    BCS @NextLoopTileCandidate

    ; Flag the zora active, and set up the object.
    INC ZoraActive
    LDA #$11                    ; Zora object type
    JMP SetTypeAndClearObject
```

Water is the tile range `$8D`-`$98`. This patches the lower bound's immediate
operand at CPU `$871F` (bank 4, originally `$8D`) to `$00`. `CMP #$00` always
leaves the carry set, so the `BCC` can never be taken and the lower bound
disappears — every tile below `$99`, water or not, is now a valid Zora spot.
One-byte patch; the compare byte (`8D`) pins it to that bank/offset.

**Caveat — only on Zora screens.** `CheckZora` still returns immediately
unless the room's attribute-A bit `$08` (the Zora flag) is set, and still
allows only one Zora at a time, so this widens *where* Zoras appear, not
*which screens* have them.

**Caveat — Zoras can surface inside scenery.** Any tile below `$99` now
qualifies, which includes tiles Link can't walk on, so expect Zoras coming up
out of rocks and trees. The Y range is unchanged (`$50`-`$DF`), so they stay
out of the status bar.

**Not live-verified:** derived from reading `CheckZora` (`src/Z_04.asm`), not
from observing it in-game.

## Start a new game with a maximum bomb capacity of 16

**Code:** `APKOKNAA`

Tags: `play-start`

**Effect:** Register a new name with this code active and that save file
starts with a bomb capacity of 16 instead of 8. Bomb pickups fill to 16 from
the very beginning, and each in-game bomb upgrade still adds another 4 on top.

**How it works:** `UpdateModeERegister` (`src/Z_02.asm`) is where a brand-new
save file gets its handful of non-zero starting values — everything else in
the `Items` block is left at zero by `FormatFileA`. The block runs once per
freshly named slot, writing through the file-B pointer at `[$C0]`, which
points at the file's `Items` block (`$0657` in profile terms):

```
    ; The save slot is not active.
    ;
    ; Initialize file B hearts value to 3 heart containers and 2 hearts.
    LDY #$18
    LDA #$22
    STA ($C0), Y
    INY                         ; Initialize file B heart partial to full.
    LDA #$FF
    STA ($C0), Y
    LDY #$25                    ; Initialize file B's max bombs to 8.
    LDA #$08
    STA ($C0), Y
```

Offset `$25` from `Items` is `MaxBombs` (`$067C`). This patches the `LDA #$08`
immediate at CPU `$9F4C` (bank 2, originally `$08`) to `$10`. The write itself
is unchanged, so `MaxBombs` is simply seeded with 16. One-byte patch; the
compare byte (`08`) pins it to that bank/offset.

The capacity is enforced by `TakeItem` (`src/Z_01.asm`), which clamps bomb
pickups with `CMP MaxBombs / BCC / LDA MaxBombs`; the in-game bomb upgrade in
the same file does `LDA MaxBombs / CLC / ADC #$04 / STA MaxBombs / STA
InvBombs`, so upgrades stack on top of the new starting value as usual.

**Caveat — this fires at name registration, not at "start".** The values are
written into the save file when you finish registering the name and press
Start over "End" on the REGISTER YOUR NAME screen. Turn the code on, register
a fresh name, and you can turn it off again — the value is baked into the
file (and covered by the checksum
`CalculateAndStoreFileBChecksumUncommitted` computes right afterwards).
Existing files are unaffected.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`) and `TakeItem` (`src/Z_01.asm`), not from observing it
in-game.

## Start a new game with 16 Bombs

**Code:** `PAKOXYIZ` + `APKOKNAA`

Tags: `play-start`

**Effect:** A newly registered save file starts with 16 Bombs already in the
inventory.

**How it works:** Same `UpdateModeERegister` new-file initialization block
(`src/Z_02.asm`) quoted in the bomb-capacity cheat above — but here *both*
halves of the `MaxBombs` write are repurposed. `PAKOXYIZ` changes the
`LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to `$01`, and
`APKOKNAA` changes the `LDA #$08` operand at CPU `$9F4C` (originally `$08`)
to `$10`. Offset `$01` from `Items` is `InvBombs` (`$0658`), so the store
writes 16 bombs instead of a bomb capacity. Two one-byte patches, each
compare-pinned to its own bank/offset.

**Caveat — the file starts with a bomb capacity of 0.** This cheat *replaces*
the only write to `MaxBombs`, so the new file's capacity is left at zero by
`FormatFileA`. You keep the 16 bombs you were given and can spend them, but
`TakeItem`'s `CMP MaxBombs / BCC / LDA MaxBombs` clamp means bomb pickups top
you up to 0 until you find a bomb upgrade (each adds 4).

**Caveat — fires at name registration.** Same as the bomb-capacity cheat
above: enable it, register a new name, and the value is baked into the file.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`) and `TakeItem` (`src/Z_01.asm`), not from observing it
in-game.

## Start a new game with the maximum number of keys

**Code:** `YPKOXYIZ` + `NYKOKNAE`

Tags: `play-start`

**Effect:** A newly registered save file starts with 255 keys — `TakeItem`'s
own ceiling, since it caps key pickups at `$FF`.

**How it works:** Same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the 16-bombs cheat above. `YPKOXYIZ` sets the
`LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to `$17` —
offset `$17` from `Items` is `InvKeys` (`$066E`) — and `NYKOKNAE` sets the
`LDA #$08` operand at CPU `$9F4C` (originally `$08`) to `$FF`. Two one-byte
patches, each compare-pinned to its own bank/offset.

**Caveat — the key counter is drawn as two digits.** The status bar has room
for a two-digit key count, so 255 will not display as "255".

**Caveat — the file starts with a bomb capacity of 0**, and the values are
written at name registration. Both as described in the 16-bombs cheat above.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`) and `TakeItem` (`src/Z_01.asm`), not from observing it
in-game.

## Start a new game with the Magical Boomerang

**Code:** `TPKOXYIX` + `PAKOKNAA`

Tags: `play-start`

**Effect:** A newly registered save file already holds the Magical Boomerang.

**How it works:** Same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the 16-bombs cheat above. `TPKOXYIX` sets the
`LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to `$1E` —
offset `$1E` from `Items` is `InvMagicBoomerang` (`$0675`) — and `PAKOKNAA`
sets the `LDA #$08` operand at CPU `$9F4C` (originally `$08`) to `$01`, the
"you have it" value that `ItemIdToDescriptor` (`src/Z_01.asm`) assigns this
item. Two one-byte patches, each compare-pinned to its own bank/offset.

**Caveat — the file starts with a bomb capacity of 0**, and the values are
written at name registration. Both as described in the 16-bombs cheat above.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`) and `ItemIdToSlot`/`ItemIdToDescriptor` (`src/Z_01.asm`), not
from observing it in-game.

## Start a new game with the Letter

**Code:** `YAKOXYIX` + `PAKOKNAA`

Tags: `play-start`

**Effect:** A newly registered save file already holds the Letter, unused, so
you can take it straight to a potion shop.

**How it works:** Same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the 16-bombs cheat above. `YAKOXYIX` sets the
`LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to `$0F` —
offset `$0F` from `Items` is `InvLetter` (`$0666`) — and `PAKOKNAA` sets the
`LDA #$08` operand at CPU `$9F4C` (originally `$08`) to `$01`. Value 1 means
"have it, not yet used"; the letter's use path in `src/Z_01.asm` does
`INC InvLetter` to move it to state 2. Two one-byte patches, each
compare-pinned to its own bank/offset.

**Caveat — the file starts with a bomb capacity of 0**, and the values are
written at name registration. Both as described in the 16-bombs cheat above.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`) and the letter handling in `src/Z_01.asm`, not from observing
it in-game.

## Start a new game with the Bow

**Code:** `LAKOXYIZ` + `PAKOKNAA`

Tags: `play-start`

**Effect:** A newly registered save file already holds the Bow.

**How it works:** Same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the 16-bombs cheat above. `LAKOXYIZ` sets the
`LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to `$03` —
offset `$03` from `Items` is `Bow` (`$065A`) — and `PAKOKNAA` sets the
`LDA #$08` operand at CPU `$9F4C` (originally `$08`) to `$01`. Two one-byte
patches, each compare-pinned to its own bank/offset.

**Caveat — you still need arrows and rupees.** The Bow alone doesn't fire;
arrows are a separate slot and each shot costs a rupee.

**Caveat — the file starts with a bomb capacity of 0**, and the values are
written at name registration. Both as described in the 16-bombs cheat above.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`), not from observing it in-game.

## Start a new game with the Food (Bait)

**Code:** `TAKOXYIZ` + `PAKOKNAA`

Tags: `play-start`

**Effect:** A newly registered save file already holds the Food.

**How it works:** Same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the 16-bombs cheat above. `TAKOXYIZ` sets the
`LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to `$06` —
offset `$06` from `Items` is `InvFood` (`$065D`) — and `PAKOKNAA` sets the
`LDA #$08` operand at CPU `$9F4C` (originally `$08`) to `$01`. Two one-byte
patches, each compare-pinned to its own bank/offset.

**Caveat — the file starts with a bomb capacity of 0**, and the values are
written at name registration. Both as described in the 16-bombs cheat above.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`), not from observing it in-game.

## Start a new game with the Red Candle

**Code:** `GAKOXYIZ` + `ZAKOKNAA`

Tags: `play-start`

**Effect:** A newly registered save file already holds the Red Candle — the
upgraded one, usable as many times per screen as you like.

**How it works:** Same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the 16-bombs cheat above. `GAKOXYIZ` sets the
`LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to `$04` —
offset `$04` from `Items` is `InvCandle` (`$065B`) — and `ZAKOKNAA` sets the
`LDA #$08` operand at CPU `$9F4C` (originally `$08`) to `$02`. The candle is
a graded item (`ItemIdToDescriptor` in `src/Z_01.asm` gives it class `$2x`):
1 is the Blue Candle, 2 the Red. Two one-byte patches, each compare-pinned to
its own bank/offset.

**Caveat — the file starts with a bomb capacity of 0**, and the values are
written at name registration. Both as described in the 16-bombs cheat above.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`) and `ItemIdToDescriptor` (`src/Z_01.asm`), not from observing
it in-game.

## Start a new game with Silver Arrows

**Code:** `ZAKOXYIZ` + `ZAKOKNAA`

Tags: `play-start`

**Effect:** A newly registered save file already holds the Silver Arrows.

**How it works:** Same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the 16-bombs cheat above. `ZAKOXYIZ` sets the
`LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to `$02` —
offset `$02` from `Items` is `InvArrow` (`$0659`) — and `ZAKOKNAA` sets the
`LDA #$08` operand at CPU `$9F4C` (originally `$08`) to `$02`. Arrows are a
graded item: 1 is the wooden arrow, 2 the silver. Two one-byte patches, each
compare-pinned to its own bank/offset.

**Caveat — you still need the Bow.** Arrows without a Bow can't be fired.

**Caveat — the file starts with a bomb capacity of 0**, and the values are
written at name registration. Both as described in the 16-bombs cheat above.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`) and `ItemIdToDescriptor` (`src/Z_01.asm`), not from observing
it in-game.

## Start a new game with the Raft

**Code:** `PAKOXYIX` + `PAKOKNAA`

Tags: `play-start`

**Effect:** A newly registered save file already holds the Raft.

**How it works:** Same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the 16-bombs cheat above. `PAKOXYIX` sets the
`LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to `$09` —
offset `$09` from `Items` is `InvRaft` (`$0660`) — and `PAKOKNAA` sets the
`LDA #$08` operand at CPU `$9F4C` (originally `$08`) to `$01`. Two one-byte
patches, each compare-pinned to its own bank/offset.

**Caveat — the file starts with a bomb capacity of 0**, and the values are
written at name registration. Both as described in the 16-bombs cheat above.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`), not from observing it in-game.

## Start a new game with the Stepladder

**Code:** `GAKOXYIX` + `PAKOKNAA`

Tags: `play-start`

**Effect:** A newly registered save file already holds the Stepladder.

**How it works:** Same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the 16-bombs cheat above. `GAKOXYIX` sets the
`LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to `$0C` —
offset `$0C` from `Items` is `InvLadder` (`$0663`) — and `PAKOKNAA` sets the
`LDA #$08` operand at CPU `$9F4C` (originally `$08`) to `$01`. Two one-byte
patches, each compare-pinned to its own bank/offset.

**Caveat — the file starts with a bomb capacity of 0**, and the values are
written at name registration. Both as described in the 16-bombs cheat above.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`), not from observing it in-game.

## Start a new game with the Book of Magic

**Code:** `ZAKOXYIX` + `PAKOKNAA`

Tags: `play-start`

**Effect:** A newly registered save file already holds the Book of Magic.

**How it works:** Same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the 16-bombs cheat above. `ZAKOXYIX` sets the
`LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to `$0A` —
offset `$0A` from `Items` is `InvBook` (`$0661`) — and `PAKOKNAA` sets the
`LDA #$08` operand at CPU `$9F4C` (originally `$08`) to `$01`. Two one-byte
patches, each compare-pinned to its own bank/offset.

**Caveat — you still need the Magical Rod.** The Book only adds flames to the
Rod's beam; on its own it does nothing.

**Caveat — the file starts with a bomb capacity of 0**, and the values are
written at name registration. Both as described in the 16-bombs cheat above.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`), not from observing it in-game.

## Start a new game with the Magical Key

**Code:** `IAKOXYIX` + `PAKOKNAA`

Tags: `play-start`

**Effect:** A newly registered save file already holds the Magical Key, so
every locked door opens without spending keys.

**How it works:** Same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the 16-bombs cheat above. `IAKOXYIX` sets the
`LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to `$0D` —
offset `$0D` from `Items` is `InvMagicKey` (`$0664`) — and `PAKOKNAA` sets
the `LDA #$08` operand at CPU `$9F4C` (originally `$08`) to `$01`. Two
one-byte patches, each compare-pinned to its own bank/offset.

**Caveat — the file starts with a bomb capacity of 0**, and the values are
written at name registration. Both as described in the 16-bombs cheat above.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`), not from observing it in-game.

## Start a new game with the Power Bracelet

**Code:** `TAKOXYIX` + `PAKOKNAA`

Tags: `play-start`

**Effect:** A newly registered save file already holds the Power Bracelet, so
Armos statues and the pushable boulder are available from the start.

**How it works:** Same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the 16-bombs cheat above. `TAKOXYIX` sets the
`LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to `$0E` —
offset `$0E` from `Items` is `InvBracelet` (`$0665`) — and `PAKOKNAA` sets
the `LDA #$08` operand at CPU `$9F4C` (originally `$08`) to `$01`. Two
one-byte patches, each compare-pinned to its own bank/offset.

**Caveat — the file starts with a bomb capacity of 0**, and the values are
written at name registration. Both as described in the 16-bombs cheat above.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`), not from observing it in-game.

## Disable low-health warning sound

**Code:** `AAXTUIAG`

Tags: `utility`

**Effect:** The nagging beep that starts when Link is down to a partial heart
never plays. Everything else about being nearly dead is unchanged — the heart
display, the damage, the death — just without the alarm.

**How it works:** The warning isn't a sound effect that gets triggered once;
it's re-requested every frame from the main world-update loop
(`src/Z_07.asm`, bank 7, the fixed `$C000` bank):

```
    ; If full hearts = 0, then only a partial heart is left.
    ; So, turn on the "heart warning".
    LDA HeartValues
    AND #$0F
    BNE @CheckUW
    LDA Tune0Request
    ORA #$40
    STA Tune0Request
```

`DriveTune0` (`src/Z_00.asm`) then treats request bit `$40` specially — it's
the one tune that only starts if nothing else is playing:

```
    ; If the requested tune is not "heart warning", then go play it.
    CMP #$40
    BNE @ChangeTune

    ; Else only play "heart warning" if nothing else is playing.
    LDX Tune0
    BEQ @ChangeTune
```

This patches the `ORA #$40` immediate at CPU `$ED23` (originally `$40`) to
`$00`. `ORA #$00` leaves `Tune0Request` exactly as it was, and the `STA` that
follows writes the unchanged value back, so the read-modify-write becomes a
no-op and the warning bit is never set. One-byte patch; the compare byte
(`40`) pins it, and the address lives in the fixed top bank, so no other bank
can ever be mapped there.

**Not live-verified:** derived from reading the world-update loop
(`src/Z_07.asm`) and `DriveTune0` (`src/Z_00.asm`), not from observing it
in-game.

## Regular Sword does more damage

**Code:** `EEOLTIAP`

**Effect:** The Wooden Sword — the one you're handed in the first cave — deals
128 damage points per hit, against the Magical Sword's 64. It stays that way
for the whole game, so upgrading to the White or Magical Sword is a
*downgrade*.

**How it works:** Sword damage is a three-entry table indexed by the sword
grade sitting in the sword item slot (`src/Z_01.asm`, part of the
`BANK_01_CODE` block that gets copied into Save RAM and executed from
`$6C90`):

```
SwordDamagePoints:
    .BYTE $10, $20, $40
...
CheckMonsterSwordCollision:
    ...
    ; Look up and set the damage points for the sword type.
    LDY Items
    LDA SwordDamagePoints-1, Y
```

The table sits at CPU `$B596` in bank 1: `$10` for the Wooden Sword, `$20`
for the White Sword, `$40` for the Magical Sword. This patches the first
entry at `$B596` (originally `$10`) to `$80` — twice the Magical Sword's
`$40`. Because bank 1's code runs from a RAM copy, the patch lands on the ROM
bytes in bank 1 and the Game Genie intercepts the read while the copy loop is
fetching them, so the relocated table gets the patched value. One-byte patch;
the compare byte (`10`) pins it to that bank/offset.

**Caveat — nothing else about the Wooden Sword changes.** The beam still
requires full hearts, and the beam's own damage is a separate value.

**Not live-verified:** derived from reading `SwordDamagePoints` and
`CheckMonsterSwordCollision` (`src/Z_01.asm`), not from observing it in-game.

## Candle flames do twice as much damage as the Magical Sword

**Code:** `EASLLIAP`

**Effect:** A standing flame from either Candle burns monsters for 128 damage
points instead of 16 — twice what the Magical Sword does, and eight times the
flame's normal strength. Most of the overworld dies in one touch.

**How it works:** `CheckMonsterBombOrFireCollision` (`src/Z_01.asm`, part of
the `BANK_01_CODE` block that gets copied into Save RAM and executed from
`$6C90`) sets fire parameters first and only overwrites them if the object in
the weapon slot turns out to be a detonating bomb instead:

```
CheckMonsterBombOrFireCollision:
    STY $00                     ; [00] holds the weapon slot

    ; Set up parameters for a fire.
    LDA #$20
    STA $09                     ; [09] holds fire damage type
    LDA #$10
    STA $07                     ; [07] holds $10 damage points
    LDA #$0E
    STA $0D                     ; [0D] holds collision threshold $E
    ...
    ; Else set up parameters for a bomb.
    LDA #$08
    STA $09                     ; [09] holds bomb damage type
    LDA #$40
    STA $07                     ; [07] holds $40 damage points
```

This patches the fire branch's `LDA #$10` immediate at CPU `$B553` (bank 1,
originally `$10`) to `$80`. The bomb branch's `$40` is a different byte and is
untouched. One-byte patch; the compare byte (`10`) pins it to that
bank/offset, and as with the sword-damage cheat above the Game Genie catches
the read during the copy into Save RAM.

**Caveat — this is every "fire", not just the Candle.** Weapon slots `$10`
and `$11` hold both Candle flames and the flames the Book of Magic leaves
behind from the Magical Rod's beam, and both run through this same routine, so
Book flames get the boost too.

**Caveat — monsters immune to fire stay immune.** The damage *type* byte
(`$09` = `$20`) is unchanged, so `HandleMonsterWeaponCollision`'s
`ObjInvincibilityMask` check still parries fire on monsters that resist it, no
matter how large the damage number is.

**Not live-verified:** derived from reading
`CheckMonsterBombOrFireCollision` and `HandleMonsterWeaponCollision`
(`src/Z_01.asm`), not from observing it in-game.

## Start a new game with every item

**Code:** `PAKZLGAA`

Tags: `play-start`

**Effect:** Register a new name with this code active and that save file
starts with the whole `Items` block filled in — every inventory item at its
base grade. Unlike the one-item-at-a-time cheats above, this is a single
one-byte patch that grants all of them at once.

The block runs from `Items` (`$0657`) to `RupeesToSubtract` (`$067E`), so a
new file begins with the Wooden Sword, 1 Bomb, the Bow, Wood Arrows, the Blue
Candle, the Recorder (`Items+5`), Food (Bait), a Life Potion, the Magical Rod
(`Items+8`), the Raft, the Book of Magic, the Blue Ring, the Stepladder, the
Magical Key, the Power Bracelet, the Letter, both dungeon Maps and Compasses
including the Level 9 pair, 1 Rupee, 1 key, one Triforce piece, the Boomerang,
the Magical Boomerang and the Magical Shield.

**How it works:** `FormatFileB` (`src/Z_02.asm`) runs on every entry to the
REGISTER YOUR NAME screen — Mode F submode 0 formats all three file B's before
you type anything — and it clears the file with a fill loop:

```
FormatFileB:
    LDY #$07                    ; Clear the name (to all spaces).
    LDA #$24

@ClearName:
    STA ($C4), Y
    DEY
    BPL @ClearName
    LDY #$27                    ; Clear $28 bytes of the Items block in file.
    LDA #$00

@ClearItems:
    STA ($C0), Y
    DEY
    BPL @ClearItems
```

`[$C0]` points at the file's `Items` block, and the loop covers all `$28`
bytes of it. This patches the `LDA #$00` immediate at CPU `$A443` (bank 2,
originally `$00`) to `$01`, so instead of zeroing the block the loop fills it
with 1 — the "you have it" value for every boolean item and the lowest grade
for the graded ones. One-byte patch; the compare byte (`00`) pins it to that
bank/offset.

Hearts and bomb capacity survive intact: `UpdateModeERegister` runs *after*
the format and rewrites `HeartValues` (offset `$18`), `HeartPartial` (`$19`)
and `MaxBombs` (`$25`) to the usual `$22` / `$FF` / `$08`. `InvClock` (`$15`)
is harmless too — `src/Z_02.asm` resets it when a save slot is chosen, so
enemies are not permanently frozen.

**Caveat — the fill also touches non-item bytes.** `LastBossDefeated` (`$1B`)
and the slots the disassembly leaves unnamed (`$14`, `$1C`, `$20`–`$24`) are
set to 1 rather than 0, as are `RupeesToAdd` and `RupeesToSubtract` (`$26`,
`$27`), which cancel each other out.

**Caveat — one row of one dungeon tile is corrupted.** Bank 3 also holds `$00`
at `$A443`, inside the `PatternBlockUWSPBoss*` graphics data. The Game Genie
patches on CPU read, so that byte reads back as `$01` while it is being copied
to the PPU, changing a pixel in one row of one underworld tile. Cosmetic only.

**Caveat — fires at name registration.** The fill happens when you enter the
REGISTER YOUR NAME screen, so turn the code on, register a fresh name, and you
can turn it off again — the values are baked into the file and covered by the
checksum. Existing files are unaffected.

**Not live-verified:** derived from reading `FormatFileB` and
`UpdateModeERegister` (`src/Z_02.asm`), not from observing it in-game.

## Start a new game with every item, upgraded versions

**Code:** `ZAKZLGAA`

Tags: `play-start`

**Effect:** As the cheat above, but the `Items` block is filled with 2 instead
of 1, so every graded item arrives at its *second* grade: the White Sword,
Silver Arrows, the Red Candle, the Red Ring and the second Potion, plus 2
Bombs, 2 Rupees and 2 keys. Every boolean item is still owned, since the game
tests those for nonzero.

**How it works:** identical to the base-grade cheat above — the `LDA #$00`
immediate of `FormatFileB`'s `@ClearItems` loop at CPU `$A443` (bank 2,
originally `$00`) becomes `$02`. One-byte patch, compare-pinned to that
bank/offset.

**Caveat — some inventory icons draw in the wrong colors.** `Items, X` doubles
as the sprite palette row attribute (`DrawItemInInventory`, `src/Z_07.asm`,
`STA $04` — "The item inventory value can also serve as a palette row
attribute"). Items whose only meaningful value is 1 therefore render with
palette row 2. Cosmetic only, and the graded items look correct because their
grade and their palette row are meant to move together.

**Caveat — the same dungeon-tile pixel corruption, the same bank-3 collision
at `$A443`,** and the same name-registration timing as the cheat above.

**Not live-verified:** derived from reading `FormatFileB` (`src/Z_02.asm`) and
`DrawItemInInventory` (`src/Z_07.asm`), not from observing it in-game.

## Start a new game with every item, maximum values

**Code:** `LAKZLGAA`

Tags: `demo-ready` `play-start` `curated`

**Effect:** As the two cheats above, but the `Items` block is filled with 3.
This is the only one of the three that grants the Magical Sword, which is the
sword slot's third grade.

**Caveat — undefined behavior.** `$03` is a valid value only for the sword.
Every other graded item in the block defines just two grades, so the rest of
the inventory is left holding an out-of-range value and the resulting behavior
is undefined. Use `ZAKZLGAA` above and add the Magical Sword cheat below if
you want a defined result.

**How it works:** identical to the two cheats above — the `LDA #$00` immediate
of `FormatFileB`'s `@ClearItems` loop at CPU `$A443` (bank 2, originally
`$00`) becomes `$03`. One-byte patch, compare-pinned to that bank/offset.

**Caveat — the same dungeon-tile pixel corruption, the same bank-3 collision
at `$A443`,** and the same name-registration timing as the cheats above.

**Not live-verified:** derived from reading `FormatFileB` (`src/Z_02.asm`), not
from observing it in-game.

## Start a new game with all 8 Triforce pieces

**Code:** `ZPKOXYIX` + `NYKOKNAE`

Tags: `play-start`

**Effect:** A newly registered save file already holds all eight Triforce
pieces, so the Level 9 entrance opens immediately.

**How it works:** the same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the other new-game item cheats above. `ZPKOXYIX`
sets the `LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to
`$1A` — offset `$1A` from `Items` is `InvTriforce` (`$0671`) — and `NYKOKNAE`
sets the `LDA #$08` operand at CPU `$9F4C` (originally `$08`) to `$FF`.
`InvTriforce` is a bitfield with one bit per dungeon, so `$FF` sets all eight.
Two one-byte patches, each compare-pinned to its own bank/offset.

**Caveat — the file starts with a bomb capacity of 0**, and the values are
written at name registration. Both as described in the 16-bombs cheat above.
Combining this with one of the "every item" cheats above avoids the capacity
problem, since the fill seeds `MaxBombs` too.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`), not from observing it in-game.

## Start a new game with the Magical Sword (and 0 max bombs)

**Code:** `AAKOXYIZ` + `LAKOKNAA`

Tags: `play-start`

**Effect:** A newly registered save file already holds the Magical Sword,
skipping both the Wooden and White Swords.

**How it works:** the same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the other new-game item cheats above. `AAKOXYIZ`
sets the `LDY #$25` operand at CPU `$9F4A` (bank 2, originally `$25`) to
`$00` — offset `$00` from `Items` is the sword slot itself (`$0657`) — and
`LAKOKNAA` sets the `LDA #$08` operand at CPU `$9F4C` (originally `$08`) to
`$03`, the sword slot's third grade. Two one-byte patches, each compare-pinned
to its own bank/offset.

This is the new-game counterpart to "Have the Magical Sword in your inventory"
above, which forces the same slot every time a file is entered instead of
seeding it once.

**Caveat — the file starts with a bomb capacity of 0**, and the values are
written at name registration. Both as described in the 16-bombs cheat above.

**Not live-verified:** derived from reading `UpdateModeERegister`
(`src/Z_02.asm`), not from observing it in-game.

## Start a new game with a "dark sword" (and 0 max bombs)

**Code:** `AAKOXYIZ` + `GAKOKNAA`

Tags: `demo-ready` `play-start`

**Effect:** A newly registered save file holds a sword one grade *past* the
Magical Sword — a grade the game has no damage entry, no icon and no color
for. Stabs hit for more than twice the Magical Sword's damage, sword beams
drop to Wooden Sword strength, and the blade is drawn in a palette row the
sword never otherwise uses.

**How it works:** the same repurposing of `UpdateModeERegister`'s `MaxBombs`
write (`src/Z_02.asm`) as the Magical Sword cheat above, one grade further.
`AAKOXYIZ` sets the `LDY #$25` operand at CPU `$9F4A` (bank 2, originally
`$25`) to `$00` — offset `$00` from `Items` is the sword slot itself
(`$0657`) — and `GAKOKNAA` sets the `LDA #$08` operand at CPU `$9F4C`
(originally `$08`) to `$04`. The slot is only defined for grades 1-3, so
every routine that reads it runs off the end of its own table:

- **Stabs hit for 132 points.** `CheckMonsterSwordCollision` (`src/Z_01.asm`)
  does `LDY Items / LDA SwordDamagePoints-1, Y`. `SwordDamagePoints` is three
  bytes (`$10, $20, $40`) at CPU `$B596`; grade 4 reads `$B599`, which is the
  `STY $00` opcode of the routine that follows the table — `$84`, i.e. 132
  damage points, against the Magical Sword's 64. Monster hit points come from
  `ObjectTypeToHpPairs` (`src/Z_07.asm`) as a nibble times 16, so this kills
  everything up to nibble 8 in one hit and halves the hit count on the rest.
- **Sword beams get *weaker*.** The beam path in the same file picks damage
  with a compare chain: `CMP #$03` gives `$40`, `CMP #$02` gives `$20`, and
  anything else falls through to `$10`. Grade 4 matches neither, so beams do
  Wooden Sword damage.
- **Ganon takes two stabs instead of four.** `Ganon_CheckCollisions`
  (`src/Z_04.asm`) calls that same `CheckMonsterSwordCollision` with
  `LDY #$0D` while he is blue. His 240 hit points go to 108, and the second
  stab (108 < 132) ends the phase, restoring `$F0` for the brown state that
  only the Silver Arrow can finish. The arrow half is untouched.
- **The icon and the blade change color.** `DrawItemBySlot` (`src/Z_07.asm`)
  adds `ItemSlotToPaletteOffsetsOrValues[0]` (`$FF`), making the sprite
  attribute *grade - 1*, and substitutes the Magical Sword's own image
  (item slot `$20`) only when that lands on exactly `$02`. Grade 4 gives 3, so
  the status bar shows the plain short-sword icon in sprite palette row 3, and
  the blade in Link's hand is drawn from the same unused row (`$83` when
  facing down — the vertical-flip bit survives the addition).

**Caveat — the file starts with a bomb capacity of 0**, exactly as for the
Magical Sword cheat above: the store being repurposed is the one that seeds
`MaxBombs`, so `MaxBombs` is never written and registration leaves it zeroed.
Bomb pickups clamp to it in `HandleClass1` (`src/Z_01.asm`), and because the
shop path debits before it takes (`PostDebit`, then `TakeItem`), **buying
bombs costs the rupees and delivers none**. The bomb slot also never becomes
selectable, so bombs are unusable — no bombable walls, no Dodongos — until the
`MaxBombs + 4` old man sells you capacity, or the second quest's
`SwitchProfileToSecondQuest` (`src/Z_02.asm`) writes 8 unconditionally.

**Caveat — no sword can be picked up afterwards.** Swords are class 2 and
`HandleClass2` (`src/Z_01.asm`) stores only a grade greater than or equal to
the one held, so the Wooden, White and Magical Sword caves all become no-ops.
Their items are still flagged taken.

**Both bytes are bank-unique.** Across all eight banks, CPU `$9F4A` holds
`$25` only in bank 2 and `$9F4C` holds `$08` only in bank 2, so neither
compare byte can match against a different bank mapped into that window.

**Partly live-verified:** the 0-capacity side of this was observed in play —
picking up bombs gave none. The damage, Ganon and palette effects are derived
from reading the routines above and confirmed against the ROM bytes at
`$9F4A`/`$9F4C` and `$B596`-`$B599`, not from observing them in-game.

## Blue Lynels die in one hit

**Code:** `PAKNVLTA`

**Effect:** Blue Lynels (object type `$01`) drop dead the instant Link's
sword (or any other weapon) connects, instead of taking repeated hits.

**How it works:** `ObjectTypeToHpPairs` (`src/Z_07.asm:5256`) packs two
object types' hit points into each byte — high nibble for the even type,
low nibble for the odd type:

```
ObjectTypeToHpPairs:
    .BYTE $06, $43, $25, $31, $12, $24, $81, $14
```

`InitObject` (`src/Z_07.asm:5592`) indexes this table with `ObjType >> 1`
and hands the byte to `ExtractHitPointValue` (`src/Z_04.asm:11002`), which
`AND #$F0`s it for even types or shifts the low nibble up by 4 (`ASL` x4)
for odd types — either way producing `nibble << 4` as the starting
`ObjHP`. Byte 0 covers type `$00` (unused, high nibble) and type `$01`
(low nibble `$6`, giving HP `$60`).

This patches `ObjectTypeToHpPairs` byte 0 at bank 7 CPU `$FB4E`
(originally `$06`) to `$01`, dropping type `$01`'s low nibble to `$1`, for
an HP of `$10` — one point of sword damage (`$10`, the Wood Sword's melee
damage per `SwordDamagePoints`) kills it outright. `ObjectTypeToHpPairs`
is read only by `InitObject`, at spawn time, so this changes the HP every
Blue Lynel is born with. Confirmed against the ROM: bank 7 `$FB4E` reads
`$06`, matching the source. Bank 7 is fixed at `$C000`-`$FFFF` under this
ROM's MMC1 setup, so no other bank can ever be mapped at this address; the
compare byte (`$06`) is included per this project's convention rather
than out of necessity. (`gg.py` also confirms no other bank holds `$06`
at this window offset.)

**Not live-verified:** derived from reading `ObjectTypeToHpPairs`,
`InitObject`, and `ExtractHitPointValue`, not from observing it in-game.

## Blue Darknuts die in one hit

**Code:** `PPSYKLOA`

**Effect:** Blue Darknuts (object type `$0C`) drop dead in one hit instead
of taking repeated hits. Blue Tektites (type `$0D`, which shares the same
HP-table byte) are unaffected.

**Correction from the backlog item:** the backlog entry for this byte
called type `$0C` "Red Darknut." That's backwards — `ParryOrShove`
(`src/Z_01.asm:6313`) explicitly names the two Darknut types:

```
    LDA ObjType, X
    CMP #$0B                    ; Red Darknut
    BEQ :+
    CMP #$0C                    ; Blue Darknut
    BNE :++
```

Type `$0B` is Red Darknut and type `$0C` is Blue Darknut. This entry
retitles the cheat accordingly; the byte, address, and mechanism are
otherwise exactly what the backlog described.

**How it works:** Same `ObjectTypeToHpPairs` table as above
(`src/Z_07.asm:5256`), byte index 6 (0-based, so the 7th byte):

```
ObjectTypeToHpPairs:
    .BYTE $06, $43, $25, $31, $12, $24, $81, $14
```

Byte index = `ObjType >> 1`, so both type `$0C` (even, high nibble) and
type `$0D` (odd, low nibble) share byte 6, which is `$81`: high nibble
`$8` → Blue Darknut HP `$80`, low nibble `$1` → Blue Tektite HP `$10`
(per the `Jumper_GetKind`-based naming already used elsewhere in this
project's backlog for `$0D`/`$0E`/`$0F` = Blue Tektite/Red
Tektite/Boulder, `src/Z_04.asm:2521`).

This patches `ObjectTypeToHpPairs` byte 6 at bank 7 CPU `$FB54`
(originally `$81`) to `$11`. The high nibble drops from `$8` to `$1`, so
Blue Darknut's HP falls from `$80` to `$10` — one point of Wood Sword
damage. The low nibble is unchanged (`$1`), so Blue Tektite's HP stays at
`$10`; it wasn't especially tough to begin with. Read only by `InitObject`
(`src/Z_07.asm:5604`), at spawn time. Bank 7 is fixed at `$C000`-`$FFFF`,
so no other bank can ever be mapped at this address; the compare byte
(`$81`) is included per this project's convention rather than out of
necessity. (`gg.py` also confirms no other bank holds `$81` at this
window offset.)

**Not live-verified:** derived from reading `ObjectTypeToHpPairs`,
`InitObject`, `ExtractHitPointValue`, and the Darknut-color comment in
`ParryOrShove` (`src/Z_01.asm`), not from observing it in-game.

## Bombs detonate almost instantly

**Code:** `PAONVPAL`

**Effect:** A bomb Link sets down explodes almost the instant it's
placed, instead of ticking for about 0.8 seconds first. The blast itself,
its wall-breaking check, and its cleanup are untouched — only the fuse
before it goes off is cut down.

**How it works:** `UpdateBomb` (`src/Z_07.asm:4803`) tracks a bomb
through five minor states (packed in the low nibble of `ObjState`) and
uses `BombTimes` to time the transition out of whichever state is
currently ending:

```
BombTimes:
    .BYTE $30, $18, $0C, $06
...
    LDA ObjTimer, X
    BNE DrawBomb
    LDA ObjState, X
    AND #$0F
    TAY
    LDA BombTimes-1, Y
    STA ObjTimer, X
    INC ObjState, X
```

`WieldBomb` (`src/Z_01.asm:3853`) places a bomb by zeroing `ObjTimer` and
setting state `$11` (minor state 1), so on the very first update
`UpdateBomb` immediately takes the "timer expired" branch: it reads
`BombTimes[0]` (`$30` = 48), stores it as the new `ObjTimer`, and
increments the state to `$12` (minor state 2) — the "armed, ticking"
bomb the player actually watches (confirmed by a comment elsewhere,
`src/Z_04.asm:6124`: "If the bomb has not exploded (state `$12`), then
..."). Byte 0 is therefore the entire fuse duration the player perceives.
When that timer runs out, the state advances to `$13` and the code plays
the explosion sound (`LDA #$10 / JSR PlayEffect`) — the bomb has gone
off.

This patches `BombTimes` byte 0 at bank 7 CPU `$F91E` (originally `$30`)
to `$01`, cutting the fuse from 48 frames (~0.8s) to 1 frame — the bomb
detonates on essentially the next frame after being placed. The remaining
three bytes (`$18`, `$0C`, `$06` — the post-explosion cloud/damage state
and the wall-break check state) are untouched. Confirmed against the ROM:
bank 7 `$F91E` reads `$30`, matching the source. Bank 7 is fixed at
`$C000`-`$FFFF`, so no other bank can ever be mapped at this address; the
compare byte (`$30`) is included per this project's convention rather
than out of necessity. (`gg.py` also confirms no other bank holds `$30`
at this window offset.)

**Not live-verified:** derived from reading `UpdateBomb`, `WieldBomb`, and
the state-`$12` comment in `src/Z_04.asm`, not from observing it in-game.

## Candle/Book flames last much longer

**Code:** `NNXNKEYU`

**Effect:** The standing flame left by the Candle (or the Magical Rod's
beam, with the Book of Magic) lingers for over 4 times as long before
disappearing — about 4.25 seconds instead of about 1.05 seconds.

**How it works:** `UpdateFire` (`src/Z_07.asm:4658`) moves the flame until
it's traveled `$10` subpixels of grid offset, then switches it to a
standing fire with a fixed lifetime:

```
    ; If the absolute value of grid offset < $10, go draw.
    ;
    ; Once the absolute value of grid offset = $10,
    ; make the fire stand instead of move.
    ; Set state $22 and last $3F frames.
    JSR Abs
    CMP #$10
    BNE @DrawAndCheckCollisions
    LDA #$3F
    STA ObjTimer, X
    INC ObjState, X
```

`@StandingFie` (the routine's standing-fire path, run every frame
afterward) simply checks `ObjTimer` and deactivates the fire once it hits
zero, so this `$3F` is the flame's entire remaining lifetime once it
stops moving.

This patches the immediate operand of `LDA #$3F` at bank 7 CPU `$F8AC`
(originally `$3F`, 63 frames ≈ 1.05s) to `$FF` (255 frames ≈ 4.25s).
Confirmed against the ROM: bank 7 `$F8AC` reads `$3F`, matching the
source. Bank 7 is fixed at `$C000`-`$FFFF`, so no other bank can ever be
mapped at this address; the compare byte (`$3F`) is included per this
project's convention rather than out of necessity. (`gg.py` also confirms
no other bank holds `$3F` at this window offset.)

**Not live-verified:** derived from reading `UpdateFire`, not from
observing it in-game.

## Candle flames travel much further before stopping

**Code:** `AKXNEAAP`

**Effect:** The flame from the Candle or the Book-empowered Rod's beam
slides much further across the room — 4x its normal travel distance —
before it plants itself and starts burning in place.

**How it works:** Same `UpdateFire` routine and instruction block as
above (`src/Z_07.asm:4658`):

```
    JSR Abs
    CMP #$10
    BNE @DrawAndCheckCollisions
    LDA #$3F
    STA ObjTimer, X
    INC ObjState, X
```

The comment states it plainly: "Once the absolute value of grid offset =
`$10`, make the fire stand instead of move." `MoveObject` advances the
fire's grid offset each frame, and once its absolute value equals this
threshold the flame stops moving and becomes a standing fire.

This patches the immediate operand of `CMP #$10` at bank 7 CPU `$F8A8`
(originally `$10`, 16 subpixels) to `$40` (64 subpixels — a clean multiple
of the per-frame step, since the test is exact-equality `BNE`, not a
threshold compare). Confirmed against the ROM: bank 7 `$F8A8` reads
`$10`, matching the source. Bank 7 is fixed at `$C000`-`$FFFF`, so no
other bank can ever be mapped at this address; the compare byte (`$10`)
is included per this project's convention rather than out of necessity.
(`gg.py` also confirms no other bank holds `$10` at this window offset.)

**Caveat — exact-equality branch:** the check is `CMP #$40 / BNE
@DrawAndCheckCollisions`, i.e. the fire only stops once the grid offset's
absolute value lands *exactly* on `$40`. `$40` was chosen as a multiple of
the fire's per-frame step (the original `$10` is one such step) so the
counter should still land on it exactly; a non-multiple value here would
risk the fire sailing past the target and never stopping.

**Not live-verified:** derived from reading `UpdateFire` and `MoveObject`,
not from observing it in-game.

## Recorder tune keeps playing far longer

**Code:** `NYNTNNEO`

**Effect:** After playing the Recorder, its tune (and the effects tied to
its duration, such as the whirlwind's travel time) keeps going for over
4 times as long as normal — about 4.25 seconds instead of about 1.6
seconds.

**How it works:** `WieldFlute` (`src/Z_07.asm:2500`) sets the flute's
duration the moment it's played:

```
WieldFlute:
    ; Play the flute's tune.
    LDA #$10
    STA Tune1Request

    ; Set the flute timer for $98 frames.
    LDA #$98
    STA FluteTimer
```

This patches the immediate operand of `LDA #$98` at bank 7 CPU `$EF77`
(originally `$98`, 152 frames ≈ 2.53s) to `$FF` (255 frames ≈ 4.25s).
Confirmed against the ROM: bank 7 `$EF77` reads `$98`, matching the
source. Bank 7 is fixed at `$C000`-`$FFFF`, so no other bank can ever be
mapped at this address; the compare byte (`$98`) is included per this
project's convention rather than out of necessity. (`gg.py` also confirms
no other bank holds `$98` at this window offset.)

**Not live-verified:** derived from reading `WieldFlute`, not from
observing it in-game. What `FluteTimer` actually gates elsewhere (e.g.
how long the whirlwind travels, or how long NPCs react to the tune) was
not traced beyond this one write.

## Move a Recorder secret to a different overworld screen

**Code:** `APVTVYZG`

**Effect:** The overworld room that reveals its Recorder secret (in Quest
1 — see caveat) moves from room `$42` to room `$10`. Standing in the new
room and playing the Recorder starts the pond-draining reveal sequence
there instead; room `$42` no longer has a flute secret of its own.

**How it works:** `WieldFlute` (`src/Z_07.asm:2500`) searches an 11-entry
table of overworld room IDs for a flute secret:

```
FluteRoomSecretsOW:
    .BYTE $42, $06, $29, $2B, $30, $3A, $3C, $58
    .BYTE $60, $6E, $72
...
    LDA RoomId
    LDY #$0A

@FindSecretRoom:
    CMP FluteRoomSecretsOW, Y
    BEQ @Found
    DEY
    BPL @FindSecretRoom
    BMI @FluteSecretNotFound

@Found:
    ; If it was the first room in the list, handle it specially.
    ; This room is the only one in Q1 with a flute secret. It's also
    ; the only one in the list without a flute secret in Q2.
    CPY #$00
    BNE @Normal
    PLA
    BNE @SummonWhirlwind
    BEQ @RevealSecret
```

Byte 0 (`$42`) is that first, specially-handled entry — the only room in
the table with a Quest-1 flute secret.

This patches `FluteRoomSecretsOW` byte 0 at bank 7 CPU `$EF66` (originally
`$42`) to `$10`. Because index 0 keeps its special-case handling
(`CPY #$00` still matches it, whatever the room ID), the new room `$10`
inherits exactly the same behavior room `$42` used to have: a flute
secret in Quest 1, and (per the `@Normal`/quest-branch logic) the
whirlwind instead in Quest 2. Confirmed against the ROM: bank 7 `$EF66`
reads `$42`, matching the source. Bank 7 is fixed at `$C000`-`$FFFF`, so
no other bank can ever be mapped at this address; the compare byte
(`$42`) is included per this project's convention rather than out of
necessity. (`gg.py` also confirms no other bank holds `$42` at this
window offset.)

**Caveat — destination room chosen arbitrarily:** `$10` was picked only
because it doesn't collide with any of the table's other 10 entries
(`$06, $29, $2B, $30, $3A, $3C, $58, $60, $6E, $72`); nothing in this
pipeline traced the overworld screen layout to confirm what's actually
on screen `$10` or whether the pond-draining/staircase visuals will look
sensible there. A different room ID works exactly the same way if `$10`
turns out to be an odd fit.

**Not live-verified:** derived from reading `WieldFlute`, not from
observing it in-game.

## Pols Voice jumps much higher

**Code:** `XNEOVUSN`

**Effect:** When a Pols Voice launches into its hopping-jump state while
facing right, it now shoots upward much faster and reaches a noticeably
greater height before gravity pulls it back down.

**How it works:** `PolsVoiceInitialJumpSpeeds` (`src/Z_04.asm:6524`) is an
8-entry table of initial vertical launch speeds, one per direction index.
`UpdatePolsVoiceState1_Jumping`'s setup code (`src/Z_04.asm:6620-6641`)
builds the index from the facing direction (`ObjDir - 1`), then overrides it
to 3 or 7 if Link's Y coordinate is very high or very low on screen:

```
    ; Subtract 1 from facing direction to make an index.
    LDY ObjDir, X
    DEY
    ...
    ; Set the vertical speed for the beginning of the jump.
    LDA PolsVoiceInitialJumpSpeeds, Y
    STA PolsVoice_ObjSpeedWhole, X
```

`ObjDir = $01` (right) yields index 0, so byte 0 is the launch speed used
whenever Pols Voice begins its jump while facing right (and Link's Y is not
near the top/bottom override range). This patches `PolsVoiceInitialJumpSpeeds`
byte 0 at bank 4 CPU `$9B8E` (originally `$FD`, i.e. signed -3) to `$FA`
(signed -6), doubling the initial upward speed, which
`UpdatePolsVoiceState1_Jumping` accelerates downward by `$38`/frame every
frame afterward — a bigger starting negative speed means more frames airborne
before it turns positive and lands. Raw form: `$9B8E:FA:FD`. No other PRG
bank holds `$FD` at that `$8000`-window offset, so the compare byte pins the
patch to bank 4.

**Caveat — direction-gated.** Because the index is overridden by Link's Y
position near the top/bottom of the screen, byte 0 (index 0) is only reached
when Pols Voice is facing right *and* Link's Y is in the mid-screen band
(`$78`-`$A7`). Jumps launched while facing left, up, or down, or while Link is
near the top/bottom, use the other seven bytes of the table and are
unaffected.

**Not live-verified:** derived from reading `PolsVoiceInitialJumpSpeeds` and
`UpdatePolsVoiceState1_Jumping` (`src/Z_04.asm`), not from observing it
in-game.

## Dodongo takes far longer to digest a bomb

**Code:** `NNUOXAAX`

**Effect:** After a Dodongo swallows a bomb and enters its bloated state, it
takes far longer (about 3.7 extra seconds) before the bomb is actually
"digested" — deactivated and counted as a hit — and it advances toward its
next bloated phase.

**How it works:** `DodongoBloatedWaitTimes` (`src/Z_04.asm:5864`) is a
3-entry table of wait durations, one per bloated substate, read by
`UpdateDodongoState1_Bloated_Sub_Wait` (`src/Z_04.asm:5945`):

```
    ; Set the bloated timer according to the substate.
    LDY Dodongo_ObjBloatedSubstate, X
    LDA DodongoBloatedWaitTimes, Y
    STA Dodongo_ObjBloatedTimer, X

    ; If substate <> 0, go decrement bloated timer.
    CPY #$00
    BNE L_Dodongo_DecrementBloatedTimer

    ; Deactivate the bomb in the first bomb slot ($10).
    LDY #$10
    LDA #$00
    STA a:ObjState, Y

    ; Increment the number of bomb hits.
    LDA Dodongo_ObjBombHits, X
```

Byte 0 is the substate-0 wait time — the phase that ends by deactivating the
bomb object and incrementing `Dodongo_ObjBombHits`. This patches
`DodongoBloatedWaitTimes` byte 0 at bank 4 CPU `$98BA` (originally `$20`, 32
frames) to `$FF` (255 frames), adding roughly 223 extra frames (~3.7s at
60fps) before the bomb is digested and the substate advances. Raw form:
`$98BA:FF:20`. No other PRG bank holds `$20` at that offset, so the patch is
bank-unique.

**Caveat — corrects the "vulnerable" framing in the backlog note.** The
bloated state (`ObjState = 1`) is fully invincible: `Dodongo_CheckCollisions`
/ `Dodongo_CheckCollisionsStandardSize` (`src/Z_04.asm:6014-6072`) only clears
the sword bit from `ObjInvincibilityMask` when `ObjState = 2` (Stunned), which
is a separate state from Bloated. This patch makes Dodongo linger inflated
and immobile-feeling far longer, but it is not thereby made hittable — that
still requires the separate Stunned state.

**Caveat — only the first bloated substate is affected.** The other two
entries of the table (`$40`, `$40`, the later wait phases) are untouched.

**Not live-verified:** derived from reading `DodongoBloatedWaitTimes`,
`UpdateDodongoState1_Bloated_Sub_Wait`, and `Dodongo_CheckCollisionsStandardSize`
(`src/Z_04.asm`), not from observing it in-game.

## Aquamentus moves much faster (one direction only)

**Code:** `GEXPAYPA`

**Effect:** Aquamentus's rightward dash speed quadruples while his leftward
speed is untouched, so he now snaps quickly to the right edge of his arena
and crawls back left at the old pace — a visibly asymmetric, faster-feeling
boss fight.

**How it works:** `AquamentusSpeeds` (`src/Z_04.asm:5610`) is a 2-byte table
— `$01, $FF`, the positive (right) and negative (left) per-frame X steps —
read by `Aquamentus_Move` (`src/Z_04.asm:5613`):

```
@ApplySpeed:
    ; Use (direction - 1) to index the speeds.
    ; This yields 0 for right, 1 for left.
    LDY ObjDir, X
    DEY

    ; Add the speed to the X coordinate.
    LDA ObjX, X
    CLC
    ADC AquamentusSpeeds, Y
    STA ObjX, X
```

This patches `AquamentusSpeeds` byte 0 at bank 4 CPU `$97A0` (originally
`$01`) to `$04`. Since movement only runs on 1 of every 8 screen frames
(`LDA FrameCounter / AND #$07 / BNE @Exit`), this still reads as fast
side-to-side motion rather than a teleport. Raw form: `$97A0:04:01`. No other
PRG bank holds `$01` at that offset, so the patch is bank-unique.

**Caveat — asymmetric by design.** Byte 1 (`$FF`, the leftward step) is left
untouched, so leftward movement stays at the original speed. Patching both
bytes would keep the motion symmetric but is less visually interesting than
the lopsided version.

**Not live-verified:** derived from reading `AquamentusSpeeds` and
`Aquamentus_Move` (`src/Z_04.asm`), not from observing it in-game.

## Patra changes formation constantly

**Code:** `APVZKUNY`

**Effect:** Patra's ring of orbiting children flips its flight-maneuver
pattern many times a second instead of roughly once every four seconds,
producing constant, rapid formation changes throughout the fight.

**How it works:** `PatraManeuverTimes` (`src/Z_04.asm:10029`) is a 2-byte
table — `$FF, $50` — read by `UpdatePatra`'s `@TryChangeManeuver` block
(`src/Z_04.asm:10067-10083`):

```
    LDA Patra_ObjManeuverIndex, X
    EOR #$01
    STA Patra_ObjManeuverIndex, X
    TYA

    ; Y is only ever 0 at this point, even though there are two elements.
    ; Maybe the TYA instruction above was supposed to be a TAY.
    LDA PatraManeuverTimes, Y
    STA ObjTimer+1, X
```

The existing comment documents that Y is always 0 here (likely a `TYA`/`TAY`
typo in the original game), so byte 0 is the only element of this table that
is ever actually read, regardless of which maneuver Patra just switched to.
This patches `PatraManeuverTimes` byte 0 at bank 4 CPU `$AB64` (originally
`$FF`, 255 frames) to `$10` (16 frames), so the formation flip that normally
happens roughly every 4.25 seconds now happens roughly every 0.27 seconds.
Raw form: `$AB64:10:FF`.

**Caveat — bank 0 shares this byte, but harmlessly.** `gg.py` reports bank 0
also holds `$FF` at CPU offset `$AB64`; reading bank 0 there
(`gg.py read 0 $AB50 $30`) shows it sits in a long run of `$FF` filler bytes,
well past the end of bank 0's actual code (bank 0's module is only about
`$1300` bytes, far short of the `$2B64` offset). If bank 0 happens to be
mapped at the moment `$AB64` is fetched as an instruction operand, this patch
would also land there, but that address is unused padding in bank 0, not live
code or data, so no practical effect is expected.

**Not live-verified:** derived from reading `PatraManeuverTimes` and
`UpdatePatra` (`src/Z_04.asm`), not from observing it in-game.

## Enemy fireballs travelling horizontally fly much faster

**Code:** `ENEEALAY`

**Effect:** Fireballs shot by statues and other monsters that happen to be
aimed directly left or right at Link (no vertical component) now streak
across the screen much faster than before.

**How it works:** `FireballQSpeedsX` (`src/Z_04.asm:981`) and the adjacent
`FireballQSpeedsY` are 8/9-entry Q-speed tables indexed by a diagonal-angle
index (0-8) computed by `_CalcDiagonalSpeedIndex` and consumed in
`UpdateFireball` (`src/Z_04.asm:1014-1019`):

```
    ; Look up and set the horizontal and vertical q-speeds.
    LDA FireballQSpeedsX, Y
    STA Fireball_ObjQSpeedX, X
    LDA FireballQSpeedsY, Y
    STA Fireball_ObjQSpeedY, X
```

Index 0's `FireballQSpeedsY` entry is `$00` (no vertical speed at all),
confirming index 0 is the purely-horizontal case, and `FireballQSpeedsX`
index 0 is correspondingly the table's largest magnitude (`$70`). This
patches `FireballQSpeedsX` byte 0 at bank 4 CPU `$8388` (originally `$70`) to
`$F0`, roughly doubling the horizontal Q-speed for perfectly-horizontal
shots. Raw form: `$8388:F0:70`. No other PRG bank holds `$70` at that offset,
so the patch is bank-unique.

**Caveat — only affects dead-horizontal shots.** `FireballQSpeedsY` is a
separate, untouched table, so any fireball aimed with even a slight vertical
component uses a different (unaffected) index and keeps its normal speed —
this cheat does not speed up diagonal or vertical fireballs.

**Not live-verified:** derived from reading `FireballQSpeedsX`,
`FireballQSpeedsY`, and `UpdateFireball` (`src/Z_04.asm`), not from observing
it in-game.

## Wallmasters emerge over a much wider part of the room

**Code:** `AENOPEPZ`

**Effect:** Wallmasters (the hand-shaped enemies that grab Link from dungeon
walls) now consider emerging from a much larger area of the room instead of
being mostly confined to when Link is near the exact horizontal center.

**How it works:** `UpdateWallmaster`'s state-0 handler (`src/Z_04.asm:4128`,
`@State0` block) gates whether the routine goes on to pick an emerge
direction, per the comment: "If (Link's X < `$29` or >= `$C8`) and (Link's Y
< `$6D` or >= `$B5`), then return."

```
    LDA ObjX
    CMP #$29
    BCC :+
    CMP #$C8
    BCC @CheckLeftAndRight
:
    LDA ObjY
    CMP #$6D
    BCC @Exit
    CMP #$B5
    BCS @Exit
```

This patches the `CMP #$29` operand at bank 4 CPU `$90F9` (originally `$29`)
to `$00`. Since `ObjX` is unsigned, `X < $00` can never be true, so the
routine now always falls through to the `$C8` check — for any `X < $C8` it
proceeds straight to `@CheckLeftAndRight` regardless of Link's Y, instead of
requiring `X >= $29` first. Only when `X >= $C8` does the Y-based exit still
apply. Raw form: `$90F9:00:29`. No other PRG bank holds `$29` at that offset,
so the patch is bank-unique.

**Caveat — single-byte version chosen deliberately.** Three companion bytes
(`$90FD` = `$C8`, `$9103` = `$6D`, `$9107` = `$B5`) could be patched too for
an even wider or asymmetric effect, but per the executor brief the
single-byte version is preferred; this cheat leaves those three untouched.

**Caveat — still gated by free monster slots and per-Wallmaster spawn
logic** downstream of this check; this patch only widens the region where the
routine considers emerging, it doesn't force an emergence.

**Not live-verified:** derived from reading `UpdateWallmaster`
(`src/Z_04.asm`), not from observing it in-game.

## Link walks much faster

**Code:** `EGVLYLAT`

Tags: `demo-ready` `play-start` `curated`

**Effect:** Link's base walking speed roughly doubles (from 1.5 pixels/frame
to 3 pixels/frame) everywhere except on mountain stairs, where he still
slows down as normal.

**How it works:** `InitLinkSpeed` (`src/Z_05.asm:7123`) sets Link's default
per-frame speed at the top of the routine:

```
InitLinkSpeed:
    LDA #$60                    ; Link gets a quarter speed (QSpeed) of $60 by default (1.5 pixels a frame).
    STA $00
```

This patches the immediate operand at bank 5 CPU `$B367` (originally `$60`)
to `$C0`, bumping the default QSpeed to 3 pixels/frame. Raw form:
`$B367:C0:60`. No other PRG bank holds `$60` at that same `$8000`-window
offset (gg.py checked all 8 banks), so this is bank-unique.

**Caveat — mountain stairs still slow:** the routine has a second,
lower speed (`LDA #$30`, unpatched) used only when Link is standing on
mountain-stairs tiles (`$74`/`$75`), and the code explicitly compares the
current speed against that lower value to decide whether to reset the
position fraction. That second speed is untouched, so Link still slows
down to the vanilla stairs pace even with this patch applied.

**Not live-verified:** derived from reading `InitLinkSpeed` (`src/Z_05.asm`),
not from observing it in-game.

## Locked doors open without keys (and give you 255 keys)

**Code:** `AANOTXGA`

**Effect:** Walking into a locked door opens it immediately even with zero
keys in inventory, and Link's key count becomes 255 (`$FF`) instead of
staying at zero.

**How it works:** `TouchDoorKey` (`src/Z_05.asm:3971`) normally blocks
movement into a locked door unless Link has the Magic Key or at least one
normal key:

```
    ; If we don't have the magic key nor any normal keys, 
    ; go block movement.
    LDA InvMagicKey
    BNE @TriggerDoor
    LDA InvKeys
    BEQ BlockAtWall

    ; If we don't have the magic key, decrease the key count.
    DEC InvKeys

@TriggerDoor:
```

This patches the branch offset byte of `BEQ BlockAtWall` at bank 5 CPU
`$927E` (originally `$0C`, a +12 jump forward to `BlockAtWall`) to `$00`.
Raw form: `$927E:00:0C`. A branch offset of zero lands on the very next
instruction, so `InvKeys = 0` no longer diverts to `BlockAtWall` — execution
falls straight through into `DEC InvKeys`. **This is the finding, not a
side effect to hide: `DEC InvKeys` on a zero byte underflows to `$FF`.**
Link's key count becomes 255, and the very next instruction (`@TriggerDoor`)
opens the door unconditionally. No other PRG bank holds `$0C` at that same
`$8000`-window offset (gg.py checked all 8 banks), so this is bank-unique.

**Caveat — key count display:** after this fires, the subscreen inventory
and any HUD key counter reads `InvKeys` as `$FF` (255), which is likely
displayed as "F" or wraps oddly depending on how the digit-drawing code
handles a value that large — that display behavior wasn't traced as part
of this candidate.

**Caveat — shared routine:** `TouchDoorKey` is the single handler for every
locked-door tile in the game (both quests, all dungeons), so this patch
applies everywhere locked doors appear, not to one specific door.

**Not live-verified:** derived from reading `TouchDoorKey` (`src/Z_05.asm`),
not from observing it in-game.

## No pause after unlocking a door

**Code:** `PEEOAZAZ`

**Effect:** Opening a locked door with a key no longer freezes Link's
movement afterward — the usual brief pause is nearly eliminated (1 frame
instead of 32).

**How it works:** `TouchDoorKey` (`src/Z_05.asm:3971`), immediately after
triggering the door open, blocks Link's movement for a short timer:

```
@TriggerDoor:
    ; Trigger this door to open.
    LDA $0C
    JSR TriggerOpenDoor

    ; Set player's timer to block for $20 frames.
    LDA #$20
    STA ObjTimer
```

This patches the immediate operand at bank 5 CPU `$9288` (originally `$20`)
to `$01`. Raw form: `$9288:01:20`. `ObjTimer` now gets set to 1 frame
instead of 32 (`$20`), so the block clears almost immediately — effectively
no pause. No other PRG bank holds `$20` at that same `$8000`-window offset
(gg.py checked all 8 banks), so this is bank-unique.

**Caveat — same routine as the key-underflow code above:** this is a
separate byte in the same `TouchDoorKey` routine as "Locked doors open
without keys." The two codes are independent and can be combined, but
both patch different bytes inside the same handler.

**Not live-verified:** derived from reading `TouchDoorKey` (`src/Z_05.asm`),
not from observing it in-game.

## Hearts refill almost instantly

**Code:** `AVNUAPTA`

**Effect:** Whenever hearts are being refilled — after finishing a dungeon,
at the fairy pond, or from a potion — each heart fills up in a fraction of
the normal time, roughly 16x faster.

**How it works:** `World_FillHearts` (`src/Z_05.asm:6763`) runs every frame
while `World_IsFillingHearts` is set, adding a small amount to the current
heart's fractional fill each time:

```
    LDA HeartPartial
    CMP #$F8
    BCS @CompleteHeart          ; If HeartPartial >= $F8, go complete a heart.
    CLC                         ; else add 6.
    ADC #$06
    STA HeartPartial
    RTS
```

This patches the immediate operand of `ADC #$06` at bank 5 CPU `$B1F8`
(originally `$06`) to `$60`. Raw form: `$B1F8:60:06`. Each call now adds
`$60` instead of `$06` to `HeartPartial`, so a heart fills in a handful of
frames instead of dozens.

**Caveat — bank 4 shares this byte:** bank 4 also holds `$06` at this same
`$8000`-window offset. Assembling bank 4's `src/Z_04.asm` and checking the
listing shows that offset lands inside `SetUpFairyObject`, specifically the
low byte of the 16-bit address operand of `STA Tune1Request` (`Tune1Request`
= `$0602`). If bank 4 happens to be the currently mapped bank when the CPU
fetches from `$B1F8`, this Game Genie patch also fires there, changing that
store's target address from `$0602` to `$6002` — a stray write to an
unintended RAM location, and `Tune1Request` no longer gets set when a fairy
object is created. This is a real risk of glitching fairy-appearance sound
behavior whenever bank 4 is active; it's a shared-byte side effect of the
6-byte GG matching window, not a corruption of `World_FillHearts` itself.

**Not live-verified:** derived from reading `World_FillHearts`
(`src/Z_05.asm`) and `SetUpFairyObject` (`src/Z_04.asm`), not from
observing it in-game.

## Ladder and raft attach from much further away

**Code:** `AKXEVYAP`

**Effect:** Link can be much farther from a deployed ladder (or raft, which
shares the same object) and still be treated as standing on it — the
"attach" distance roughly quadruples.

**How it works:** `CheckLadder` (`src/Z_05.asm:3217`) computes the absolute
distance between Link and the ladder object along whichever axis is
relevant, then decides whether Link is still on it:

```
@CheckDistanceToLadder:
    ; If absolute distance < $10, go handle movement on the ladder and set state 2.
    ; If > $10, go put the ladder away.
    JSR Abs
    STA $00                     ; [00] holds the absolute distance between Link and the ladder in whichever axis is relevant.
    CMP #$10
    BCC @SetState2
```

This patches the immediate operand of `CMP #$10` at bank 5 CPU `$8FAE`
(originally `$10`) to `$40`. Raw form: `$8FAE:40:10`. The "still on the
ladder" threshold rises from 16 to 64 (in whichever pixel-fraction units the
distance is measured in), so Link stays attached from much farther off.
No other PRG bank holds `$10` at that same `$8000`-window offset (gg.py
checked all 8 banks), so this is bank-unique.

**Caveat — second, untouched `CMP #$10`:** two instructions after this
patched comparison, the routine does a second `CMP #$10` (bank 5 CPU
`$8FB2`, left unpatched) that handles the exact-equality case — if the
distance equals exactly `$10` and Link faces the same direction as the
ladder, a special "still facing it, haven't stepped off" path runs. That
second check still fires only at the original threshold of `$10`, not the
new `$40`, so the exact-equality special case no longer lines up with the
new "still attached" boundary; it now triggers partway through the widened
attach range rather than at its edge.

**Not live-verified:** derived from reading `CheckLadder` (`src/Z_05.asm`),
not from observing it in-game.

## "Continue" on the death screen does something else

**Code:** `IEVEOZLE`

**Effect:** On the death-screen menu, selecting "Continue" no longer resumes
play from where you died — it instead does whatever "Save" normally does
(saves the file and returns to the save-select screen).

**How it works:** `Mode8SelectionToMode` (`src/Z_05.asm:2190`) is a 3-byte
table mapping the death-screen menu's three rows (Continue, Save, Retry) to
the game mode each one activates:

```
Mode8SelectionToMode:
    .BYTE $03, $0D, $00
```

`UpdateMode8ContinueQuestion_Full` (`src/Z_05.asm:2199`) reads this table by
selection index once the player confirms a choice: `LDA Mode8SelectionToMode, Y
/ STA GameMode`. Byte 0 (index 0, "Continue") is `$03`; byte 1 ("Save") is
`$0D`, which the code elsewhere reaches via `UpdateModeDSave_Sub2`
(`src/Z_02.asm`), confirming mode `$0D` is the save-and-quit mode.

This patches byte 0 of the table at bank 5 CPU `$8AE9` (originally `$03`)
to `$0D`. Raw form: `$8AE9:0D:03`. Choosing "Continue" now sets `GameMode`
to `$0D` (Save) instead of `$03`, so it saves and quits instead of resuming.
No other PRG bank holds `$03` at that same `$8000`-window offset (gg.py
checked all 8 banks), so this is bank-unique.

**Caveat — label still reads "Continue":** the patch only changes which mode
the selection activates; the on-screen text/cursor still says "Continue" —
nothing about the menu's rendering changes, only its effect.

**Not live-verified:** derived from reading `Mode8SelectionToMode` and
`UpdateMode8ContinueQuestion_Full` (`src/Z_05.asm`), not from observing it
in-game.

## Dungeon ambient sound plays where it normally doesn't

**Code:** `APXPGLAA`

**Effect:** In dungeon rooms that normally play no ambient boss/room sound
effect (the game's "silent" entry), an ambient sound effect now plays
instead — the same effect normally reserved for boss rooms whose sound
index is table entry 1 (`$10`).

**How it works:** `BossSoundEffects` (`src/Z_05.asm:4121`) is a 4-byte table
indexed by a 2-bit sound-effect selector pulled from the room's attribute
byte:

```
BossSoundEffects:
    .BYTE $00, $10, $20, $40

CheckBossSoundEffectUW:
    ...
    LDA BossSoundEffects, X
    BEQ :+                      ; If the room has no boss sound effect, go turn off any that might be playing.
    ORA #$80                    ; Add the flag to repeat
    STA SampleRequest
    RTS
:
    LDA #$80                    ; Silence sample and tune1.
    JMP PlayEffect
```

Byte 0 (`$00`) is the "no ambient sound" entry — `CheckBossSoundEffectUW`
(`src/Z_05.asm:4124`) treats a zero table value as "turn off any sample
that might be playing" instead of requesting one.

This patches byte 0 at bank 5 CPU `$9324` (originally `$00`) to `$10`.
Raw form: `$9324:10:00`. Rooms whose sound-effect index selects entry 0 now
request sample `$10` (repeating) instead of silence. No other PRG bank
holds `$00` at that same `$8000`-window offset (gg.py checked all 8 banks),
so this is bank-unique.

**Caveat — boss-defeated silencing still works separately:** this table is
only consulted when the boss for the room has *not* been marked defeated;
`CheckBossSoundEffectUW`'s earlier check (room flags `AND #$C0` `CMP #$C0`)
still silences ambient sound unconditionally once a boss is flagged beaten,
regardless of this patch.

**Not live-verified:** derived from reading `BossSoundEffects` and
`CheckBossSoundEffectUW` (`src/Z_05.asm`), not from observing it in-game.

## Link can walk further past the screen border

**Code:** `VVEAEIVI`

**Effect:** Link can push slightly further past the bottom edge of an
overworld screen before the game masks his input to stop him (roughly 16
more pixels of "give" on that one edge).

**How it works:** `BorderBounds` (`src/Z_05.asm:2728`) is a 12-byte table of
three border-coordinate sets (outer overworld, outer underworld, inner),
each arranged down/up/right/left:

```
BorderBounds:
    .BYTE $D6, $45, $E9, $07, $C6, $55, $D9, $17
    .BYTE $BE, $54, $D1, $1F
```

`Link_FilterInput` / `MaskInputInBorder` (`src/Z_05.asm:2732`, `2798`) read
this table to mask out any input direction that would push Link past the
listed coordinate for the relevant edge. Byte 0 (`$D6`) is the outer
overworld's "down" bound.

This patches byte 0 at bank 5 CPU `$8D80` (originally `$D6`) to `$E6`.
Raw form: `$8D80:E6:D6`. The overworld's down-edge boundary moves 16 pixels
further down before input gets masked. No other PRG bank holds `$D6` at
that same `$8000`-window offset (gg.py checked all 8 banks), so this is
bank-unique.

**Caveat — one edge, one context only:** this patches only the overworld
"down" bound; the outer-underworld and inner border sets (the other 11
bytes of the table) are untouched, so this only affects walking off the
bottom of overworld screens. It's plausible (not confirmed here) that
pushing the border out this far could let Link walk into an area the
screen-scroll/room-transition logic doesn't expect — that interaction
wasn't traced as part of this candidate.

**Not live-verified:** derived from reading `BorderBounds` and
`Link_FilterInput` (`src/Z_05.asm`), not from observing it in-game.

## Boomerang flies much further

**Code:** `PYOEXTPL`

**Effect:** The regular wooden boomerang now travels almost as far as the
Magic Boomerang before turning back — most of the way across a full screen
instead of a short toss.

**How it works:** `BoomerangLimits` (`src/Z_05.asm:2880`) is a 2-byte table
holding the maximum travel distance for the wooden and magic boomerangs:

```
BoomerangLimits:
    .BYTE $31, $FF
```

`WieldBoomerang` (`src/Z_05.asm:2901`) reads the entry selected by
`InvMagicBoomerang` (0 = wooden, nonzero = magic) into the thrown weapon's
`ObjMovingLimit`:

```
    ; Set the farthest distance the boomerang can fly based on
    ; the type of boomerang.
    LDY InvMagicBoomerang
    LDA BoomerangLimits, Y
    STA ObjMovingLimit, X
```

This patches byte 0 (wooden boomerang) at bank 5 CPU `$8E1A` (originally
`$31`) to `$71`. Raw form: `$8E1A:71:31`. The wooden boomerang's distance
limit rises from `$31` to `$71`, close to the magic boomerang's `$FF`
(effectively-unlimited) range without literally matching it. No other PRG
bank holds `$31` at that same `$8000`-window offset (gg.py checked all 8
banks), so this is bank-unique.

**Caveat — magic boomerang untouched:** byte 1 (`$FF`, the magic
boomerang's limit) isn't patched, so this only affects the wooden
boomerang; anyone who already owns the magic boomerang sees no change when
using it.

**Not live-verified:** derived from reading `BoomerangLimits` and
`WieldBoomerang` (`src/Z_05.asm`), not from observing it in-game.

## Losing the overworld money game costs 80 rupees instead of 10

**Code:** `ASUATSZA`

**Effect:** In the overworld money-mini-game caves (the "give a rupee, get more back" cave type), one of the two possible "you lose" amounts the game can randomly hand you is bumped from 10 rupees to 80. Roughly half the time you play, the loss column of the three displayed prices reads 80 instead of 10; the other half it's still the unpatched 40.

**How it works:** `InitCaveContinue` (`src/Z_01.asm`), which runs when Link enters a money-game cave, rolls a random bit to pick one of two possible loss amounts and stores it for later display alongside a fixed 10-rupee loss and a random win amount:

```
    ; With the first bit of another random number, choose 10 or 40
    ; to put in [046F]. This is a random amount to lose.
    LDA Random+2
    AND #$01
    TAY
    LDA MoneyGameLossAmounts, Y
    STA $046F
```

This patches `MoneyGameLossAmounts` byte 0 (`src/Z_01.asm:63`), bank 1 CPU `$85B6` (originally `$0A`) to `$50`. Raw form: `$85B6:50:0A`. The table's raw byte value is the literal decimal rupee amount rendered on screen elsewhere (its sibling entries `$28`/`$14`/`$32` display as 40/20/50), so this turns the "10-rupee loss" option into an "80-rupee loss" option; the routine's own fixed 10-rupee loss (a separate hardcoded `LDA #$0A` a few lines later) and the win amounts (20 or 50) are untouched. One-byte patch; gg.py reports no other PRG bank holds `$0A` at this same `$8000`-window offset, so the code is bank-unique.

**Caveat — only half the time:** `Random+2`'s low bit picks byte 0 or byte 1 of the table with roughly even odds each time the cave is entered, so this patched value only shows up in about half of your money-game visits; the other half still show the original 40-rupee loss (table byte 1, unpatched).

**Not live-verified:** derived from reading `InitCaveContinue` and the money-game display/rupee-debit path in `UpdateCavePersonState_HintOrMoneyGame` (`src/Z_01.asm`), not from observing it in-game. Note: the backlog item that seeded this candidate cited `UpdateCavePersonState_HintOrMoneyGame` as the reader of this table; the actual read is in `InitCaveContinue` — `UpdateCavePersonState_HintOrMoneyGame` only consumes the already-computed `MoneyGameAmounts` copy, not this table directly. The byte and its role are still exactly as described.

## One trap in a six-trap group freezes in place and never lunges

**Code:** `AAKZGLIA`

**Effect:** Underworld rooms that place a group of 6 traps (object type `$49`) have their first trap (object slot offset 1 of the 6) permanently stuck in its sensing state: it still sits on its starting tile and can still be walked into like a stationary hazard, but it never charges at Link no matter how close he gets. The other five traps in the same group behave normally. Four-trap groups (object type `$4A`) are unaffected, since their traps are indexed at higher table offsets.

**How it works:** `UpdateTrap_Full` (`src/Z_01.asm`) picks a direction toward Link (horizontal or vertical, whichever axis is closer) and then gates the actual charge behind a per-trap direction mask:

```
    ; If the direction we determined is not allowed for this trap, then
    ; go draw and check collisions.
    AND TrapAllowedDirs-1, X
    BEQ @DrawAndCheckCollisions

    ; Advance to state 1 with q-speed $70 (1.75 pixels a frame) (fast).
```

This patches `TrapAllowedDirs` byte 0 (`src/Z_01.asm:2456`), bank 1 CPU `$A344` (originally `$05`) to `$00`. Raw form: `$A344:00:05`. `TrapAllowedDirs` is indexed as `TrapAllowedDirs-1, X` with `X` = the trap's own object slot, so byte 0 governs whichever trap occupies the first slot of a 6-trap group. With the mask forced to `$00`, `AND`ing it against *any* attempted direction always yields zero, so the `BEQ @DrawAndCheckCollisions` is always taken and the trap can never advance out of state 0 — it's permanently "sensing" and never reaches the state-1 charge that the q-speed-`$70` code above sets up. `L_Trap_DrawAndCheckCollisions` (called every frame regardless of state) still draws the trap and still runs the shared `Person_DrawAndCheckCollisions_Common` collision/damage check, so the frozen trap remains a real, touchable hazard sitting still at its spawn tile. One-byte patch; gg.py reports no other PRG bank holds `$05` at this offset, so the code is bank-unique.

**Caveat — corrected from the backlog title:** the original candidate description called this "traps only fire from one axis," but that's not what byte 0 → `$00` actually does. `TrapAllowedDirs`'s existing entries already encode a mix of "one horizontal + one vertical direction allowed" (bytes 0-3, two bits set) and "one direction only" (bytes 4-5, one bit set) — some traps already fire from only one axis, unpatched. Masking byte 0 to `$00` (zero bits set) doesn't narrow it to one axis; it removes every allowed direction, so that specific trap goes fully inert instead. The title above reflects the verified behavior.

**Not live-verified:** derived from reading `UpdateTrap_Full`, `InitTrap_Full`, and `Person_DrawAndCheckCollisions_Common` (`src/Z_01.asm`), not from observing it in-game.

## Traps sense Link from much further away

**Code:** `AGSZYUTA`

**Effect:** Every 6-trap and 4-trap group in the game starts its charge toward Link from a much greater vertical range — roughly 4x the normal detection distance — so traps that were previously safe to walk past at a short diagonal now start lunging while Link is still well off to the side.

**How it works:** `UpdateTrap_Full` (`src/Z_01.asm`) checks the absolute vertical distance between Link and the trap first, falling back to a horizontal check only if the vertical gap is too wide:

```
    ; State 0. Sensing.
    ;
    ; If the absolute vertical distance between Link and the trap >= $E,
    ; then go see if the horizontal distance is shorter.
    LDA ObjY
    SEC
    SBC ObjY, X
    JSR Abs
    CMP #$0E
    BCS @CheckHorizontal
```

This patches the immediate operand of that `CMP` at bank 1 CPU `$A357` (originally `$0E`) to `$40`. Raw form: `$A357:40:0E`. The vertical-distance early-out now only triggers at a gap of 64 pixels or more (instead of 14), so traps consider Link "close enough vertically" across most of a room before ever falling through to the (unpatched) horizontal check at `$A386`. One-byte patch.

**Caveat — not bank-unique:** gg.py reports bank 2 also holds `$0E` at this same `$8000`-window offset (file offset `$0A367`), as the zero-page operand of an unrelated `LDA $0E` inside what looks like a 16-bit accumulator routine in bank 2 (`... ADC $0F / STA $0F / LDA $0E / ADC #$00 / STA $0E / RTS`, around bank 2 CPU `$A356`-`$A360`, not independently named/annotated in `src/Z_02.asm`). If bank 2 happens to be the currently-mapped bank when the CPU reads `$A357`, this code will also fire there, changing that instruction from `LDA $0E` to `LDA $40` and corrupting whatever that bank-2 routine's result is used for. The compare byte (`0E`) is still required and still narrows the blast radius to exactly these two banks instead of all eight, but does not eliminate the bank-2 collision the way it does for the other codes in this batch.

**Not live-verified:** derived from reading `UpdateTrap_Full`, not from observing it in-game.

## Traps charge at more than double their normal speed

**Code:** `EYNZTLAY`

**Effect:** Once a trap starts its charge toward Link, it crosses the room much faster than normal — well over double the vanilla speed — making triggered traps much harder to outrun or dodge.

**How it works:** `UpdateTrap_Full` (`src/Z_01.asm`) sets the trap's per-frame movement speed the moment it commits to charging:

```
    ; Advance to state 1 with q-speed $70 (1.75 pixels a frame) (fast).
    INC ObjState, X
    LDA #$70
    STA ObjQSpeedFrac, X
```

This patches the immediate operand of that `LDA` at bank 1 CPU `$A376` (originally `$70`) to `$F0`. Raw form: `$A376:F0:70`. `ObjQSpeedFrac` is the same fractional-speed field used throughout the engine's movement code, so this takes the trap from 1.75 pixels/frame to 3.75 pixels/frame — over double its original, already-"fast" charge speed. One-byte patch; gg.py reports no other PRG bank holds `$70` at this offset, so the code is bank-unique.

**Not live-verified:** derived from reading `UpdateTrap_Full`, not from observing it in-game.

## One rupee in a ten-rupee stash spawns far to the left of the rest

**Code:** `AXKXTXAN`

**Effect:** Ten-rupee stashes (the "generic rupee" reward object placed by cave persons) normally cluster their ten individual rupees in a tight, deliberate arrangement. With this code, one of those ten rupees — the last one placed by the spawn loop — appears well off to the left of the cluster instead of in its usual spot, breaking up the pattern.

**How it works:** `InitRupeeStash_Full` (`src/Z_01.asm`) spawns ten individual rupee objects in a loop, indexed from the end of two 10-byte position tables backward to the start:

```
    LDX #$0A

@LoopRupee:
    JSR InitOneSimpleObject

    ; Look up and set the coordinates for one rupee stash/rupee.
    LDA RupeeStashXs-1, X
    STA ObjX, X
    LDA RupeeStashYs-1, X
    STA ObjY, X
    DEX
    BNE @LoopRupee
```

Because the loop reads `RupeeStashXs-1, X` with `X` counting down from 10 to 1, table byte 0 is actually consumed on the *final* iteration (`X` = 1), positioning the rupee placed in object slot 1. This patches `RupeeStashXs` byte 0 (`src/Z_01.asm:2366`), bank 1 CPU `$A2CE` (originally `$78`) to `$28`. Raw form: `$A2CE:28:78`. The table's other nine X positions (and all ten Y positions in `RupeeStashYs`) are untouched, so nine of the ten rupees keep their original layout and only the one in object slot 1 jumps from X-coordinate `$78` to `$28` — well outside the cluster of `$60`-`$90` values the rest of the table uses, but still a normal, on-screen X coordinate with no risk of an off-screen or invalid position. One-byte patch; gg.py reports no other PRG bank holds `$78` at this offset, so the code is bank-unique.

**Not live-verified:** derived from reading `InitRupeeStash_Full`, not from observing it in-game.

## Title-screen "sword strike" animation starts out much slower

**Code:** `AGVOOUAA`

**Effect:** The animated sequence on the title screen where the sword strikes and the palette cycles through its flash colors begins with a long, sluggish first step instead of a quick one — the very first color/frame change in that sequence takes about a full second instead of a fraction of one, before the rest of the (unpatched) sequence continues at its normal pace.

**How it works:** `AnimateDemoPhase0Subphase1` (`src/Z_02.asm`) steps through a palette-cycling sequence, reloading a per-step delay from a table each time it advances:

```
    ; Advance the subphase cycle.
    INC DemoPhase0Subphase1Cycle

    ; Set the timer to the delay for the current point in the cycle.
    LDY DemoPhase0Subphase1Cycle
    LDA DemoPhase0Subphase1Delays-1, Y
    STA DemoPhase0Subphase1Timer
```

`DemoPhase0Subphase1Cycle` is reset to 0 when this title-screen phase begins, so its very first increment sets `Y` = 1, and `DemoPhase0Subphase1Delays-1, Y` reads table byte 0 — confirmed as the delay used for the first step of the sequence. This patches `DemoPhase0Subphase1Delays` byte 0 (`src/Z_02.asm:1245`), bank 2 CPU `$9B69` (originally `$08`) to `$40`. Raw form: `$9B69:40:08`. The delay for that first step goes from 8 frames (~0.13s) to 64 frames (~1.07s); the remaining 13 documented bytes of the table, governing every later step, are untouched. One-byte patch; gg.py reports no other PRG bank holds `$08` at this offset, so the code is bank-unique.

**Caveat — stay inside the documented table:** the disassembly marks the two bytes immediately after this 14-byte table as an "Unknown block" (`src/Z_02.asm:1249`-`1250`). This patch only touches byte 0, well inside the documented region, so it doesn't risk that ambiguity.

**Not live-verified:** derived from reading `AnimateDemoPhase0Subphase1`, not from observing it in-game.

## Title-screen item parade shows the Triforce instead of the first item

**Code:** `TAKPAZZX`

**Effect:** During the attract-mode sequence where pairs of items scroll up the title screen, the very first pair shown has its left-hand item replaced by the Triforce — the same item graphic normally reserved for the game's ending sequence — instead of whatever item would normally lead the parade. The right-hand item of that first pair, and every later pair, is unaffected.

**How it works:** `ProcessDemoLineItems` (`src/Z_02.asm`) spawns a new pair of item objects by reading the current row out of two parallel tables:

```
@SetUpObject:
    LDY DemoItemRow
    LDA DemoLeftItemIds, Y      ; Allocate an object for the item on the left.
    STA DemoItemIds, X
```

`DemoItemRow` is reset to 0 when this title-screen phase begins and increments by one each time a pair is placed, so the first pair placed reads row 0 — table byte 0 — confirming this is genuinely the first item shown, not dead/unreachable data. This patches `DemoLeftItemIds` byte 0 (`src/Z_02.asm:410`), bank 2 CPU `$9240` (originally `$22`) to `$0E`. Raw form: `$9240:0E:22`. Both `$22` and `$0E` are valid indices into the shared `ItemIdToSlot`/`ItemIdToDescriptor` tables (`src/Z_01.asm:4318`, `4341`) that the item-drawing code (`AnimateItemObject`, `src/Z_07.asm:852`) uses for every item id below `$30`, so no bounds are exceeded. `$0E` is confirmed elsewhere in the disassembly as "Triforce item ID" — it's the exact value `UpdateMode13WinGame_Sub4` (`src/Z_02.asm:3640`) uses to draw the Triforce at the end of the game — making it an easy, recognizable, and safe substitute rather than an arbitrary guess. `DemoRightItemIds` byte 0 (`$9248`, read the same frame from the same row) is untouched. One-byte patch; gg.py reports no other PRG bank holds `$22` at this offset, so the code is bank-unique.

**Caveat — cosmetic, attract mode only:** this only affects the title-screen demo sequence; it has no effect on actual gameplay.

**Not live-verified:** derived from reading `ProcessDemoLineItems`, `Demo_AnimateObjects`, and `AnimateItemObject`, not from observing it in-game.

## The Lost Woods shortcut wants a different first move

**Code:** `PEOZNSAA`

**Effect:** The four-step direction sequence that opens the secret passage
through the Lost Woods (room `$61`) no longer starts with the vanilla first
move. Walking the old opening step now resets the sequence instead of
advancing it; a different direction is required to take the first step
correctly.

**How it works:** `ForestMazeDirs` (`src/Z_01.asm:4828`) is a 4-byte table
read by `CheckMazes` (`src/Z_01.asm:4837`), which compares Link's current
direction (`ObjDir`) against `ForestMazeDirs, X` with `X = MazeStep` while
Link is in room `$61`, advancing the step counter on a match and resetting it
on a mismatch (except that moving right always exits, per the
`@Mismatch`/`CMP #$01` special case):

```
ForestMazeDirs:
    .BYTE $08, $02, $04, $02
...
CheckMazes:
    LDX MazeStep
    LDA ObjDir
    LDY RoomId
    CPY #$61
    BNE @CheckMountainMaze      ; If not in forest maze, go check mountain maze.
    CMP ForestMazeDirs, X
    BNE @Mismatch               ; If direction doesn't match current step, go handle it.
```

`ForestMazeDirs` lives inside the `BANK_01_CODE` block, which `src/Z.cfg`
loads at bank 1 CPU `$A500` but runs from Save RAM at `$6C90`
(`CopyCommonCodeToRam`, `src/Z_01.asm:1569`). `bin/Z.lbl` records the label at
its **run** address, `$7527`, which a Game Genie code cannot patch directly —
the fix is to convert to the load (ROM) address with
`rom_addr = run_addr - $6C90 + $A500` = `$7527 - $6C90 + $A500` = `$AD97`.
Reading the ROM at bank 1 `$AD97` returns `$08`, matching the source, which
confirms the conversion; the block is re-copied from ROM to Save RAM on every
boot, so a patch at the ROM address takes effect after the copy runs.

This patches `ForestMazeDirs` byte 0 at bank 1 CPU `$AD97` (originally `$08`)
to `$01`. Raw form: `$AD97:01:08`. No other switchable bank holds `$08` at
that same `$8000`-window offset, so the patch is bank-unique.

**Caveat — Save RAM timing:** the patched value only takes effect after
`CopyCommonCodeToRam` runs at boot; this happens well before the maze room is
reachable, so there's no practical window where the old value is still live.

**Not live-verified:** derived from reading `ForestMazeDirs` and `CheckMazes`
(`src/Z_01.asm`), not from observing it in-game.

## The Lost Hills shortcut loses its uniform pattern

**Code:** `GEOXUSAA`

**Effect:** All four steps of the Lost Hills (mountain maze, room `$1B`)
shortcut normally require the same direction. With this code the first step
requires a different direction than the other three, so the sequence a player
already knows from the overworld only works for its last three moves.

**How it works:** `MountainMazeDirs` (`src/Z_01.asm:4831`) is read by the same
`CheckMazes` routine (`src/Z_01.asm:4837`) as the forest maze table, but
against room `$1B`:

```
MountainMazeDirs:
    .BYTE $08, $08, $08, $08
...
    CPY #$1B
    BNE @ResetMazeStep          ; If not in the mountain maze either, go reset the maze step and leave room alone.
    CMP MountainMazeDirs, X
    BEQ @Match                  ; If the direction matches the current step, go see if it's the last one.
```

Like `ForestMazeDirs`, this table lives in the `BANK_01_CODE` block that loads
at bank 1 CPU `$A500` and runs from Save RAM at `$6C90`. `bin/Z.lbl` gives its
run address as `$752B`; converting with
`rom_addr = run_addr - $6C90 + $A500` = `$752B - $6C90 + $A500` = `$AD9B`
matches the value the executor instructions state. Reading the ROM at bank 1
`$AD9B` returns `$08`, confirming both the source and the conversion.

This patches `MountainMazeDirs` byte 0 at bank 1 CPU `$AD9B` (originally
`$08`) to `$04`. Raw form: `$AD9B:04:08`. No other switchable bank holds `$08`
at that same offset, so the patch is bank-unique.

**Not live-verified:** derived from reading `MountainMazeDirs` and
`CheckMazes` (`src/Z_01.asm`), not from observing it in-game.

## Blue Lynels barely hurt you

**Code:** `PEUULZZA`

**Effect:** Getting hit by a Blue Lynel still knocks Link back and still costs
some life, but only about half of the usual damage.

**How it works:** `ObjTypeToDamagePoints` (`src/Z_01.asm:5574`) is a
one-byte-per-object-type table indexed directly by `ObjType`, unlike the
paired-nibble `ObjectTypeToHpPairs` table used elsewhere. `HarmLink`
(`src/Z_01.asm:5719`) reads it and unpacks a 16-bit damage amount from a
single byte:

```
    ; Unpack the damage points for the monster's type.
    ; The low nibble is the high byte.
    ; (Damage points byte AND $F0) is the low byte.
    LDY ObjType, X
    LDA ObjTypeToDamagePoints, Y
    PHA
    AND #$0F
    STA $0D
    PLA
    AND #$F0
    STA $0E
```

Type `$01` is the Blue Lynel, so byte 1 of the table (originally `$02`)
controls its damage. This is a different table from `SwordDamagePoints`
(already patched by the "sword damage" codes elsewhere in this document),
which governs how much damage Link's sword does to monsters, not how much
monsters hurt Link.

`ObjTypeToDamagePoints` also lives in the `BANK_01_CODE` block: loaded at bank
1 CPU `$A500`, run from Save RAM at `$6C90`. `bin/Z.lbl` lists the table's run
address as `$7A4A`; converting with
`rom_addr = run_addr - $6C90 + $A500` = `$7A4A - $6C90 + $A500` = `$B2BA`
puts byte 1 at `$B2BB`, matching the executor instructions. Reading the ROM at
bank 1 `$B2BB` returns `$02`, confirming both the source and the conversion.

This patches `ObjTypeToDamagePoints` byte 1 at bank 1 CPU `$B2BB` (originally
`$02`) to `$01` — unpacking to high byte `$01`, low byte `$00`, half the
vanilla `$0200`. Raw form: `$B2BB:01:02`. No other switchable bank holds `$02`
at that same offset, so the patch is bank-unique.

**Not live-verified:** derived from reading `ObjTypeToDamagePoints` and
`HarmLink` (`src/Z_01.asm`), not from observing it in-game.

## Shop wares are laid out differently

**Code:** `ALKATNAI`

**Effect:** The three items for sale in an overworld shop cave are normally
evenly spaced left to right. With this code the leftmost item's icon (and its
touch/collision spot) shifts well to the left of where the price/selection
cursor expects it, throwing off the shop's layout.

**How it works:** `CaveWareXs` (`src/Z_01.asm:392`) holds the three X
positions used to draw and position the cave wares:

```
CaveWareXs:
    .BYTE $58, $78, $98
```

`DrawCaveItems` (`src/Z_01.asm:395`) loops over the three wares and uses this
table (alongside `CaveFlags`) to place each item sprite. The three vanilla
values are evenly spaced 32 pixels apart.

This patches `CaveWareXs` byte 0 at bank 1 CPU `$8746` (originally `$58`) to
`$30`. Raw form: `$8746:30:58`. No other switchable bank holds `$58` at that
same offset, so the patch is bank-unique.

**Caveat — shared table:** `CaveWareXs` is also implicitly relied on by
whatever code reads Link's position to detect which ware he's standing next
to for purchase; moving the drawn icon without moving the purchase-detection
logic could make the icon and its "buy" hotspot disagree. This has not been
traced further and is called out as a risk, not a confirmed effect.

**Not live-verified:** derived from reading `CaveWareXs` and `DrawCaveItems`
(`src/Z_01.asm`), not from observing it in-game.

## The "life or money" door shows the wrong item icon

**Code:** `ZOKEOUZP`

**Effect:** The underworld room that offers "a heart container or 50 Rupees"
still charges exactly the same as before — either the heart container is
taken or 50 Rupees are deducted — but the heart-container choice is drawn as
a different item (here, a ring) instead of a heart container.

**How it works:** `LifeOrMoneyItemTypes` (`src/Z_01.asm:1354`) is a two-byte
table of item IDs, one per ware slot, used only for the visuals:

```
LifeOrMoneyItemXs:
    .BYTE $58, $98

LifeOrMoneyItemTypes:
    .BYTE $1A, $18
```

`DrawLifeOrMoneyItems` (`src/Z_01.asm:1357`) loops `X` from 1 down to 0 and
passes `LifeOrMoneyItemTypes, X` to `AnimateItemObject`
(`src/Z_07.asm:852`), which resolves the item ID through `ItemIdToSlot` /
`ItemIdToDescriptor` purely to pick a sprite to draw — it does not touch the
inventory. The actual payment logic in
`UpdateUnderworldPersonLifeOrMoneyState_2` (`src/Z_01.asm:1390`) branches on
the loop index itself (`CPX #$00`), not on the item ID: `X = 0` always
subtracts a heart container and `X = 1` always subtracts 50 Rupees,
regardless of what `LifeOrMoneyItemTypes` says. So changing byte 0 (index 0,
the heart-container slot) only changes the icon shown there, not what
happens when Link takes it. Item ID `$12` maps through `ItemIdToSlot`/
`ItemIdToDescriptor` to the ring inventory slot at grade 1 — the same ID
confirmed as the Blue Ring in this document's "Blue Ring costs 1 Rupee"
entry — so this substitution draws a ring sprite in the heart-container spot.

This patches `LifeOrMoneyItemTypes` byte 0 at bank 1 CPU `$8BC9` (originally
`$1A`) to `$12`. Raw form: `$8BC9:12:1A`. No other switchable bank holds
`$1A` at that same offset, so the patch is bank-unique.

**Caveat — cosmetic only:** despite the backlog description, this table does
not control what the door actually charges. The heart-container-vs-50-Rupees
logic is hardcoded by loop index in
`UpdateUnderworldPersonLifeOrMoneyState_2` and is unaffected by this byte.
Taking the mislabeled item still costs a heart container exactly as before.

**Not live-verified:** derived from reading `LifeOrMoneyItemTypes`,
`DrawLifeOrMoneyItems`, `UpdateUnderworldPersonLifeOrMoneyState_2`
(`src/Z_01.asm`), and `AnimateItemObject` (`src/Z_07.asm`), not from
observing it in-game.

## Whirlwind drops you at a different height

**Code:** `IIOXPOSE`

**Effect:** Riding the whirlwind out of dungeon level 1 (and any other level
that shares byte 0's Y coordinate) now sets Link down at a noticeably
different vertical position in the destination room.

**How it works:** `TeleportYs` (`src/Z_01.asm:1989`) holds one landing
Y-coordinate per dungeon level:

```
TeleportYs:
    .BYTE $8D, $AD, $8D, $8D, $AD, $8D, $AD, $5D
```

`CheckInitWhirlwindAndBeginUpdate` (`src/Z_01.asm:1992`) reads
`TeleportingLevelIndex AND #$07` as the index and passes
`TeleportYs, Y` to `InitWhirlwind` as the Y coordinate for the whirlwind
object (and thus where Link is dropped) in the destination room.

This patches `TeleportYs` byte 0 at bank 1 CPU `$A119` (originally `$8D`) to
`$5D` — the same value already used by byte 7 in vanilla, so it's a value the
game already uses elsewhere for a valid landing spot. Raw form:
`$A119:5D:8D`.

**Caveat — shared byte, other bank:** bank 2 holds `$8D` at that same
`$8000`-window offset (bank 1 `$A119`), so the compare byte also matches
there. In bank 1 that byte is data (the `TeleportYs` table). In bank 2 the
same file offset falls inside title/file-select code and is the opcode byte
of a `STA $0421` (`NameCharOffset`) instruction — opcode `$8D` is 6502
`STA abs`; the patch's new value `$5D` is the opcode for `EOR abs,X`. Whenever
bank 2 is mapped into `$8000`-`$BFFF` (the title screen and save-file naming
screen), this same Game Genie code would silently turn that `STA $0421` into
`EOR $0421,X`, corrupting the save-slot name-entry character offset instead
of writing it. This is a real risk, not a hypothetical: the code is not
bank-unique.

**Not live-verified:** derived from reading `TeleportYs` and
`CheckInitWhirlwindAndBeginUpdate` (`src/Z_01.asm`), the bank-2 disassembly
at `$A119`, and `NameCharOffset` usage in `src/Z_02.asm`, not from observing
it in-game.

## Ladder works on a different overworld screen

**Code:** `AAENIZYP`

**Effect:** On the overworld, pressing toward water while holding the ladder
normally only lays a ladder down in six specific rooms. This code swaps one
of those six rooms for a different one: room `$00` gains the ability to lay
a ladder across water, and room `$17` (which used to have it) loses it.

**How it works:** `LadderRoomsOW` (`src/Z_07.asm:3175`) is a 6-byte list of
overworld room IDs:

```
LadderRoomsOW:
    .BYTE $17, $18, $19, $27, $4F, $5F
```

`Link_EndMoveAndAnimate` (`src/Z_07.asm:3210`) checks the current overworld
room against this list every time Link is grid-aligned and not in a
doorway:

```
    ; If in OW and we're not in this list of 6 rooms, go check warps and animate.
    LDA CurLevel
    BNE @CheckLadder
    LDA RoomId
    LDY #$05

@LoopLadderRoom:
    CMP LadderRoomsOW, Y
    BEQ @CheckLadder
    DEY
    BPL @LoopLadderRoom
    BMI @CheckWarps
```

A room ID matching any list entry falls through to `@CheckLadder`, which
(after confirming Link isn't in a doorway, does own the ladder, isn't
already using it, and is facing a water tile per the code just below) lays
down a ladder object at the water's edge — the same code block quoted in
the backlog item that instantiates the ladder via `FindEmptyMonsterSlot`
and `LinkToLadderOffsetsX`/`LinkToLadderOffsetsY`. A room ID that matches
nothing falls off the end of the loop into `@CheckWarps`, skipping the
ladder logic entirely.

This patches `LadderRoomsOW` byte 0 at bank 7 CPU `$F20D` (originally
`$17`) to `$00`. Raw form: `$F20D:00:17`. No other PRG bank holds `$17` at
that offset (bank 7 is the fixed `$C000`-`$FFFF` window, so no other bank
can ever be mapped there regardless).

**Caveat — room `$17` loses the behavior:** because this replaces the list
entry rather than adding a seventh one, room `$17` (one of the original six
ladder-crossing screens) no longer matches the list and no longer allows
laying a ladder across water; room `$00` gains the ability in its place.

**Not live-verified:** derived from reading `LadderRoomsOW` and
`Link_EndMoveAndAnimate` (`src/Z_07.asm`), not from observing it in-game.

## Level 1 plays the final dungeon's song instead of the usual dungeon theme

**Code:** `AXVTOLAG`

**Effect:** Entering Level 1 plays the song normally reserved for Level 9
(the final dungeon) instead of the standard dungeon theme every other
early level uses.

**How it works:** `LevelSongIds` (`src/Z_07.asm:1766`) is a 10-byte table
indexed by `CurLevel` (0 = overworld, 1-9 = dungeon levels):

```
LevelSongIds:
    .BYTE $01, $40, $40, $40, $40, $40, $40, $40
    .BYTE $40, $20

GoToNextModePlayLevelSong:
    LDY CurLevel
    LDA LevelSongIds, Y
    STA SongRequest             ; Play the song for the level.
```

Byte 0 (`$01`) is the overworld song, bytes 1-8 (`$40` each) are the
default dungeon song shared by Levels 1-8, and byte 9 (`$20`) is the
distinct song used only for Level 9. `GoToNextModePlayLevelSong` reads
this table and hands the result straight to `SongRequest`, which is what
actually queues the song change, whenever a level transition finishes.

This patches `LevelSongIds` byte 1 at bank 7 CPU `$EBE1` (originally
`$40`) to `$20`, the same value already used for Level 9's song at byte 9
— a value the sound-request path is already known to handle safely.
Raw form: `$EBE1:20:40`. No other PRG bank holds `$40` at that offset
(bank 7 is the fixed `$C000`-`$FFFF` window, so no other bank can ever be
mapped there regardless).

**Not live-verified:** derived from reading `LevelSongIds` and
`GoToNextModePlayLevelSong` (`src/Z_07.asm`), not from observing it
in-game.

## Boomerang curves back more steeply for one angle of approach

**Code:** `ANNNAGAZ`

**Effect:** When a thrown boomerang (Link's or a monster's) curves back
toward whoever threw it, one specific angle bucket of the return flight
now pulls much harder toward vertical — the boomerang's return arc bends
more sharply for throws that land in that bucket, instead of the gentler
curve it uses normally.

**How it works:** `BoomerangQSpeedFracsY` (`src/Z_07.asm:3831`), paired
with `BoomerangQSpeedFracsX` (`src/Z_07.asm:3835`), supplies the vertical
speed component for the boomerang's return-to-thrower flight:

```
BoomerangQSpeedFracsY:
    .BYTE $00, $20, $36, $4C, $60, $68, $70, $78
    .BYTE $80

BoomerangQSpeedFracsX:
    .BYTE $80, $78, $70, $68, $60, $4C, $36, $20
    .BYTE $00
```

`UpdateArrowOrBoomerang` (`src/Z_07.asm:3857`) reaches major states `$40`
(slow) and `$50` (fast) — the header comment there reads "State $40 or
$50. Return to thrower: $40 slow, $50 fast" — and, in
`@MoveTowardThrower`, picks a diagonal speed index from
`_CalcDiagonalSpeedIndex` based on the angle to the thrower, then uses it
to index both tables in turn:

```
    ; Move vertically towards the thrower.
    LDA BoomerangQSpeedFracsY, Y
    JSR SetBoomerangSpeed
    ...
    ; Move horizontally towards the thrower.
    ...
    LDA BoomerangQSpeedFracsX, Y
    JSR SetBoomerangSpeed
```

This patches `BoomerangQSpeedFracsY` byte 1 at bank 7 CPU `$F4F8`
(originally `$20`) to `$70`, which is the value byte 6 already uses on the
opposite end of the table — a value the speed-setting path is already
known to handle safely. Raw form: `$F4F8:70:20`. No other PRG bank holds
`$20` at that offset (bank 7 is the fixed `$C000`-`$FFFF` window, so no
other bank can ever be mapped there regardless).

**Caveat — shared by monsters too:** `UpdateArrowOrBoomerang` handles both
Link's boomerang and any monster's boomerang through the same code path
(the routine explicitly branches on "if this is a monster's boomerang" at
the catch step), so any monster boomerang throw that lands in this angle
bucket during its return flight is affected identically.

**Not live-verified:** derived from reading `BoomerangQSpeedFracsY`,
`BoomerangQSpeedFracsX`, and `UpdateArrowOrBoomerang` (`src/Z_07.asm`),
not from observing it in-game.

## Link can walk further up before the screen scrolls

**Code:** `IXSNYEIU`

**Effect:** Walking toward the top edge of a room, Link can now push about
one grid cell (16 pixels) further up than normal before the game triggers
the transition to the room above. The same applies to any other movement
that relies on this specific boundary check for the up direction.

**How it works:** `PlayerScreenEdgeBounds` (`src/Z_07.asm:2831`) is a
4-byte table of screen-edge coordinates, one per direction (up, down,
left, right):

```
; Up, down, left, right.
;
PlayerScreenEdgeBounds:
    .BYTE $3D, $DD, $00, $F0
```

`CheckScreenEdge` (`src/Z_07.asm:3005`) compares Link's coordinate in his
single moving direction against the matching table entry every frame he's
grid-aligned and moving:

```
    ; If Link's coordinate does not match the screen edge coordinate
    ; in the single moving direction, then return.
    LDA $00
    CMP PlayerScreenEdgeBounds, Y
    BNE ExitX0

    ; We're moving to the next screen.
```

A match falls through into `GoToNextModeFromPlay`, which advances
`GameMode` and starts the room transition.

This patches `PlayerScreenEdgeBounds` byte 0 (the up-direction bound) at
bank 7 CPU `$F0DF` (originally `$3D`) to `$2D`, moving the trigger
coordinate one grid cell (16 pixels) further up the screen. Raw form:
`$F0DF:2D:3D`. No other PRG bank holds `$3D` at that offset (bank 7 is the
fixed `$C000`-`$FFFF` window, so no other bank can ever be mapped there
regardless).

**Caveat — this is the only trigger for the transition:** `CheckScreenEdge`
is the sole mechanism that starts an upward room transition for Link;
there's no independent bounds check elsewhere. A large change to this byte
(much bigger than the one this code makes) could move the trigger
coordinate outside the range Link's movement ever reaches, which would
skip upward room transitions entirely. The one-cell shift this code makes
stays well within reach.

**Not live-verified:** derived from reading `PlayerScreenEdgeBounds` and
`CheckScreenEdge` (`src/Z_07.asm`), not from observing it in-game.

## Recorder's lake secret starts its water-color cycle on a different shade

**Code:** `AUVNETZP`

**Effect:** When the Recorder reveals the Level 7 entrance at the lake
(room `$42`, or any room via the "reveals on any screen" code elsewhere in
this document), the water-palette color cycle that plays during the
reveal starts on a different shade for its first step, instead of the
original blue-green tone.

**How it works:** `PondCycleColors` (`src/Z_07.asm:5873`) is a 12-byte
table of NES palette values, one per step of the flute-secret reveal
animation:

```
PondCycleColors:
    .BYTE $12, $11, $22, $21, $31, $32, $33, $35
    .BYTE $34, $36, $37, $37
```

`CueTransferPondPaletteRow` (`src/Z_07.asm:5901`), called from both
`UpdateFluteSecret` (`src/Z_07.asm:5877`, stepping forward through the
cycle every 8 frames) and `AnimatePond` (`src/Z_07.asm:5934`, stepping it
back down when reversing), indexes this table with the current cycle
position and writes the result into the dynamic tile transfer buffer that
becomes the water's palette entry:

```
    LDA PondCycleColors, Y      ; Patch byte 3 of palette row with the right color in the cycle.
    STA DynTileBuf+6
```

`SecretColorCycle` (the index into this table) is the same variable
tracked and initialized by the flute-secret code documented elsewhere in
this file (`InitFluteSecret`) — this is the lake/Level-7-entrance secret,
not the separate health-restoring fairy that appears in ponds
(`InitPondFairy`/`UpdatePondFairy` in `src/Z_04.asm`), which uses none of
this code.

This patches `PondCycleColors` byte 0 at bank 7 CPU `$FEE8` (originally
`$12`) to `$30`, a valid NES palette index that reads as a strongly
different (much brighter/whiter) shade than the original. Raw form:
`$FEE8:30:12`. No other PRG bank holds `$12` at that offset (bank 7 is the
fixed `$C000`-`$FFFF` window, so no other bank can ever be mapped there
regardless).

**Caveat — cosmetic only:** this changes only the first step's color; the
remaining 11 steps of the cycle, the timing, the stairs reveal, and the
"secret found" flag are all untouched.

**Not live-verified:** derived from reading `PondCycleColors`,
`CueTransferPondPaletteRow`, `UpdateFluteSecret`, and `AnimatePond`
(`src/Z_07.asm`), not from observing it in-game.

## Enemies spawn in different spots when you enter a room

**Code:** `PPKETTII`

**Effect:** When you walk into an overworld room from the south (i.e. moving
north) and the room spawns enemies fresh, one of the up-to-nine spawn slots
that used to land at column 5 / row 5 now lands at column 1 / row 1 instead —
much closer to the top-left corner of the play area.

**How it works:** `SpawnPosList0` (`src/Z_05.asm:1425`) is one of four
8/9-byte position lists (`SpawnPosList0`-`3`), selected by
`SpawnPosListAddrsLo`/`Hi` (`src/Z_05.asm:1413`) according to Link's entering
direction. `AssignObjSpawnPositions` (`src/Z_05.asm:1879`, called from
`InitMode_EnterRoom`, `src/Z_05.asm:1540`, at line 1812) unpacks each byte:

```
    LDA ($06), Y                ; Get a spawn spot from the list.
    PHA
    ASL                         ; Turn the column component into an X coordinate.
    ASL
    ASL
    ASL
    STA ObjX, X
    PLA                         ; Turn the row component into a Y coordinate.
    AND #$F0
    ORA #$0D                    ; Add $D to the Y coordinate.
    STA ObjY, X
```

The low nibble is the column (shifted left 4 to become an X pixel coordinate)
and the high nibble is the row (masked and OR'd with `$0D` to become a Y
pixel coordinate). Byte 0, `$55`, decodes to X `$50`, Y `$5D`. This patches
`SpawnPosList0` byte 0 at bank 5 CPU `$864E` (originally `$55`) to `$11`,
which decodes to X `$10`, Y `$1D`. No other PRG bank holds `$55` at that
`$8000`-window offset, so the patch can't misfire elsewhere.

**Caveat — shared slot logic:** This only affects the spawn cycle's first
slot in the "Link entered facing up" list (list 0); the other eight bytes in
the list, and the other three direction lists, are untouched. `IsSafeToSpawn`
(called from the loop) can still reject the new spot and fall through to the
next spawn cycle position if it's judged unsafe (e.g. too close to Link).

**Not live-verified:** derived from reading `AssignObjSpawnPositions` and
`SpawnPosList0` (`src/Z_05.asm`), not from observing it in-game.

## Objects can move further into the overworld screen edges

**Code:** `PASLGAPP`

**Effect:** In the overworld, Link and every other object can be pushed
(or walk) a little further past the left edge of the play area than normal
before world-bounds clamping stops them.

**How it works:** `ObjectRoomBoundsOW` (`src/Z_05.asm:6438`) is a 5-byte
table — left/right/up/down object bounds, then first-unwalkable-tile — with
the header comment "The first set is for OW. The second is for UW."
`SetupObjRoomBounds` (`src/Z_05.asm:6444`) copies it into the live bound
variables on every overworld room entry:

```
ObjectRoomBoundsOW:
    .BYTE $11, $E0, $4E, $CD, $89
...
    LDA ObjectRoomBoundsOW, Y
    STA RoomBoundLeft, X
```

Byte 0 is `RoomBoundLeft`. This patches `ObjectRoomBoundsOW` byte 0 at bank 5
CPU `$B054` (originally `$11`) to `$01`. No other PRG bank holds `$11` at
that `$8000`-window offset, so the patch can't misfire elsewhere.

**Caveat — applies to everything, not just Link.** `SetupObjRoomBounds`
copies this bound for every object in the room, not just Link, so enemies and
projectiles get the same widened left edge.

**Caveat — different byte from the existing left-edge/water code.** The
published `zelda_1_game_genie.md` already has a code patching this same
table's byte 4 (`$B058`, the first-unwalkable-tile entry) to make water
walkable. That is a different byte in the same 5-byte table; the two codes
are independent and stack safely if both are enabled.

**Not live-verified:** derived from reading `SetupObjRoomBounds` and
`ObjectRoomBoundsOW` (`src/Z_05.asm`), not from observing it in-game.

## Dungeon doors lead to unexpected rooms

**Code:** `AOVXYIPA`

**Effect:** Opening a shutter/regular door in a dungeon room that isn't
already flagged open can flag the *wrong* door as open in the neighboring
room — over time, the map's door-open state can end up inconsistent with
what's actually reachable.

**How it works:** `DoorNextRoomIdOffsets` (`src/Z_05.asm:5027`) is a 4-byte
table — `$01, $FF, $10, $F0`, i.e. right/left/down/up offsets in room-ID
space — read by `UpdateDoors` (`src/Z_05.asm:5030`) specifically in the
branch that sets the opposite door's flag in the room across a newly-opened
shutter:

```
    ; Get the next room's ID.
    TYA
    CLC
    ADC DoorNextRoomIdOffsets, X
    TAY
    ; Flip the door direction index.
    TXA
    EOR #$01
    TAX
    ; Set the door flag for the opposite door in the next room.
    LDA ($00), Y
    ORA LevelMasks, X
    STA ($00), Y
```

This patches `DoorNextRoomIdOffsets` byte 0 (the "right" offset, `X=0`) at
bank 5 CPU `$A5EF` (originally `$01`) to `$10`. No other PRG bank holds `$01`
at that `$8000`-window offset, so the patch can't misfire elsewhere.

**Caveat — this is the door-flagging table, not the room-transition table.**
`NextRoomIdOffsets` (below) holds the same four values `$01, $FF, $10, $F0`
but in a *different order* (`$F0, $10, $FF, $01`) and is read by a completely
different routine (`CalculateNextRoomForDoor` / `CalcNextRoomByDir`) that
computes the room Link actually walks/warps into. This code patches only
`DoorNextRoomIdOffsets`, i.e. only the bookkeeping that marks the far side of
a shutter door as open — it does not change which room a door or screen edge
leads to.

**Not live-verified:** derived from reading `UpdateDoors` and
`DoorNextRoomIdOffsets` (`src/Z_05.asm`), not from observing it in-game.

## Walking off a screen edge takes you somewhere else

**Code:** `PAOLLIEY`

**Effect:** Walking through a door or off the "up" edge of a dungeon room no
longer moves you to the room above — it moves you toward the room that would
normally be reached by walking down (or an equivalent offset in the wrong
direction), producing a disconnected or looping map layout.

**How it works:** `NextRoomIdOffsets` (`src/Z_05.asm:7474`) is a 4-byte
table — `$F0, $10, $FF, $01` — read by both `CalculateNextRoomForDoor`
(`src/Z_05.asm:7491`) and `CalcNextRoomByDir` (`src/Z_05.asm:7541`), the
routines that compute the destination room ID when Link passes through a
door or off a screen edge:

```
NextRoomIdOffsets:
    .BYTE $F0, $10, $FF, $01
...
    LDA NextRoomIdOffsets, X    ; Look up offset used to calculate next room ID from current one.
    CLC
    ADC RoomId
    STA NextRoomId              ; Adding the offset to RoomId yields the room ID in the desired direction.
```

Per the comment above `CalculateNextRoomForDoor`, the index mapping is
"1:3, 2:2, 4:1, 8:0" (direction bit to table index), so byte 0 (`X=0`)
corresponds to direction bit `8` (up). This patches `NextRoomIdOffsets` byte
0 at bank 5 CPU `$B513` (originally `$F0`, i.e. -16 rooms, the normal
"room above" offset in this 16-columns-wide room-ID space) to `$01` (the
normal "room to the right" offset). No other PRG bank holds `$F0` at that
`$8000`-window offset, so the patch can't misfire elsewhere.

**Caveat — this is the room-transition table, not the door-flagging table.**
`DoorNextRoomIdOffsets` (above) holds the same four values `$01, $FF, $10,
$F0` in a different order (`$01, $FF, $10, $F0`) and is read only by
`UpdateDoors` to flag the opposite door in the next room as open when a
shutter opens. This code patches only `NextRoomIdOffsets`, i.e. only the
actual room Link is moved to — the door-open bookkeeping in the room he
leaves is untouched, so previously-opened doors can end up marked open in
rooms that are no longer reachable the way they used to be.

**Caveat — shared by overworld and underworld.** Both `CalculateNextRoomForDoor`
(dungeon doors) and `CalcNextRoomByDir` (screen-edge walking, used in both OW
and UW) read the same table, so this affects every "up" transition in the
game, not just one room.

**Not live-verified:** derived from reading `CalculateNextRoomForDoor`,
`CalcNextRoomByDir`, and `NextRoomIdOffsets` (`src/Z_05.asm`), not from
observing it in-game.

## Doorway transitions trigger from a different position

**Code:** `IZVOGOIU`

**Effect:** Link is treated as standing "in" a doorway (letting him walk
straight through instead of being blocked, and letting the game start
scrolling to the next room) a little earlier than normal when approaching a
vertical doorway from the left.

**How it works:** `DoorwayBoundsMinOver` (`src/Z_05.asm:3705`) is one of
four paired min/max tables (`…MinOver`/`…MaxOver`/`…MinUnder`/`…MaxUnder`)
read by `CheckDoorway` (`src/Z_05.asm:3747`) to decide whether Link's
along-the-wall coordinate falls inside a doorway:

```
; Player coordinate must be >= these bounds.
; Using these bounds; the player will be considered within the
; bounds of a doorway, if strictly inside or 1 pixel outside.
;
DoorwayBoundsMinOver:
    .BYTE $3D, $BD, $00, $CF
...
    LDA $01                     ; [01] is Link's X, if facing horizontally; else Y.
    CMP DoorwayBoundsMinOver, Y
    BCC :+
    CMP DoorwayBoundsMaxOver, Y
    BCC @TestDoorwayDoor        ; If found a doorway, go see what it does when you touch it.
```

This patches `DoorwayBoundsMinOver` byte 0 (index 0, one of the two vertical
doorway entries per `DoorwayRequiredCoord`) at bank 5 CPU `$916C` (originally
`$3D`) to `$2D`. No other PRG bank holds `$3D` at that `$8000`-window offset,
so the patch can't misfire elsewhere.

**Caveat — three sibling tables untouched.** `DoorwayBoundsMaxOver`
(`$9173`), `DoorwayBoundsMinUnder` (`$917A`), and `DoorwayBoundsMaxUnder`
(`$9182`) are separate tables at their own fixed offsets and are not
patched; only the "overflow, minimum" bound for this one doorway direction
changes, so the doorway's detection zone becomes lopsided (wider on the
low-coordinate side) rather than uniformly larger.

**Not live-verified:** derived from reading `CheckDoorway` and
`DoorwayBoundsMinOver` (`src/Z_05.asm`), not from observing it in-game.

## Cellar Keese spawn somewhere else

**Code:** `AYVAVPAX`

**Effect:** In an underground "cellar" room (the small chest rooms reached
by falling through a trap door — game mode 9), the first of the four Blue
Keese that spawn there appears near the center of the room instead of
against the left wall.

**How it works:** `CellarKeeseXs` (`src/Z_05.asm:1870`) is a 4-byte X
position table, paired with `CellarKeeseYs` (`$1873`), read by
`AssignObjSpawnPositions` (`src/Z_05.asm:1879`, called from
`InitMode_EnterRoom`, `src/Z_05.asm:1540`) in the special-case block that
fires when `GameMode` is 9:

```
CellarKeeseXs:
    .BYTE $20, $60, $90, $D0
...
    ; If in mode 9 (play cellar), then spawn 4 blue keeses.
    LDA GameMode
    CMP #$09
    BNE @CheckCaves
    LDX #$03
:
    LDA #$1B                    ; Blue Keese
    STA ObjType+1, X
    LDA CellarKeeseXs, X
    STA ObjX+1, X
```

This patches `CellarKeeseXs` byte 0 at bank 5 CPU `$8966` (originally `$20`)
to `$78`.

**Caveat — shared byte with bank 4 executable code.** Bank 4 holds `$20` at
the same `$8000`-window offset, but as part of a `JSR` instruction
(`20 11 8A` = `JSR $8A11`) rather than table data — `gg.py`'s bank-uniqueness
check confirms bank 4 is the only other bank sharing this byte at this
offset. Because a Game Genie code matches on window offset and compare byte
regardless of which bank is currently mapped in, enabling this code will
*also* corrupt that `JSR` opcode into `$78` (`SEI`) whenever bank 4 is
swapped into `$8000`-`$BFFF` (i.e. during most enemy-AI code in
`src/Z_04.asm`), which is likely to cause a crash or hang the first time that
bank-4 routine runs. This code should be considered unsafe to leave enabled
outside of a controlled test session in a cellar room.

**Not live-verified:** derived from reading `AssignObjSpawnPositions` and
`CellarKeeseXs` (`src/Z_05.asm`), not from observing it in-game.

## Swap which tile object type appears first

**Code:** `YTNZEPZT`

**Effect:** Certain overworld tiles that normally hide a pushable rock (the
kind you push aside or bomb to find something underneath) instead reveal an
Armos statue — a type of hidden object the vanilla game's tile-object table
never actually uses — while still looking the same on screen until touched.

**How it works:** `TileObjectTypes` (`src/Z_05.asm:5743`) is a 6-byte table
paired index-for-index with `TileObjectPrimarySquaresOW` (`src/Z_05.asm:5746`),
read by `CheckTileObject` (`src/Z_05.asm:5924`, called from `LayoutRoomOW`)
while laying out an overworld room:

```
TileObjectTypes:
    .BYTE $62, $63, $64, $65, $66, $67
TileObjectPrimarySquaresOW:
    .BYTE $C8, $D8, $C4, $BC, $C0, $C0
...
    LDA TileObjectPrimarySquaresOW, X
    PHA                         ; Save primary square.
    LDA TileObjectTypes, X
    STA RoomTileObjType
```

Elsewhere the disassembly documents object type `$62` as "rock" (compared
directly in `InitPlayModes`/palette-selection code, `src/Z_07.asm:1546`:
"If type is not rock (`$62`)...") and notes that primary squares `$E9`/`$EA`
(indices 4 and 5, whose types are `$66`/`$67`) are unused in the shipped room
data — "Instead, armos is represented by primary square `$C0`." This patches
`TileObjectTypes` byte 0 at bank 5 CPU `$A970` (originally `$62`, rock) to
`$67` (Armos2, per the palette-selection code's "not rock ($62), so Armos2"
branch). No other PRG bank holds `$62` at that `$8000`-window offset, so the
patch can't misfire elsewhere.

**Caveat — the paired primary square is untouched.** `CheckTileObject`
restores the original `TileObjectPrimarySquaresOW` byte 0 (`$C8`) as the
tile actually drawn on screen before the secret is found, so nothing looks
different until the tile is uncovered — the mismatch is exactly the
intended effect, as the backlog item calls out, and it means the visible
overworld square gives no visual hint that an Armos rather than a rock is
underneath it.

**Not live-verified:** derived from reading `CheckTileObject`,
`InitPlayModes`, and `TileObjectTypes` (`src/Z_05.asm`, `src/Z_07.asm`), not
from observing it in-game.

## Move the Armos that hides the Power Bracelet secret

**Code:** `AKUAXGGZ`

**Effect:** The armos that guards the overworld's hidden Power Bracelet in
room `$24` is checked for instead in room `$40`. Standing an armos at the
right spot in the new room and burning/bombing/pushing it reveals the
Power Bracelet item there instead; room `$24`'s armos no longer triggers
anything special.

**How it works:** `InitArmosOrFlyingGhini` (`src/Z_04.asm:3158`) walks
`SecretArmosRoomIds` (`src/Z_04.asm:3152`) looking for the current room, and
the comments call out that index 0 is not a generic stairway secret:

```asm
    ; Look for the current room ID in an array of room ID's that
    ; have armos secrets.
    LDY #$06

@LoopArmosRoom:
    LDA RoomId

    ; If this element does not match the current room ID, go loop again.
    CMP SecretArmosRoomIds, Y
    BNE @NextLoopArmosRoom
    ...
    ; If the loop index <> 0, go use the stairs tile to patch the floor.
    CPY #$00
    BNE @UseChosenTile

    ; The room ID at index 0 is $24. Instead of stairs, this room
    ; has the power bracelet.
```

This patches `SecretArmosRoomIds` byte 0 at bank 4 CPU `$8CB2` (originally
`$24`) to `$40`. Raw form: `$8CB2:40:24`. No other PRG bank holds `$24` at
that `$8000`-window offset.

**Caveat — the paired X coordinate does not move.** `SecretArmosXs` byte 0
(`$8CB9`, `$E0`) still expects an armos at X `$E0`, Y `$80` in the new room.
If room `$40` has no armos sitting exactly there, the power bracelet check
never fires and the item becomes unobtainable until the code is reverted.

**Not live-verified:** derived from reading `InitArmosOrFlyingGhini`
(`src/Z_04.asm`), not from observing it in-game.

## Tektites start out jumping a different way

**Code:** `ZAUALYPE`

**Effect:** When a Tektite spawns, the random starting direction it's given
is drawn from a different set of values, so its first jump (and the object
timer derived from it) plays out differently than stock.

**How it works:** `InitTektite` (`src/Z_04.asm:1839`) picks a random index
0-3 and looks it up in `TektiteStartingDirs` (`src/Z_04.asm:1828`):

```asm
TektiteStartingDirs:
    .BYTE $01, $02, $05, $0A

InitTektite:
    ; Set a random starting direction.
    LDA Random+1, X
    AND #$03
    TAY
    LDA TektiteStartingDirs, Y
    STA ObjDir, X

    ; Multiply the direction value by 4 to set the object timer.
    ASL
    ASL
    STA ObjTimer, X
```

This patches `TektiteStartingDirs` byte 0 at bank 4 CPU `$8733` (originally
`$01`) to `$0A`. Raw form: `$8733:0A:01`. No other PRG bank holds `$01` at
that `$8000`-window offset.

**Caveat — the same byte feeds the initial jump timer.** Because the direction
value is shifted left twice to seed `ObjTimer`, this also changes how long the
Tektite waits before its first jump, not just which way it faces.

**Not live-verified:** derived from reading `InitTektite`
(`src/Z_04.asm`), not from observing it in-game.

## The raft launches in a different direction

**Code:** `PANAKYGA`

**Effect:** When Link boards the raft dock and it starts moving, Link is
turned to face a different direction than normal for the crossing.

**How it works:** `UpdateDock` (`src/Z_04.asm:3863`) reads `RaftDirections`
(`src/Z_04.asm:3860`) once Link is aligned with the dock and animates the
crossing:

```asm
RaftDirections:
    .BYTE $04, $08
...
    ; Play the "secret found" tune, and halt Link.
    JSR PlaySecretFoundTune
    LDA #$40
    STA ObjState

    ; Set Link's direction based on the raft's state.
    LDA RaftDirections-1, Y
    STA ObjDir
```

This patches `RaftDirections` byte 0 at bank 4 CPU `$8F74` (originally `$04`)
to `$01`. Raw form: `$8F74:01:04`. No other PRG bank holds `$04` at that
`$8000`-window offset.

**Caveat — a mismatched direction on this axis is very likely to strand
Link.** The dock's dock-state-1 crossing runs along one axis of the screen;
setting a direction that doesn't match that axis means Link will not track
along the raft's travel path correctly, and may appear to walk off the raft
or get stuck at the dock.

**Not live-verified:** derived from reading `UpdateDock`
(`src/Z_04.asm`), not from observing it in-game.

## Blue Wizzrobes teleport much further

**Code:** `EKUPETET`

**Effect:** When a Blue Wizzrobe picks a random diagonal to teleport toward,
one of the two possible horizontal offsets it can add to its position is
much larger than normal, so that particular teleport travels a lot farther
horizontally before the walkability check and re-alignment kick in.

**How it works:** `BlueWizzrobe_ChooseTeleportTarget` (`src/Z_04.asm:7240`)
adds a random entry from `BlueWizzrobeTeleportMaxOffsetsX`
(`src/Z_04.asm:7231`) to the object's X before testing whether the
destination tile is walkable:

```asm
BlueWizzrobeTeleportMaxOffsetsX:
    .BYTE $E0, $20, $E0, $20
...
BlueWizzrobe_ChooseTeleportTarget:
    ; Choose a random value between 0 and 3 that will be used
    ; to test and set a direction to move in.
    LDA Random, X
    AND #$03
    TAY

    ; The random value implies a random direction.
    ; Save the original X coordinate; and add to it the offset for
    ; the random direction.
    LDA ObjX, X
    PHA
    CLC
    ADC BlueWizzrobeTeleportMaxOffsetsX, Y
    STA ObjX, X
```

This patches `BlueWizzrobeTeleportMaxOffsetsX` byte 0 at bank 4 CPU `$9EB0`
(originally `$E0`, i.e. -32 as a signed offset) to `$C0` (-64). Raw form:
`$9EB0:C0:E0`.

**Caveat — bank 1 shares this byte at the same offset.** Bank 1 also holds
`$E0` at CPU `$9EB0`; if bank 1 is the bank mapped in `$8000`-`$BFFF` when
this compare fires, the Game Genie will patch whatever byte bank 1 has there
instead of (or in addition to) this table, with unpredictable results in
whatever bank-1 code that offset belongs to.

**Caveat — the walkability check can reject the target.** If the tile at the
much-farther destination is not walkable, `BlueWizzrobe_ChooseTeleportTarget`
falls back to `BlueWizzrobe_AlignWithNearestSquareAndRandomizeTimer` instead
of actually teleporting that far, so the visible effect may be inconsistent
frame to frame.

**Not live-verified:** derived from reading
`BlueWizzrobe_ChooseTeleportTarget` (`src/Z_04.asm`), not from observing it
in-game.

## Dodongo gets stunned by a dust cloud from further away

**Code:** `ALXOVXGA`

**Effect:** After Dodongo blows up a bomb without eating it, the leftover
dust cloud stuns Dodongo (knocking it briefly out of its normal behavior)
from a much greater distance than normal, instead of only when the cloud is
right next to it.

**How it works:** the caller in `src/Z_04.asm` (around line 6134) checks the
dust cloud's proximity with `Y=#$00` before setting Dodongo's stunned state,
and `Dodongo_IsBombInRange` (`src/Z_04.asm:6231`) documents the index:

```asm
DodongoBombPositiveLimits:
    .BYTE $0C, $11
...
; Params:
; Y: limit index (0 for dust cloud, 1 for the bomb)
...
Dodongo_IsBombInRange:
    LDA DodongoBombPositiveLimits, Y
    STA $06
```

```asm
    ; The bomb already blew up.
    ; If the dust cloud is in range of the monster,
    ; then set stunned state (2).
    LDY #$00
    JSR Dodongo_IsBombInRange
    BNE @Exit
    LDA #$02
    STA ObjState, X
```

This patches `DodongoBombPositiveLimits` byte 0 (the dust-cloud index) at
bank 4 CPU `$9A2E` (originally `$0C`) to `$30`. Raw form: `$9A2E:30:0C`. No
other PRG bank holds `$0C` at that `$8000`-window offset.

**Caveat — this is the dust-cloud radius, not the bomb-eating radius.** Byte
1 of the same table (`$9A2F`, originally `$11`) governs how close an
unexploded bomb must be for Dodongo to eat it in `Dodongo_TryEatBomb`; this
code does not change that distance.

**Not live-verified:** derived from reading `Dodongo_IsBombInRange` and its
caller (`src/Z_04.asm`), not from observing it in-game.

## A different object slot can pick up dropped items

**Code:** `IENUPEYE`

**Effect:** When an item drops and Link has an active sword shot out, the
game checks the boomerang's position for pickup purposes instead of the
sword's, so an active boomerang (not the sword) can now scoop up the item
from where the sword normally would.

**How it works:** `UpdateItem` (`src/Z_04.asm:11206`) substitutes each of
three weapon object slots for Link's position in turn while checking for a
pickup, using `ItemTakerObjSlots` (`src/Z_04.asm:11203`):

```asm
ItemTakerObjSlots:
    .BYTE $00, $0F, $0D, $12
...
    ; In addition to Link, there are 3 objects that can pick up items:
    ; * arrow
    ; * sword
    ; * boomerang
    ;
    ; For each weapon that's active, substitute it's location for
    ; Link's and try taking the item. Have Link himself check last.
    LDA #$04
    STA $0D                     ; [0D] holds index into array of item slots that can take an item.

@LoopItemTaker:
    ...
    LDY $0D
    LDX ItemTakerObjSlots-1, Y
    LDA ObjX, X
    STA ObjX
```

This patches `ItemTakerObjSlots` byte 1 (the sword slot) at bank 4 CPU
`$B0F9` (originally `$0F`) to `$0D` — the same slot already used for the
boomerang at byte 2. Raw form: `$B0F9:0D:0F`. No other PRG bank holds `$0F`
at that `$8000`-window offset.

**Caveat — the sword slot is no longer checked.** With byte 1 repointed to
the boomerang's slot, the game checks the boomerang's position twice (bytes
1 and 2) and never checks the sword's position, so items can no longer be
picked up via an active sword shot.

**Not live-verified:** derived from reading `UpdateItem`
(`src/Z_04.asm`), not from observing it in-game.

## Ganon starts somewhere else in the room

**Code:** `AYXXSIAU`

**Effect:** When Ganon becomes visible/vulnerable and his position is
re-randomized, one of the two possible starting X coordinates he can appear
at is different, changing where he shows up in his room.

**How it works:** `Ganon_RandomizeLocation` (`src/Z_04.asm:10416`, called
from `Ganon_UpdateBrownState`) places Ganon at a fixed Y and a random X
chosen from `GanonStartXs` (`src/Z_04.asm:10454`):

```asm
GanonStartXs:
    .BYTE $30, $B0

; Description:
; Put Ganon at Y=$A0, and a random X of $30 or $B0.
;
Ganon_RandomizeLocation:
    LDA #$A0
    STA ObjY, X
    LDA FrameCounter
    AND #$01
    TAY
    LDA GanonStartXs, Y
    STA ObjX, X
```

This patches `GanonStartXs` byte 0 at bank 4 CPU `$AD2D` (originally `$30`)
to `$78`. Raw form: `$AD2D:78:30`. No other PRG bank holds `$30` at that
`$8000`-window offset.

**Not live-verified:** derived from reading `Ganon_RandomizeLocation`
(`src/Z_04.asm`), not from observing it in-game.

## Gleeok's necks sit at a different height

**Code:** `NEEZYEYV`

**Effect:** When Gleeok spawns, the first of its (up to) six neck segments is
initialized at a different Y coordinate than normal, so that neck starts out
noticeably lower on screen relative to the others.

**How it works:** `InitGleeok` (`src/Z_04.asm:7641`) loops over
`GleeokSegmentYs` (`src/Z_04.asm:7638`) to set each neck segment's starting
Y:

```asm
GleeokSegmentYs:
    .BYTE $6F, $74, $79, $7E, $83, $88
...
    ; Look up and set the Y of the current segment of each neck.
    LDA GleeokSegmentYs, X
    STA Gleeok_NeckYs0, X
    STA Gleeok_NeckYs1, X
    STA Gleeok_NeckYs2, X
    STA Gleeok_NeckYs3, X
```

This patches `GleeokSegmentYs` byte 0 at bank 4 CPU `$A087` (originally
`$6F`) to `$8F`. Raw form: `$A087:8F:6F`. No other PRG bank holds `$6F` at
that `$8000`-window offset.

**Caveat — byte 0 seeds all four necks' first segment.** The same loop
iteration writes this value into `Gleeok_NeckYs0`-`3`, so all four of
Gleeok's necks (not just one) get their innermost segment repositioned.

**Not live-verified:** derived from reading `InitGleeok`
(`src/Z_04.asm`), not from observing it in-game.

## Vire jumps differently

**Code:** `XNEOKSSN`

**Effect:** As a Vire wanders left or right and its horizontal grid offset
reaches the value that triggers a jump, the vertical offset it jumps by at
that point is slightly different than normal, changing the shape of its
jump arc.

**How it works:** `UpdateVireState0` (`src/Z_04.asm:6963`) indexes
`VireJumpOffsets` (`src/Z_04.asm:6959`) with the absolute value of the
Vire's grid offset:

```asm
VireJumpOffsets:
    .BYTE $00, $FD, $FE, $FF, $FF, $00, $FF, $00
    .BYTE $00, $01, $00, $01, $01, $02, $03, $00

UpdateVireState0:
    LDA #$80                    ; Turn rate $80
    JSR UpdateCommonWanderer
    ...
    ; Get the absolute value of the grid offset (0 to $F);
    ; so it becomes an index into the jump offset array.
    LDA ObjGridOffset, X
    JSR Abs
    TAY

    ; Add the vertical offset; so that as the vire moves left or right,
    ; it jumps.
```

This patches `VireJumpOffsets` byte 1 at bank 4 CPU `$9D8C` (originally
`$FD`, i.e. -3 as a signed offset) to `$FA` (-6). Raw form: `$9D8C:FA:FD`.
No other PRG bank holds `$FD` at that `$8000`-window offset.

**Not live-verified:** derived from reading `UpdateVireState0`
(`src/Z_04.asm`), not from observing it in-game.

## Ganon's guard fires stand somewhere else

**Code:** `AKKZEEAY`

**Effect:** When Zelda's room is set up at the end of Level 9, the first of
her four guarding flame objects (in slot 4) spawns at a different X
coordinate, so that flame sits somewhere else in the room relative to the
other three.

**How it works:** `InitZelda` (`src/Z_04.asm:9462`) loops over
`GuardFireXs`/`GuardFireYs` (`src/Z_04.asm:9456`) to place four guard-fire
objects and Zelda herself:

```asm
GuardFireXs:
    .BYTE $78, $60, $70, $80, $90

GuardFireYs:
    .BYTE $88, $B5, $9D, $9D, $B5

InitZelda:
    ; Make Zelda and 4 flames that guard her, in object slots 5 to 1.
    LDX #$05
:
    ; Look up and set the location of each object.
    LDA GuardFireXs-1, X
    STA ObjX, X
    LDA GuardFireYs-1, X
    STA ObjY, X
    LDA #$3F                    ; Guard fire object type
    STA ObjType, X
    DEX
    BNE :-
```

This patches `GuardFireXs` byte 0 at bank 4 CPU `$A8C0` (originally `$78`)
to `$40`. Raw form: `$A8C0:40:78`. No other PRG bank holds `$78` at that
`$8000`-window offset.

**Caveat — the backlog cited `UpdateGuardFire` as the reader; that routine
does not touch this table.** `GuardFireXs`/`GuardFireYs` are only read by
`InitZelda` when the room is set up (once, via the loop above); `src/Z_04.asm:9654`'s
`UpdateGuardFire` handles per-frame behavior of an already-placed flame and
never re-reads this table.

**Not live-verified:** derived from reading `InitZelda`
(`src/Z_04.asm`), not from observing it in-game.

## Group-0 monsters always drop an item

**Code:** `NYUUTAAS`

**Effect:** Octoroks, Red Tektites, Moblins, Blue Leevers and Blue Wizzrobes
drop an item every single time they die, instead of roughly one time in three.

**How it works:** `DropItemRates` (`src/Z_04.asm:11054`) holds one threshold
per monster group, under the header comment "To drop an item, a random value
must be less than the element for the monster group":

```
DropItemRates:
    .BYTE $50, $98, $68, $68
```

Byte 0 is the group-0 threshold. Group 0 is `DropItemMonsterTypes0`
(`src/Z_04.asm:11040`), `.BYTE $07, $08, $0E, $04, $0F, $23`. Resolving those
types through `UpdateObject_JumpTable` (`src/Z_07.asm:5321`): `$07` and `$08`
are Octoroks, `$0E` is a Tektite (Red — `Jumper_GetKind`, `src/Z_04.asm:2521`,
makes `$0D` Blue and `$0E` Red), `$04` is a Moblin, `$0F` is the Blue Leever
and `$23` is the Blue Wizzrobe.
`SetUpDroppedItem` (`src/Z_04.asm:11070`) scans the three
`DropItemMonsterTypes*` lists in order to pick the row, then compares a random
byte against `DropItemRates[row]`.

This patches `DropItemRates` byte 0 at bank 4 CPU `$B03E` (originally `$50`)
to `$FF`. Raw form: `$B03E:FF:50`. A random byte is always less than `$FF`
except when it is exactly `$FF`, so the drop becomes near-certain. No other
PRG bank holds `$50` at that `$8000`-window offset.

**Caveat — the *other* three groups are untouched.** Bytes 1-3 (`$98`, `$68`,
`$68`) still govern every other monster, so most of the bestiary drops at its
normal rate.

**Not live-verified:** derived from reading `DropItemRates`,
`DropItemMonsterTypes0` and `SetUpDroppedItem` (`src/Z_04.asm`), not from
observing it in-game.

## Group-0 monsters drop a heart container first in the kill cycle

**Code:** `ZPKLZAZX`

**Effect:** The first slot of the drop cycle for the group-0 monsters
(Octoroks, Red Tektites, Moblins, Blue Leevers, Blue Wizzrobes) yields a heart
container instead of its usual item.

**How it works:** `DropItemTable` (`src/Z_04.asm:11063`) is a 4-row by 10-column
table of item IDs, under the header comment "ID's for items dropped by
monsters. WorldKillCycle addresses the column. Monsters are arranged in groups
that determine the row. There are four rows.":

```
DropItemTable:
    .BYTE $22, $18, $22, $18, $23, $18, $22, $22
    .BYTE $18, $18, $0F, $18, ...
```

`SetUpDroppedItem` (`src/Z_04.asm:11070`) resolves the row from the monster's
type, adds `DropItemSetBaseOffsets[row]` (`$00, $0A, $14, $1E` — multiples of
`$A`, `src/Z_04.asm:11049`) and then adds `WorldKillCycle`
(`src/Z_04.asm:11140`), which `src/Z_07.asm:5466`-`5473` advances on each kill.
Byte 0 is therefore row 0, column 0.

This patches `DropItemTable` byte 0 at bank 4 CPU `$B042` (originally `$22`)
to `$1A`. Raw form: `$B042:1A:22`. Item ID `$1A` is the heart container —
the same ID this project's "Every overworld screen has a heart container
waiting outside" entry established from `ItemIdToSlot`/`ItemIdToDescriptor`
(`src/Z_01.asm:4318`). No other PRG bank holds `$22` at that `$8000`-window
offset.

**Caveat — only one column of one row changes.** The kill cycle keeps
rotating, so this is the drop you get at one particular point in the cycle,
not on every kill. Combining it with the `NYUUTAAS` code above (which makes
group 0 always drop *something*) makes it come up far more often.

**Not live-verified:** derived from reading `DropItemTable`,
`DropItemSetBaseOffsets`, `SetUpDroppedItem` (`src/Z_04.asm`) and
`ItemIdToSlot` (`src/Z_01.asm`), not from observing it in-game.

## Dead Patra children drop items

**Code:** `NYOULEIS`

**Effect:** The corpse object that a killed Patra child turns into becomes
eligible to drop an item, which it normally never is.

**How it works:** `NoDropMonsterTypes` (`src/Z_04.asm:11032`) lists the object
types that never drop, under the header "Types of objects that do not drop
items":

```
NoDropMonsterTypes:
    .BYTE $5D, $14, $15, $1B, $1C, $1D, $17
```

Counting through `UpdateObject_JumpTable` (`src/Z_07.asm:5321`), type `$5D` is
`UpdateDeadDummy` — the "dead dummy" corpse object. `SetDeadDummyObjType`
(`src/Z_04.asm:9664`) is what creates one (`LDA #$5D / STA ObjType, X`), and
its only caller is `UpdatePatraChild` (`src/Z_04.asm:10270`): "If the monster
died, then change to the dead dummy object." The rest of the list is Gels
(`$14`, `$15`), the three Keese (`$1B`-`$1D`) and Like Like (`$17`).

`SetUpDroppedItem` (`src/Z_04.asm:11070`) walks this seven-entry list first
and destroys the monster outright on a match. This patches byte 0 at bank 4
CPU `$B01B` (originally `$5D`) to `$FF`. Raw form: `$B01B:FF:5D`. No object
type is ever `$FF`, so the entry stops matching anything and a dead dummy
falls through to the group search instead. `$5D` appears in none of
`DropItemMonsterTypes0`/`1`/`2`, so the row counter reaches 3 and the dummy
draws from row 3 of `DropItemTable`. No other PRG bank holds `$5D` at that
`$8000`-window offset.

**Caveat — narrow observable scope.** Patra children are the only source of
dead dummies, so this only shows up in Patra's room (Level 9). Whether a dead
dummy actually reaches `SetUpDroppedItem`'s caller in bank 7
(`src/Z_07.asm:5488`) a second time is not established from the source alone;
if it does not, the code is a no-op.

**Not live-verified:** derived from reading `NoDropMonsterTypes`,
`SetUpDroppedItem`, `SetDeadDummyObjType`, `UpdatePatraChild`
(`src/Z_04.asm`) and `UpdateObject_JumpTable` (`src/Z_07.asm`), not from
observing it in-game.

## Four-statue rooms fire twice as many fireballs at once

**Code:** `TAUATTLA`

**Effect:** The dungeon rooms whose layout puts a statue in each corner spit
out up to seven fireballs in a burst instead of four.

**How it works:** `StatueFireballCounts` (`src/Z_04.asm:1574`) holds one entry
per statue pattern:

```
StatueRoomLayouts:
    .BYTE $24, $23

StatueFireballCounts:
    .BYTE $03, $01, $01
```

`UpdateStatues` (`src/Z_04.asm:1593`) selects the pattern (0 for room layout
`$24`, the four-statue rooms), then loads `StatueFireballCounts, Y` as the
number of fireballs to make minus 1. Byte 0 is therefore the four-statue
burst: `$03` means four fireballs.

This patches byte 0 at bank 4 CPU `$8636` (originally `$03`) to `$06`. Raw
form: `$8636:06:03`. No other PRG bank holds `$03` at that `$8000`-window
offset.

**Caveat — free monster slots cap the effect.** `UpdateStatues` bails unless
it finds an empty monster slot with index `>= 6`, so in a busy room the extra
fireballs simply will not be created.

**Not live-verified:** derived from reading `StatueFireballCounts`,
`StatueRoomLayouts` and `UpdateStatues` (`src/Z_04.asm`), not from observing
it in-game.

## Four-statue rooms start shooting almost immediately

**Code:** `GAUEPTAI`

**Effect:** The corner statues in four-statue dungeon rooms open fire the
moment you walk in, instead of after a pause.

**How it works:** `StatueFireballStartTimes` (`src/Z_04.asm:1577`) sits
directly after `StatueFireballCounts` and is indexed the same way by
`UpdateStatues` (`src/Z_04.asm:1593`):

```
StatueFireballStartTimes:
    .BYTE $50, $80, $F0, $60
```

Byte 0 is the pattern-0 (four-statue) start delay.

This patches byte 0 at bank 4 CPU `$8639` (originally `$50`) to `$04`. Raw
form: `$8639:04:50`. No other PRG bank holds `$50` at that `$8000`-window
offset.

**Not live-verified:** derived from reading `StatueFireballStartTimes` and
`UpdateStatues` (`src/Z_04.asm`), not from observing it in-game.

## Zols and Gels move almost continuously

**Code:** `PENATSAP`

**Effect:** Zols and Gels stop pausing between hops in their first movement
phase, so they close on Link far more aggressively.

**How it works:** `ZolGelDelays` (`src/Z_04.asm:1517`) is an eight-entry table
of pauses:

```
ZolGelDelays:
    .BYTE $18, $28, $38, $48, $08, $18, $28, $38
```

`UpdateNormalZolOrGel` (`src/Z_04.asm:1476`) loads `ZolGelDelays, Y` and
stores it into `ObjTimer, X` under the comment "Set a delay at a tile edge for
the next time to move." Byte 0 is the shortest of the first four.

This patches byte 0 at bank 4 CPU `$85F6` (originally `$18`) to `$01`. Raw
form: `$85F6:01:18`. No other PRG bank holds `$18` at that `$8000`-window
offset.

**Caveat — one of eight entries.** The other seven delays are untouched, so
the effect only shows when the index lands on 0; Zols and Gels will still
pause the rest of the time.

**Not live-verified:** derived from reading `ZolGelDelays` and
`UpdateNormalZolOrGel` (`src/Z_04.asm`), not from observing it in-game.

## Blue Tektites jump much higher

**Code:** `XNNAXESN`

**Effect:** Blue Tektites launch themselves considerably higher on each hop.

**How it works:** `JumperStartSpeedsHi` (`src/Z_04.asm:2244`) supplies the
high byte of the signed upward launch speed:

```
JumperStartSpeedsHi:
    .BYTE $FD, $FD, $FF
```

`Jumper_GetKind` (`src/Z_04.asm:2521`) maps object type minus `$0D` to the
index, so index 0 is the Blue Tektite (type `$0D`), 1 the Red Tektite and 2
the Boulder. The value is negative (upward).

This patches byte 0 at bank 4 CPU `$88F2` (originally `$FD`) to `$FA`. Raw
form: `$88F2:FA:FD`. Making the high byte more negative increases the launch
speed. No other PRG bank holds `$FD` at that `$8000`-window offset.

**Caveat — the table overlaps `JumperYAccelerations`.** The annotation on
`JumperYAccelerations` (`src/Z_04.asm:2238`, CPU `$88D5`) notes that its
unused upward-acceleration slots are reused as these starting speeds, so the
two tables share ROM. The byte patched here was read back from the ROM at
`$88F2` and matched the source line, but be aware the two names describe the
same region.

**Not live-verified:** derived from reading `JumperStartSpeedsHi`,
`Jumper_GetKind` and `UpdateTektiteOrBoulder` (`src/Z_04.asm`), not from
observing it in-game.

## Blue Leevers surface and charge far faster

**Code:** `AGSAUXAA`

**Effect:** Blue Leevers rip across the ground at eight times their normal
speed during the state that byte 0 governs.

**How it works:** `BlueLeeverStateQSpeeds` (`src/Z_04.asm:2592`) gives a
quarter-speed per leever state:

```
BlueLeeverStateQSpeeds:
    .BYTE $08, $08, $08, $20, $08, $08
```

`UpdateBlueLeever`/`UpdateBurrower` (`src/Z_04.asm:2601`, `2606`) cycles the
state 0-5 and loads `BlueLeeverStateQSpeeds, Y` straight into
`ObjQSpeedFrac, X` alongside `BlueLeeverStateTimes, Y`.

This patches byte 0 at bank 4 CPU `$8A53` (originally `$08`) to `$40`. Raw
form: `$8A53:40:08`. No other PRG bank holds `$08` at that `$8000`-window
offset.

**Caveat — state 0 is the buried state.** Byte 0 corresponds to state 0, in
which `Burrower_AnimateDrawAndCheckCollisions` (`src/Z_04.asm:2664`) returns
early without drawing, so the leever covers ground while still underground.
Expect it to pop up somewhere unexpected rather than to visibly sprint.

**Not live-verified:** derived from reading `BlueLeeverStateQSpeeds`,
`UpdateBlueLeever` and `UpdateBurrower` (`src/Z_04.asm`), not from observing
it in-game.

## Red Leevers submerge almost immediately

**Code:** `AAEAEUNN`

**Effect:** Red Leevers dive back under the sand almost as soon as they have
fully emerged, instead of staying up and chasing Link.

**How it works:** `RedLeeverStateTimes` (`src/Z_04.asm:2738`) gives a duration
per state:

```
RedLeeverStateQSpeeds:
    .BYTE $00, $00, $00, $20, $00, $00

RedLeeverStateTimes:
    .BYTE $00, $10, $08, $FF, $08, $10
```

State 3 is the fully-emerged, moving state: it is the only state with a
nonzero speed in `RedLeeverStateQSpeeds` (`$20`), and the only one with a
`$FF` duration. `RedLeever_CycleStateDrawAndCheckCollisions`
(`src/Z_04.asm:2938`) loads `RedLeeverStateTimes, Y` into `ObjTimer, X` each
time it advances the state.

This patches byte 3 at bank 4 CPU `$8B00` (originally `$FF`) to `$08`. Raw
form: `$8B00:08:FF`.

**Caveat — bank collision.** Bank 0 also holds `$FF` at this `$8000`-window
offset, so if bank 0 is mapped in when the CPU touches `$8B00` the Game Genie
will patch bank 0's byte instead. Bank 0 is the audio engine; treat any sound
oddity while this code is on as that collision, not as a leever effect.

**Not live-verified:** derived from reading `RedLeeverStateTimes`,
`RedLeeverStateQSpeeds` and `RedLeever_CycleStateDrawAndCheckCollisions`
(`src/Z_04.asm`), not from observing it in-game.

## Goriyas throw their boomerangs from anywhere on the screen

**Code:** `NNEAIPPS`

**Effect:** Goriyas (and Lynels, which share the same routine) no longer need
to be close to Link before deciding to throw — they line up and throw from
across the whole room.

**How it works:** `UpdateGoriya` (`src/Z_04.asm:434`) works out the vertical
and horizontal distances to the chase target, picks whichever is longer, and
then tests it:

```
    ; If the distance chosen < $51, then
    ; set the "wants to shoot" flag to 1,
    ; and face in the chosen direction.
    LDA $0000, Y
    CMP #$51
    BCS L_Walker_SetInputDirAndTryShootingBoomerang
    INC ObjWantsToShoot, X
```

This patches the compare operand at bank 4 CPU `$8185` (originally `$51`) to
`$FF`. Raw form: `$8185:FF:51`. Only a distance of exactly `$FF` now fails the
test, so `ObjWantsToShoot` is set essentially wherever Link is. No other PRG
bank holds `$51` at that `$8000`-window offset.

**Caveat — shared with Lynels.** `UpdateLynel` (`src/Z_04.asm:1958`) calls
`UpdateGoriya` before substituting the sword-shot object type, so Lynels get
the same extended decision range.

**Not live-verified:** derived from reading `UpdateGoriya` and `UpdateLynel`
(`src/Z_04.asm`), not from observing it in-game.

## Goriya boomerangs fly much faster

**Code:** `ENSEPPEZ`

**Effect:** A thrown Goriya boomerang crosses the room at roughly 3.75 pixels
a frame instead of 2.5.

**How it works:** After a successful throw, `UpdateGoriya`
(`src/Z_04.asm:603`) sets up the projectile:

```
    ; Fly at q-speed $A0 (2.5 pixels a frame).
    LDA #$A0
    STA ObjQSpeedFrac, Y
```

This patches the immediate at bank 4 CPU `$81D9` (originally `$A0`) to `$F0`.
Raw form: `$81D9:F0:A0`. No other PRG bank holds `$A0` at that `$8000`-window
offset.

**Caveat — set once, at throw time.** `ObjQSpeedFrac` for the boomerang slot
is written here only, so this is the speed the boomerang keeps for its whole
flight, outbound and returning.

**Not live-verified:** derived from reading `UpdateGoriya` (`src/Z_04.asm`),
not from observing it in-game.

## Goriya boomerangs fly much further before turning back

**Code:** `EKSETPPI`

**Effect:** A Goriya's boomerang travels about `$C0` pixels out before
reversing, instead of `$51`.

**How it works:** The same setup block in `UpdateGoriya`
(`src/Z_04.asm:607`):

```
    ; For boomerangs, move up to $51 pixels (horizontally or vertically).
    LDA #$51
    STA ObjMovingLimit, Y
```

This patches the immediate at bank 4 CPU `$81DE` (originally `$51`) to `$C0`.
Raw form: `$81DE:C0:51`. No other PRG bank holds `$51` at that `$8000`-window
offset.

**Caveat — the same `$51` appears twice in this routine.** The other one, at
`$8185`, is the *decision* range (see the `NNEAIPPS` code above) and is a
`CMP`, not an `LDA`. This code patches the `LDA #$51` that feeds
`ObjMovingLimit`; the two are independent and can be used together.

**Not live-verified:** derived from reading `UpdateGoriya` (`src/Z_04.asm`),
not from observing it in-game.

## Goriyas throw again almost immediately

**Code:** `LEVEYOYL`

**Effect:** A Goriya's post-throw cooldown drops from up to 63 frames to up to
3, so it can throw again nearly at once.

**How it works:** The last thing `UpdateGoriya` (`src/Z_04.asm:620`) does
after a successful throw:

```
    ; Have the monster wait a random amount of time, up to $3F frames.
    LDA Random, X
    AND #$3F
    STA ObjTimer, X
```

This patches the mask at bank 4 CPU `$81EF` (originally `$3F`) to `$03`. Raw
form: `$81EF:03:3F`. The mask must stay a low-bits mask for the "up to N
frames" reading to hold, which `$03` is. No other PRG bank holds `$3F` at that
`$8000`-window offset.

**Caveat — a second gate still applies to Red Goriyas.** `UpdateGoriya`
(`src/Z_04.asm:553`) also requires `Random, X` to be exactly `$23` or `$77`
before a Red Goriya will throw at all, so Red Goriyas stay comparatively
sparing. Blue Goriyas (type `$05`) skip that test and get the full benefit.

**Not live-verified:** derived from reading `UpdateGoriya` (`src/Z_04.asm`),
not from observing it in-game.

## Zoras surface far more often

**Code:** `AKNAGVIA`

**Effect:** Zoras appear much more readily in overworld water — the game tries
`$40` candidate spots per attempt instead of `$0D`, so it far more often finds
a water tile to place one on.

**How it works:** `CheckZora` (`src/Z_04.asm:1772`) sets up a bounded search:

```
    ; Loop $D times looking for a water tile to put a zora on.
    ; Indexed by [0D].
    LDA #$0D
    STA $0D
```

This patches the immediate at bank 4 CPU `$86F4` (originally `$0D`) to `$40`.
Raw form: `$86F4:40:0D`. No other PRG bank holds `$0D` at that `$8000`-window
offset.

**Caveat — the extra tries are not really random.** The loop body reads
`LDA a:Random, Y` with `Y = [0D]`, so a count above `$0D` indexes past the end
of the `Random` array into adjacent RAM. That is harmless — the bytes are only
used as candidate coordinates, and each candidate is still rejected unless it
lands on a water tile — but the additional candidates are whatever those RAM
bytes happen to hold, not fresh random numbers.

**Caveat — two other Zora codes live in this routine.** The existing codes
patching `$86E6` and `$871F` are independent of this byte, but all three are in
`CheckZora` and can interact.

**Not live-verified:** derived from reading `CheckZora` (`src/Z_04.asm`), not
from observing it in-game.

## Red Leevers swarm — up to ten at once

**Code:** `ZAOEELZE`

**Effect:** Up to ten Red Leevers can be active at the same time instead of
two.

**How it works:** `UpdateRedLeever` (`src/Z_04.asm:2755`) gates new eruptions
on a running count:

```
    ; Only allow two red leevers at a time.
    LDA ActiveRedLeeverCount
    CMP #$02
    BCS @Exit
```

This patches the compare operand at bank 4 CPU `$8B18` (originally `$02`) to
`$0A`. Raw form: `$8B18:0A:02`. No other PRG bank holds `$02` at that
`$8000`-window offset.

**Caveat — other limits still apply.** Red Leevers must still pass the
`RedLeeverLongTimer` gate and find a walkable tile, and they compete for the
same monster object slots as everything else on the screen, so ten at once is
a ceiling rather than a promise.

**Not live-verified:** derived from reading `UpdateRedLeever`
(`src/Z_04.asm`), not from observing it in-game.

## Red Leevers erupt right on top of Link

**Code:** `AAUAUUAX`

**Effect:** A Red Leever that surfaces below or beside Link comes up `$08`
pixels away instead of `$28` — practically underfoot.

**How it works:** `UpdateRedLeever` (`src/Z_04.asm:2778`) picks the vertical
offset from Link before placing the new leever:

```
    ; If facing down, then use Y offset $28.
    ; Else store Y offset -$28 in [00].
    LDY #$28
    LDA ObjDir, X
    AND #$08
    BEQ :+
    LDY #$D8
:
    STY $00
```

This patches the `LDY #$28` immediate at bank 4 CPU `$8B33` (originally `$28`)
to `$08`. Raw form: `$8B33:08:28`. No other PRG bank holds `$28` at that
`$8000`-window offset.

**Caveat — the effect is asymmetric.** Only the positive (downward) offset is
patched. The `$D8` twin at `$8B3B`, taken when direction bit 3 is set, and the
horizontal pair at `$8B57`/`$8B5F` are untouched, so leevers coming from the
other side still keep their full distance.

**Not live-verified:** derived from reading `UpdateRedLeever`
(`src/Z_04.asm`), not from observing it in-game.

## Red Leevers start bursting out sooner

**Code:** `PAKEYYIA`

**Effect:** The initial Red Leever delay after entering a screen drops from 5
to 1.

**How it works:** `InitLeever` (`src/Z_04.asm:1853`):

```
    ; Set red leever long timer to 5, for use in determining when
    ; to burst out of the ground.
    LDA #$05
    STA RedLeeverLongTimer
```

This patches the immediate at bank 4 CPU `$874F` (originally `$05`) to `$01`.
Raw form: `$874F:01:05`. No other PRG bank holds `$05` at that `$8000`-window
offset.

**Caveat — only the first delay changes.** `UpdateRedLeever`
(`src/Z_04.asm:2880`) reloads `RedLeeverLongTimer` from an `ASL` of the
animation counter afterwards, so subsequent eruptions go back to the stock
timing. Pair it with `ZAOEELZE` (ten at once) if you want the swarm to build
up quickly.

**Not live-verified:** derived from reading `InitLeever` and `UpdateRedLeever`
(`src/Z_04.asm`), not from observing it in-game.

## Peahats freeze while flying

**Code:** `ENEAAYEZ`

**Effect:** Raises the flying speed cap set when a Peahat or a flying Ghini is
initialized, from `$A0` to `$F0`.

**How it works:** `EndInitFlyer` (`src/Z_04.asm:1893`):

```
EndInitFlyer:
    JSR ResetFlyerState
    LDA #$A0
    STA FlyingMaxSpeedFrac
    LDA #$1F
    STA Flyer_ObjSpeed, X
    RTS
```

This patches the immediate at bank 4 CPU `$8780` (originally `$A0`) to `$F0`.
Raw form: `$8780:F0:A0`. No other PRG bank holds `$A0` at that `$8000`-window
offset.

**Caveat — which monsters this covers.** `EndInitFlyer` is reached two ways:
`InitPeahat` (`src/Z_04.asm:1887`) falls through into it, and
`L_EndInitFlyingGhini` (`src/Z_04.asm:3308`) jumps to it. Keese use
`InitBlueKeese` (`src/Z_04.asm:1100`), which writes its own `$C0`, so Keese are
**not** affected by this code.

**Caveat — `FlyingMaxSpeedFrac` is a single global, not per-object.** Whichever
flyer initialized most recently sets the cap for all of them, so in a mixed
room the effect depends on spawn order.

**Not live-verified:** derived from reading `EndInitFlyer`, `InitPeahat` and
`InitBlueKeese` (`src/Z_04.asm`), not from observing it in-game.

## Peahats and flying Ghinis start out much faster

**Code:** `YNEAINYO`

**Effect:** The starting flight speed for a Peahat or flying Ghini jumps from
`$1F` to `$7F` — the same speed red and black Keese are given.

**How it works:** The second half of the same `EndInitFlyer` block
(`src/Z_04.asm:1896`):

```
    LDA #$1F
    STA Flyer_ObjSpeed, X
```

This patches the immediate at bank 4 CPU `$8785` (originally `$1F`) to `$7F`.
Raw form: `$8785:7F:1F`. `$7F` is the value `InitRedOrBlackKeese`
(`src/Z_04.asm:1114`) uses, so it is a documented speed for this field. No
other PRG bank holds `$1F` at that `$8000`-window offset.

**Caveat — same callers as `ENEAAYEZ`.** Peahats and flying Ghinis only; Keese
init elsewhere. Unlike the max-speed byte, `Flyer_ObjSpeed, X` *is* per-object,
so each flyer keeps its own starting speed.

**Not live-verified:** derived from reading `EndInitFlyer` and
`InitRedOrBlackKeese` (`src/Z_04.asm`), not from observing it in-game.

## Gleeok heads fly faster

**Code:** `EYNXIPEV`

**Effect:** Raises the severed Gleeok heads' flying speed cap from `$E0` to
`$F8`.

**How it works:** `InitGleeokHead` (`src/Z_04.asm:7822`):

```
InitGleeokHead:
    JSR InitBlueKeese

    ; Set flying speed $BF and maximum $E0.
    LDA #$E0
    STA FlyingMaxSpeedFrac
    LDA #$BF
    STA Flyer_ObjSpeed, X
    RTS
```

This patches the immediate at bank 4 CPU `$A17D` (originally `$E0`) to `$F8`.
Raw form: `$A17D:F8:E0`. No other PRG bank holds `$E0` at that `$8000`-window
offset.

**Caveat — the paired starting speed is a separate byte.** The `LDA #$BF` at
bank 4 CPU `$A182` (`src/Z_04.asm:7826`) sets the head's initial speed and is
not touched here; raising the cap only matters once a head accelerates toward
it.

**Caveat — `FlyingMaxSpeedFrac` is global.** As with the Peahat code above, the
cap is one variable shared by every flyer, so it belongs to whichever flyer
initialized last.

**Not live-verified:** derived from reading `InitGleeokHead` (`src/Z_04.asm`),
not from observing it in-game.

## Zoras spit again almost immediately after surfacing

**Code:** `ZEUAZYAZ`

**Effect:** After a Zora fires its fireball it submerges after 2 frames instead
of `$20`, so it cycles back up to spit again far more often.

**How it works:** `UpdateZora` (`src/Z_04.asm:1935`):

```
    ; Shoot a fireball; and set the timer so that it expires faster.
    LDA #$55
    JSR ShootFireball
    LDA #$20
    STA ObjTimer, X
```

This patches the immediate at bank 4 CPU `$87B2` (originally `$20`) to `$02`.
Raw form: `$87B2:02:20`.

**Caveat — bank 1 also holds `$20` at this offset.** The compare byte does not
make this code bank-unique: bank 1 has `$20` at the same `$8000`-window offset
(`$07B2`). If bank 1 is mapped in and execution or a read reaches `$87B2`, the
Game Genie will substitute there too. Bank 1 is the Save-RAM/common-code bank,
so this is unlikely to matter in practice, but it is not impossible.

**Not live-verified:** derived from reading `UpdateZora` (`src/Z_04.asm`), not
from observing it in-game.

## Moblins throw boomerangs instead of arrows

**Code:** `GSKEANLS`

**Effect:** A Moblin's ranged attack becomes the boomerang object rather than
the arrow object.

**How it works:** `UpdateMoblin` (`src/Z_04.asm:1955`) passes the shot's object
type to `_TryShooting` in Y:

```
    LDY #$5B                    ; Arrow object type
    JMP :+
```

This patches the immediate at bank 4 CPU `$87C8` (originally `$5B`) to `$5C`.
Raw form: `$87C8:5C:5B`. `$5C` is the boomerang object type thrown by
`UpdateGoriya` (`src/Z_04.asm:542`); `$57`, the sword shot used by
`UpdateLynel` (`src/Z_04.asm:1960`), is the other documented value for this
field. No other PRG bank holds `$5B` at that `$8000`-window offset.

**Caveat — expect it to behave oddly.** A boomerang thrown this way is
initialized by `_ShootIfWanted`, not by `UpdateGoriya`, so it gets whatever
`ObjMovingLimit` that path supplies rather than the `$51` Goriya boomerangs
are given. Its range and return behaviour are therefore not the same as a
Goriya's, and this is part of the finding rather than a defect in the code.

**Not live-verified:** derived from reading `UpdateMoblin`, `UpdateGoriya` and
`UpdateLynel` (`src/Z_04.asm`), not from observing it in-game.

## Ranged monsters get trigger-happy

**Code:** `AENAANEN`

**Effect:** Red Moblins, red Lynels and red Octoroks shoot at nearly every
opportunity instead of on roughly a 1-in-32 roll.

**How it works:** `_TryShooting` (`src/Z_04.asm:1984`) rolls against a
threshold before allowing a shot:

```
    ; and a random value < $F8, then return.
    LDA Random, X
    CMP #$F8
    BCC @Exit
```

This patches the compare operand at bank 4 CPU `$87F0` (originally `$F8`) to
`$08`. Raw form: `$87F0:08:F8`. Almost every random value now clears the test
instead of only the top eight. No other PRG bank holds `$F8` at that
`$8000`-window offset.

**Caveat — shared by three monster routines.** `_TryShooting` is entered from
`UpdateMoblin`, `UpdateLynel` and `UpdateOctorock`, so this is a global change
to ranged monsters, not a per-species one.

**Caveat — blue variants are unaffected.** `_TryShooting`
(`src/Z_04.asm:1971`) branches straight to `@TryShootingNow` for types `$03`
(blue Moblin), `$01` (blue Lynel), `$09` (blue slow Octorok) and `$0A` (blue
fast Octorok), skipping the random test entirely. Those monsters already shoot
at every opportunity and see no change.

**Not live-verified:** derived from reading `_TryShooting` (`src/Z_04.asm`),
not from observing it in-game.

## Shooting monsters fire the instant they decide to

**Code:** `APEEUAAL`

**Effect:** Removes the wind-up between a monster deciding to shoot and the
shot appearing.

**How it works:** `_TryShooting` (`src/Z_04.asm:2026`) arms a countdown:

```
    ; So, if "wants to shoot" flag is set, then set shoot timer to $30.
    ; Else go set a non-zero speed and return.
    BPL @SetShootTimer
    LDA ObjWantsToShoot, X
    BEQ @SetSpeed
    LDY #$30
```

The shot itself is released when the timer counts down to exactly `$10`
(`CPY #$10` at bank 4 CPU `$8813`). This patches the immediate at bank 4 CPU
`$880B` (originally `$30`) to `$10`. Raw form: `$880B:10:30`. Starting at `$10`
means the release test matches on the very first tick. No other PRG bank holds
`$30` at that `$8000`-window offset.

**Caveat — do not lower it further.** The release test is an equality against
`$10`, so any starting value below `$10` counts straight past it and the
monster never shoots at all.

**Caveat — same three callers** as `AENAANEN` above: `UpdateMoblin`,
`UpdateLynel` and `UpdateOctorock`.

**Not live-verified:** derived from reading `_TryShooting` (`src/Z_04.asm`),
not from observing it in-game.

## Stalfos shoot constantly (second quest)

**Code:** `AEOPYUEN`

**Effect:** Second-quest Stalfos fire on nearly every opportunity instead of on
roughly a 1-in-32 roll.

**How it works:** `UpdateStalfos` (`src/Z_04.asm:4686`), inside the block
guarded by `QuestNumbers`:

```
    ; If shoot timer = 0 and Random < $F8, then return.
    LDA ObjShootTimer, X
    BNE @PrepareToShoot
    LDA Random, X
    CMP #$F8
    BCC @Exit
```

This patches the compare operand at bank 4 CPU `$9397` (originally `$F8`) to
`$08`. Raw form: `$9397:08:F8`. No other PRG bank holds `$F8` at that
`$8000`-window offset.

**Caveat — does nothing in the first quest.** The whole shooting block sits
behind a `QuestNumbers` test (`src/Z_04.asm:4680`) that exits immediately on
quest 1, where Stalfos do not shoot at all.

**Caveat — this is a different byte from `AENAANEN`.** `UpdateStalfos` has its
own copy of the random gate; patching one does not affect the other.

**Not live-verified:** derived from reading `UpdateStalfos` (`src/Z_04.asm`),
not from observing it in-game.

## Blue Wizzrobes fire eight times as often

**Code:** `LAVPENYP`

**Effect:** Blue Wizzrobes get a shooting opportunity every 4 frames instead of
every `$20`.

**How it works:** `BlueWizzrobe_TryShooting` (`src/Z_04.asm:7398`) gates on the
frame counter:

```
    ; Once every $20 frames, and when not fading, we'll try to shoot.
    ; Otherwise, return.
    LDA ObjRemDistance, X
    BNE L11F7E_Exit
    LDA FrameCounter
    AND #$1F
    BNE L11F7E_Exit
```

This patches the mask at bank 4 CPU `$9F60` (originally `$1F`) to `$03`. Raw
form: `$9F60:03:1F`. The value must stay a low-bits mask (`$01`/`$03`/`$07`/…)
for the "once every N frames" reading to hold. No other PRG bank holds `$1F`
at that `$8000`-window offset.

**Caveat — the alignment tests still apply.** After this gate the routine still
requires Link to share a square row or column with the Wizzrobe, and the
Wizzrobe must not be fading in or out (`ObjRemDistance`). So it is eight times
as many *attempts*, not eight times as many shots.

**Not live-verified:** derived from reading `BlueWizzrobe_TryShooting`
(`src/Z_04.asm`), not from observing it in-game.

## Monster arrows move very slowly

**Code:** `AZKAEAEA`

**Effect:** Arrows fired at Link travel at half a pixel a frame instead of two,
slow enough to walk around.

**How it works:** `UpdateMonsterArrow` (`src/Z_04.asm:2096`):

```
UpdateMonsterArrow:
    ; Set q-speed $80 (2 pixels a frame).
    LDA #$80
    STA ObjQSpeedFrac, X
```

This patches the immediate at bank 4 CPU `$8840` (originally `$80`) to `$20`.
Raw form: `$8840:20:80`. No other PRG bank holds `$80` at that `$8000`-window
offset.

**Caveat — rewritten every frame.** The store is at the top of the arrow's
update routine, so this is the arrow's speed for its whole flight, not just its
launch speed, and nothing else can raise it back.

**Not live-verified:** derived from reading `UpdateMonsterArrow`
(`src/Z_04.asm`), not from observing it in-game.

## Ropes charge from much further out of line

**Code:** `AGXPLUAA`

**Effect:** Ropes will break into their charge even when Link is well off their
horizontal line, instead of needing to be within 8 pixels of it.

**How it works:** `UpdateRope` (`src/Z_04.asm:4598`) measures the horizontal
gap first:

```
    LDA ObjX
    SEC
    SBC ObjX, X
    JSR Abs
    CMP #$08
    BCS @CheckVertical
```

A distance below `$08` falls through into the charge; `$08` or more goes on to
compare the vertical distance instead. This patches the compare operand at
bank 4 CPU `$9323` (originally `$08`) to `$40`. Raw form: `$9323:40:08`. No
other PRG bank holds `$08` at that `$8000`-window offset.

**Caveat — only the horizontal test is widened.** The vertical twin at bank 4
CPU `$9368` (`src/Z_04.asm:4656`) is untouched, so ropes get a wide *vertical*
charge lane while keeping the narrow horizontal one — the effect is
deliberately asymmetric.

**Not live-verified:** derived from reading `UpdateRope` (`src/Z_04.asm`), not
from observing it in-game.

## Ropes charge much faster

**Code:** `EYUPLLAT`

**Effect:** A charging Rope moves at q-speed `$F0` (3.75 pixels a frame)
instead of `$60` (1.5).

**How it works:** `UpdateRope` (`src/Z_04.asm:4619`):

```
@Rush:
    ; Make the rope rush (qspeed $60).
    LDA #$60
    STA ObjQSpeedFrac, X
```

This patches the immediate at bank 4 CPU `$9333` (originally `$60`) to `$F0`.
Raw form: `$9333:F0:60`. No other PRG bank holds `$60` at that `$8000`-window
offset.

**Caveat — this also breaks the "am I rushing?" test, on purpose.**
`UpdateRope` (`src/Z_04.asm:4567`) detects a charge by comparing the stored
q-speed against `$60`:

```
    ; If not rushing (qspeed <> $60) and timer = 0, then
    ; set timer to a random value up to $3F, and turn to face
    ; an unblocked direction.
    LDA ObjQSpeedFrac, X
    CMP #$60
    BEQ @CheckSpeed
```

Only the store is patched, so a charging rope now holds `$F0` and never matches
that test. It therefore keeps re-rolling its wander timer while charging. That
side effect is part of the finding, not an accident: expect charging ropes to
behave more erratically than a pure speed change would suggest.

**Not live-verified:** derived from reading `UpdateRope` (`src/Z_04.asm`), not
from observing it in-game.

## Ropes are as tough in the first quest as in the second

**Code:** `AKKPLZAP`

**Effect:** Ropes start with `$40` HP in the first quest instead of `$10`.

**How it works:** `InitRope` (`src/Z_04.asm:4600`):

```
InitRope:
    ; Rope has $10 HP in quest 1, $40 HP in quest 2.
    LDA #$10
    STA ObjHP, X
    LDY CurSaveSlot
    LDA QuestNumbers, Y
    BEQ :+
    LDA #$40
    STA ObjHP, X
```

This patches the first immediate at bank 4 CPU `$92C3` (originally `$10`) to
`$40`. Raw form: `$92C3:40:10`. No other PRG bank holds `$10` at that
`$8000`-window offset.

**Caveat — no effect in the second quest.** The `$40` store at bank 4 CPU
`$92CF` overwrites the patched value whenever `QuestNumbers` says quest 2, so
second-quest ropes are unchanged.

**Not live-verified:** derived from reading `InitRope` (`src/Z_04.asm`), not
from observing it in-game.

## Darknuts can be hurt by every weapon

**Code:** `AAXPOLVY`

**Effect:** Darknuts lose their weapon immunities entirely — boomerang, arrow,
fire, everything damages them, and from any direction the collision code
allows.

**How it works:** `InitDarknut` (`src/Z_04.asm:6450`):

```
InitDarknut:
    LDA #$F6                    ; Invincible to everything but sword and bomb.
    STA ObjInvincibilityMask, X
```

In `ObjInvincibilityMask` a **set** bit means immune to that weapon and a
**clear** bit means vulnerable. Reading the documented masks in this bank back
confirms the convention and the bit assignments: `$FE` = "invincible to
everything but sword" (`InitPatra`, `src/Z_04.asm:9526`) clears bit 0, so bit 0
is the sword; `$FA` = "everything but sword and arrow" (`InitGanon`,
`src/Z_04.asm:9572`) clears bits 0 and 2, so bit 2 is the arrow; `$F6` clears
bits 0 and 3, so bit 3 is the bomb. `$00` therefore means no immunities at all.

This patches the immediate at bank 4 CPU `$9B21` (originally `$F6`) to `$00`.
Raw form: `$9B21:00:F6`. No other PRG bank holds `$F6` at that `$8000`-window
offset.

**Caveat — the front-shield behaviour is separate.** A Darknut's refusal to
take sword hits from the front is handled in its collision code, not by this
mask, so it is unaffected.

**Not live-verified:** derived from reading `InitDarknut`, `InitPatra` and
`InitGanon` (`src/Z_04.asm`), not from observing it in-game.

## Blue Darknuts move much faster

**Code:** `ATXONUAZ`

**Effect:** Blue Darknuts move at q-speed `$60` (1.5 pixels a frame) instead of
`$28` (0.625) — over twice their normal speed.

**How it works:** `InitDarknut` (`src/Z_04.asm:6453`) picks a speed by type:

```
    ; If the darknut is red, then move at q-speed $20 (0.5 pixels a frame).
    LDA #$20
    LDY ObjType, X
    CPY #$0B
    BEQ :+

    ; Else move a blue darknut at q-speed $28 (0.625 pixels a frame).
    LDA #$28
:
    STA ObjQSpeedFrac, X
```

This patches the second immediate at bank 4 CPU `$9B2F` (originally `$28`) to
`$60`. Raw form: `$9B2F:60:28`. No other PRG bank holds `$28` at that
`$8000`-window offset.

**Caveat — red Darknuts are unaffected.** Type `$0B` takes the `$20` at bank 4
CPU `$9B26` and branches past the patched byte.

**Not live-verified:** derived from reading `InitDarknut` (`src/Z_04.asm`), not
from observing it in-game.

## Like Likes eat the Magical Shield instantly

**Code:** `ZAUPOIAT`

**Effect:** A Like Like strips the Magical Shield after 2 frames of holding
Link instead of `$60`, so there is effectively no window to escape.

**How it works:** `UpdateLikeLike` (`src/Z_04.asm:6886`):

```
    ; Once capture time >= $60 screen frames, remove the magic shield.
    LDA ObjCaptureTimer, X
    CMP #$60
    BCC @DrawAfterCapture
    LDA #$00
    STA InvMagicShield
```

This patches the compare operand at bank 4 CPU `$9D31` (originally `$60`) to
`$02`. Raw form: `$9D31:02:60`. No other PRG bank holds `$60` at that
`$8000`-window offset.

**Caveat — the timer pin is unchanged.** After stripping the shield the routine
writes `$C0` back into `ObjCaptureTimer` (`src/Z_04.asm:6894`) to keep the
branch taken, and `$C0` is still above the patched `$02`, so that part behaves
exactly as before.

**Not live-verified:** derived from reading `UpdateLikeLike` (`src/Z_04.asm`),
not from observing it in-game.

## Aquamentus fires volleys back to back

**Code:** `AENPTYAY`

**Effect:** The gap between Aquamentus's three-fireball volleys becomes purely
random instead of always at least `$70` frames, so volleys can follow each
other almost immediately.

**How it works:** `Aquamentus_Shoot` (`src/Z_04.asm:5692`):

```
    ; Set the timer to a random time, at least $70 frames.
    LDA Random, X
    ORA #$70
    STA ObjTimer, X
```

The `ORA` is what forces the minimum. This patches its operand at bank 4 CPU
`$97F6` (originally `$70`) to `$00`. Raw form: `$97F6:00:70`. With `$00` the
`ORA` becomes a no-op and the interval is whatever the random byte holds. No
other PRG bank holds `$70` at that `$8000`-window offset.

**Caveat — expect the fireball spread to look wrong.** A very short interval
leaves more than three `$55` fireballs alive at once, all competing for monster
object slots, so `@SpreadOutFireballs` will be assigning vertical offsets to a
set of fireballs it was never designed to handle.

**Not live-verified:** derived from reading `Aquamentus_Shoot`
(`src/Z_04.asm`), not from observing it in-game.

## Gohma glides instead of inching

**Code:** `NYUZTLEE`

**Effect:** Gohma moves nearly a pixel every frame instead of one pixel every
other frame.

**How it works:** `UpdateGohma` (`src/Z_04.asm:8219`) advances a fractional
accumulator and moves one pixel each time it overflows:

```
@Move:
    ; Add $80 to the movement accumulator.
    LDA Gohma_ObjMoveAccum, X
    CLC
    ADC #$80
    STA Gohma_ObjMoveAccum, X

    ; If movement accumulator didn't overflow, then go animate the eye.
    BCC @AnimateEye
```

`$80` overflows every second frame. This patches the operand at bank 4 CPU
`$A336` (originally `$80`) to `$FF`. Raw form: `$A336:FF:80`. No other PRG bank
holds `$80` at that `$8000`-window offset.

**Not live-verified:** derived from reading `UpdateGohma` (`src/Z_04.asm`), not
from observing it in-game.

## Gohma changes direction every few pixels

**Code:** `GAVZYLAZ`

**Effect:** Gohma reverses after travelling 4 pixels instead of `$20`, turning
its slow patrol into a twitchy shuffle.

**How it works:** `UpdateGohma` (`src/Z_04.asm:8262`):

```
    ; If Gohma has not traveled $20 pixels, then go animate the eye.
    LDA Gohma_ObjDistTraveled, X
    CMP #$20
    BNE @AnimateEye
```

Note the test is a `BNE`, an exact-equality check, so the replacement must be a
distance the counter actually lands on. This patches the compare operand at
bank 4 CPU `$A367` (originally `$20`) to `$04`. Raw form: `$A367:04:20`. The
counter is incremented by one per pixel moved, so `$04` is reached normally. No
other PRG bank holds `$20` at that `$8000`-window offset.

**Caveat — it also drives the sprint counter.** Reaching this distance resets
`Gohma_ObjDistTraveled`, flips the facing direction *and* increments the number
of sprints, so Gohma will run through its sprint count far faster than usual.

**Not live-verified:** derived from reading `UpdateGohma` (`src/Z_04.asm`), not
from observing it in-game.

## Gohma spits fireballs four times as fast

**Code:** `AOUZTLPG`

**Effect:** Gohma's fireball interval drops from `$41` frames to `$10`.

**How it works:** `UpdateGohma` (`src/Z_04.asm:8330`):

```
    ; If it became 0, then set it to $41, and shoot fireball $56.
    BNE @AnimateAndCheckCollisions
    LDA #$41
    STA Gohma_ObjShootTimer, X
    LDA #$56
    JSR ShootFireball
```

This patches the immediate at bank 4 CPU `$A3B6` (originally `$41`) to `$10`.
Raw form: `$A3B6:10:41`. No other PRG bank holds `$41` at that `$8000`-window
offset.

**Not live-verified:** derived from reading `UpdateGohma` (`src/Z_04.asm`), not
from observing it in-game.

## Ganon can be hurt by every weapon

**Code:** `AANZEOXY`

**Effect:** Clears Ganon's invincibility mask, so the boomerang, bombs, fire
and the rest register hits instead of only the sword and arrows.

**How it works:** `InitGanon` (`src/Z_04.asm:9572`):

```
InitGanon:
    LDA #$FA                    ; Invincible to everything but sword and arrow.
    STA ObjInvincibilityMask, X
```

A set bit in `ObjInvincibilityMask` means immune to that weapon; `$FA` clears
bit 0 (sword) and bit 2 (arrow). `$00` clears them all. This patches the
immediate at bank 4 CPU `$A970` (originally `$FA`) to `$00`. Raw form:
`$A970:00:FA`. No other PRG bank holds `$FA` at that `$8000`-window offset —
worth stating explicitly here, because bank 5 has `TileObjectTypes` at the same
`$A970` and an existing published code patches it. Those are two different
banks at one window offset, and the compare byte keeps them apart.

**Caveat — the Silver Arrow requirement is separate.** Ganon's own damage
handling still demands the Silver Arrow for the finishing blow; this mask only
governs which weapons register a hit at all.

**Not live-verified:** derived from reading `InitGanon` (`src/Z_04.asm`), not
from observing it in-game.

## Patra's children can be hurt by every weapon

**Code:** `AAVZSOVY`

**Effect:** The orbiting Patra children lose their sword-only immunity, so the
boomerang, arrows and everything else can strip them away.

**How it works:** `InitPatra`'s child-init loop (`src/Z_04.asm:9564`):

```
    LDA #$FE                    ; Patra children are also only weak to the sword.
    STA ObjInvincibilityMask, Y
```

`$FE` clears only bit 0 (the sword). This patches the immediate at bank 4 CPU
`$A965` (originally `$FE`) to `$00`. Raw form: `$A965:00:FE`. No other PRG bank
holds `$FE` at that `$8000`-window offset.

**Caveat — this is the children's byte, not Patra's own.** `InitPatra` writes
its own identical `LDA #$FE` for the parent at bank 4 CPU `$A92F`
(`src/Z_04.asm:9527`), which this code leaves alone. Patra herself stays
sword-only; patch `$A92F` separately if you want both.

**Not live-verified:** derived from reading `InitPatra` (`src/Z_04.asm`), not
from observing it in-game.

## Lamnola counts as cleared after one segment

**Code:** `PAXXOOAA`

**Effect:** The Lamnola room registers as fully cleared once a single segment
dies.

**How it works:** `InitLamnola` (`src/Z_04.asm:9522`) declares how many objects
the room contains:

```
    LDA #$08                    ; 8 instead of 10, because 8 is the max kill count to save.
    STA RoomObjCount
```

This patches the immediate at bank 4 CPU `$A929` (originally `$08`) to `$01`.
Raw form: `$A929:01:08`. No other PRG bank holds `$08` at that `$8000`-window
offset.

**Caveat — the remaining segments stay alive.** `RoomObjCount` is the room's
bookkeeping figure, not the number of segments spawned; the rest of the Lamnola
keeps moving and can still hurt Link even though the room is already counted as
cleared.

**Not live-verified:** derived from reading `InitLamnola` (`src/Z_04.asm`), not
from observing it in-game.

## Fairy pond hearts orbit in a tighter ring

**Code:** `GAXASTTA`

**Effect:** Cosmetic. The hearts circling a fairy pond spin in a noticeably
smaller ring.

**How it works:** `PondFairy_MoveHearts` (`src/Z_04.asm:3537`):

```
    ; Rotate the heart's location by the change in angle.
    ; Use 6 for the number of bits of sine/cosine to use
    ; for a large ring.
    LDA #$06
    TAY
    JSR RotateObjectLocation
```

The value is the number of sine/cosine bits `RotateObjectLocation` uses, which
sets the radius. This patches the immediate at bank 4 CPU `$8E25` (originally
`$06`) to `$04`. Raw form: `$8E25:04:06`. No other PRG bank holds `$06` at that
`$8000`-window offset.

**Caveat — cosmetic only.** The fairy pond's refill behaviour does not depend
on where the hearts are drawn.

**Not live-verified:** derived from reading `PondFairy_MoveHearts`
(`src/Z_04.asm`), not from observing it in-game.

## Fairy pond hearts whirl much faster

**Code:** `ETXAETAT`

**Effect:** Cosmetic. The hearts orbit the fairy pond at more than twice their
usual rate.

**How it works:** `PondFairy_MoveHearts` (`src/Z_04.asm:3530`) advances each
heart's angle by a fixed-point step:

```
@MoveHeart:
    ; Decrease the angle by $00.60.
    LDA #$00
    STA $0B
    LDA #$60
    JSR DecreaseObjectAngle
```

`$0B` holds the whole part and A the fractional part. This patches the
fractional immediate at bank 4 CPU `$8E20` (originally `$60`) to `$E0`. Raw
form: `$8E20:E0:60`. No other PRG bank holds `$60` at that `$8000`-window
offset.

**Caveat — combines with `GAXASTTA`.** The two bytes are independent: one sets
the radius, the other the angular step, so both codes can be used together for
a tight, fast whirl.

**Not live-verified:** derived from reading `PondFairy_MoveHearts`
(`src/Z_04.asm`), not from observing it in-game.

## Sword-beam burst covers a much wider area

**Code:** `ATSYTGAZ`

**Effect:** When a sword beam hits and bursts into four corner sprites, those
corners keep spreading to `$60` pixels from the centre instead of being culled
at `$20`.

**How it works:** `SpreadShot` (`src/Z_07.asm:3687`) draws each of the four
corners and drops any that has travelled too far:

```
@CheckDistance:
    ; If distance >= $20, skip this corner.
    CMP #$20
    BCS @NextCorner
```

This patches the compare operand at bank 7 CPU `$F456` (originally `$20`) to
`$60`. Raw form: `$F456:60:20`. Bank 7 is fixed at `$C000`-`$FFFF` and is the
only bank that can be mapped there, so no other bank can match this compare
byte.

**Caveat — vertical clipping still applies.** In dungeons the corners are also
clipped against the play area by the `CMP #$3E` and `CMP #$E8` tests at bank 7
CPU `$F465`/`$F469` (and again at `$F499`), which this code does not touch. The
burst therefore widens horizontally more than it does vertically.

**Not live-verified:** derived from reading `SpreadShot` (`src/Z_07.asm`), not
from observing it in-game.

## Sword-beam burst starts wider apart

**Code:** `EYONPKVY`

**Effect:** The four corners of a bursting sword beam start `$10` pixels out
from the centre instead of 2.

**How it works:** `SetShotSpreadingState` (`src/Z_07.asm:3609`):

```
    ; Set [98][X] to base negative offset -2. This is how far the left
    ; corners will be shown relative to the center point at object X, Y.
    ; The right corners will be shown 2 pixels in the opposite direction
    ; of the center point.
    INC ObjState, X
    LDA #$FE
    STA ObjDir, X
```

`$FE` is -2 as a signed byte. This patches the immediate at bank 7 CPU `$F419`
(originally `$FE`) to `$F0`, i.e. -16. Raw form: `$F419:F0:FE`. Bank 7 is
fixed, so the address is unambiguous.

**Caveat — `ObjDir` is a reused field here.** The disassembly marks this
`MULTI: ObjDir -> ObjSwordShotNegativeOffset` (`src/Z_07.asm:3624`): for the
shot object this slot holds the spread offset rather than a direction. That
reinterpretation only applies to the shot object, whose only consumer of the
field is `SpreadShot`, so other users of `ObjDir` are unaffected.

**Caveat — combines with `ATSYTGAZ`.** This sets the starting separation; the
other sets how far the corners may travel before being culled.

**Not live-verified:** derived from reading `SetShotSpreadingState` and
`SpreadShot` (`src/Z_07.asm`), not from observing it in-game.

## Sword and rod stay extended much longer

**Code:** `AGNNZNAA`

**Effect:** The sword's fully-extended pose is held for `$40` frames instead of
8, so a swing lingers on screen (and stays able to hit) for about a second.

**How it works:** `UpdateSwordOrRod` (`src/Z_07.asm:4402`):

```
    ; State 2 will last 8 frames. The higher ones last 1.
    LDA ObjState, X
    AND #$0F
    TAY
    LDA #$08
    DEY
    BEQ :+
    LDA #$01
:
    ; Set both the player's animation counter and the sword's
    ; animation counter/timer to this value.
    STA ObjAnimCounter
    STA ObjAnimCounter, X
```

This patches the immediate at bank 7 CPU `$F77A` (originally `$08`) to `$40`.
Raw form: `$F77A:40:08`. Bank 7 is fixed, so the address is unambiguous.

**Caveat — Link is held in the swing pose too.** The value is stored into both
`ObjAnimCounter` (Link's) and `ObjAnimCounter, X` (the weapon's), so Link
cannot act for the whole extended duration.

**Caveat — this is the shared sword/rod routine.** `UpdateSwordOrRod` drives
the Magical Rod as well, so the rod's extension is lengthened identically.

**Not live-verified:** derived from reading `UpdateSwordOrRod`
(`src/Z_07.asm`), not from observing it in-game.

## Bombs blow open bombable walls from much further away

**Code:** `ATNNSOAP`

**Effect:** A bomb opens a bombable wall from up to `$60` pixels away
horizontally instead of `$18`.

**How it works:** `UpdateBomb` (`src/Z_07.asm:4864`) walks the room's four wall
hotspots and rejects any that the bomb is not close enough to:

```
    ; If the bomb's X is not within $18 pixels of the hotspot, then
    ; go check the next hotspot.
    LDA BombableWallHotspotsX, Y
    SEC
    SBC ObjX, X
    JSR Abs
    CMP #$18
    BCS @LoopHotspot
```

This patches the compare operand at bank 7 CPU `$F97D` (originally `$18`) to
`$60`. Raw form: `$F97D:60:18`. Bank 7 is fixed, so the address is unambiguous.

**Caveat — only the horizontal test is loosened.** The vertical twin at bank 7
CPU `$F98A` (`src/Z_07.asm:4880`) still requires `$18`, so the bomb must still
be roughly level with the hotspot.

**Caveat — dungeon rooms only.** `UpdateBomb` (`src/Z_07.asm:4850`) skips this
whole block in the overworld and in cellars (game mode `$09`).

**Not live-verified:** derived from reading `UpdateBomb` (`src/Z_07.asm`), not
from observing it in-game.

## Enemies can spawn right on top of Link

**Code:** `ZAOEKZZZ`

**Effect:** The horizontal keep-away zone that stops monsters from appearing on
Link shrinks from `$22` pixels to `$02`, so spawns can land almost on him.

**How it works:** `IsDistanceSafeToSpawn` (`src/Z_05.asm:2014`) treats a spot as
unsafe only when Link is close on **both** axes:

```
IsDistanceSafeToSpawn:
    ; Get the absolute X distance to Link.
    LDA ObjX
    SEC
    SBC ObjX, X
    JSR Abs
    CMP #$22
    BCS :+                      ; If distance > $22, return walkable.
```

This patches the compare operand at bank 5 CPU `$8A1C` (originally `$22`) to
`$02`. Raw form: `$8A1C:02:22`. Because the two tests are an AND, loosening the
horizontal one alone is enough to make nearly every spot count as safe. No other
PRG bank holds `$22` at that `$8000`-window offset.

**Caveat — the vertical twin is untouched.** The matching `CMP #$22` at bank 5
CPU `$8A28` (`src/Z_05.asm:2029`) still uses the full distance; it simply stops
mattering once the horizontal test passes.

**Caveat — both spawn paths are affected.** `IsSafeToSpawn` falls straight
through into this routine, so this covers room-entry spawns and in-play spawns
alike.

**Not live-verified:** derived from reading `IsDistanceSafeToSpawn`
(`src/Z_05.asm`), not from observing it in-game.

## Boss rooms spawn a full complement of monsters

**Code:** `ZUXAUAZT`

**Effect:** Rooms whose object list is a boss or other one-off are no longer
forced to a single monster; they use the level's normal foe count instead.

**How it works:** `InitMode_EnterRoom` (`src/Z_05.asm:1722`) special-cases a
range of object list IDs:

```
    ; But make the count 1, if  the object list ID >= $32 and < $62.
    ; This includes bosses and other non-recurring objects.
    LDY $02
    CPY #$62
    BCS :+
    CPY #$32
    BCC :+
    LDA #$01
:
    STA $03                     ; Put the count in [03].
```

This patches the first compare operand at bank 5 CPU `$88A3` (originally `$62`)
to `$32`. Raw form: `$88A3:32:62`. That collapses the range `[$32, $62)` to
empty — every value now takes one of the two branches around `LDA #$01` — so
the count stays whatever `LevelInfo_FoeCounts` supplied. No other PRG bank
holds `$62` at that `$8000`-window offset.

**Caveat — expect glitches.** This is very likely to put several bosses in one
room, all competing for object slots, and the room-clear bookkeeping was never
written with that in mind. Treat the results as a curiosity rather than a
playable change.

**Not live-verified:** derived from reading `InitMode_EnterRoom`
(`src/Z_05.asm`), not from observing it in-game.

## Monsters that keep the default speed start out faster

**Code:** `AINANAAZ`

**Effect:** Raises the default object speed written into every slot on room
entry from q-speed `$20` (0.5 pixels a frame) to `$50` (1.25).

**How it works:** `InitMode_EnterRoom` (`src/Z_05.asm:1691`) pre-initializes
each object slot before the per-type init routines run:

```
    INC ObjMetastate, X         ; By default, objects start in metastate 1 (first cloud state).
    LDA #$20                    ; Set the default speed.
    STA ObjQSpeedFrac, X
    DEX
    BNE :-
```

This patches the immediate at bank 5 CPU `$8877` (originally `$20`) to `$50`.
Raw form: `$8877:50:20`. No other PRG bank holds `$20` at that `$8000`-window
offset.

**Caveat — most monsters overwrite this.** Any type whose init routine writes
`ObjQSpeedFrac` itself — Darknuts (`InitDarknut`), Goriya boomerangs, Zols,
Leevers and so on — discards the default immediately. The effect is therefore
"monsters whose init leaves the default speed alone move faster", and which
types those are has not been enumerated here. It is a genuinely selective code,
not a global speed-up.

**Not live-verified:** derived from reading `InitMode_EnterRoom`
(`src/Z_05.asm`), not from observing it in-game.

## Link steps out of caves lower down the screen

**Code:** `SENEYNIK`

**Effect:** Link emerges from a cave or dungeon entrance `$40` pixels further
down the screen than usual.

**How it works:** `InitMode_EnterRoom` (`src/Z_05.asm:1587`) computes Link's
exit position:

```
    ; Add the first Y where Link can come out of underground.
    ; $4D is $50 (the second square row) - 3 (Link's offset above the row).
    ADC #$4D
    STA ObjY
```

This patches the immediate at bank 5 CPU `$87FF` (originally `$4D`) to `$8D`.
Raw form: `$87FF:8D:4D`. No other PRG bank holds `$4D` at that `$8000`-window
offset.

**Caveat — the walking-out animation uses the same base.** The `ADC #$10` at
bank 5 CPU `$880D` sets the Y that Link walks to after stepping out, measured
from this value, so a large change can leave Link walking out through solid
tiles. `$8D` is still `$50` above the bottom of the play area, but the tiles he
crosses depend on the screen.

**Not live-verified:** derived from reading `InitMode_EnterRoom`
(`src/Z_05.asm`), not from observing it in-game.

## Rock-wall shortcuts always open

**Code:** `ESOXSLKK`

**Effect:** On a screen where the overworld shortcut has been revealed, a
rock-wall tile is turned into the stairs square unconditionally, instead of
only when the room's tile object is a rock.

**How it works:** `CheckShortcut` (`src/Z_05.asm:6094`) reads the tile where the
shortcut belongs and decides what to do with it:

```
    LDA ($00), Y                ; Get the tile that's where the shortcut should be.
    CMP #$C4
    BEQ @WriteStairs            ; If it's a tree, go prepare a stairs square.
    CMP #$BC
    BEQ @Exit                   ; If it's a gravestone, then return.
    CMP #$D8
    BNE @WriteStairs            ; If it's not a rock wall, then go prepare a stairs square.
    LDA RoomTileObjType
    CMP #$62
    BEQ @WriteStairs            ; If the room's tile object is a rock, go prepare a stairs square.
```

This patches the first compare operand at bank 5 CPU `$AB9D` (originally `$C4`,
the tree) to `$D8`, the rock wall. Raw form: `$AB9D:D8:C4`. A rock-wall tile
now matches the very first test and jumps straight to `@WriteStairs`, skipping
the `RoomTileObjType` check below. No other PRG bank holds `$C4` at that
`$8000`-window offset.

**Caveat — trees still work.** Losing the `$C4` test does not cost trees their
stairs: a tree tile matches none of `$D8`/`$BC`/`$D8`, so it reaches
`BNE @WriteStairs` and gets the stairs anyway. The code *adds* a case rather
than moving one, which is the opposite of what the shorthand "hides under a
different feature" would suggest.

**Caveat — it makes a dead branch deader.** The fall-through after the
`RoomTileObjType` check is flagged in the disassembly as unverified and
apparently unused; with this patch a rock wall can never reach it at all.

**Not live-verified:** derived from reading `CheckShortcut` (`src/Z_05.asm`),
not from observing it in-game.

## The end-of-dungeon pause is much longer

**Code:** `NNXZSAEE`

**Effect:** Pacing. The delay before the next submode of the level-completion
sequence goes from `$7F` frames to `$FE` — about four seconds instead of two.

**How it works:** `UpdateMode12EndLevel_Sub3` (`src/Z_05.asm:5608`):

```
    LDA #$80                    ; Set up a delay of $7F ($80-1) frames for next submode.
    STA ObjTimer
    INC GameSubmode
```

This patches the immediate at bank 5 CPU `$A8A5` (originally `$80`) to `$FF`.
Raw form: `$A8A5:FF:80`. No other PRG bank holds `$80` at that `$8000`-window
offset.

**Caveat — cosmetic.** Nothing but the length of the pause changes; the
submode advances the same way afterwards.

**Not live-verified:** derived from reading `UpdateMode12EndLevel_Sub3`
(`src/Z_05.asm`), not from observing it in-game.

## Pushable blocks can be shoved from way off to the side

**Code:** `AGUALZPP`

**Effect:** Link no longer has to line up with a pushable dungeon block to
move it. Standing well off to one side and walking into the block still
counts as pushing, so blocks give from positions that normally do nothing.

**How it works:** `UpdateBlock` (`src/Z_04.asm:686`) measures how far Link is
from alignment with the block on the perpendicular axis, and abandons the push
if he is too far off:

```
    ; If the distance >= $11, then go reset the push timer and return.
    CMP #$11
    BCS ResetPushTimer

    ; At this point, Link is aligned with the block.
    ;
    ; If the input direction is not the required direction based on
    ; Link's placement; then go reset the push timer and return.
    LDA ObjInputDir
    CMP BlockPushDirections, Y
    BNE ResetPushTimer
```

This patches the compare operand at bank 4 CPU `$8233` (originally `$11`) to
`$40`. Raw form: `$8233:40:11`. The alignment window widens from `$11` pixels
to `$40`, so `ObjPushTimer` keeps accumulating from much further off-centre.
No other PRG bank holds `$11` at that `$8000`-window offset.

**Note on the value.** The candidate backlog suggested lowering this byte to
`$02` on the reading that it was a push *duration*. It is not — it is an
alignment tolerance, and the branch is `BCS` (reset when the distance is
`>=` the operand), so lowering it would make blocks *harder* to push. `$40`
is used here instead because it produces the intended effect.

**Caveat — the direction test still applies.** Immediately after this
compare, `BlockPushDirections, Y` requires Link's input direction to match
the side he is on. Widening the alignment window does not let a block be
pushed from the wrong side; it only relaxes how centred Link must be.

**Not live-verified:** derived from reading `UpdateBlock` (`src/Z_04.asm`),
not from observing it in-game.

## A pushed block leaves a gravestone-grey square behind

**Code:** `TZKEYZGY`

**Effect:** When a pushable dungeon block finishes moving, the square it
came *from* is redrawn as tile `$26` instead of the usual floor tile.

**How it works:** `UpdateBlock` (`src/Z_04.asm:713`) writes the vacated
square once Link has pushed far enough:

```
    ; Link has pushed enough.
    ; Set the block's direction to Link's, set state 1,
    ; and change tiles at the source to a floor tile.
    STA ObjDir, X
    INC ObjState, X
    INC ReturnToBank4           ; Switch back to bank 4 when returning from the call below.
    LDA #$74                    ; Floor tile tile
    JSR ChangeTileObjTiles
```

This patches the immediate at bank 4 CPU `$824F` (originally `$74`) to
`$26`. Raw form: `$824F:26:74`. No other PRG bank holds `$74` at that
`$8000`-window offset.

**Caveat — the tile id decides walkability, not just looks.** The square the
block vacated becomes whatever `$26` is in the current room's tile set, so
this can change whether Link can stand there. It is not purely cosmetic.

**Not live-verified:** derived from reading `UpdateBlock` (`src/Z_04.asm`),
not from observing it in-game.

## A pushed block turns into floor where it lands

**Code:** `GNEAAZEL`

**Effect:** When a pushable dungeon block reaches its destination, the
destination square is drawn as the floor tile instead of the block tile —
so the block appears to vanish at the end of the push.

**How it works:** `UpdateBlock` (`src/Z_04.asm:751`) writes the destination
square when the push completes:

```
    ; The block has moved enough.
    ; Play the "secret revealed" tune.
    ; Change the tiles at the destination to the block tile.
    ; Set state 2, and increment BlockPushComplete.
    LDA #$04
    STA Tune1Request
    INC ReturnToBank4           ; Switch back to bank 4 when returning from the call below.
    LDA #$B0
    JSR ChangeTileObjTiles
    INC ObjState, X
    INC BlockPushComplete
```

This patches the immediate at bank 4 CPU `$8280` (originally `$B0`, the
block tile) to `$74`, the floor tile that the same routine uses for the
vacated square at `$824F`. Raw form: `$8280:74:B0`. No other PRG bank holds
`$B0` at that `$8000`-window offset.

**Caveat — the block's sprite is separate from the square.** This writes the
background square only. `BlockPushComplete` and the "secret revealed" tune
still fire, and the stairs the push reveals still appear, so the puzzle
still solves; the block just leaves walkable floor where it stopped.

**Not live-verified:** derived from reading `UpdateBlock` (`src/Z_04.asm`),
not from observing it in-game.

## Monster shots ricochet three times as long before dying

**Code:** `ATVEGLAZ`

**Effect:** Shots that bounce off walls (rather than being absorbed) keep
ricocheting around the room roughly three times longer before they expire.

**How it works:** `BounceShot` (`src/Z_04.asm:948`) accumulates a bounce
distance and destroys the shot when it reaches a limit:

```
    ; Add 2 to the bounce distance.
    ; The absolute value of one of the displacements is 2.
    LDA Shot_ObjBounceDist, X
    CLC
    ADC #$02
    STA Shot_ObjBounceDist, X

    ; Go destroy the shot, if the bounce counter has reached the limit.
    ; Otherwise, go draw.
    CMP #$20
    BCS DestroyMonsterShot
    BCC L_DrawShot
```

This patches the compare operand at bank 4 CPU `$836C` (originally `$20`) to
`$60`. Raw form: `$836C:60:20`. With the increment left at `$02`, the shot
survives `$30` bounce steps instead of `$10`. No other PRG bank holds `$20`
at that `$8000`-window offset.

**Caveat — pairs with the increment at `$8367`.** The other published option
for this routine raises the `ADC #$02` step instead, which *shortens* the
bounce because the `$20` limit is reached sooner. This code patches the
limit, not the step; do not combine the two expecting them to add up.

**Caveat — long-lived shots occupy object slots.** A shot that lives three
times longer keeps its monster slot that much longer, which can crowd out
new monsters or fireballs in a busy room.

**Not live-verified:** derived from reading `BounceShot` (`src/Z_04.asm`),
not from observing it in-game.

## Ricochets take much bigger steps and die much sooner

**Code:** `AAVAYLZE`

**Effect:** Bouncing monster shots burn through their bounce allowance four
times faster, so they disappear after roughly a quarter as many ricochets.

**How it works:** `BounceShot` (`src/Z_04.asm:943`) adds a fixed step to the
bounce counter on every bounce:

```
    ; Add 2 to the bounce distance.
    ; The absolute value of one of the displacements is 2.
    LDA Shot_ObjBounceDist, X
    CLC
    ADC #$02
    STA Shot_ObjBounceDist, X
```

This patches the immediate at bank 4 CPU `$8367` (originally `$02`) to
`$08`. Raw form: `$8367:08:02`. The `CMP #$20` limit two instructions later
is untouched, so the counter reaches it in 4 bounces instead of `$10`. No
other PRG bank holds `$02` at that `$8000`-window offset.

**Caveat — this is the *step*, not the limit.** Raising it shortens the
ricochet. The companion code at `$836C` raises the limit and lengthens it.
Which of the two bytes was patched is the whole difference between the two
codes, so they are documented separately rather than as one effect.

**Not live-verified:** derived from reading `BounceShot` (`src/Z_04.asm`),
not from observing it in-game.

## Keese almost always chase instead of wandering

**Code:** `AOUEAGEZ`

**Effect:** Keese (bats) pick the chasing flight state far more often than
normal, so they home in on Link instead of flitting around the room.

**How it works:** `Flyer_KeeseDecideState` (`src/Z_04.asm:1225`) rolls a
random byte to choose the next flying state:

```
    ; Go to the next state randomly:
    ; Random >= $A0: 2
    ; Random >= $20: 3
    ; Else:          4
    ;
    ; Set up 6 turns.
    LDY #$02
    LDA Random+1, X
    CMP #$A0
    BCS Flyer_SetStateAndTurns  ; If >= $A0, go to state 2.
    INY
    CMP #$20
    BCS Flyer_SetStateAndTurns  ; If >= $20, go to state 3.
    INY                         ; Else go to state 4.
```

This patches the first compare operand at bank 4 CPU `$84B8` (originally
`$A0`) to `$10`. Raw form: `$84B8:10:A0`. State 2 is now chosen whenever the
random byte is `>= $10` — about 94% of the time instead of about 38%. No
other PRG bank holds `$A0` at that `$8000`-window offset.

**Caveat — only the first of the two compares is patched.** The sibling
`CMP #$20` at `$84BE` is left alone; it becomes nearly unreachable, since
almost every roll now satisfies the first test. States 3 and 4 are
effectively retired rather than rebalanced.

**Caveat — "state 2" is a flying state, not literally "chase".** The
routine's own comment names the states by number only; state 2 is the state
`Flyer_SetStateAndTurns` is entered with on the high roll. The disassembly
documents the numbers, not a behavioural name, so "chases more" is inferred
from state 2 being the high-roll branch shared with the other flyers'
decide-state routines.

**Not live-verified:** derived from reading `Flyer_KeeseDecideState`
(`src/Z_04.asm`), not from observing it in-game.

## Zols crawl four times faster

**Code:** `AVVEIKAP`

**Effect:** Zols (the large gelatinous blobs that split in two) wander at
about 1.5 pixels a frame instead of 0.375 — roughly Link's own walking
speed.

**How it works:** `UpdateZolState0_Wander` (`src/Z_04.asm:1264`) is the whole
of the Zol's wander state, and it does nothing but pick a speed:

```
UpdateZolState0_Wander:
    LDA #$18                    ; QSpeed $18 (0.375 pixels a frame)
    JMP UpdateNormalZolOrGel
```

This patches the immediate at bank 4 CPU `$84ED` (originally `$18`) to
`$60`. Raw form: `$84ED:60:18`. `UpdateNormalZolOrGel` stores the value
straight into `ObjQSpeedFrac`, so `$60` is 1.5 pixels a frame. No other PRG
bank holds `$18` at that `$8000`-window offset.

**Caveat — Gels are unaffected.** `UpdateNormalZolOrGel` is shared, but the
Gel path supplies its own speed before jumping in; only the Zol's wander
state passes this constant.

**Not live-verified:** derived from reading `UpdateZolState0_Wander`
(`src/Z_04.asm`), not from observing it in-game.

## Zols split into Red Keese instead of Gels

**Code:** `GPOEZIGO`

**Effect:** When a Zol is struck and splits, the two children that appear
are Red Keese (bats) rather than the usual pair of Gels.

**How it works:** `CreateChildGel` (`src/Z_04.asm:1301`) chooses the object
type for each half:

```
CreateChildGel:
    LDA #$14                    ; Child Gel object type

    ; Use the shooting operation to create the gel object.
    STA $00
    JSR ShootLimited
```

This patches the immediate at bank 4 CPU `$851A` (originally `$14`, Child
Gel) to `$1C`. Raw form: `$851A:1C:14`. `$1C` is the Red Keese type — the
same value `UpdateVire` (`src/Z_04.asm:6940`) passes to the sibling `Shoot`
routine when a Vire splits, which is why it is a safe substitute: the engine
is already known to create this type through the shoot mechanism.
`$1C` maps to `UpdateKeese` in `UpdateObject_JumpTable` (`src/Z_07.asm:5321`).
No other PRG bank holds `$14` at that `$8000`-window offset.

**Caveat — the children are still set up as Gels.** The instructions right
after this one force the new object into state 0 (because shot objects
normally start in state `$10`) and the caller assigns each child a direction.
A Keese does not use those fields the way a Gel does, so expect the halves to
start facing or moving oddly for a frame or two. That glitchiness is part of
the finding, not something the code avoids.

**Not live-verified:** derived from reading `CreateChildGel` and `UpdateVire`
(`src/Z_04.asm`), not from observing it in-game.

## Zols and Gels turn toward Link at every opportunity

**Code:** `NNSAZIAX`

**Effect:** Zols and Gels re-aim at Link constantly instead of drifting, so
they track him around the room far more tightly.

**How it works:** `UpdateNormalZolOrGel` (`src/Z_04.asm:1483`) sets a turn
rate before asking the shared wanderer logic to aim at Link:

```
    ; If object timer >= 5, then return.
    LDA ObjTimer, X
    CMP #$05
    BCS @Exit
    LDA #$20                    ; Turn rate $20
    STA ObjTurnRate, X
    JSR Wanderer_TargetPlayer
```

This patches the immediate at bank 4 CPU `$85D2` (originally `$20`) to
`$FF`. Raw form: `$85D2:FF:20`. `$FF` is the same value `UpdateGhini`
(`src/Z_04.asm:3071`) passes with the comment "turn rate `$FF` to turn as
often as possible", which fixes the meaning of the high end of the range.
No other PRG bank holds `$20` at that `$8000`-window offset.

**Caveat — affects both Zols and Gels.** This routine is the common tail for
`UpdateZolState0_Wander` and the Gel update path, so a single byte changes
both monsters.

**Not live-verified:** derived from reading `UpdateNormalZolOrGel` and
`UpdateGhini` (`src/Z_04.asm`), not from observing it in-game.

## Four-statue rooms stop firing fireballs

**Code:** `LZUAGTGZ`

**Effect:** In dungeon rooms whose layout puts four fireball-spitting
statues in the corners, the statues go inert. Two-statue rooms are
unaffected.

**How it works:** `UpdateStatues` (`src/Z_04.asm:1593`) matches the current
room against a two-entry table to pick a fireball pattern:

```
    ; Else if the room layout has two or four statues that shoot fireballs,
    ; then go shoot fireballs with the corresponding pattern in Y register:
    ; - layout $23: pattern 1: 2 statues
    ; - layout $24: pattern 0: 4 statues
    JSR GetUniqueRoomId
    LDY #$01
:
    CMP StatueRoomLayouts, Y
    BEQ @Shoot
    DEY
    BPL :-
    RTS
```

with

```
StatueRoomLayouts:
    .BYTE $24, $23
```

This patches `StatueRoomLayouts` byte 0 at bank 4 CPU `$8634` (originally
`$24`) to `$23`. Raw form: `$8634:23:24`. Both entries now read `$23`, and
because the loop counts *down* from `Y = 1`, layout `$23` still matches byte
1 first and keeps pattern 1 (two statues). Layout `$24` now matches neither
entry, so the routine returns without shooting. No other PRG bank holds
`$24` at that `$8000`-window offset.

**Caveat — the effect is subtractive, not a reassignment.** The obvious
reading of "point the four-statue pattern at a different layout" does not
hold, because the search order makes byte 1 win any tie. What the patch
actually does is remove layout `$24` from the table. This is documented as
the real effect rather than the intended one, because a different room-layout
id would be a guess: the disassembly documents only `$23` and `$24`.

**Caveat — the two-fires case still works.** The `PersonFireballsEnabled`
branch at the top of `UpdateStatues` bypasses the table entirely and shoots
with pattern 2, so rooms where the two flames spit fireballs are unaffected.

**Not live-verified:** derived from reading `UpdateStatues`
(`src/Z_04.asm`), not from observing it in-game.

## One corner statue fires from the middle of the room

**Code:** `GYKAATGZ`

**Effect:** In four-statue rooms, one of the four fireball sources moves
from the room's left edge toward the centre, so fireballs appear to come
out of open floor.

**How it works:** `StatueXs` (`src/Z_04.asm:1586`) holds the X coordinates
the fireball "shooter" is placed at, grouped into sets per pattern:

```
; A list of coordinates divided into sets for each pattern.
;
StatueXs:
    .BYTE $24, $C8, $24, $C8, $64, $88, $48, $A8

; A list of coordinates divided into sets for each pattern.
;
StatueYs:
    .BYTE $C0, $BC, $64, $5C, $94, $8C, $82, $86
```

`StatuePatternToBasePositionIndex` (`$8638`, `.BYTE $00, $04, $06`) shows
that pattern 0 — the four-statue pattern — uses entries 0-3, so byte 0 is one
of the four corners. This patches `StatueXs` byte 0 at bank 4 CPU `$8640`
(originally `$24`) to `$74`. Raw form: `$8640:74:24`. No other PRG bank holds
`$24` at that `$8000`-window offset.

**Caveat — only the X moves.** The paired `StatueYs` byte 0 (`$8648`, `$C0`)
is untouched, so the fireball still originates at the bottom of the room,
just horizontally centred. The statue *graphic* is part of the room's tile
layout and does not move at all — only the point the fireball spawns from.

**Not live-verified:** derived from reading `UpdateStatues` and its
coordinate tables (`src/Z_04.asm`), not from observing it in-game.

## Statue fireballs take the low object slots away from monsters

**Code:** `PANAATTA`

**Effect:** Statue fireballs are allowed to use object slots normally
reserved for the room's monsters, so busy rooms can end up with fewer
monsters and more fireballs.

**How it works:** `UpdateStatues` (`src/Z_04.asm:1638`) rejects any free slot
below 6:

```
    TYA                         ; Save the fireball pattern.
    PHA
    JSR FindEmptyMonsterSlot
    CMP #$01
    PLA                         ; Restore the fireball pattern.
    BCS @Exit

    ; If we found a slot, but it < 6, return.
    CPY #$06
    BCC @Exit
```

This patches the compare operand at bank 4 CPU `$8670` (originally `$06`) to
`$01`. Raw form: `$8670:01:06`. Slots 1 and up are now acceptable, so a
fireball can be created whenever any slot above 0 is free rather than only
when a high slot is. No other PRG bank holds `$06` at that `$8000`-window
offset.

**Caveat — this test exists to protect the monsters.** The reserved low
slots are where room monsters live; letting fireballs occupy them means a
monster that would have respawned or spawned into slot 1-5 can find the room
full. Expect fewer monsters in statue rooms, not just more fireballs.

**Caveat — slot 0 is still excluded.** `BCC @Exit` on `CPY #$01` rejects
slot 0, which is Link's own slot, so the patch cannot displace the player.

**Not live-verified:** derived from reading `UpdateStatues`
(`src/Z_04.asm`), not from observing it in-game.

## Boulder storm on the mountain screens

**Code:** `AEEEVALE`

**Effect:** Overworld screens that rain boulders keep up to 8 boulders in
the air at once instead of 3, turning the mountain paths into a barrage.

**How it works:** `UpdateBoulderSet` (`src/Z_04.asm:2175`) is the invisible
"spawner" object that feeds boulders into the room, and it stops once the
live count hits the maximum:

```
UpdateBoulderSet:
    ; If the object timer has not expired, then return.
    LDA ObjTimer, X
    BNE @Exit

    ; If the maximum number (3) of boulders are active, then
    ; go set the timer to wait a random amount of time.
    LDA ActiveBoulders
    CMP #$03
    BEQ @RandomizeTimer
```

This patches the compare operand at bank 4 CPU `$888E` (originally `$03`) to
`$08`. Raw form: `$888E:08:03`. No other PRG bank holds `$03` at that
`$8000`-window offset.

**Caveat — the test is `BEQ`, not `BCS`.** The spawner only backs off on an
*exact* match with this byte. `ActiveBoulders` is incremented one at a time
by this same routine so it should never overshoot, but any path that skipped
a value would let the count run away past the limit.

**Caveat — boulders still need free object slots.** `FindEmptyMonsterSlot`
immediately below gates every spawn, so the practical ceiling is whatever
slots the room has spare, which may be fewer than 8.

**Not live-verified:** derived from reading `UpdateBoulderSet`
(`src/Z_04.asm`), not from observing it in-game.

## Boulders come down almost continuously

**Code:** `LEUEVEYP`

**Effect:** The gap between boulders dropping onto a mountain screen shrinks
from up to `$1F` frames to at most 3, so they arrive in a near-constant
stream.

**How it works:** `UpdateBoulderSet` (`src/Z_04.asm:2213`) randomises the
wait before the next boulder:

```
    ; Set the boulder set's timer to ((Random + 8) AND $1F).
    LDX CurObjIndex
    LDA #$08
    CLC
    ADC Random+1, X
    AND #$1F
    STA ObjTimer, X
```

This patches the AND mask at bank 4 CPU `$88BE` (originally `$1F`) to `$03`.
Raw form: `$88BE:03:1F`. No other PRG bank holds `$1F` at that
`$8000`-window offset.

**Caveat — keep it a low-bits mask.** The comment's "(Random + 8) AND `$1F`"
reading only holds for masks of the form `$01`/`$03`/`$07`/`$0F`/`$1F`. A
value like `$30` would gate on scattered bits and produce a timer that jumps
between a couple of values rather than a short random range.

**Caveat — the active-boulder cap still applies.** With the vanilla cap of 3
live boulders, a shorter timer mostly means boulders are replaced faster
rather than piling up; pair it with the `$888E` code for the full storm.

**Not live-verified:** derived from reading `UpdateBoulderSet`
(`src/Z_04.asm`), not from observing it in-game.

## Tektites and boulders fall three times faster

**Code:** `TANEKPZA`

**Effect:** The downward half of a Tektite's hop — and a rolling boulder's
descent — is capped at 6 pixels a frame instead of 2, so they drop like
stones.

**How it works:** `UpdateBoulder`'s movement path (`src/Z_04.asm:2391`) hands
`Jumper_MoveY` a maximum downward speed:

```
    CLC
    ADC ObjDir, X
    TAY
    LDA JumperYAccelerations, Y
    LDY #$02                    ; Max speed 2 pixels going down
    JSR Jumper_MoveY
```

This patches the immediate at bank 4 CPU `$897C` (originally `$02`) to `$06`.
Raw form: `$897C:06:02`. No other PRG bank holds `$02` at that
`$8000`-window offset.

**Caveat — shared by every "jumper".** `Jumper_MoveY` and the surrounding
code serve Blue Tektites, Red Tektites and boulders alike
(`Jumper_GetKind`, `src/Z_04.asm:2521`, maps object type minus `$0D` to the
kind index). All three fall faster. The upward speeds in
`JumperStartSpeedsHi` are untouched, so jumps still start the same height —
they just come down much harder.

**Not live-verified:** derived from reading the jumper movement code
(`src/Z_04.asm`), not from observing it in-game.

## Boulders roll to the very bottom of the screen

**Code:** `VNNEXPEN`

**Effect:** Boulders survive `$E` extra pixels of travel before being
destroyed, so they roll all the way off the bottom edge instead of popping
out of existence just above it.

**How it works:** `UpdateBoulder` (`src/Z_04.asm:2508`) destroys the boulder
once it is low enough:

```
    ; If the boulder's Y < $F0, return.
    LDA ObjY, X
    CMP #$F0
    BCC L10A10_Exit

    ; Else the boulder is close enough to the bottom of the screen
    ; to destroy it.
    DEC ActiveBoulders
    JMP DestroyMonster
```

This patches the compare operand at bank 4 CPU `$89FA` (originally `$F0`) to
`$FE`. Raw form: `$89FA:FE:F0`. No other PRG bank holds `$F0` at that
`$8000`-window offset.

**Caveat — do not raise it to `$FF` or beyond.** `ObjY` is a single byte and
the test is `BCC` (destroy when `Y >= $FE`). At `$FF` the boulder would still
be destroyed on the frame it reaches `$FF`, but any value the coordinate
steps *over* rather than landing on risks a boulder that wraps its Y and
never dies, permanently consuming a slot and holding `ActiveBoulders` high.
`$FE` is chosen to stay inside the range the movement code actually visits.

**Not live-verified:** derived from reading `UpdateBoulder`
(`src/Z_04.asm`), not from observing it in-game.

## Ghinis drift instead of hounding Link

**Code:** `APVEKKNY`

**Effect:** Overworld Ghinis (the ground-bound grim-reaper heads) re-aim at
Link far less often, so they wander loosely rather than tracking him.

**How it works:** `UpdateGhini` (`src/Z_04.asm:3071`) is one of the clearest
labelled constants in the bank — the routine opens by passing a turn rate to
the shared wanderer:

```
UpdateGhini:
    LDA #$FF                    ; Pass in turn rate $FF to turn as often as possible.
    JSR UpdateCommonWanderer
```

This patches the immediate at bank 4 CPU `$8C6C` (originally `$FF`) to `$10`.
Raw form: `$8C6C:10:FF`. The comment fixes `$FF` as the maximum of the range,
so a small value is the minimum-turning end.

**Caveat — not bank-unique.** Bank 0 also holds `$FF` at this `$8000`-window
offset. If a code is active while bank 0 is mapped in, the patch will also
rewrite that byte. Bank 0 is the audio engine, so the risk is a corrupted
sound routine rather than corrupted gameplay, but it is a real risk — treat
this code as one to switch off when it is not wanted.

**Not live-verified:** derived from reading `UpdateGhini` (`src/Z_04.asm`),
not from observing it in-game.

## The secret Armos hides a cave entrance instead of stairs

**Code:** `GXKENGAY`

**Effect:** On the overworld screens where an Armos statue hides a secret,
walking the Armos off reveals the black cave-entrance square rather than the
usual stairs.

**How it works:** `InitArmosOrFlyingGhini` (`src/Z_04.asm:3177`) stashes the
tile it will later write under the Armos:

```
    ; Else we have an armos.
    ;
    ; Store stairs tile $70 in [00] for use later.
    LDA #$70
    STA $00

    ; Look for the current room ID in an array of room ID's that
    ; have armos secrets.
    LDY #$06
```

This patches the immediate at bank 4 CPU `$8CCF` (originally `$70`, the
stairs tile) to `$24`. Raw form: `$8CCF:24:70`. `$24` is the black tile that
`UpdateRockWall` (`src/Z_04.asm:3740`) writes for a bombed-open shortcut, so
its meaning is documented elsewhere in this same bank rather than guessed.
No other PRG bank holds `$70` at that `$8000`-window offset.

**Caveat — the square's behaviour follows the tile.** Whether Link can enter
the revealed square is decided by the tile id, so swapping stairs for the
black tile changes where the secret leads (or whether it leads anywhere).

**Not live-verified:** derived from reading `InitArmosOrFlyingGhini` and
`UpdateRockWall` (`src/Z_04.asm`), not from observing it in-game.

## The Armos gives up a Heart Container, not the Power Bracelet

**Code:** `ZONASGGO`

**Effect:** The item sitting under the secret Armos becomes a Heart
Container instead of the Power Bracelet.

**How it works:** `UpdateArmos` (`src/Z_04.asm:3220`) sets the room item once
the secret Armos has been walked off its square:

```
    ; This resets the room item's state, which activates it.
    STY ObjState+19

    ; Set the room item ID.
    LDA #$14
    STA RoomItemId

    ; If the bracelet has not been taken, then play the "secret found" tune.
```

The comment two lines later ("if the bracelet has not been taken") is what
fixes `$14` as the Power Bracelet's item id. This patches the immediate at
bank 4 CPU `$8CF5` (originally `$14`) to `$1A`. Raw form: `$8CF5:1A:14`.
Item id `$1A` is the Heart Container — the same id an existing published code
substitutes into `DropItemTable`, resolved through `ItemIdToSlot` /
`ItemIdToDescriptor` (`src/Z_01.asm:4318`, `4341`) to slot `$18` with
descriptor `$10`. Both ids are well inside those tables, so no bounds are
exceeded. No other PRG bank holds `$14` at that `$8000`-window offset.

**Caveat — the room flag is still the bracelet's.** The "already taken" check
around this store uses the room's item flag, not the item id, so the Heart
Container can only be collected once per screen exactly as the bracelet could.

**Not live-verified:** derived from reading `UpdateArmos` (`src/Z_04.asm`),
not from observing it in-game.

## Woken Armos charge at double speed

**Code:** `EGXANIAT`

**Effect:** The faster of the two speeds an Armos can wake up with doubles,
from 1.5 to 3 pixels a frame, so roughly half of the statues in a group come
to life sprinting.

**How it works:** `UpdateArmos` (`src/Z_04.asm:3277`) rolls for one of two
speeds when a statue animates:

```
    ; Set a speed (q-speed fraction) randomly:
    ; $20 if random value < $80
    ; $60 otherwise
    LDA #$20
    LDY Random+1, X
    CPY #$80
    BCC :+
    LDA #$60
:
    STA ObjQSpeedFrac, X
```

This patches the second immediate at bank 4 CPU `$8D27` (originally `$60`) to
`$C0`. Raw form: `$8D27:C0:60`. No other PRG bank holds `$60` at that
`$8000`-window offset.

**Caveat — only the fast half changes.** The `LDA #$20` at `$8D1F` is
untouched, so the coin flip still produces a slow Armos about half the time.
The contrast between the two is the visible effect.

**Not live-verified:** derived from reading `UpdateArmos` (`src/Z_04.asm`),
not from observing it in-game.

## Bombed rock walls reveal stairs instead of a cave mouth

**Code:** `AYEEOYGZ`

**Effect:** Blowing open an overworld rock wall uncovers the stairs square
rather than the black cave entrance.

**How it works:** `UpdateRockWall` (`src/Z_04.asm:3740`) writes the revealed
square once a bomb connects:

```
    ; If the tile object and weapon collide, then reveal the secret.
    JSR CheckTileObjWeaponCollision
    BEQ @Exit
    LDA #$24                    ; Black tile
    JSR RevealAndFlagSecretTileObj
```

This patches the immediate at bank 4 CPU `$8F09` (originally `$24`) to `$70`.
Raw form: `$8F09:70:24`. `$70` is the stairs tile named in
`InitArmosOrFlyingGhini` (`src/Z_04.asm:3177`), so the substituted value's
meaning comes from the disassembly rather than a guess. No other PRG bank
holds `$24` at that `$8000`-window offset.

**Caveat — this is the exact inverse of the Armos code above.** Running both
at once swaps the two secrets' appearances rather than cancelling out; they
patch different bytes in different routines.

**Not live-verified:** derived from reading `UpdateRockWall` (`src/Z_04.asm`),
not from observing it in-game.

## Burnt trees open the instant the flame lands

**Code:** `AGXEXYZA`

**Effect:** A burnable overworld tree opens as soon as the candle flame
settles on it, instead of only in the last couple of frames before the flame
goes out.

**How it works:** `UpdateTree` (`src/Z_04.asm:3769`) waits for the standing
fire to be nearly spent before it will accept the burn:

```
@FoundFire:
    ; Store the fire's object slot in [00].
    STY $00

    ; If the standing fire's timer >= 2, return.
    LDA a:ObjTimer, Y
    CMP #$02
    BCS L10F3E_Exit

    ; If the tile object and weapon collide, then reveal the secret.
    JSR CheckTileObjWeaponCollision
    BEQ L10F3E_Exit
```

This patches the compare operand at bank 4 CPU `$8F2A` (originally `$02`) to
`$40`. Raw form: `$8F2A:40:02`. A standing flame is created with a timer of
`$3F` (`UpdateFire`, `src/Z_07.asm:4658` — "make the fire stand instead of
move. Set state `$22` and last `$3F` frames"), so a threshold of `$40` is
satisfied from the flame's very first frame instead of its last two. No other
PRG bank holds `$02` at that `$8000`-window offset.

**Note on the direction.** The candidate backlog described this byte as
"trees stay lit far longer before opening". It is the opposite: the test is
`BCS` — *return* while the timer is `>=` the operand — so raising the operand
makes the tree open sooner, not later.

**Caveat — the collision check still has to pass.** `CheckTileObjWeaponCollision`
immediately below still requires the flame to be close enough to the tree, so
this removes the timing requirement, not the positioning one.

**Not live-verified:** derived from reading `UpdateTree` and `UpdateFire`
(`src/Z_04.asm`, `src/Z_07.asm`), not from observing it in-game.

## Burn and bomb secrets open from four times further away

**Code:** `AGSAUYAP`

**Effect:** Bombs and candle flames pop open rocks, trees and rock walls from
`$40` pixels away instead of `$10`, so a bomb dropped anywhere near a
secret triggers it.

**How it works:** `CheckTileObjWeaponCollision` (`src/Z_04.asm:3819`) is the
shared proximity test for every tile object that reacts to a weapon:

```
    ; Put the tile object's midpoint coordinates in [02] and [03].
    JSR GetObjectMiddle
    LDA #$10                    ; 10 pixel collision threshold
    JMP DoObjectsCollide
```

This patches the immediate at bank 4 CPU `$8F53` (originally `$10`) to `$40`.
Raw form: `$8F53:40:10`. (The comment's "10 pixel" is the hexadecimal `$10`,
i.e. 16 pixels.) No other PRG bank holds `$10` at that `$8000`-window offset.

**Caveat — this is global across tile objects.** The routine's callers in this
bank are `UpdateRockWall` (`src/Z_04.asm:3738`), `UpdateTree`
(`src/Z_04.asm:3773`), and the rock/gravestone path — every burnable and
bombable secret widens at once. That breadth is the point of the code, but it
means the effect is not limited to one kind of secret.

**Not live-verified:** derived from reading `CheckTileObjWeaponCollision`
(`src/Z_04.asm`), not from observing it in-game.

## Second-quest tile secrets open in the first quest

**Code:** `AASEOYPA`

**Effect:** Overworld secrets that are gated to the second quest — bombable
walls and burnable trees that do nothing on a first-quest file — become
active in the first quest as well.

**How it works:** `IsQuestSecretMismatch` (`src/Z_04.asm:3829`) compares the
room's secret quest number against the save slot's:

```
SecretQuestNumbers:
    .BYTE $00, $00, $01

; Returns:
; C: 1 if there is a mismatch between current quest
;    and quest number for the secret in the room
;
IsQuestSecretMismatch:
    ; The quest secret is in the high two bits.
    LDA LevelBlockAttrsByteF
    ...
    ; If it's 0, then return C=0.
    BEQ @ReturnFalse

    ; Look up a quest number (0 or 1) indexed by quest secret (0 or 1).
    TAY
    LDA SecretQuestNumbers, Y

    ; If the save slot's quest number matches the room's
    ; secret quest number, then return C=0.
    LDY CurSaveSlot
    CMP QuestNumbers, Y
    BEQ @ReturnFalse
```

This patches `SecretQuestNumbers` **byte 2** at bank 4 CPU `$8F59`
(originally `$01`) to `$00`. Raw form: `$8F59:00:01`. Byte 2 is the entry a
room with quest-secret value 2 looks up; changing it from `$01` (second
quest) to `$00` (first quest) makes those secrets match a first-quest save.
No other PRG bank holds `$01` at that `$8000`-window offset.

**Note on which byte.** The candidate backlog nominated byte 0 (`$8F57`).
Byte 0 is unreachable: the routine takes `BEQ @ReturnFalse` when the
quest-secret value is zero, so the lookup never runs with `Y = 0` and a patch
there would do nothing. Byte 2 was used instead, and it is the byte that
carries the intended effect.

**Caveat — it flips the gate rather than removing it.** Secrets keyed to
quest-secret value 2 now require the *first* quest and stop working in the
second. `IsQuestSecretMismatch` is called from three places
(`src/Z_04.asm:3586`, `3719`, `3749`), so the change applies to every tile
object that consults the quest gate.

**Not live-verified:** derived from reading `IsQuestSecretMismatch`
(`src/Z_04.asm`), not from observing it in-game.

## The raft dock sits further left on its screen

**Code:** `ASEAEYEA`

**Effect:** On the overworld screen where the raft launches from room `$55`,
the dock's alignment point moves from X `$80` to `$50`, so Link has to stand
further left to board.

**How it works:** `UpdateDock` (`src/Z_04.asm:3875`) picks the dock's X from
the room, then requires Link to be lined up with it:

```
    ; State 0
    ;
    ; Choose an X coordinate for the dock:
    ; $80 in room $55
    ; $60 in the other room ($3F)
    LDA #$80
    LDY RoomId
    CPY #$55
    BEQ :+
    LDA #$60
:
    ; If the player is not aligned with the dock, return.
    CMP ObjX
```

This patches the first immediate at bank 4 CPU `$8F80` (originally `$80`) to
`$50`. Raw form: `$8F80:50:80`. No other PRG bank holds `$80` at that
`$8000`-window offset.

**Caveat — only room `$55` is affected.** The `LDA #$60` at `$8F89` covers
the other dock room (`$3F`) and is untouched.

**Caveat — the dock graphic does not move.** This is the coordinate the code
compares Link against, not the drawn tiles, so the boarding spot and the
visible dock will no longer line up. That mismatch is the observable effect.

**Not live-verified:** derived from reading `UpdateDock` (`src/Z_04.asm`),
not from observing it in-game.

## Peahats almost always chase

**Code:** `APVOTAEL`

**Effect:** Peahats pick the chasing flight state on nearly every decision
instead of about a third of the time, so they bear down on Link rather than
drifting across the screen.

**How it works:** `Flyer_PeahatDecideState` (`src/Z_04.asm:4081`) rolls for
the next flying state:

```
    ; Go to the next state randomly:
    ; Random >= $B0: 2
    ; Random >= $20: 3
    ; Else:          4
    ;
    ; Set up 6 turns.
    LDY #$02
    LDA Random, X
    CMP #$B0
    BCS Flyer_SetFlyingStateAnd6Turns    ; If >= $B0, go to state 2.
```

This patches the first compare operand at bank 4 CPU `$906E` (originally
`$B0`) to `$10`. Raw form: `$906E:10:B0`. State 2 is now taken for roughly
94% of rolls instead of 31%. No other PRG bank holds `$B0` at that
`$8000`-window offset.

**Caveat — states 3 and 4 become nearly unreachable.** The second test
(`CMP #$20` at `$9074`) is untouched but almost never reached.

**Caveat — Peahats are only vulnerable when stopped.** Making them fly more
does not make them easier to hit; if anything it reduces the windows in which
Link can damage them.

**Not live-verified:** derived from reading `Flyer_PeahatDecideState`
(`src/Z_04.asm`), not from observing it in-game.

## Wallmasters come back out of the wall almost at once

**Code:** `AAVPZPAV`

**Effect:** The delay before the next Wallmaster emerges drops from `$60`
frames (about a second) to `$08`, so hands stream out of the walls in quick
succession.

**How it works:** `UpdateWallmaster` (`src/Z_04.asm:4242`) sets the wait as
part of starting a wallmaster's trip:

```
    ; Wait $60 frames for the next wallmaster. Set this monster's
    ; QSpeed to $18, and animation counter to 8.
    LDA #$60
    STA ObjTimer+1
    LDA #$18
    STA ObjQSpeedFrac, X
```

This patches the first immediate at bank 4 CPU `$9162` (originally `$60`) to
`$08`. Raw form: `$9162:08:60`. No other PRG bank holds `$60` at that
`$8000`-window offset.

**Caveat — the timer lives in a neighbouring slot.** The store is to
`ObjTimer+1`, i.e. the *next* object slot's timer, which is how the routine
paces the following wallmaster rather than itself. Shortening it can put
several wallmasters on screen at once, competing for object slots with the
room's other monsters.

**Not live-verified:** derived from reading `UpdateWallmaster`
(`src/Z_04.asm`), not from observing it in-game.

## Wallmasters crawl three times faster

**Code:** `AIVPTOAP`

**Effect:** Wallmasters cross the room at about 1.25 pixels a frame instead
of 0.375, so grabbing Link is much harder to avoid.

**How it works:** `UpdateWallmaster` (`src/Z_04.asm:4244`), immediately after
setting the respawn delay:

```
    ; Wait $60 frames for the next wallmaster. Set this monster's
    ; QSpeed to $18, and animation counter to 8.
    LDA #$60
    STA ObjTimer+1
    LDA #$18
    STA ObjQSpeedFrac, X
```

This patches the second immediate at bank 4 CPU `$9166` (originally `$18`) to
`$50`. Raw form: `$9166:50:18`. No other PRG bank holds `$18` at that
`$8000`-window offset.

**Caveat — the animation is not resynchronised.** `ObjAnimCounter` is set to
8 two instructions later and is untouched, so a faster wallmaster will appear
to slide rather than crawl.

**Not live-verified:** derived from reading `UpdateWallmaster`
(`src/Z_04.asm`), not from observing it in-game.

## Wallmasters make a much longer run across the room

**Code:** `AOUOPPYE`

**Effect:** A wallmaster's trip lasts `$18` tiles instead of 7 before it
retreats into the wall, so it traverses most of the room rather than dipping
in and out at the edge.

**How it works:** `UpdateWallmaster` (`src/Z_04.asm:4305`) counts tiles
crossed and ends the trip at the limit:

```
    ; Increase the count of tiles crossed.
    INC Wallmaster_ObjTilesCrossed, X

    ; If the monster has crossed less than 7 tiles, then
    ; go draw and check collisions.
    LDA Wallmaster_ObjTilesCrossed, X
    CMP #$07
    BCC @Wallmaster_DrawAndCheckCollisions
```

This patches the compare operand at bank 4 CPU `$91B9` (originally `$07`) to
`$18`. Raw form: `$91B9:18:07`. No other PRG bank holds `$07` at that
`$8000`-window offset.

**Caveat — the path is a fixed sequence of steps.** Direction for each leg
comes from `WallmasterDirsAndAttrsLeft` indexed by `Wallmaster_ObjStep`. A
trip longer than the table's documented path will keep indexing past the end
of that sequence, so the extra legs' directions are whatever bytes follow the
table. Expect the wallmaster to behave normally for the first 7 tiles and
erratically after that — that is the finding, not a clean "longer path".

**Not live-verified:** derived from reading `UpdateWallmaster`
(`src/Z_04.asm`), not from observing it in-game.

## Wallmasters reach out of the wall further ahead of Link

**Code:** `ATVOAZGZ`

**Effect:** A wallmaster aims its emergence point `$60` pixels ahead of Link
instead of `$24`, so it appears well in front of where he is standing rather
than right beside him.

**How it works:** `Wallmaster_CalcStartPosition` (`src/Z_04.asm:4458`) picks
the lead distance from whether Link is moving:

```
Wallmaster_CalcStartPosition:
    STA Wallmaster_ObjStep, X
    STY $03                     ; [03] holds the Link's minimum major coordinate.

    ; If Link is still (input dir = 0), then use distance $24, else $32.
    LDA #$24
    LDY ObjInputDir
    BEQ :+
    LDA #$32
:
```

This patches the first immediate at bank 4 CPU `$9268` (originally `$24`) to
`$60`. Raw form: `$9268:60:24`. No other PRG bank holds `$24` at that
`$8000`-window offset.

**Caveat — only the "Link is standing still" case changes.** The `LDA #$32`
at `$926D` covers a moving Link and is untouched, so the effect only shows
when Link is stopped at the moment the wallmaster picks its spot.

**Not live-verified:** derived from reading `Wallmaster_CalcStartPosition`
(`src/Z_04.asm`), not from observing it in-game.

## Moldorm starts out crawling

**Code:** `AZEOPGEA`

**Effect:** Each Moldorm segment begins the fight at a quarter of its normal
starting speed, so the worm oozes into motion instead of immediately
whipping around the room.

**How it works:** `InitMoldorm` (`src/Z_04.asm:4800`) seeds every segment as
it builds the chain:

```
    ; Start with flying speed $80, and in flying state 2.
    LDA #$80
    STA Flyer_ObjSpeed+1, Y
    LDA #$02
    STA Flyer_ObjFlyingState+1, Y
    LDA #$41                    ; All segments are considered Moldorm.
    STA ObjType+1, Y
```

This patches the immediate at bank 4 CPU `$9409` (originally `$80`) to `$20`.
Raw form: `$9409:20:80`. No other PRG bank holds `$80` at that
`$8000`-window offset.

**Caveat — it is a starting speed, not a cap.** The flyer logic accelerates
toward `FlyingMaxSpeedFrac` (set to `$80` further down the same routine), so
Moldorm will work its way back up to normal speed; the effect is on the
opening moments of the fight.

**Not live-verified:** derived from reading `InitMoldorm` (`src/Z_04.asm`),
not from observing it in-game.

## Moldorm's top speed is nearly doubled

**Code:** `ETUOIGEA`

**Effect:** Moldorm can accelerate to `$E0` instead of `$80`, roughly 3.5
pixels a frame, turning the fight into a chase.

**How it works:** `InitMoldorm` (`src/Z_04.asm:4836`) sets the flyer speed
cap for the room:

```
    LDA #$80                    ; The maximum speed for Moldorm is $80.
    STA FlyingMaxSpeedFrac
    LDA #$08                    ; 8 instead of 10, because 8 is the max kill count to save.
    STA RoomObjCount
```

This patches the immediate at bank 4 CPU `$943D` (originally `$80`) to `$E0`.
Raw form: `$943D:E0:80`. No other PRG bank holds `$80` at that
`$8000`-window offset.

**Caveat — `FlyingMaxSpeedFrac` is a single global.** It is one variable
shared by every flying monster in the room, not a per-object field. Anything
else airborne in Moldorm's room inherits the raised cap. `EndInitFlyer`
(`src/Z_04.asm:1895`) and `InitGleeokHead` (`src/Z_04.asm:7826`) write the
same variable for their own monsters, so whichever init ran last wins.

**Not live-verified:** derived from reading `InitMoldorm` (`src/Z_04.asm`),
not from observing it in-game.

## Killing Moldorm barely counts toward the room

**Code:** `PAKPZKAA`

**Effect:** Moldorm's room is registered as holding 1 object instead of 8,
which changes when the room counts as cleared.

**How it works:** `InitMoldorm` (`src/Z_04.asm:4838`) declares the room's
object count:

```
    LDA #$08                    ; 8 instead of 10, because 8 is the max kill count to save.
    STA RoomObjCount
```

This patches the immediate at bank 4 CPU `$9442` (originally `$08`) to `$01`.
Raw form: `$9442:01:08`. No other PRG bank holds `$08` at that
`$8000`-window offset.

**Caveat — this is bookkeeping, not health.** `RoomObjCount` feeds the
kill-count/room-clear logic; it does not make Moldorm die faster. The
observable effect is on when the room registers as emptied and what gets
saved, not on the fight.

**Caveat — the comment explains the vanilla value.** `$08` was chosen
because it is the maximum kill count the save format can hold; a smaller
value is safe in that respect, but it also means the saved count no longer
reflects the segments actually destroyed.

**Not live-verified:** derived from reading `InitMoldorm` (`src/Z_04.asm`),
not from observing it in-game.

## Digdogger starts out much faster

**Code:** `EGVOZKYL`

**Effect:** Digdogger's initial speed fraction jumps from `$3F` to `$C0`, so
it darts around the room from the moment the fight begins.

**How it works:** `InitDigdogger1` (`src/Z_04.asm:4870`):

```
    ; Set low speed byte to $3F.
    ; This assumes that the high byte is 0 from when the room
    ; was reset; or will bet set during digdogger split-up.
    LDA #$3F
    STA Digdogger_ObjSpeedFrac, X
```

This patches the immediate at bank 4 CPU `$946A` (originally `$3F`) to `$C0`.
Raw form: `$946A:C0:3F`. No other PRG bank holds `$3F` at that
`$8000`-window offset.

**Caveat — the target speed is unchanged.** The `LDA #$80` at `$946F` sets
`Digdogger_ObjTargetSpeedFrac`, and `Digdogger_SlowDown` will pull the speed
back down toward it, so the boost is strongest at the start.

**Not live-verified:** derived from reading `InitDigdogger1`
(`src/Z_04.asm`), not from observing it in-game.

## Digdogger splits into five children instead of three

**Code:** `IANPGGLA`

**Effect:** Playing the Recorder at Digdogger breaks it into five smaller
Digdoggers rather than three.

**How it works:** `InitDigdogger1` (`src/Z_04.asm:4880`):

```
    ; Set child count of 3.
    LDA #$03
    STA ChildDigdoggerCount
    RTS
```

This patches the immediate at bank 4 CPU `$9474` (originally `$03`) to `$05`.
Raw form: `$9474:05:03`. No other PRG bank holds `$03` at that
`$8000`-window offset.

**Caveat — `InitDigdogger2` sets its own count.** The one-child variant
writes `$01` at `$9483` and is unaffected, so only the three-child Digdogger
changes.

**Caveat — children need free object slots.** Two extra children must find
somewhere to live; in a room already holding fireballs or other objects, some
may simply not appear.

**Not live-verified:** derived from reading `InitDigdogger1`
(`src/Z_04.asm`), not from observing it in-game.

## A severed Moldorm tail dies almost immediately

**Code:** `GEKPIGAZ`

**Effect:** When a Moldorm segment is destroyed and the chain is repacked,
the recycled slot is left with `$04` HP instead of `$20`, so the tail end of
the worm falls apart under a couple of extra hits.

**How it works:** `UpdateMoldorm` (`src/Z_04.asm:4953`) rebuilds the chain
when a segment dies:

```
    ; This segment is dead. We'll swap the tail segment with this
    ; dead segment. This way, moldorm heads are always rooted
    ; in slots 5 and $A; and the segments are continguous.
    ;
    ; Start by setting the HP for this dead segment's slot to $20.
    ;
    ; Note that this is not a true swap, because the tail's HP
    ; might be less than $20.
    LDA #$20
    STA ObjHP, X
```

This patches the immediate at bank 4 CPU `$94C5` (originally `$20`) to `$04`.
Raw form: `$94C5:04:20`.

**Caveat — not bank-unique.** Bank 3 also holds `$20` at this `$8000`-window
offset. Bank 3 is CHR pattern-transfer data, so a stray match would corrupt
graphics data rather than code, but it is a real second hit — disable the code
when it is not in use.

**Caveat — the comment already flags the value as approximate.** The
disassembly notes that this is "not a true swap, because the tail's HP might
be less than `$20`", so vanilla behaviour already varies; the patch makes the
recycled slot uniformly weak.

**Not live-verified:** derived from reading `UpdateMoldorm` (`src/Z_04.asm`),
not from observing it in-game.

## Digdogger almost always turns straight at Link

**Code:** `APEOZTEA`

**Effect:** Instead of a coin flip between homing in and turning at random,
Digdogger aims at Link on nearly every turn.

**How it works:** `L_Digdogger_Turn` (`src/Z_04.asm:5289`):

```
    ; If the object timer has expired, then set it to $10,
    ; and randomly choose to turn toward Link or randomly.
    LDA ObjTimer, X
    BNE L_Digdogger_Move
    LDA #$10
    STA ObjTimer, X
    LDA Random, X
    CMP #$80
    BCS L_Digdogger_TurnTowardLink
    JSR TurnRandomlyDir8
```

This patches the compare operand at bank 4 CPU `$960A` (originally `$80`) to
`$10`. Raw form: `$960A:10:80`. No other PRG bank holds `$80` at that
`$8000`-window offset.

**Note on the direction.** The branch is `BCS` — turn toward Link when the
random byte is `>=` the operand — so the operand must be *lowered* to make
homing more frequent. The candidate backlog suggested raising it to `$F0`,
which would have produced the opposite effect.

**Not live-verified:** derived from reading `L_Digdogger_Turn`
(`src/Z_04.asm`), not from observing it in-game.

## Digdogger accelerates much harder after it splits

**Code:** `EVUPGTAG`

**Effect:** The target speed Digdogger accelerates toward after speeding up
rises from `$40` to `$E0`, so it hurtles around the room.

**How it works:** `Digdogger_SpeedUp` (`src/Z_04.asm:5420`) hands a new
target speed to `SetTargetSpeed` once the current speed has been reached:

```
    ; Set speed flag to 1 meaning decelerate.
    INC Digdogger_ObjSpeedFlag, X

    ; Go set target speed to $0040 (or $0140 if this is a child).
    LDA #$40
    JMP SetTargetSpeed
```

This patches the immediate at bank 4 CPU `$96B4` (originally `$40`) to `$E0`.
Raw form: `$96B4:E0:40`. No other PRG bank holds `$40` at that
`$8000`-window offset.

**Caveat — children get a higher target still.** The comment notes the value
becomes `$0140` for a child Digdogger (the high byte is added elsewhere), so
the split children are affected more strongly than the parent.

**Caveat — the deceleration target is untouched.** `Digdogger_SlowDown`'s
`$80` at `$96D5` still pulls the speed back down, so the result is a wider
oscillation between fast and slow rather than a uniformly fast boss.

**Not live-verified:** derived from reading `Digdogger_SpeedUp`
(`src/Z_04.asm`), not from observing it in-game.

## Aquamentus paces continuously instead of one frame in eight

**Code:** `AEUOGYYA`

**Effect:** Aquamentus moves on every frame rather than one frame in eight,
so it strides back and forth across its ledge about eight times faster.

**How it works:** `Aquamentus_Move` (`src/Z_04.asm:5637`) gates movement on
the frame counter:

```
@Move:
    ; 7 of 8 screen frames return without moving.
    LDA FrameCounter
    AND #$07
    BNE @Exit
```

This patches the AND mask at bank 4 CPU `$97BC` (originally `$07`) to `$00`.
Raw form: `$97BC:00:07`. With a zero mask the result is always zero, so the
`BNE` never taken and the move runs every frame. No other PRG bank holds
`$07` at that `$8000`-window offset.

**Caveat — the movement step is unchanged.** `AquamentusSpeeds` (`$97A0`)
still supplies `$01`/`$FF` per step, so this multiplies the frequency of the
steps, not their size.

**Caveat — combine carefully with the published `AquamentusSpeeds` code.**
An existing code raises the positive step to `$04`; running both makes
Aquamentus cover its ledge roughly 32 times faster in one direction, which
will slam it into the clamp at `$97C6` every few frames.

**Not live-verified:** derived from reading `Aquamentus_Move`
(`src/Z_04.asm`), not from observing it in-game.

## Aquamentus wanders off the left of its ledge

**Code:** `AKKPZNEA`

**Effect:** Aquamentus can walk far to the left of where the boss normally
turns around, then snaps back to its usual limit.

**How it works:** `Aquamentus_Move` (`src/Z_04.asm:5643`) tests the boss's X
against a left limit and clamps it:

```
    ; If the boss crossed the left limit, then
    ; put it back at the left limit ($88), and face right.
    LDA ObjX, X
    CMP #$88
    BCS @CheckRightLimit
    LDA #$88
    STA ObjX, X
    LDA #$01
    STA ObjDir, X
```

This patches the compare operand at bank 4 CPU `$97C2` (originally `$88`) to
`$40`. Raw form: `$97C2:40:88`. No other PRG bank holds `$88` at that
`$8000`-window offset.

**Caveat — only the test moves, not the clamp.** The `LDA #$88` at `$97C6`
still snaps the boss back to `$88` when the test finally fires, so what the
player sees is Aquamentus drifting left past its normal boundary and then
jumping back rather than a smoothly wider patrol. That teleport is the real
effect and is why only one of the two bytes is patched.

**Caveat — the right-hand pair is untouched.** `CMP #$C8` / `LDA #$C7` at
`$97CE` / `$97D2` still bound the right side normally.

**Not live-verified:** derived from reading `Aquamentus_Move`
(`src/Z_04.asm`), not from observing it in-game.

## Aquamentus fireballs cannot be blocked

**Code:** `TIUPEAII`

**Effect:** Aquamentus's three-way fireball volley becomes the unblockable
fireball type, so the shield no longer stops it — and the three shots fly as
one straight line instead of fanning out.

**How it works:** `ShootFireball55` (`src/Z_04.asm:5749`) is the tiny shim
Aquamentus shoots through:

```
; Params:
; X: object index
;
ShootFireball55:
    LDA #$55
    JMP ShootFireball
```

This patches the immediate at bank 4 CPU `$9830` (originally `$55`) to `$56`.
Raw form: `$9830:56:55`. `$56` is the unblockable fireball type, named in
`UpdateManhandla` (`src/Z_04.asm:7958`) as "Fireball object type `$56`
(unblockable)"; both `$55` and `$56` map to `UpdateFireball` in
`UpdateObject_JumpTable` (`src/Z_07.asm:5321`). No other PRG bank holds `$55`
at that `$8000`-window offset.

**Caveat — the volley stops spreading.** `Aquamentus_Shoot`'s
`@SpreadOutFireballs` loop looks for objects of type `$55` in order to fan the
three fireballs apart. With type `$56` none of them match, so all three travel
on the same trajectory. This is a genuine second effect of the same byte, not
a side note.

**Not live-verified:** derived from reading `ShootFireball55`,
`Aquamentus_Shoot` and `UpdateManhandla` (`src/Z_04.asm`), not from observing
it in-game.

## One bomb kills Dodongo

**Code:** `PAKPVPZA`

**Effect:** Dodongo dies after swallowing a single bomb instead of two.

**How it works:** `UpdateDodongoState1_Bloated_Sub_Wait` (`src/Z_04.asm:5946`)
decides, once the bloated substate reaches 2, whether Dodongo has taken enough
bombs to die:

```
    ; New bloated substate >= 2.
    ;
    ; If bomb hits < 2, then set bloated substate 4,
    ; which will transition to state 0 (moving).
    LDY Dodongo_ObjBombHits, X
    CPY #$02
    BCS L_Dodongo_DecrementBloatedTimer
    LDA #$04
    STA Dodongo_ObjBloatedSubstate, X
```

This patches the `CPY` operand at bank 4 CPU `$9946` (originally `$02`) to
`$01`. Raw form: `$9946:01:02`. With `CPY #$01`, one recorded bomb hit already
satisfies the `BCS`, so the substate walks on to 3 and Dodongo dies the next
frame. No other PRG bank holds `$02` at that `$8000`-window offset.

**Caveat — the bomb still has to be swallowed.** `Dodongo_TryEatBomb` requires
the bomb to be in front of the mouth; a blast that merely lands nearby only
stuns. This code shortens the fight, it does not make it easier to land the
hit.

**Not live-verified:** derived from reading `UpdateDodongoState1_Bloated_Sub_Wait`
(`src/Z_04.asm`), not from observing it in-game.

## Dodongo stays bloated four times as long

**Code:** `NNUOUAAK`

**Effect:** After swallowing a bomb, Dodongo stands inflated and motionless for
about four seconds instead of about one before either dying or resuming its
walk.

**How it works:** `DodongoBloatedWaitTimes` (`src/Z_04.asm:5864`) holds one
wait length per bloated substate, read by
`UpdateDodongoState1_Bloated_Sub_Wait`:

```
DodongoBloatedWaitTimes:
    .BYTE $20, $40, $40
```

```
    ; Set the bloated timer according to the substate.
    LDY Dodongo_ObjBloatedSubstate, X
    LDA DodongoBloatedWaitTimes, Y
    STA Dodongo_ObjBloatedTimer, X
```

This patches byte 1 of the table at bank 4 CPU `$98BB` (originally `$40`) to
`$FF`. Raw form: `$98BB:FF:40`. Substate 1 is the stretch that runs after the
bomb has been counted, so the inflated pose holds for `$FF` frames. No other
PRG bank holds `$40` at that `$8000`-window offset.

**Caveat — byte 0 is a separate code.** `$98BA` (`$20`, substate 0) and `$98BC`
(`$40`, substate 2) are untouched; only the middle wait is stretched.

**Not live-verified:** derived from reading `DodongoBloatedWaitTimes` and
`UpdateDodongoState1_Bloated_Sub_Wait` (`src/Z_04.asm`), not from observing it
in-game.

## Dodongo turns toward Link constantly

**Code:** `NNSOKAAX`

**Effect:** Dodongo re-aims at Link at every square boundary instead of
wandering, so it tracks him around the room.

**How it works:** `UpdateDodongoState0_Move` (`src/Z_04.asm:5899`) sets the
turn rate before calling the shared wanderer movement:

```
@Move:
    TYA
    PHA
    LDA #$20                    ; Turn rate $20
    STA ObjTurnRate, X
    JSR Wanderer_TargetPlayer
```

`Wanderer_TargetPlayer` (`src/Z_04.asm:314`) does `LDA ObjTurnRate, X /
CMP Random+1, X / BCC @TurnIfTime` — a turn rate *below* the random byte sends
the monster off to a random turn, so a high rate means "chase". This patches
the immediate at bank 4 CPU `$98DC` (originally `$20`) to `$FF`. Raw form:
`$98DC:FF:20`. No other PRG bank holds `$20` at that `$8000`-window offset.

**Caveat — Dodongo already only moves in state 0.** While bloated or stunned it
does not run this code at all, so the change is invisible during those phases.

**Not live-verified:** derived from reading `UpdateDodongoState0_Move` and
`Wanderer_TargetPlayer` (`src/Z_04.asm`), not from observing it in-game.

## A bomb blast stuns Dodongo for eight times as long

**Code:** `NNNOUAAX`

**Effect:** A bomb that explodes near Dodongo without being swallowed pins it
in place far longer, giving Link a long window to attack it with the sword.

**How it works:** `UpdateDodongoState2_Stunned` (`src/Z_04.asm:5919`) reloads
the stun timer the first time it runs in the stunned state:

```
UpdateDodongoState2_Stunned:
    ; Take action depending on the value of stun timer:
    ; 0:     set stun timer to $20
    ; 1:     go back to state 0
    ; other: return
    LDY a:ObjStunTimer, X
    DEY
    BEQ UpdateDodongoState1_Bloated_Sub_End
    BPL :+
    LDA #$20
    STA a:ObjStunTimer, X
```

This patches the immediate at bank 4 CPU `$98FB` (originally `$20`) to `$FF`.
Raw form: `$98FB:FF:20`. Stun timers are decremented by the main loop's
`@UpdateTimers` block only once every ten frames (`src/Z_07.asm:481`), so
`$20` is already roughly five seconds and `$FF` is roughly forty. No other PRG
bank holds `$20` at that `$8000`-window offset.

**Caveat — a stunned Dodongo is harmless but also unshakeable.** A nonzero stun
timer makes `CheckLinkCollision` (`src/Z_01.asm:5610`) report no contact
damage, so a stunned Dodongo cannot hurt Link either.

**Not live-verified:** derived from reading `UpdateDodongoState2_Stunned`
(`src/Z_04.asm`) and the timer loop in `src/Z_07.asm`, not from observing it
in-game.

## Dodongo swallows bombs from much further to the right

**Code:** `ALXONZPP`

**Effect:** Dodongo eats a bomb that is sitting well past its mouth, instead of
only one placed almost exactly in front of it.

**How it works:** `DodongoBombPositiveLimits` (`src/Z_04.asm:6209`) is the
positive half of the range test in `Dodongo_IsBombInRange`, whose header
documents the index:

```
DodongoBombPositiveLimits:
    .BYTE $0C, $11

DodongoBombNegativeLimits:
    .BYTE $F4, $F0
```

```
; Y: limit index (0 for dust cloud, 1 for the bomb)
Dodongo_IsBombInRange:
    LDA DodongoBombPositiveLimits, Y
    STA $06
    LDA DodongoBombNegativeLimits, Y
    STA $07
```

This patches byte 1 — the live-bomb entry, used by `Dodongo_TryEatBomb` — at
bank 4 CPU `$9A2F` (originally `$11`) to `$30`. Raw form: `$9A2F:30:11`. No
other PRG bank holds `$11` at that `$8000`-window offset.

**Caveat — only the positive side is widened.** The matching negative limit
`$F0` at `$9A32` is untouched, so the accepted region becomes lopsided: bombs
below and to the right of the hotspot are picked up from much further away
than bombs above and to the left. Both axes use the same pair, so the
asymmetry applies vertically as well.

**Caveat — the mouth test still applies.** After the coarse range check,
`Dodongo_TryEatBomb` compares against `DodongoMouthNegativeLimits0/1` and
`DodongoMouthPositiveLimits0/1`, which this code does not change.

**Not live-verified:** derived from reading `DodongoBombPositiveLimits`,
`Dodongo_IsBombInRange` and `Dodongo_TryEatBomb` (`src/Z_04.asm`), not from
observing it in-game.

## Killing Dodongo no longer hands you a bomb

**Code:** `AEEPKOZA`

**Effect:** The guaranteed bomb drop that normally follows a Dodongo kill is
replaced by the ordinary random drop for the room.

**How it works:** `Dodongo_CheckCollisions` (`src/Z_04.asm:6014`) arms the
"help" drop when Dodongo dies:

```
@Die:
    JSR UpdateDodongoState1_Bloated_Sub_Die

    ; Drop a bomb from this fight.
    LDA #$0A
    STA HelpDropCount
    STA HelpDropValue
```

The drop routine at `src/Z_04.asm:11152` reads both:

```
    ; If help drop counter < $A, then use the dropped item ID as is.
    ; But there is a random chance that the item drop will be canceled.
    LDA HelpDropCount
    CMP #$0A
    BCC @RandomlyCancel

    ; Otherwise, the item will be guaranteed to be made.
    ; [51] HelpDropValue determines which kind:
    ; - 0:     5 rupees
    ; - other: bomb
```

This patches the immediate at bank 4 CPU `$9984` (originally `$0A`) to `$00`.
Raw form: `$9984:00:0A`. `HelpDropCount` stays below `$0A`, so the `BCC` takes
the ordinary path. Raw form aside, note that the same instruction feeds
`HelpDropValue`, so both halves of the guarantee are removed at once. No other
PRG bank holds `$0A` at that `$8000`-window offset.

**Caveat — this makes the game harder, not easier.** In Level 2 the guaranteed
bomb is what lets you keep fighting the remaining Dodongos; without it you may
run dry.

**Caveat — the ordinary help counter still works.** `src/Z_01.asm:6001`
increments `HelpDropCount` as Link takes damage, so the general pity-drop
system is unaffected — only the Dodongo-specific guarantee is.

**Not live-verified:** derived from reading `Dodongo_CheckCollisions`
(`src/Z_04.asm`) and the drop routine at `src/Z_04.asm:11152`, not from
observing it in-game.

## Gibdos wander aimlessly

**Code:** `APUPNLEA`

**Effect:** Gibdos stop homing in on Link and pick random directions at almost
every square instead.

**How it works:** `UpdateGibdo` (`src/Z_04.asm:6465`) passes its turn rate to
the shared wanderer:

```
UpdateGibdo:
    LDA #$80                    ; Turn rate $80
    JSR UpdateCommonWanderer
```

`Wanderer_TargetPlayer` (`src/Z_04.asm:314`) compares the rate against a random
byte:

```
    ; If turn rate < a random value, or Link's state = $FF;
    ; then go turn if turn timer has expired.
    LDA ObjTurnRate, X
    CMP Random+1, X
    BCC @TurnIfTime
```

This patches the immediate at bank 4 CPU `$9B37` (originally `$80`) to `$10`,
so the `BCC` is taken about 94% of the time instead of 50%. Raw form:
`$9B37:10:80`. No other PRG bank holds `$80` at that `$8000`-window offset.

**Caveat — Darknuts have their own copy.** The identical `LDA #$80` in
`UpdateDarknut` sits at `$9B45` and is not affected; this code changes Gibdos
only.

**Not live-verified:** derived from reading `UpdateGibdo` and
`Wanderer_TargetPlayer` (`src/Z_04.asm`), not from observing it in-game.

## Darknuts freeze solid

**Code:** `NYSPKLAE`

**Effect:** Darknuts stop moving entirely and stop hurting Link on contact,
standing where they are as harmless statues. They can still be killed from
behind.

**How it works:** `UpdateDarknut` (`src/Z_04.asm:6481`) clears the stun timer
every single frame, which is how the game enforces "Darknuts are never
stunned":

```
UpdateDarknut:
    LDA #$80                    ; Turn rate $80
    JSR UpdateCommonWanderer
    JSR CheckMonsterCollisions

    ; Darknuts are never stunned.
    LDA #$00
    STA ObjStunTimer, X
```

This patches the immediate at bank 4 CPU `$9B54` (originally `$00`) to `$FF`.
Raw form: `$9B54:FF:00`. Because the store runs unconditionally every frame,
the timer is refilled far faster than the main loop's ten-frame stun cycle
(`src/Z_07.asm:481`) can drain it, so it is permanently nonzero. Two readers
then act on it: `UpdateCommonWanderer` (`src/Z_04.asm:295`) returns before
moving —

```
    ; If we have the magic clock or the monster is stunned, then return.
    LDA InvClock
    ORA ObjStunTimer, X
    BNE Exit
```

— and `CheckLinkCollision` (`src/Z_01.asm:5610`) reports no contact damage from
a stunned monster.

**Caveat — not bank-unique.** Bank 3 also holds `$00` at this `$8000`-window
offset, so the patch fires there too whenever bank 3 is mapped in. `$00` is an
extremely common byte; expect collateral effects.

**Caveat — the shield still faces forward.** Nothing here changes the darknut's
facing or its front-side invulnerability, so you still have to strike from the
side or back.

**Not live-verified:** derived from reading `UpdateDarknut`,
`UpdateCommonWanderer` (`src/Z_04.asm`) and `CheckLinkCollision`
(`src/Z_01.asm`), not from observing it in-game.

## Pols Voice can be hurt by anything

**Code:** `AAUPXKVY`

**Effect:** Pols Voice takes damage from any weapon during ordinary collision
detection, not just the sword.

**How it works:** `L_PolsVoice_DrawAndCheckCollisions` (`src/Z_04.asm:6656`)
sets the invincibility mask immediately before the shared collision check:

```
    ; Pols Voice is invincible to everything but the sword,
    ; during normal collision detection.
    ;
    ; The arrow is a special case.
    LDA #$FE
    STA ObjInvincibilityMask, X
    JSR CheckMonsterCollisions
```

The mask is consumed by `AND $09` against the weapon's damage type
(`src/Z_01.asm:6154` and `src/Z_01.asm:6512`); a set bit means immune. This
patches the immediate at bank 4 CPU `$9C32` (originally `$FE`) to `$00`. Raw
form: `$9C32:00:FE`. With `$00`, no damage type is masked out. No other PRG
bank holds `$FE` at that `$8000`-window offset.

**Caveat — the arrow special case is elsewhere.** The one-hit arrow kill is
handled separately in `UpdatePolsVoice` and is unaffected.

**Not live-verified:** derived from reading `L_PolsVoice_DrawAndCheckCollisions`
(`src/Z_04.asm`) and the mask readers in `src/Z_01.asm`, not from observing it
in-game.

## Pols Voice hangs in the air

**Code:** `APUONKAL`

**Effect:** Pols Voice's hop becomes a slow, floating arc — it rises much
higher and takes several times as long to come back down.

**How it works:** `UpdatePolsVoiceState1_Jumping` (`src/Z_04.asm:6671`) applies
gravity to the 16-bit vertical speed each frame:

```
UpdatePolsVoiceState1_Jumping:
    ; Add acceleration $38 to low speed byte (vertical).
    LDA PolsVoice_ObjSpeedFrac, X
    CLC
    ADC #$38
    STA PolsVoice_ObjSpeedFrac, X
```

This patches the `ADC` operand at bank 4 CPU `$9C3F` (originally `$38`) to
`$10`. Raw form: `$9C3F:10:38`. The initial upward speed is unchanged, so with
weaker gravity the monster spends roughly three and a half times as long
before the speed turns positive again. No other PRG bank holds `$38` at that
`$8000`-window offset.

**Caveat — the landing test is a floor, not a timer.** The state ends only when
the speed is non-negative *and* `ObjY >= PolsVoice_ObjTargetY`, so the hop
still terminates at the same square; it just takes much longer to get there.

**Not live-verified:** derived from reading `UpdatePolsVoiceState1_Jumping`
(`src/Z_04.asm`), not from observing it in-game.

## Pols Voice jumps twice as far

**Code:** `ATNPSGAL`

**Effect:** Each Pols Voice hop covers `$60` or `$A0` pixels instead of `$30`
or `$70`, so they cross most of a room in one leap.

**How it works:** `UpdatePolsVoiceState1_Jumping` (`src/Z_04.asm:6713`) rolls
the distance for the next hop when the current one lands:

```
    ; Randomly set distance-to-move to $30 or $70.
    LDA Random, X
    AND #$40
    ADC #$30
    STA ObjRemDistance, X
```

This patches the `ADC` operand at bank 4 CPU `$9C75` (originally `$30`) to
`$60`. Raw form: `$9C75:60:30`. The paired `AND #$40` at `$9C71` is untouched,
so the roll still picks between two values `$40` apart — they are simply both
shifted up. No other PRG bank holds `$30` at that `$8000`-window offset.

**Caveat — long hops can run into walls.** `ObjRemDistance` is a budget, not a
destination; the monster still stops when it hits a wall, so in small rooms the
extra distance is often wasted.

**Not live-verified:** derived from reading `UpdatePolsVoiceState1_Jumping`
(`src/Z_04.asm`), not from observing it in-game.

## Vires split into Gels instead of Red Keese

**Code:** `GPNPVSGP`

**Effect:** Killing a Vire produces two Gels — the small grounded blobs — in
place of the usual pair of Red Keese.

**How it works:** `UpdateVire`'s `@SplitUp` path (`src/Z_04.asm:6925`) shoots
two children of a fixed object type:

```
    LDA #$1C                    ; Red Keese object type
    STA $00
    JSR Shoot
```

This patches the immediate at bank 4 CPU `$9D76` (originally `$1C`, Red Keese)
to `$14`, the Gel object type used by `UpdateZol`'s matching split. Raw form:
`$9D76:14:1C`. Both ids come from `UpdateObject_JumpTable`
(`src/Z_07.asm:5321`). No other PRG bank holds `$1C` at that `$8000`-window
offset.

**Caveat — the children keep Keese setup.** `Shoot` initialises the new objects
along the Vire/Keese path, so the Gels inherit flying-monster fields they do
not normally have. Expect them to look or move wrong; that is a real part of
the finding, not a bug in the code.

**Not live-verified:** derived from reading `UpdateVire` (`src/Z_04.asm`) and
`UpdateObject_JumpTable` (`src/Z_07.asm`), not from observing it in-game.

## Blue Wizzrobes teleport three times as far

**Code:** `AVVOKTAZ`

**Effect:** Each Blue Wizzrobe teleport hop covers `$60` pixels on both axes
instead of `$20`, so they jump across the room rather than one square at a
time.

**How it works:** `BeginTeleporting` (`src/Z_04.asm:7283`) sets the travel
budget for the hop:

```
BeginTeleporting:
    ; Will move $20 pixels horizontally and vertically.
    LDA #$20
    STA ObjRemDistance, X
```

This patches the immediate at bank 4 CPU `$9EEC` (originally `$20`) to `$60`.
Raw form: `$9EEC:60:20`. No other PRG bank holds `$20` at that `$8000`-window
offset.

**Caveat — the walkability probe still tests one square out.**
`BlueWizzrobe_ChooseTeleportTarget` checks only the tile at
`BlueWizzrobeTeleportMaxOffsetsX/Y` (`$20` away) before committing, so with the
longer hop the wizzrobe can now commit to a direction and then plough on past
walls it never tested.

**Not live-verified:** derived from reading `BeginTeleporting` and
`BlueWizzrobe_ChooseTeleportTarget` (`src/Z_04.asm`), not from observing it
in-game.

## Blue Wizzrobes reappear almost immediately

**Code:** `AONONTAY`

**Effect:** The pause between a Blue Wizzrobe fading out and coming back drops
from at least `$70` frames to at least `$10`, so they flicker in and out
constantly.

**How it works:**
`BlueWizzrobe_AlignWithNearestSquareAndRandomizeTimer` (`src/Z_04.asm:7298`)
ORs a floor onto a random byte:

```
BlueWizzrobe_AlignWithNearestSquareAndRandomizeTimer:
    ; Set a random timer >= $70.
    LDA Random, X
    ORA #$70
:
    STA ObjTimer, X
```

This patches the `ORA` mask at bank 4 CPU `$9EFF` (originally `$70`) to `$10`.
Raw form: `$9EFF:10:70`. It stays a high-bits mask, so the "random timer >= N"
reading still holds — the floor simply drops from `$70` to `$10` and the
average wait falls by roughly half. No other PRG bank holds `$70` at that
`$8000`-window offset.

**Not live-verified:** derived from reading
`BlueWizzrobe_AlignWithNearestSquareAndRandomizeTimer` (`src/Z_04.asm`), not
from observing it in-game.

## Blue Wizzrobes almost never teleport up and to the right

**Code:** `AVUPOTAZ`

**Effect:** One of the four Blue Wizzrobe teleport directions becomes very hard
to satisfy, so they hop up-right far less often and stand still waiting
instead.

**How it works:** `BlueWizzrobe_ChooseTeleportTarget` (`src/Z_04.asm:7240`)
rolls an index 0–3, temporarily offsets the monster's position by the matching
entries, and probes whether the tile there is walkable:

```
BlueWizzrobeTeleportMaxOffsetsX:
    .BYTE $E0, $20, $E0, $20

BlueWizzrobeTeleportMaxOffsetsY:
    .BYTE $E0, $E0, $20, $20

BlueWizzrobeTeleportDirs:
    .BYTE $0A, $09, $06, $05
```

```
    LDA ObjX, X
    PHA
    CLC
    ADC BlueWizzrobeTeleportMaxOffsetsX, Y
    STA ObjX, X
    ...
    ; If not walkable, then all we can do is align with the nearest square.
    BCS BlueWizzrobe_AlignWithNearestSquareAndRandomizeTimer
```

This patches byte 1 of the X table at bank 4 CPU `$9EB1` (originally `$20`) to
`$60`. Raw form: `$9EB1:60:20`. Index 1 is the up-and-right diagonal
(`dir $09`, X `+$20`, Y `-$20`); with `+$60` the game now tests a square three
tiles to the right instead of one, which is usually a wall, so the `BCS` sends
the wizzrobe to the align-and-wait path. No other PRG bank holds `$20` at that
`$8000`-window offset.

**Caveat — this is a probe offset, not the hop distance.** The coordinates are
restored after the test; the actual travel comes from `BeginTeleporting`'s
`ObjRemDistance`. Nothing in this code makes the wizzrobe land further away.

**Caveat — one byte, one direction.** Bytes 0, 2 and 3 at `$9EB0`, `$9EB2`,
`$9EB3` and the whole Y table at `$9EB4` are untouched.

**Not live-verified:** derived from reading `BlueWizzrobe_ChooseTeleportTarget`
and `Wizzrobe_GetCollidableTileForDir` (`src/Z_04.asm`), not from observing it
in-game.

## Red Wizzrobes linger four times as long before vanishing

**Code:** `TNNPKNYK`

**Effect:** After a Red Wizzrobe finishes its attack it flickers on screen for
about 63 frames instead of 16 before disappearing, so it stays a target for
much longer.

**How it works:** `UpdateRedWizzrobe` (`src/Z_04.asm:7473`) decrements
`ObjState` every frame and uses the top two bits as a phase index. Group 1
(`$7F` down to `$40`) is the fade-out, and `UpdateRedWizzrobe_1`
(`src/Z_04.asm:7509`) skips most of it:

```
UpdateRedWizzrobe_1:
    ; Handle state group 1 ($40 to $7F).
    ;
    ; If state = $7F, make it $4F.
    ; $7F is the first frame of state group ($40 to $7F).
    ; By doing this, we skip $30 frames.
    LDA ObjState, X
    CMP #$7F
    BNE :+
    LDA #$4F
    STA ObjState, X
```

This patches the immediate at bank 4 CPU `$9FF4` (originally `$4F`) to `$7E`.
Raw form: `$9FF4:7E:4F`. `$7E` is still inside group 1 and is one below the
`CMP #$7F` gate, so the skip is effectively removed and the monster walks the
full group. No other PRG bank holds `$4F` at that `$8000`-window offset.

**Note on the value.** The backlog suggested `$10`, but `$10` is in state group
0 — `UpdateRedWizzrobe_0` is a bare `RTS`, so the wizzrobe would become
invisible and inert *sooner*, the opposite of the intent. `$7E` is the value
that actually lengthens the visible phase, and it is the largest one that does
not re-trigger the `CMP #$7F` test.

**Caveat — group 1 draws intermittently.** The monster is drawn every other
frame during this phase (`INC RedWizzrobe_ObjFadeCounter`), so the extra time is
spent flickering, not fully solid.

**Caveat — `$A041` is one byte away in the next entry.** Do not confuse this
address with the Wizzrobe invincibility mask.

**Not live-verified:** derived from reading `UpdateRedWizzrobe` and
`UpdateRedWizzrobe_1` (`src/Z_04.asm`), not from observing it in-game.

## Wizzrobes can be hurt by anything

**Code:** `AAKZPAVY`

**Effect:** Wizzrobes take damage from every weapon — boomerang, arrows, fire,
the wand — instead of only the sword and bombs.

**How it works:** `Wizzrobe_DrawAndCheckCollisions` (`src/Z_04.asm:7589`) sets
the invincibility mask before running the weapon checks:

```
Wizzrobe_DrawAndCheckCollisions:
    ; Invincible to everything but sword and bomb.
    LDA #$F6
    STA ObjInvincibilityMask, X
    JSR GetObjectMiddle
```

The mask is ANDed with the weapon's damage type at `src/Z_01.asm:6154` and
`src/Z_01.asm:6512`; a set bit means immune, so `$F6` leaves bit 0 (sword) and
bit 3 (bomb) clear. This patches the immediate at bank 4 CPU `$A041`
(originally `$F6`) to `$00`. Raw form: `$A041:00:F6`. No other PRG bank holds
`$F6` at that `$8000`-window offset.

**Caveat — the routine only calls the checks it already called.** The mask
governs which damage types get through, but `Wizzrobe_DrawAndCheckCollisions`
still invokes a fixed list of weapon-collision routines
(`CheckMonsterSwordShotOrMagicShotCollision`, `CheckMonsterBombOrFireCollision`
twice, and the sword). Weapons outside that list are unaffected; what this
opens up is the shot, magic-shot and fire damage types those routines already
test for.

**Not live-verified:** derived from reading `Wizzrobe_DrawAndCheckCollisions`
(`src/Z_04.asm`) and the mask readers in `src/Z_01.asm`, not from observing it
in-game.

## Gleeok's necks start off to the left of its body

**Code:** `AKOZIEGY`

**Effect:** All four of Gleeok's necks are seeded at X `$40` instead of `$7C`,
so the heads begin the fight bunched against the left side of the room and have
to drag themselves back across it.

**How it works:** `InitGleeok` (`src/Z_04.asm:7640`) loops over the six
segments of each neck and seeds every segment's X coordinate from one
immediate:

```
    ; Set the X of the current segment of each neck to $7C.
    LDA #$7C
    STA Gleeok_NeckXs0, X
    STA Gleeok_NeckXs1, X
    STA Gleeok_NeckXs2, X
    STA Gleeok_NeckXs3, X
```

This patches the immediate at bank 4 CPU `$A095` (originally `$7C`) to `$40`.
Raw form: `$A095:40:7C`. No other PRG bank holds `$7C` at that `$8000`-window
offset.

**Caveat — only the X seed moves.** The Y seeds come from `GleeokSegmentYs`
and the body itself is placed by the room data, so at spawn the necks are
visibly detached from the body until `Gleeok_KeepSegsBetweenNeighbors` and the
segment-limit logic pull them back into a chain.

**Not live-verified:** derived from reading `InitGleeok` (`src/Z_04.asm`), not
from observing it in-game.

## Gleeok heads come off in one hit

**Code:** `AOUZTAEZ`

**Effect:** Each neck starts with `$10` HP instead of `$A0`, so a single wooden
sword strike severs a head.

**How it works:** `InitGleeok` (`src/Z_04.asm:7663`) gives every neck the same
starting HP:

```
    ; Set HP of each neck to $A0.
    ;
    ; Because there's only one HP value for each neck,
    ; it's stored right in the object slot -- unlike coordinates.
    LDA #$A0
    STA ObjHP+1, X
```

This patches the immediate at bank 4 CPU `$A0B6` (originally `$A0`) to `$10`.
Raw form: `$A0B6:10:A0`. `SwordDamagePoints` (`src/Z_01.asm:6163`) is
`$10, $20, $40`, so even the wooden sword now takes a neck off in one blow. No
other PRG bank holds `$A0` at that `$8000`-window offset.

**Caveat — the severed heads still fly.** Cutting a neck spawns a free-flying
Gleeok head, and this code does not shorten that phase; a fast start can leave
four heads loose at once.

**Not live-verified:** derived from reading `InitGleeok` (`src/Z_04.asm`) and
`SwordDamagePoints` (`src/Z_01.asm`), not from observing it in-game.

## Gleeok can be hurt by anything

**Code:** `AEKZLEVY`

**Effect:** Gleeok's necks take damage from every weapon rather than only the
sword.

**How it works:** `InitGleeok` (`src/Z_04.asm:7679`) sets each neck's
invincibility mask inside the same init loop:

```
    ; Invincible to everything but the sword.
    LDA #$FE
    STA ObjInvincibilityMask+1, X
```

The mask is ANDed with the weapon's damage type in
`HandleMonsterWeaponCollision` (`src/Z_01.asm:5919`); a set bit means immune.
This patches the immediate at bank 4 CPU `$A0C3` (originally `$FE`) to `$00`.
Raw form: `$A0C3:00:FE`. No other PRG bank holds `$FE` at that `$8000`-window
offset.

**Caveat — the boomerang now stuns instead of parrying.** With the boomerang
bit clear, `HandleMonsterWeaponCollision` falls through to the branch that sets
`ObjStunTimer` to `$10`, so a thrown boomerang freezes a neck for a while.

**Not live-verified:** derived from reading `InitGleeok` (`src/Z_04.asm`) and
`HandleMonsterWeaponCollision` (`src/Z_01.asm`), not from observing it in-game.

## Manhandla can be hurt by anything

**Code:** `AAXXAPXT`

**Effect:** Manhandla's five segments take damage from the boomerang and from
fire, not just from the sword and bombs.

**How it works:** `InitManhandla` (`src/Z_04.asm:7760`) sets one mask for all
five segments as it builds them:

```
    ; Set the segment invincible to fire and boomerang.
    LDA #$E2
    STA ObjInvincibilityMask+1, Y
```

This patches the immediate at bank 4 CPU `$A128` (originally `$E2`) to `$00`.
Raw form: `$A128:00:E2`. The loop runs `Y` from 4 down to 0 over object slots 5
through 1, so a single byte covers the whole boss. No other PRG bank holds
`$E2` at that `$8000`-window offset.

**Caveat — the boomerang becomes a stun weapon.** As with Gleeok, clearing the
boomerang bit sends `HandleMonsterWeaponCollision` (`src/Z_01.asm:5906`) down
the path that sets `ObjStunTimer` to `$10` on the hit segment.

**Not live-verified:** derived from reading `InitManhandla` (`src/Z_04.asm`)
and `HandleMonsterWeaponCollision` (`src/Z_01.asm`), not from observing it
in-game.

## Manhandla starts out crawling

**Code:** `AZSXPPEA`

**Effect:** Manhandla begins the fight at a quarter of its usual speed.

**How it works:** `InitManhandla` (`src/Z_04.asm:7798`) gives each segment the
same starting speed fraction:

```
    ; Set low speed byte $80.
    LDA #$80
    STA Manhandla_ObjSpeedFrac+1, Y
```

This patches the immediate at bank 4 CPU `$A159` (originally `$80`) to `$20`.
Raw form: `$A159:20:80`. Only the fractional byte is seeded here — the whole
byte starts at zero — so `$80` is half a pixel a frame and `$20` is an eighth.
No other PRG bank holds `$80` at that `$8000`-window offset.

**Caveat — killing heads still speeds it up.** `UpdateManhandla` adds `$80` to
every segment's speed fraction each time a segment dies, so the fight
accelerates back toward normal as you cut it down.

**Not live-verified:** derived from reading `InitManhandla` and
`UpdateManhandla` (`src/Z_04.asm`), not from observing it in-game.

## An upward sword thrust can hurt Gohma

**Code:** `AAVZYOUY`

**Effect:** Weapons other than the arrow are allowed to reach Gohma's damage
handler, so a sword stab delivered upward into the open eye deals damage.

**How it works:** `InitGohma` (`src/Z_04.asm:7809`) sets the mask that normally
turns everything but arrows into a parry:

```
InitGohma:
    LDA #$20                    ; Play Dodongo/Gohma roar.
    STA SampleRequest

    ; Invincible to everything but arrows.
    LDA #$FB
    STA ObjInvincibilityMask, X
```

`HandleMonsterWeaponCollision` (`src/Z_01.asm:5919`) checks the mask *before*
dispatching to Gohma's own handler:

```
HandleMonsterWeaponCollision:
    ; If the monster is invincible to this damage type, then
    ; go play parry sound if needed, and return.
    LDA ObjInvincibilityMask, X
    AND $09
    BNE L_PlayParrySoundForDamageType
```

This patches the immediate at bank 4 CPU `$A167` (originally `$FB`) to `$00`.
Raw form: `$A167:00:FB`. No other PRG bank holds `$FB` at that `$8000`-window
offset.

**Caveat — this is not "any weapon kills Gohma".** Clearing the mask only gets
the weapon past the first gate. `Gohma_HandleWeaponCollision`
(`src/Z_04.asm:8466`) still requires all three of its own conditions before it
calls `DealDamage`: the hit must land on body part 3 or 4, `Gohma_ObjEyeState`
must be 3 (eye fully open), and the *weapon's* direction must be `$08` (up).
A sword thrust made while facing up satisfies all three; a horizontal slash,
or a hit while the eye is shut, still parries. The arrow-to-spark special case
at the top of that routine is unaffected.

**Not live-verified:** derived from reading `InitGohma` and
`Gohma_HandleWeaponCollision` (`src/Z_04.asm`) and
`HandleMonsterWeaponCollision` (`src/Z_01.asm`), not from observing it in-game.

## Manhandla barely speeds up as its heads die

**Code:** `AXOZYPEA`

**Effect:** Cutting off a head adds only a quarter of the usual speed boost, so
Manhandla never reaches its frantic final-head pace.

**How it works:** `UpdateManhandla` (`src/Z_04.asm:7844`) bumps every segment's
16-bit speed each time a segment dies:

```
@LoopSegment:
    ; Add $80 to the low speed byte of this segment.
    LDA Manhandla_ObjSpeedFrac+1, Y
    CLC
    ADC #$80
    STA Manhandla_ObjSpeedFrac+1, Y
```

This patches the `ADC` operand at bank 4 CPU `$A197` (originally `$80`) to
`$20`. Raw form: `$A197:20:80`. Because the add is to the fractional byte, the
`$80` step also carries into the whole byte every other death — with `$20` the
carry only happens on the fourth. No other PRG bank holds `$80` at that
`$8000`-window offset.

**Not live-verified:** derived from reading `UpdateManhandla`
(`src/Z_04.asm`), not from observing it in-game.

## Manhandla changes direction every frame

**Code:** `PEUXAPAP`

**Effect:** Manhandla re-rolls its direction sixteen times as often, so it
jitters around the room instead of committing to a heading.

**How it works:** `UpdateManhandla` (`src/Z_04.asm:7869`) reloads the timer
that gates the direction decision:

```
@TurnIfNeeded:
    ; If object timer = 0, then
    ; 1. set timer to $10
    ; 2. randomly choose to turn toward Link or turn randomly
    ; 3. assign the base's direction to all segments and bounce direction
    LDA ObjTimer, X
    BNE @MoveBase
    LDA #$10
    STA ObjTimer, X
    LDA Random, X
    CMP #$80
    BCS @TurnTowardLink
```

This patches the immediate at bank 4 CPU `$A1B8` (originally `$10`) to `$01`.
Raw form: `$A1B8:01:10`. The `CMP #$80` coin flip at `$A1BD` is untouched, so
the mix of "toward Link" and "random" is unchanged — only the rate. No other
PRG bank holds `$10` at that `$8000`-window offset.

**Caveat — this may make Manhandla easier, not harder.** Re-deciding every
frame means the boss rarely travels far in any direction, so it tends to
hover near where it started.

**Not live-verified:** derived from reading `UpdateManhandla`
(`src/Z_04.asm`), not from observing it in-game.

## Manhandla's fireballs become blockable

**Code:** `IIOXAZTI`

**Effect:** Manhandla shoots ordinary fireballs that Link's shield can deflect
instead of the unblockable variety.

**How it works:** `UpdateManhandla` (`src/Z_04.asm:7952`) picks the projectile
type before shooting:

```
    LDA #$56                    ; Fireball object type $56 (unblockable)
    JSR ShootFireball
```

This patches the immediate at bank 4 CPU `$A218` (originally `$56`) to `$55`,
the blockable fireball type used elsewhere in the same bank. Raw form:
`$A218:55:56`. Both ids come from `UpdateObject_JumpTable`
(`src/Z_07.asm:5321`). No other PRG bank holds `$56` at that `$8000`-window
offset.

**Caveat — the four-fireball cap is unchanged.** The `CMP #$E0` random gate and
the `ObjType+7` slot test just above still limit how many are in flight.

**Caveat — Gleeok and Ganon have their own copies.** The identical `LDA #$56`
in `UpdateGleeok` and in Ganon's shooting code are separate bytes and separate
codes.

**Not live-verified:** derived from reading `UpdateManhandla` (`src/Z_04.asm`)
and `UpdateObject_JumpTable` (`src/Z_07.asm`), not from observing it in-game.

## Severed Gleeok heads almost always chase

**Code:** `ENUXYGEI`

**Effect:** A free-flying Gleeok head picks the chase state on about 94% of its
decisions instead of 81%, so the loose heads hound Link rather than drifting.

**How it works:** `Flyer_GleeokHeadDecideState` (`src/Z_04.asm:8546`) rolls for
the next flying state:

```
Flyer_GleeokHeadDecideState:
    ; Go to the next flying state randomly:
    ; Random < $D0: 2
    ; Else:         3
    ;
    ; Set up 6 turns.
    LDY #$02
    LDA Random+1, X
    CMP #$D0
    BCC :+
    INY
:
    JMP Flyer_SetStateAndTurns
```

This patches the `CMP` operand at bank 4 CPU `$A4BF` (originally `$D0`) to
`$F0`. Raw form: `$A4BF:F0:D0`. State 2 is `Flyer_Chase` and state 3 is
`Flyer_Wander` in `ControlGleeokHeadFlight_JumpTable`; the `BCC` keeps `Y` at 2,
so *raising* the operand is what increases chasing. No other PRG bank holds
`$D0` at that `$8000`-window offset.

**Not live-verified:** derived from reading `Flyer_GleeokHeadDecideState` and
`ControlGleeokHeadFlight_JumpTable` (`src/Z_04.asm`), not from observing it
in-game.

## Only one of Gleeok's necks ever moves

**Code:** `AAOZAILA`

**Effect:** Neck 0 does all the moving and all the shooting; the other three
heads hang motionless where they spawned.

**How it works:** `UpdateGleeok` (`src/Z_04.asm:8618`) rotates the active neck
by frame number:

```
    ; Each screen frame, one neck is chosen to move and try to shoot.
    LDA FrameCounter
    AND #$03
    STA $00
    CPX $00
    BNE @DrawAndCheckCollisions
    JSR Gleeok_MoveNeck
    JSR Gleeok_MoveHead
```

This patches the `AND` mask at bank 4 CPU `$A510` (originally `$03`) to `$00`.
Raw form: `$A510:00:03`. With the mask cleared, `$00` is always 0, so the
`CPX $00` test only ever passes for neck index 0. No other PRG bank holds `$03`
at that `$8000`-window offset.

**Note on the direction.** The backlog described this as "moves every neck every
frame"; the code does the opposite — the mask *selects* one neck, so narrowing
it narrows the selection. Widening it is not possible with one byte either,
since `$03` already covers all four neck indices.

**Caveat — the frozen necks are still solid.** `Gleeok_DrawHeadAndCheckCollisions`
runs for all four necks regardless, so the motionless heads still draw and can
still be cut off.

**Not live-verified:** derived from reading `UpdateGleeok` (`src/Z_04.asm`), not
from observing it in-game.

## Gleeok spits fireballs constantly

**Code:** `EYXZZIAZ`

**Effect:** The neck that moves each frame fires on about 94% of its turns
instead of 12%, so fireballs come almost continuously.

**How it works:** `UpdateGleeok` (`src/Z_04.asm:8630`) gates the shot on a
random roll:

```
    ; If Random < $20, and there's no object (fireball) in slot $B,
    ; then shoot fireball $56.
    LDA Random, X
    CMP #$20
    BCS @DrawAndCheckCollisions
    LDA ObjType+11
    BNE @DrawAndCheckCollisions
    LDA #$56
    JSR ShootFireball
```

This patches the `CMP` operand at bank 4 CPU `$A522` (originally `$20`) to
`$F0`. Raw form: `$A522:F0:20`. No other PRG bank holds `$20` at that
`$8000`-window offset.

**Caveat — slot `$B` is still the real limiter.** Only one Gleeok fireball can
exist at a time, so the practical effect is that a new fireball appears the
moment the previous one clears rather than after a random wait.

**Not live-verified:** derived from reading `UpdateGleeok` (`src/Z_04.asm`), not
from observing it in-game.

## Gleeok's necks stretch nearly three times further

**Code:** `LAXZZTGE`

**Effect:** The primary segment-distance cap rises from 4 to 10, so the necks
can trail much further behind their heads before being reeled in.

**How it works:** `Gleeok_CalcSegmentLimits` (`src/Z_04.asm:8877`) clamps three
nested limits from one input distance:

```
; Store primary distance, capped at 4.
;
Gleeok_CalcSegmentLimits:
    CMP #$04
    BCC :+
    LDA #$04
:
    STA GleeokPrimarySegmentLimits, X
```

This patches the `CMP` operand at bank 4 CPU `$A622` (originally `$04`) to
`$0B`. Raw form: `$A622:0B:04`. Distances from 0 to `$0A` now pass through
uncapped instead of being pinned at 4. No other PRG bank holds `$04` at that
`$8000`-window offset.

**Caveat — the clamp value is a different byte.** `$A625` is the `LDA #$04`
that supplies the replacement; it is untouched, so any distance of `$0B` or
more still collapses to 4. That discontinuity is real, not a mistake in the
code.

**Caveat — only the primary cap moved.** The secondary (`$08` at `$A62F`) and
tertiary (`$0B` at `$A638`) caps are separate bytes and separate codes, and
both still bound the outer segments.

**Not live-verified:** derived from reading `Gleeok_CalcSegmentLimits`
(`src/Z_04.asm`), not from observing it in-game.

## Zelda's rescue triggers from anywhere along her row

**Code:** `ENOZSPOA`

**Effect:** The horizontal window for touching Zelda widens from `$70`–`$80` to
`$70`–`$EF`, so walking anywhere along that row to her right ends the game.

**How it works:** `UpdateZelda` (`src/Z_04.asm:9592`) tests Link's position
against a small box before starting the rescue:

```
    ; State 0.
    ;
    ; If Link's X < $70 or >= $81, or Link's Y <> $95, then return.
    LDA ObjX
    CMP #$70
    BCC L129B7_Exit
    CMP #$81
    BCS L129B7_Exit
    LDA ObjY
    CMP #$95
    BNE L129B7_Exit
```

This patches the upper X bound at bank 4 CPU `$A995` (originally `$81`) to
`$F0`. Raw form: `$A995:F0:81`. No other PRG bank holds `$81` at that
`$8000`-window offset.

**Note on the target byte.** The backlog pointed at `$A99B` (`CMP #$95`, the Y
test) with a suggested `$C0`. That test is an *equality* against Link's Y, and
Link's Y in a dungeon room only ever takes the values `$5D + 8k`; `$C0` is not
one of them, so that patch would make Zelda permanently unreachable and lock
the ending out. The X bound is a real inequality and is the byte that actually
widens the trigger.

**Caveat — the row is still exact.** Link must still be standing on Y `$95`;
only the left-right span changed. The lower bound `CMP #$70` at `$A991` is
untouched.

**Not live-verified:** derived from reading `UpdateZelda` (`src/Z_04.asm`), not
from observing it in-game.

## The ending fanfare starts much sooner

**Code:** `AOUZKPEA`

**Effect:** The pause between reaching Zelda and the closing scene drops from
`$80` frames to `$10`.

**How it works:** `UpdateZelda` (`src/Z_04.asm:9620`) arms the delay as it
hands off to state 1:

```
    ; Set a delay of $80 frames at the beginning of the next state.
    LDA #$80
    STA ObjTimer, X
```

This patches the immediate at bank 4 CPU `$A9B4` (originally `$80`) to `$10`.
Raw form: `$A9B4:10:80`. No other PRG bank holds `$80` at that `$8000`-window
offset.

**Caveat — cosmetic only.** The music request (`SongRequest = $06`) is issued
before the timer is set, so the fanfare itself still starts at the same moment;
what shortens is the wait before the rest of the ending sequence runs.

**Not live-verified:** derived from reading `UpdateZelda` (`src/Z_04.asm`), not
from observing it in-game.

## Lamnolas nearly always turn straight at Link

**Code:** `ENUXUZEA`

**Effect:** A Lamnola head aims at Link on about 94% of its turn decisions
instead of 50%, so the chains home in instead of snaking around.

**How it works:** `Lamnola_UpdateHead` (`src/Z_04.asm:9845`) flips a coin at
each turn opportunity:

```
    ; There's a 50% chance of going to try to turn toward Link.
    LDA Random, X
    CMP #$80
    BCC @TurnTowardLink
```

This patches the `CMP` operand at bank 4 CPU `$AABB` (originally `$80`) to
`$F0`. Raw form: `$AABB:F0:80`. The `BCC` fires when the random byte is below
the operand, so raising it is what increases the chase. No other PRG bank holds
`$80` at that `$8000`-window offset.

**Caveat — the second coin flip is a different byte.** The `CPY #$80` at
`$AAC7`, which decides whether to keep going straight when the first roll fails,
is untouched.

**Caveat — walls still win.** The chosen direction is still validated against
the room tiles, so a Lamnola aiming at Link through a wall keeps going straight.

**Not live-verified:** derived from reading `Lamnola_UpdateHead`
(`src/Z_04.asm`), not from observing it in-game.

## Patra almost always chases

**Code:** `GEKZOLAG`

**Effect:** Patra's body picks the chase state on about 98% of its decisions
instead of 75%, so it bears down on Link rather than wandering.

**How it works:** `Flyer_PatraDecideState` (`src/Z_04.asm:10098`) rolls for the
next flying state:

```
    ; Go to the next state randomly:
    ; Random >= $40: 2
    ; Else:          3
    ;
    ; Set up 8 turns.
    LDY #$02
    LDA Random, X
    CMP #$40
    BCS :+
    INY
:
```

This patches the `CMP` operand at bank 4 CPU `$ABC1` (originally `$40`) to
`$04`. Raw form: `$ABC1:04:40`. State 2 is the chase state, and the `BCS` keeps
`Y` at 2 when the random byte is at or above the operand — so *lowering* the
operand is what increases chasing. No other PRG bank holds `$40` at that
`$8000`-window offset.

**Note on the direction.** The backlog suggested `$F0`, which would have had
the opposite effect: the comment reads "Random >= `$40`: 2", so a higher
threshold means state 2 is chosen less often.

**Not live-verified:** derived from reading `Flyer_PatraDecideState`
(`src/Z_04.asm`), not from observing it in-game.

## Patra's inner ring orbits more than twice as wide

**Code:** `ATEXOKGZ`

**Effect:** The Patra 1 variant's children start their orbit `$60` pixels out
instead of `$2C`, so the ring is far larger than the body it guards.

**How it works:** `UpdatePatraChild` (`src/Z_04.asm:10186`) picks the orbit
radius from the child's object type:

```
    ; If patra child type = $25, then the radius of its orbit is $2C.
    ; Else use radius $18. Store the chosen value in [00].
    LDA #$2C
    LDY ObjType, X
    CPY #$25
    BEQ :+
    LDA #$18
:
    STA $00
```

This patches the first immediate at bank 4 CPU `$AC09` (originally `$2C`) to
`$60`. Raw form: `$AC09:60:2C`. No other PRG bank holds `$2C` at that
`$8000`-window offset.

**Caveat — only the type `$25` variant changes.** The `$18` radius used by the
other Patra child type sits at `$AC0F` and is a separate code, so in a Patra 2
room nothing looks different.

**Caveat — this is the *initial* placement.** The radius here seeds the child's
starting coordinates; the ongoing rotation is driven separately in
`PatraChild_State1`, so the ring will settle into whatever shape that produces.

**Not live-verified:** derived from reading `UpdatePatraChild`
(`src/Z_04.asm`), not from observing it in-game.

## Patra's children whirl more than twice as fast

**Code:** `EYUZXGAY`

**Effect:** The Patra 1 children sweep around their orbit at roughly one angle
step per frame instead of a little under half a step, completing a revolution
in about a third of the time.

**How it works:** `PatraChild_State1` (`src/Z_04.asm:10224`) picks the
per-frame angle decrement from the child's type:

```
    ; If the monster is type $25 Patra Child1, then decrease the
    ; monster's angle by $70, else by $60 to go slower.
    LDA #$70
    LDY ObjType, X
    CPY #$25
    BEQ :+
    LDA #$60
:
    JSR DecreaseObjectAngle
```

`DecreaseObjectAngle` (`src/Z_04.asm:12025`) subtracts this as the low byte of
a 16-bit angle whose high byte is masked to `$1F` — 32 positions around the
circle. This patches the first immediate at bank 4 CPU `$AC32` (originally
`$70`) to `$F0`. Raw form: `$AC32:F0:70`. No other PRG bank holds `$70` at that
`$8000`-window offset.

**Note on the direction.** The backlog suggested `$20`. That is a *smaller*
per-frame decrement, so it would slow the ring down, not speed it up. `$F0` is
the value that matches the stated intent.

**Caveat — only the type `$25` variant changes.** The `$60` used by the other
child type is at `$AC38` and is a separate code.

**Not live-verified:** derived from reading `PatraChild_State1` and
`DecreaseObjectAngle` (`src/Z_04.asm`), not from observing it in-game.

## A wooden arrow kills Ganon — and a silver one no longer does

**Code:** `PAUZNYZA`

**Effect:** The inventory check that guards Ganon's killing blow asks for the
wooden arrow instead of the silver one, so the plain bow finishes the fight.

**How it works:** `Ganon_CheckCollisions`'s `@CheckArrowCollision` path
(`src/Z_04.asm:10877`) gates everything on the arrow you own:

```
@CheckArrowCollision:
    ; If the silver arrow is not in the inventory, then return.
    LDA InvArrow
    CMP #$02
    BNE @Exit
```

This patches the `CMP` operand at bank 4 CPU `$AF37` (originally `$02`) to
`$01`. Raw form: `$AF37:01:02`. `InvArrow` is 0 for none, 1 for wooden, 2 for
silver. No other PRG bank holds `$02` at that `$8000`-window offset.

**Caveat — this is an equality test, so it swaps rather than widens.** With
`$01` in place, owning the silver arrow (`InvArrow = 2`) fails the `BNE` and
Ganon becomes unkillable. Use this code with the wooden bow only, or turn it
off once you pick up the silver arrow.

**Caveat — the rest of the sequence is unchanged.** Ganon still has to be in
his brown, stunned phase with an arrow actually in flight
(`ObjState` of slot `$12` equal to `$10`) for the hit to land; this code only
changes which arrow the inventory test accepts.

**Not live-verified:** derived from reading `Ganon_CheckCollisions`
(`src/Z_04.asm`), not from observing it in-game.

## Ganon takes far fewer sword hits per cycle

**Code:** `ALOZNYEY`

**Effect:** Each time Ganon is beaten down and turns brown, his HP is restored
to `$30` instead of `$F0`, so every subsequent cycle takes a fraction of the
sword hits.

**How it works:** `Ganon_CheckCollisions` (`src/Z_04.asm:10847`) intercepts the
death that the ordinary collision rules would have caused:

```
    ; If Ganon has died according to the usual collision check rules
    ; (HP = 0), then:
    ; 1. Restore HP to the initial value $F0
    ; 2. Set state to $FF to note that Ganon is vulnerable to silver arrows
    ; 3. Change palette row 7 to make Ganon brown
    LDA ObjMetastate, X
    BEQ @CheckHarmed
    LDA #$F0
    STA ObjHP, X
```

This patches the immediate at bank 4 CPU `$AF17` (originally `$F0`) to `$30`.
Raw form: `$AF17:30:F0`. No other PRG bank holds `$F0` at that `$8000`-window
offset.

**Caveat — the first knockdown is unaffected.** Ganon's starting HP comes from
the object attribute tables, not from here; this byte only supplies the value
on each *restore*.

**Not live-verified:** derived from reading `Ganon_CheckCollisions`
(`src/Z_04.asm`), not from observing it in-game.

## Ganon stays visible four times as long after a hit

**Code:** `NYXXOYAK`

**Effect:** A successful sword hit leaves Ganon on screen for `$FF` frames
instead of `$40`, so he spends most of the fight visible rather than blinking
in and out.

**How it works:** `Ganon_CheckCollisions` (`src/Z_04.asm:10858`) sets the
visibility window when Ganon is harmed:

```
@CheckHarmed:
    ; If Ganon was harmed, then play the sound effect
    ; and set timer to $40, so that he's visible for $40 frames.
    LDA ObjInvincibilityTimer, X
    BEQ @UndoDeath
    JSR PlayBossHitCryIfNeeded
    LDA #$40
    STA ObjTimer, X
```

This patches the immediate at bank 4 CPU `$AF29` (originally `$40`) to `$FF`.
Raw form: `$AF29:FF:40`. No other PRG bank holds `$40` at that `$8000`-window
offset.

**Caveat — a nonzero timer also blocks the sword check.** The routine begins
with `LDA ObjTimer, X / BNE @Exit`, so while Ganon is visible he cannot be hit
again. Stretching the window makes him easier to *see* and harder to *hurt*.

**Not live-verified:** derived from reading `Ganon_CheckCollisions`
(`src/Z_04.asm`), not from observing it in-game.

## Ganon fires eight times as often

**Code:** `YAXZKSYL`

**Effect:** Ganon throws a fireball every 8 frames instead of every `$40`.

**How it works:** `Ganon_MoveAndShoot` (`src/Z_04.asm:10443`) gates the shot on
the global frame counter:

```
    ; Shoot every $40 frames.
    LDA FrameCounter
    AND #$3F
    BNE @Exit
    LDA #$56                    ; Fireball
    JSR ShootFireball
```

This patches the `AND` mask at bank 4 CPU `$AD24` (originally `$3F`) to `$07`.
Raw form: `$AD24:07:3F`. It stays a contiguous low-bits mask, so the "every N
frames" reading holds. No other PRG bank holds `$3F` at that `$8000`-window
offset.

**Caveat — `ShootFireball` has its own slot limit.** The number of fireballs
actually in flight is bounded by the free object slots, so beyond a point the
extra attempts are simply dropped.

**Not live-verified:** derived from reading `Ganon_MoveAndShoot`
(`src/Z_04.asm`), not from observing it in-game.

## Ganon's fireballs become blockable

**Code:** `IIXXEITI`

**Effect:** Ganon shoots ordinary fireballs that Link's shield can deflect
instead of the unblockable type.

**How it works:** `Ganon_MoveAndShoot` (`src/Z_04.asm:10447`) chooses the
projectile type:

```
    LDA #$56                    ; Fireball
    JSR ShootFireball
```

This patches the immediate at bank 4 CPU `$AD28` (originally `$56`) to `$55`,
the blockable fireball type. Raw form: `$AD28:55:56`. Both ids come from
`UpdateObject_JumpTable` (`src/Z_07.asm:5321`). No other PRG bank holds `$56`
at that `$8000`-window offset.

**Caveat — the shield still has to be facing the shot.** Blockable only means
the normal shield rules apply; it does not make Ganon's fireballs harmless.

**Not live-verified:** derived from reading `Ganon_MoveAndShoot`
(`src/Z_04.asm`) and `UpdateObject_JumpTable` (`src/Z_07.asm`), not from
observing it in-game.

## The Ganon intro is much shorter

**Code:** `AOUZKGEG`

**Effect:** The scripted pause at the start of the Ganon fight drops from `$C0`
frames to `$10`.

**How it works:** `Ganon_ScenePhase0` (`src/Z_04.asm:10334`) arms Link's timer
as it hands off to the next scene phase:

```
    ; Set Link's timer to $C0 for the next scene phase.
    LDA #$C0
    STA ObjTimer

    ; Set scene phase 1, and go draw Ganon.
    INC Ganon_ScenePhase
```

This patches the immediate at bank 4 CPU `$ACB4` (originally `$C0`) to `$10`.
Raw form: `$ACB4:10:C0`. No other PRG bank holds `$C0` at that `$8000`-window
offset.

**Caveat — the timer belongs to Link, not Ganon.** The store is to `ObjTimer`
(slot 0), so the shortened wait is Link's paralysis; the fade cycle that gates
entry into this branch is unchanged.

**Not live-verified:** derived from reading `Ganon_ScenePhase0`
(`src/Z_04.asm`), not from observing it in-game.

## Ganon's death burst blows out six times wider

**Code:** `ALSZNNAA`

**Effect:** The ring of dust that scatters when the silver arrow lands starts
`$30` pixels out instead of `$08`, so the death burst begins already spread
across the room.

**How it works:** `Ganon_CheckCollisions` (`src/Z_04.asm:10903`) seeds the
cloud radius when the killing arrow connects:

```
    ; Set initial cloud distance 8.
    LDA #$08
    STA Ganon_ObjCloudDist, X
    RTS
```

This patches the immediate at bank 4 CPU `$AF57` (originally `$08`) to `$30`.
Raw form: `$AF57:30:08`. No other PRG bank holds `$08` at that `$8000`-window
offset.

**Caveat — purely cosmetic, and it runs out sooner.** The distance grows from
this seed toward a fixed limit, so starting further out also means the
animation reaches its end faster.

**Not live-verified:** derived from reading `Ganon_CheckCollisions`
(`src/Z_04.asm`), not from observing it in-game.

## Darknuts drop from the Octorock table

**Code:** `GAXLZAYE`

**Effect:** Object type `$0C` — the second Darknut variant — takes object type
`$07`'s place in drop group 0, so Darknuts drop group-0 items while that
Octorock variant falls through to the default group 3.

**How it works:** `SetUpDroppedItem` (`src/Z_04.asm:11069`) searches three
membership lists to decide which row of `DropItemTable` a dead monster uses:

```
DropItemMonsterTypes0:
    .BYTE $07, $08, $0E, $04, $0F, $23
```

```
    ; Look for object type in array of 6. These use drop item table row 0.
    LDY #$05

@FindDrop0Type:
    CMP DropItemMonsterTypes0, Y
    BEQ @Found                  ; If found, use row 0.
    DEY
    BPL @FindDrop0Type
```

This patches byte 0 of the group-0 list at bank 4 CPU `$B022` (originally
`$07`) to `$0C`. Raw form: `$B022:0C:07`. Both ids are entries in
`UpdateObject_JumpTable` (`src/Z_07.asm:5321`): `$07` is one of the four
Octorock variants and `$0C` is the second of the two Darknut variants. No other
PRG bank holds `$07` at that `$8000`-window offset.

**Caveat — this is a swap, so two monsters change at once.** Type `$0C` is not
in any of the three lists today, so it currently falls through to row 3;
type `$07` moves the other way. Along with the row, the *drop chance* changes:
`DropItemRates` is `$50, $98, $68, $68`, so group 0 drops about 31% of the time
and group 3 about 41%.

**Caveat — the other Octorock variants are unaffected.** Types `$08`, `$09` and
`$0A` keep their existing groups; only `$07` moves.

**Not live-verified:** derived from reading `SetUpDroppedItem`,
`DropItemMonsterTypes0` and `DropItemRates` (`src/Z_04.asm`) and
`UpdateObject_JumpTable` (`src/Z_07.asm`), not from observing it in-game.

## Dungeon monsters drop from the overworld table

**Code:** `AAUULEZA`

**Effect:** Group-1 monsters — Ropes, Stalfos, Wallmasters, Zols, Pols Voice,
Red Leevers, Tektites and boulders — read row 0 of the drop table instead of
row 1, so they stop dropping the items unique to their own row.

**How it works:** `SetUpDroppedItem` (`src/Z_04.asm:11135`) indexes the drop
table by group:

```
; Multiples of $A to index the base of each row of items in DropItemTable.
;
DropItemSetBaseOffsets:
    .BYTE $00, $0A, $14, $1E
```

```
    ; Look up the base offset of the row in the drop item table.
    ; Add it and WorldKillCycle to look up the dropped item for
    ; this object type and store it in [00].
    LDY $01
    LDA DropItemSetBaseOffsets, Y
    CLC
    ADC WorldKillCycle
    TAY
    LDA DropItemTable, Y
```

This patches byte 1 at bank 4 CPU `$B03B` (originally `$0A`) to `$00`. Raw
form: `$B03B:00:0A`. Group 1 now shares group 0's row. No other PRG bank holds
`$0A` at that `$8000`-window offset.

**Caveat — `$00` is still a legal multiple of `$A`.** Rows are ten entries
wide and `WorldKillCycle` supplies the column, so this stays inside row 0 and
never reads across a row boundary. An offset that is *not* a multiple of `$A`
would straddle rows — legal, but not what this code does.

**Caveat — you lose the group-1-only drops.** Row 1 (`$0F, $18, $22, $18, $0F,
$22, $21, $18, $18, $18`) is the only row containing item id `$21`, which
`ItemIdToSlot` (`src/Z_01.asm:4318`) maps to the `InvClock` slot. Row 0
(`$22, $18, $22, $18, $23, $18, $22, $22, $18, $18`) has no `$21` and no `$0F`,
but does carry a `$23` — the fairy — in its fifth column.

**Caveat — the drop *rate* does not move.** `DropItemRates` is indexed by group,
not by row, so group 1 keeps its `$98` chance; only what it rolls up changes.

**Not live-verified:** derived from reading `SetUpDroppedItem`,
`DropItemSetBaseOffsets` and `DropItemTable` (`src/Z_04.asm`), not from
observing it in-game.

## The pity fairy arrives after four kills instead of sixteen

**Code:** `GEKLAAAP`

**Effect:** The free fairy that normally shows up on the sixteenth kill without
taking damage now appears on the fourth.

**How it works:** `SetUpDroppedItem` (`src/Z_04.asm:11145`) short-circuits the
whole drop calculation at one exact kill count:

```
    ; If the global kill count = $10, set the dropped item to a fairy.
    LDA #$23
    LDY WorldKillCount
    CPY #$10
    BEQ @SetHelpItem
```

This patches the `CPY` operand at bank 4 CPU `$B0C0` (originally `$10`) to
`$04`. Raw form: `$B0C0:04:10`. `WorldKillCount` is incremented by
`HandleMonsterDied` (`src/Z_01.asm:5998`) and reset to zero whenever Link takes
damage (`src/Z_01.asm:5761`), so this is a run of unhurt kills. No other PRG
bank holds `$10` at that `$8000`-window offset.

**Caveat — it is an equality test, not a threshold.** The fairy appears on
exactly the fourth kill of a run and not again until the counter is reset by
taking damage and rebuilt. Killing five monsters without being touched gets you
one fairy, not two.

**Not live-verified:** derived from reading `SetUpDroppedItem`
(`src/Z_04.asm`) and `HandleMonsterDied` (`src/Z_01.asm`), not from observing it
in-game.

## The pity fairy becomes a Heart Container

**Code:** `ZOUULALX`

**Effect:** The guaranteed drop at the sixteenth unhurt kill is item `$1A`, the
Heart Container, instead of the fairy.

**How it works:** `SetUpDroppedItem` (`src/Z_04.asm:11145`) loads the item id
just above the kill-count test, and the same register also serves the
help-drop path below:

```
    ; If the global kill count = $10, set the dropped item to a fairy.
    LDA #$23
    LDY WorldKillCount
    CPY #$10
    BEQ @SetHelpItem
```

This patches the immediate at bank 4 CPU `$B0BB` (originally `$23`) to `$1A`.
Raw form: `$B0BB:1A:23`. No other PRG bank holds `$23` at that `$8000`-window
offset.

**Caveat — the fairy-specific setup is skipped, correctly.** `@Commit` ends
with `CMP #$23 / BNE :+ / JMP SetUpFairyObject`; with `$1A` in `[00]` that test
fails and the item is committed as an ordinary pickup, which is what a Heart
Container should be.

**Caveat — this makes the game much easier.** A Heart Container every sixteen
unhurt kills raises Link's maximum hearts without bounds.

**Not live-verified:** derived from reading `SetUpDroppedItem`
(`src/Z_04.asm`), not from observing it in-game.

## Guaranteed drops kick in five times sooner

**Code:** `ZEKLTEZA`

**Effect:** A drop is guaranteed after two kills instead of ten, so roughly
every other monster leaves an item.

**How it works:** `SetUpDroppedItem` (`src/Z_04.asm:11152`) uses the help
counter to decide between a guaranteed item and the ordinary random roll:

```
    ; If help drop counter < $A, then use the dropped item ID as is.
    ; But there is a random chance that the item drop will be canceled.
    LDA HelpDropCount
    CMP #$0A
    BCC @RandomlyCancel

    ; Otherwise, the item will be guaranteed to be made.
```

This patches the `CMP` operand at bank 4 CPU `$B0C6` (originally `$0A`) to
`$02`. Raw form: `$B0C6:02:0A`. `HelpDropCount` is incremented on every monster
death by `HandleMonsterDied` (`src/Z_01.asm:6000`) and reset to zero both when
Link takes damage and whenever a guaranteed item is handed out. No other PRG
bank holds `$0A` at that `$8000`-window offset.

**Caveat — the item is almost always 5 rupees.** `HelpDropValue`, which chooses
bomb over rupees, is only set when `HelpDropCount` reaches `$0A` *and* the
killing blow was a bomb (`src/Z_01.asm:6008`). That test is in bank 1 and is not
patched, so at a threshold of `$02` the guaranteed drop is the rupee case
nearly every time.

**Caveat — the `$A` cap in bank 1 is a different byte.** `HandleMonsterDied`
still stops counting at `$0A`; only the reader moved.

**Not live-verified:** derived from reading `SetUpDroppedItem` (`src/Z_04.asm`)
and `HandleMonsterDied` (`src/Z_01.asm`), not from observing it in-game.

## The guaranteed drop is a fairy instead of rupees

**Code:** `LXKUZEYA`

**Effect:** When the help counter grants a guaranteed drop, it produces a fairy
rather than the usual five rupees.

**How it works:** `SetUpDroppedItem` (`src/Z_04.asm:11158`) picks between two
help items:

```
    ; Otherwise, the item will be guaranteed to be made.
    ; [51] HelpDropValue determines which kind:
    ; - 0:     5 rupees
    ; - other: bomb
    LDA #$0F
    LDY HelpDropValue
    BEQ @SetHelpItem
    LDA #$00                    ; Bomb
```

This patches the rupee immediate at bank 4 CPU `$B0CA` (originally `$0F`) to
`$23`, the fairy id named in the comment just above the kill-count test. Raw
form: `$B0CA:23:0F`. No other PRG bank holds `$0F` at that `$8000`-window
offset.

**Caveat — the fairy setup does run.** `@Commit` re-tests `CMP #$23` and jumps
to `SetUpFairyObject`, so the substituted item is initialised as a proper
moving fairy rather than a static pickup.

**Caveat — the bomb branch is untouched.** The `LDA #$00` at `$B0D0` still
supplies a bomb when `HelpDropValue` is nonzero, which is the case after ten
kills whose last blow was a bomb.

**Not live-verified:** derived from reading `SetUpDroppedItem`
(`src/Z_04.asm`), not from observing it in-game.

## Dropped items vanish almost at once

**Code:** `AXVLIENY`

**Effect:** An item dropped by a monster lasts about a second instead of about
eight and a half, so most drops disappear before Link can reach them.

**How it works:** `SetUpDroppedItem`'s `@Commit` path (`src/Z_04.asm:11183`)
stamps the lifetime onto the new item object:

```
@Commit:
    ; Set ObjItemLifetime to $FF.
    LDA #$FF
    STA Item_ObjItemLifetime, X
```

This patches the immediate at bank 4 CPU `$B0E5` (originally `$FF`) to `$20`.
Raw form: `$B0E5:20:FF`. `UpdateItem` decrements the lifetime every other
frame, so `$FF` is roughly 510 frames and `$20` roughly 64.

**Caveat — not bank-unique, and badly so.** Banks 0, 2, 3 and 6 all hold `$FF`
at this `$8000`-window offset, so this code fires in five banks rather than
one. `$FF` is one of the most common bytes in the ROM; expect unrelated
side effects whenever another bank is mapped in over `$B0E5`. Of the codes in
this pass this is the one most likely to misbehave.

**Caveat — room items are unaffected.** Only monster drops go through
`SetUpDroppedItem`; items placed by the room data have no lifetime.

**Not live-verified:** derived from reading `SetUpDroppedItem`
(`src/Z_04.asm`), not from observing it in-game.

## Can't walk off the north edge of an overworld screen

**Code:** `AESNYEIL`

**Effect:** In the overworld, walking up to the top of a screen no longer
scrolls to the screen above — Link just stops at the top wall. Every other
direction still works, so you can only travel north by going around.

**How it works:** `CheckScreenEdge` (`src/Z_07.asm`) compares Link's
coordinate against `PlayerScreenEdgeBounds` and only starts the room change
on an exact match:

```
PlayerScreenEdgeBounds:
    .BYTE $3D, $DD, $00, $F0     ; up, down, left, right

    ; If Link's coordinate does not match the screen edge coordinate
    ; in the single moving direction, then return.
    LDA $00
    CMP PlayerScreenEdgeBounds, Y
    BNE ExitX0
```

The table is indexed by the reverse-direction index from `GetOppositeDir`
(up=0, down=1, left=2, right=3). This patches byte 0 at bank 7 CPU `$F0DF`
(originally `$3D`) to `$00`. Raw form: `$F0DF:00:3D`. Link's Y never reaches
`$00` — `BoundByRoom` stops him at the top wall well before that — so the
comparison never fires and the north transition never happens.

**Caveat — bank-unique by construction.** `$C000`-`$FFFF` is the fixed bank 7
window, so no other bank can be mapped in at this address.

**Caveat — overworld only.** Underworld room changes go through
`CheckDoorway`, not `CheckScreenEdge`, and Link's Y in a dungeon room never
reaches these values anyway.

**Not live-verified:** derived from reading `CheckScreenEdge`
(`src/Z_07.asm`), not from observing it in-game.

## Overworld screens scroll when you reach the middle going east

**Code:** `EEVYZAEY`

**Effect:** Walking right, the screen changes as soon as Link reaches the
horizontal centre of the screen instead of the right-hand edge. The right
half of every overworld screen becomes unreachable from the left, so the
overworld is effectively half as wide going east. Walking back west still
uses the normal left edge, so you can re-enter a screen and stand in the
half you couldn't walk into.

**How it works:** the same `PlayerScreenEdgeBounds` table read by
`CheckScreenEdge` (`src/Z_07.asm`). This patches byte 3 — the "right" entry —
at bank 7 CPU `$F0E2` (originally `$F0`) to `$80`. Raw form: `$F0E2:80:F0`.
`$80` is a multiple of 8, and `CheckScreenEdge` only runs when Link's grid
offset is 0 (every 8 pixels), so the exact-match comparison still lands.

**Caveat — bank-unique by construction.** Bank 7's window is fixed.

**Caveat — the destination is unchanged.** The room-id arithmetic
(`NextRoomIdOffsets`) is untouched, so you still arrive at the correct
neighbouring screen — just from a different starting position.

**Not live-verified:** derived from reading `CheckScreenEdge`
(`src/Z_07.asm`), not from observing it in-game.

## Bait lasts about three times as long

**Code:** `AEUYZGLE`

**Effect:** Dropped Bait sits on the ground for roughly 2000 frames (about 34
seconds) instead of about 765 frames (13 seconds).

**How it works:** `UpdateBoomerangOrFood` (`src/Z_07.asm`) uses the food
object's minor state purely as a way to chain timers:

```
    ; Nothing changes between the states. So, they are used as
    ; a way to extend the timer. $2FD screen frames in total.
    LDA ObjTimer, X
    BNE @CheckMonsterType
    INC ObjState, X
    LDA ObjState, X
    AND #$0F
    CMP #$03
    BEQ @Deactivate
    LDA #$FF
    STA ObjTimer, X
```

Food starts in state `$80`; each time its `$FF`-frame timer expires the state
increments, and the object is deactivated once the low nibble reaches 3. This
patches the `CMP` operand at bank 7 CPU `$F4B2` (originally `$03`) to `$08`,
so it takes eight `$FF`-frame stretches to expire instead of three. Raw form:
`$F4B2:08:03`.

**Caveat — bank-unique by construction.** Bank 7's window is fixed.

**Caveat — Grumble still eats it instantly.** `UpdateGrumble1`
(`src/Z_01.asm`) only checks that a food object exists in slot `$F`; the
longer lifetime doesn't change that exchange.

**Not live-verified:** derived from reading `UpdateBoomerangOrFood`
(`src/Z_07.asm`), not from observing it in-game.

## Bait attracts nearly every kind of monster

**Code:** `AXKYPKLA`

**Effect:** Bait pulls in far more monster types than usual. Normally only
rooms whose template monster is one of a short list (moblins through the
types just below Red Darknut, plus Vire and the two Keese) chase the food;
this widens that list to almost every monster type in the game.

**How it works:** `UpdateBoomerangOrFood` (`src/Z_07.asm`) decides whether the
food overrides the chase target for the room:

```
@CheckMonsterType:
    ; If the template object type in the room is one of:
    ; moblin, goriya, octorock, vire, keese
    ; then attract these monsters to the food.
    ;
    ; They will chase the food instead of Link when given a chance.
    LDA RoomObjTemplateType
    CMP #$03                    ; Blue moblin
    BCC @Draw
    CMP #$0B                    ; Red darknut
    BCC @AttractMonsters
```

`@AttractMonsters` stores the food's position into `ChaseTargetX`/
`ChaseTargetY`. The main loop (`src/Z_07.asm`, `@CheckChaseTarget`) writes
Link's position there every frame, and `UpdateBoomerangOrFood` runs
afterwards in weapon slot `$0F`, so the food's write wins. This patches the
upper-bound operand at bank 7 CPU `$F4C1` (originally `$0B`) to `$20`, so
every template type from `$03` to `$1F` qualifies. Raw form: `$F4C1:20:0B`.

**Caveat — bank-unique by construction.** Bank 7's window is fixed.

**Caveat — only chasers respond.** The patch just makes the food own the
chase target; a monster type in the widened range still has to be one whose
AI in `src/Z_04.asm` reads `ChaseTargetX`/`ChaseTargetY` (the wanderers and
walkers do; stationary and pattern-driven bosses do not).

**Caveat — it's the room's template type, not each monster.** `RoomObjTemplateType`
is one value for the whole room, so this is decided per room.

**Not live-verified:** derived from reading `UpdateBoomerangOrFood`
(`src/Z_07.asm`), not from observing it in-game.

## Sword beams and Magical Rod shots crawl

**Code:** `AZKYXAEG`

Tags: `demo-ready` `play-start` `curated`

**Effect:** The beam thrown by a full-health sword travels at about a quarter
of its normal speed — slow enough to watch it drift across the room. The
Magical Rod's shot is unaffected.

**How it works:** `SetUpWeaponWithState` (`src/Z_07.asm`) picks the shot's
speed from its state's high bit:

```
@ChooseSpeed:
    ; If high bit of state is set, use $A0 else $C0 for the q-speed fraction.
    ;
    ; The high bit is set for magic shot, and reset for sword shot.
    LDY #$C0
    LDA ObjState, X
    ASL
    BCC :+
    LDY #$A0
:
    TYA
    STA ObjQSpeedFrac, X
```

`ObjQSpeedFrac` is a quarter-speed fraction applied four times per frame by
`MoveObject`, so `$C0` is 3 pixels a frame. This patches the sword-shot
default at bank 7 CPU `$F842` (originally `$C0`) to `$20` — half a pixel a
frame. Raw form: `$F842:20:C0`.

**Caveat — bank-unique by construction.** `$C000`-`$FFFF` is bank 7's fixed
window.

**Caveat — the rod keeps its speed.** The `$A0` magic-shot value at `$F846`
is a separate byte and is untouched, so only sword beams slow down.

**Caveat — the spreading shot is unaffected.** Once a beam hits something,
`SetShotSpreadingState`/`SpreadShot` drive the four corner pieces from their
own offsets rather than `ObjQSpeedFrac`.

**Not live-verified:** derived from reading `SetUpWeaponWithState`
(`src/Z_07.asm`), not from observing it in-game.

## Can't collide with flames from the Candle or Magic Book

**Code:** `AENYUETA`

**Effect:** Link can stand in his own Candle (or Book of Magic) flame without
being shoved or taking damage. The flame still burns bushes and still hurts
monsters.

**How it works:** `UpdateFire`'s draw-and-collide tail (`src/Z_07.asm`) tests
Link against the flame with an explicit radius:

```
    ; If the objects don't collide (< $E pixels in X and Y), then return.
    LDY $00
    LDX #$00
    LDA #$0E
    JSR DoObjectsCollide
    BEQ L1F91D_Exit
```

Only if that test passes does the code fall through to `BeginShove` and the
`$80`-point `Link_BeHarmed` call below it. This patches the radius operand at
bank 7 CPU `$F8F3` (originally `$0E`) to `$00`. Raw form: `$F8F3:00:0E`.
`DoObjectsCollide` compares each axis distance against the value in A, so a
radius of zero can only match when the two centre points are numerically
identical on both axes — and both are computed through the same
`GetWideObjectMiddle` offset, so in practice the test stops firing.

**Caveat — bank-unique by construction.** Bank 7's window is fixed.

**Caveat — monsters are unaffected.** Monster damage from fire is handled by
the shared weapon-collision code, not by this player-only test.

**Caveat — an exact-overlap hit is still possible in principle.** A zero
radius is "distance must be 0", not "never"; if Link's and the flame's centre
coordinates ever coincide exactly on both axes, the hit still lands.

**Not live-verified:** derived from reading `UpdateFire`
(`src/Z_07.asm`), not from observing it in-game.

## Boomerang overshoots much further before turning back

**Code:** `AGVNIIAP`

**Effect:** When the boomerang reaches the end of its throw it coasts four
times as far before slowing to a stop and heading home, so throws reach much
deeper into a room.

**How it works:** `UpdateArrowOrBoomerang` (`src/Z_07.asm`) switches the
boomerang from "fly out" to "slow down" and reuses `ObjMovingLimit` as the
timer for that phase:

```
@CompareLimit:
    ; If it reached the limit, set state $20 and a new movement
    ; limit of $10, and go handle the rest as if blocked.
    ; ...
    ; In major state $30, ObjMovingLimit is a timer to change the state to $40.
    CMP ObjMovingLimit, X
    BCC @AnimateBoomerang
    LDA #$10
    STA ObjMovingLimit, X
```

State `$3x` (`CheckState30`) then moves the boomerang one pixel a frame and
decrements that timer until it hits zero. This patches the new limit at bank 7
CPU `$F56D` (originally `$10`) to `$40`. Raw form: `$F56D:40:10`.

**Caveat — bank-unique by construction.** Bank 7's window is fixed.

**Caveat — monsters' boomerangs too.** Goriyas' boomerangs run through the
same routine, so theirs also overshoot further.

**Caveat — room bounds still apply.** `BoundByRoom` stops the boomerang at a
wall regardless, so the extra travel only shows in open space.

**Not live-verified:** derived from reading `UpdateArrowOrBoomerang`
(`src/Z_07.asm`), not from observing it in-game.

## Boomerang takes far longer to come back

**Code:** `EAUYTTAZ`

**Effect:** After the boomerang turns around it spends four times as long in
its slow return phase before speeding up, so it hangs in the air much longer
and Link waits noticeably longer to catch it and throw again.

**How it works:** the return is split into a slow half-speed phase (state
`$40`) and a full-speed one (state `$50`). `CheckState30` (`src/Z_07.asm`)
sets the timer for the slow phase:

```
@SetState40:
    ; Set state $40, and a time to move of $20 frames.
    ;
    ; In major state $40, ObjMovingLimit is a timer to change the state to $50.
    LDA #$20
    STA ObjMovingLimit, X
    LDA #$40
    STA ObjState, X
```

`SetBoomerangSpeed` (`src/Z_01.asm`) halves the speed while the state is `$40`
and decrements that timer each move, promoting the boomerang to `$50` when it
reaches zero. This patches the timer at bank 7 CPU `$F636` (originally `$20`)
to `$80`. Raw form: `$F636:80:20`.

**Caveat — bank-unique by construction.** Bank 7's window is fixed.

**Caveat — it still homes in.** The return path tracks the thrower's current
position, so a long slow return follows Link around rather than missing him.

**Caveat — Link can't throw again until he catches it.** The extra delay
directly limits how often the boomerang can be used.

**Not live-verified:** derived from reading `CheckState30` and
`SetBoomerangSpeed` (`src/Z_07.asm`, `src/Z_01.asm`), not from observing it
in-game.

## The door-repair old man charges nothing

**Code:** `AEOAEAGP`

**Effect:** Walking into one of the "PAY ME FOR THE DOOR REPAIR CHARGE" caves
costs 0 rupees instead of 20. The text still appears; your wallet just doesn't
move.

**How it works:** `UpdateCavePersonState_TalkOrShopOrDoorCharge`
(`src/Z_01.asm`) special-cases cave type `$71`:

```
    ; If this is not the "door charge" old man, then return.
    ; The person only talks.
    LDA ObjType+1
    CMP #$71
    BNE @Exit

    ; Post 20 rupees to subtract.
    LDA RupeesToSubtract
    CLC
    ADC #$14
    STA RupeesToSubtract
```

`World_ChangeRupees` (`src/Z_01.asm`) drains `RupeesToSubtract` one rupee every
other frame. This patches the amount at bank 1 CPU `$8890` (originally `$14`)
to `$00`. Raw form: `$8890:00:14`.

**Caveat — bank-unique.** No other PRG bank holds `$14` at this `$8000`-window
offset.

**Caveat — the room is still flagged taken.** `SetRoomFlagUWItemState` runs
either way, so the cave still only charges (nothing) once.

**Not live-verified:** derived from reading
`UpdateCavePersonState_TalkOrShopOrDoorCharge` (`src/Z_01.asm`), not from
observing it in-game.

## Take the White Sword with no heart containers

**Code:** `AENESAAG`

**Effect:** The White Sword cave hands over the sword no matter how few heart
containers Link has, so it can be picked up straight out of the starting cave.

**How it works:** `UpdateCavePersonState_TalkOrShopOrDoorCharge`
(`src/Z_01.asm`) gates heart-requirement caves:

```
@TryToTake:
    ; ...
    ; Check heart container requirements.
    ;
    ; 5 is the minimum for cave type $6C (white sword)
    ; $C is the minimum otherwise
    LDY #$40
    LDA ObjType+1
    CMP #$6C
    BEQ :+
    LDY #$B0
:
    CPY HeartValues
    BEQ @Take
    BCC @Take
```

`HeartValues` packs the container count in its high nibble, so `$40` is 5
containers (4 plus the starting one) and `$B0` is `$C`. This patches the White
Sword threshold at bank 1 CPU `$88FD` (originally `$40`) to `$00`. Raw form:
`$88FD:00:40`. Zero is `BCC`/`BEQ` against any `HeartValues`, so the check
always passes.

**Caveat — bank-unique.** No other PRG bank holds `$40` at this
`$8000`-window offset.

**Caveat — only cave type `$6C`.** The other heart-gated cave keeps its `$B0`
threshold at `$8906`; see the next code for that one.

**Not live-verified:** derived from reading
`UpdateCavePersonState_TalkOrShopOrDoorCharge` (`src/Z_01.asm`), not from
observing it in-game.

## Take the Magical Sword with no heart containers

**Code:** `AAEAVPEL`

**Effect:** The Magical Sword cave (and any other heart-gated cave that isn't
the White Sword's) gives up its item regardless of Link's heart containers.

**How it works:** the same `@TryToTake` check as above. Cave type `$6C` uses
`$40`; everything else falls through to `LDY #$B0` — `$C` heart containers.
This patches that fallback at bank 1 CPU `$8906` (originally `$B0`) to `$00`.
Raw form: `$8906:00:B0`.

**Caveat — bank-unique.** No other PRG bank holds `$B0` at this
`$8000`-window offset.

**Caveat — the price still applies.** The heart check runs *after* the "pay"
cave flag has already debited `CavePrices`, so a heart-gated cave that also
charges rupees still charges them.

**Not live-verified:** derived from reading
`UpdateCavePersonState_TalkOrShopOrDoorCharge` (`src/Z_01.asm`), not from
observing it in-game.

## The bomb-capacity upgrade is free

**Code:** `AANAXLGT`

**Effect:** The dungeon old man who offers more bomb capacity for 100 rupees
gives it away for nothing, and will do so with an empty wallet.

**How it works:** `UpdateUnderworldPersonComplexState_SenseLink`
(`src/Z_01.asm`) checks affordability with the price in A:

```
@CheckCanPay:
    ; If rupee count < 100, then return.
    LDA #$64
    CMP InvRupees
    BEQ :+
    BCS @Exit
:
    ; Post 100 rupees more to subtract.
    CLC
    ADC RupeesToSubtract
    STA RupeesToSubtract
```

The same register both gates the purchase and supplies the amount to debit.
This patches it at bank 1 CPU `$8B72` (originally `$64`) to `$00`. Raw form:
`$8B72:00:64`. With `$00`, `CMP InvRupees` is either equal (0 rupees, takes
the `BEQ`) or borrows (any rupees, so `BCS` isn't taken) — the check always
passes — and the amount added to `RupeesToSubtract` is zero.

**Caveat — bank-unique.** No other PRG bank holds `$64` at this
`$8000`-window offset.

**Caveat — one purchase per room.** `L_Person_FlagItemTakenAndAdvanceState`
still marks the offer taken, so the same old man won't sell twice.

**Not live-verified:** derived from reading
`UpdateUnderworldPersonComplexState_SenseLink` (`src/Z_01.asm`), not from
observing it in-game.

## The bomb-capacity upgrade adds 32 bombs instead of 4

**Code:** `AXEEULGA`

**Effect:** Each bomb-capacity old man raises Link's maximum bomb count by
`$20` (32) rather than 4, and fills him to the new maximum on the spot. Two
visits push the maximum past what the status bar can show.

**How it works:** the same routine, just after the purchase is approved:

```
    ; Increase max bombs by 4, set the amount on hand to the max.
    LDA MaxBombs
    CLC
    ADC #$04
    STA MaxBombs
    STA InvBombs
```

This patches the increment at bank 1 CPU `$8B8B` (originally `$04`) to `$20`.
Raw form: `$8B8B:20:04`.

**Caveat — bank-unique.** No other PRG bank holds `$04` at this
`$8000`-window offset.

**Caveat — the count is a byte.** `MaxBombs` wraps past `$FF`; eight upgrades
would roll it back to a low value.

**Caveat — the status bar formats two digits.** `FormatDecimalCountByteInTextBuf`
(`src/Z_01.asm`) draws the bomb count into a three-character field, so counts
above 99 will read oddly.

**Not live-verified:** derived from reading
`UpdateUnderworldPersonComplexState_SenseLink` (`src/Z_01.asm`), not from
observing it in-game.

## "Take any one you want" costs no heart container

**Code:** `NYXASGAU`

**Effect:** In the life-or-money rooms, choosing the heart container never
costs Link a container or a heart — the shutters open and the offer is marked
taken, but his health is untouched.

**How it works:** `UpdateUnderworldPersonLifeOrMoneyState_2` (`src/Z_01.asm`)
decides whether to charge:

```
@PayWithHeartContainer:
    ; If the number of heart containers < 4, then
    ; - leave the number of heart containers alone
    ; - set HeartPartial to 0, so Link will die with one more hit
    ;
    ; Then go flag this offer taken.
    LDA HeartValues
    AND #$F0
    CMP #$30
    BCS @Reduce
    STA HeartValues
    LDA #$00
    STA HeartPartial
```

Only the `@Reduce` path (taken when Link has 4 or more containers) subtracts a
container and a heart. This patches the threshold at bank 1 CPU `$8C25`
(originally `$30`) to `$FF`. Raw form: `$8C25:FF:30`. `HeartValues & $F0` can
never be `>= $FF`, so `@Reduce` is never reached.

**Caveat — bank-unique.** No other PRG bank holds `$30` at this
`$8000`-window offset.

**Caveat — the low-heart path still writes.** The fall-through still stores
`HeartValues & $F0` back and clears `HeartPartial`, which rounds Link's
partial heart down — so the choice is free of containers, but can cost a
fraction of the current heart.

**Not live-verified:** derived from reading
`UpdateUnderworldPersonLifeOrMoneyState_2` (`src/Z_01.asm`), not from
observing it in-game.

## Play the money-making game with no rupees

**Code:** `AEOAVOZA`

**Effect:** The gambling caves let Link play with an empty wallet instead of
requiring 10 rupees to start. Losses still can't take him below zero, so a
broke Link can keep playing until he wins.

**How it works:** `UpdateCavePersonState_HintOrMoneyGame` (`src/Z_01.asm`)
guards the wager:

```
@HandleMoneyGame:
    ; Money game
    ;
    ; If rupees < $A, then return.
    LDA InvRupees
    CMP #$0A
    BCC L493A_Exit
```

This patches the minimum at bank 1 CPU `$8996` (originally `$0A`) to `$00`.
Raw form: `$8996:00:0A`. Any rupee count is `>= 0`, so the branch never
returns early.

**Caveat — bank-unique.** No other PRG bank holds `$0A` at this
`$8000`-window offset.

**Caveat — the payouts are unchanged.** The amounts still come from
`MoneyGameAmounts`, arranged by `InitCave` from `MoneyGameLossAmounts` and the
random permutation; only the entry requirement moves.

**Caveat — subtraction floors at zero.** `World_ChangeRupees` stops draining
once `InvRupees` reaches 0, so a loss you can't afford is simply capped.

**Not live-verified:** derived from reading
`UpdateCavePersonState_HintOrMoneyGame` (`src/Z_01.asm`), not from observing
it in-game.

## Blue Candle works as many times as you like per screen

**Code:** `AEKXVPPA`

**Effect:** The Blue Candle stops being once-per-screen. Link can light flame
after flame without leaving the room, the way the Red Candle does.

**How it works:** `WieldCandle` (`src/Z_01.asm`) only consults the
"already used" flag when the inventory holds the Blue Candle:

```
@NotInUse:
    ; If we have the blue candle and it was used, then return.
    LDA InvCandle
    CMP #$01
    BNE :+
    LDA UsedCandle
    BNE L69BE_Exit
:
    ; Set the candle used.
    LDA #$01
    STA UsedCandle
```

`InvCandle` is 1 for the Blue Candle and 2 for the Red one, which is exactly
why the Red Candle has no limit. This patches the comparison at bank 1 CPU
`$A9CE` (originally `$01`) to `$00`. Raw form: `$A9CE:00:01`. `InvCandle` is
never 0 when you are holding a candle, so the `BNE` always skips the
`UsedCandle` test.

**Caveat — this byte is copied into Save RAM before it runs.** `WieldCandle`
lives in the `BANK_01_CODE` segment (`src/Z.cfg`), which is stored in ROM at
`$A500` but *runs* from Save RAM at `$6C90` — this instruction executes at
`$715E`. `CopyCommonCodeToRam` (`src/Z_01.asm`, bank 1 CPU `$8D00`) reads the
block through the cartridge bus at `$A500`+, so the Game Genie substitution
happens during that copy and the patched byte is what ends up in RAM. The
patch therefore has to be active at boot, not just when you use the candle.

**Caveat — NOT bank-unique.** Bank 4 also holds `$01` at this `$8000`-window
offset, so this code fires there too. Watch for unrelated effects whenever
bank 4 (enemy AI) is mapped in over `$A9CE`.

**Caveat — one flame at a time still applies.** The two fire slots (`$10` and
`$11`) are still the hard limit on simultaneous flames.

**Not live-verified:** derived from reading `WieldCandle` (`src/Z_01.asm`),
not from observing it in-game.

## Candle flames shoot out four times as fast

**Code:** `EEVZKPAZ`

**Effect:** The flame from the Candle (or the Book of Magic) leaves Link at 2
pixels a frame instead of half a pixel, reaching its stopping distance almost
immediately.

**How it works:** `WieldCandle` (`src/Z_01.asm`) initialises the new fire
object's movement:

```
    ; Reset the new fire object's movement info.
    ; Set quarter speed (q-speed) to $20 (half a pixel a frame).
    LDA #$00
    STA ObjGridOffset, X
    STA ObjPosFrac, X
    LDA #$20
    STA ObjQSpeedFrac, X
```

This patches the speed at bank 1 CPU `$A9E4` (originally `$20`) to `$80`. Raw
form: `$A9E4:80:20`.

**Caveat — this byte is copied into Save RAM before it runs.** As with the
Blue Candle code above, `WieldCandle` is part of the `BANK_01_CODE` block that
`CopyCommonCodeToRam` copies from ROM `$A500`+ to `$6C90`+ at boot; this
instruction executes at `$7174`. The patch must be active at boot.

**Caveat — bank-unique.** No other PRG bank holds `$20` at this
`$8000`-window offset.

**Caveat — the flame stops at the same place.** `UpdateFire` (`src/Z_07.asm`)
halts the flame once the absolute value of its grid offset equals `$10`, and
that test is exact. A larger per-frame step can overshoot `$10` without ever
matching it, in which case the flame keeps travelling until something else
stops it. `$80` is a whole number of pixels per frame and divides `$10`
evenly, which is why this value was chosen over an odd one.

**Not live-verified:** derived from reading `WieldCandle` (`src/Z_01.asm`) and
`UpdateFire` (`src/Z_07.asm`), not from observing it in-game.

## Every gravestone and Armos square releases a Flying Ghini

**Code:** `NNUXGZEK`

**Effect:** Pushing against an Armos statue makes a Flying Ghini fade in
instead of an Armos. Gravestones already produce Ghinis, so in effect every
"passive" overworld square now spits out a Ghini.

**How it works:** `CheckPassiveTileObjects` (`src/Z_01.asm`) chooses the
object type from the tile Link collided with:

```
@ChooseObjType:
    ; Choose the right object type for the tile.
    LDA #$1E                    ; Armos
    LDY $02                     ; [02] collided tile
    CPY #$C0
    BCS :+                      ; If tile >= $C0, then instantiate an armos.
    LDA #$22                    ; Flying Ghini
:
    STA ObjType, X
```

Tiles `$BC`-`$BF` are the gravestone squares and `$C0`-`$C3` the Armos ones.
This patches the threshold at bank 1 CPU `$A2BC` (originally `$C0`) to `$FF`.
Raw form: `$A2BC:FF:C0`. No tile in the checked range reaches `$FF`, so the
`BCS` never fires and every square takes the Flying Ghini branch.

**Caveat — bank-unique.** No other PRG bank holds `$C0` at this
`$8000`-window offset.

**Caveat — the secrets under the graves still work.** This only changes which
monster the square releases; the separate gravestone/Armos secret handling in
`src/Z_04.asm` is untouched.

**Not live-verified:** derived from reading `CheckPassiveTileObjects`
(`src/Z_01.asm`), not from observing it in-game.

## Walk right through shopkeepers and old men

**Code:** `AEUXPVVA`

Tags: `play-start`

**Effect:** Cave people no longer block Link from walking up past them. He can
step onto and behind the shopkeeper, the old men and the Grumble Moblin.

**How it works:** `CheckPersonBlocking` (`src/Z_01.asm`) is called from
`Walker_Move` when a person occupies object slot 1, and cancels upward
movement below a fixed line:

```
CheckPersonBlocking:
    LDA ObjY
    CMP #$8E
    BCS :-                      ; Return if Y coordinate >= $8E.
    LDA $0F
    AND #$08
    BEQ :-                      ; If not moving up, then return.
    JMP ResetMovingDir
```

This patches the boundary at bank 1 CPU `$A6B9` (originally `$8E`) to `$00`.
Raw form: `$A6B9:00:8E`. Link's Y is always `>= $00`, so the routine always
returns before it can clear the movement direction.

**Caveat — this byte is copied into Save RAM before it runs.**
`CheckPersonBlocking` is in the `BANK_01_CODE` block that
`CopyCommonCodeToRam` copies from ROM `$A500`+ to `$6C90`+ at boot; the
instruction executes at `$6E48`. The patch must be active at boot to reach the
copy.

**Caveat — bank-unique.** No other PRG bank holds `$8E` at this
`$8000`-window offset.

**Caveat — the room boundary still holds Link in.** `BoundByRoom` and the
walkable-tile check are separate; this only removes the person's own veto on
upward movement.

**Not live-verified:** derived from reading `CheckPersonBlocking`
(`src/Z_01.asm`), not from observing it in-game.

## Push-blocks, rocks and gravestones don't block Link

**Code:** `AAVZZPAP`

Tags: `play-start`

**Effect:** Link walks straight through the tile objects that normally stop
him — the pushable dungeon block, overworld rocks and gravestones — instead of
being halted next to them.

**How it works:** `CheckTileObjectsBlocking` (`src/Z_01.asm`) scans object
slots 1-12 for a blocking tile object and cancels Link's movement when he is
within `$10` pixels on both axes:

```
    ; If X distance between Link and the object >= $10, skip it.
    LDA ObjX
    SEC
    SBC ObjX, X
    JSR Abs
    CMP #$10
    BCS @NextTileObj
```

This patches the horizontal threshold at bank 1 CPU `$A162` (originally `$10`)
to `$00`. Raw form: `$A162:00:10`. Any absolute distance is `>= 0`, so every
candidate object is skipped and `[0F]` (the movement direction) is never
cleared.

**Caveat — bank-unique.** No other PRG bank holds `$10` at this
`$8000`-window offset.

**Caveat — the vertical test is a second byte.** The matching `CMP #$10` for
the Y axis has its operand at `$A171`; it is left alone because clearing the X test alone
already skips every object before the Y test is reached.

**Caveat — the tile underneath still matters.** This is the *object* form of
these obstacles. The walkability of the tiles they sit on is decided by
`Walker_CheckTileCollision` against `ObjectFirstUnwalkableTile`, so Link may
still be stopped by the terrain in some rooms.

**Not live-verified:** derived from reading `CheckTileObjectsBlocking`
(`src/Z_01.asm`), not from observing it in-game.

## Level 9's entrance opens with no Triforce pieces

**Code:** `AEXASXNY`

**Effect:** The old man at the mouth of Level 9 raises the shutter and steps
aside when Link has *no* Triforce pieces at all, instead of requiring all
eight.

**How it works:** `InitUnderworldPersonC` (`src/Z_01.asm`) handles the person
at the Level 9 entrance (object type `$4B`):

```
    ; Return, if this is not the man at the entrance of Level 9,
    ; or Link has not gotten all the triforce pieces.
    CMP #$4B
    BNE @Exit
    LDA InvTriforce
    CMP #$FF
    BNE @Exit

    ; Otherwise, open the shutters, and destroy this object.
    LDA #$01
    STA ShutterTrigger
```

`InvTriforce` is a bitmask with one bit per dungeon, so `$FF` means all eight.
This patches the comparison at bank 1 CPU `$8AA5` (originally `$FF`) to `$00`.
Raw form: `$8AA5:00:FF`. The condition inverts: the shutter opens on exactly
zero pieces.

**Caveat — it inverts rather than disables.** With this code active, collecting
*any* Triforce piece makes the entrance stop opening. Turn the code off once
you are inside, or leave it off during a normal run.

**Caveat — NOT bank-unique.** Banks 0 and 3 also hold `$FF` at this
`$8000`-window offset, so the patch fires in three banks rather than one.
`$FF` is a common filler byte; expect unrelated side effects when bank 0
(audio) or bank 3 (CHR transfer tables) is mapped in over `$8AA5`.

**Not live-verified:** derived from reading `InitUnderworldPersonC`
(`src/Z_01.asm`), not from observing it in-game.

## Shutters slam without freezing Link

**Code:** `AAOZPTAL`

**Effect:** When a dungeon room's shutters slam shut behind Link, he is no
longer locked in place for the half-second the doors take to close. He keeps
walking immediately.

**How it works:** `UpdateDoors` (`src/Z_05.asm:5030`) is the per-frame door
state machine. `TriggeredDoorCmd` carries the command; the header comment
documents commands 2/3 as "close" and 6/7 as "open". Command 2 — the one that
starts a shutter closing — also parks Link:

```
    CMP #$02
    BNE :+

    ; Command 2 sets Link's timer to $30.
    LDY #$30
    STY ObjTimer
:
```

`ObjTimer` is object slot 0's timer, i.e. Link's, and a nonzero object timer
holds the player still. This patches the `LDY #$30` immediate at bank 5 CPU
`$A611` (originally `$30`) to `$00`. Raw form: `$A611:00:30`. Link's timer is
loaded with 0, so nothing freezes him and he can walk while the shutters come
down. No other PRG bank holds `$30` at that `$8000`-window offset, so the
patch cannot misfire elsewhere.

**Caveat — only the *close* command.** Command 6 (open) never touched
`ObjTimer`, so this changes nothing about doors opening.

**Caveat — the doors still close.** The tile transfer and the door flags are
handled further down in `UpdateDoors` and are untouched; only the player lock
is removed. Walking into the closing doorway during those frames is
unexplored behaviour.

**Not live-verified:** derived from reading `UpdateDoors` (`src/Z_05.asm`),
not from observing it in-game.

## Dungeon doors open and close almost instantly

**Code:** `PAVXLVAA`

**Effect:** Shutters and key doors snap open or shut roughly eight times
faster than normal — the two-step door animation runs back to back instead of
pausing between halves.

**How it works:** `UpdateDoors` (`src/Z_05.asm:5030`) writes the door's new
tiles into the dynamic transfer buffer, bumps `TriggeredDoorCmd`, and then
either finishes the sequence or arms `DoorTimer` and returns:

```
    ; Increment the command.
    INC TriggeredDoorCmd
    ...
    LDA TriggeredDoorCmd
    AND #$03
    BEQ :+
    LDA #$08
    STA DoorTimer
    RTS
```

The routine's own entry guard is `LDA DoorTimer / BNE L165D4_Exit`, so
`DoorTimer` is exactly the delay between the two halves of the open/close
animation. This patches the `LDA #$08` immediate at bank 5 CPU `$A66B`
(originally `$08`) to `$01`. Raw form: `$A66B:01:08`. The delay drops from 8
frames to 1. No other PRG bank holds `$08` at that `$8000`-window offset.

**Caveat — shared by every triggered door.** `DoorTimer` gates all door
commands, so shutters, key doors and bomb holes all speed up together.

**Not live-verified:** derived from reading `UpdateDoors` (`src/Z_05.asm`),
not from observing it in-game.

## Link spins four times as long when he dies

**Code:** `AOEANZGA`

**Effect:** The death sequence's spin — Link turning down, left, up, right in
place before the screen fades — runs 16 rotations instead of 4.

**How it works:** `InitMode11_Sub1` (`src/Z_05.asm:2067`) finishes setting up
game mode `$11` (death) and seeds the rotation counter:

```
    LDA #$04                    ; There will be 4 turns starting from down direction.
    STA DeathModeCounter
    STA ObjDir
```

`UpdateMode11Death_Sub7` decrements `DeathModeCounter` once per completed
rotation and moves on to the grey fade when it reaches 0. This patches the
`LDA #$04` immediate at bank 5 CPU `$8A87` (originally `$04`) to `$10`. Raw
form: `$8A87:10:04`. No other PRG bank holds `$04` at that `$8000`-window
offset.

**Caveat — distinct from the existing spin-speed code.** The published "Link
keeps spinning much longer when he dies" code patches `$8CE3`, the *frames
per direction*. This one patches the *number of rotations*. They are
independent bytes and stack — enabling both gives 16 very slow rotations.

**Caveat — the same store also sets `ObjDir`.** `STA ObjDir` immediately
follows, so the patched value is also Link's starting facing direction for
the spin. `$10` is not one of the four single-direction bits (`$01`/`$02`/
`$04`/`$08`), so the first frame's facing is unexplored behaviour before the
spin logic overwrites it.

**Not live-verified:** derived from reading `InitMode11_Sub1`
(`src/Z_05.asm`), not from observing it in-game.

## Link and monsters walk through dungeon walls

**Code:** `SYSUIEAY`

**Effect:** In the underworld, almost every tile becomes walkable. Link (and
every other object) can walk straight through dungeon walls, blocks and
statues instead of being stopped by them.

**How it works:** Walkability is a single RAM threshold,
`ObjectFirstUnwalkableTile` (`$34A`): any tile ID `>= ObjectFirstUnwalkableTile`
blocks movement. `SetupObjRoomBounds` (`src/Z_05.asm:6444`) loads it, along
with the four room bounds, from a 5-byte table per world:

```
ObjectRoomBoundsOW:
    .BYTE $11, $E0, $4E, $CD, $89

ObjectRoomBoundsUW:
    .BYTE $21, $D0, $5E, $BD, $78
...
    LDA ObjectRoomBoundsOW, Y
    STA RoomBoundLeft, X
```

Byte 4 of each row is the threshold — `$89` in the overworld, `$78` in the
underworld. This patches `ObjectRoomBoundsUW` byte 4 at bank 5 CPU `$B05D`
(originally `$78`) to `$F5`. Raw form: `$B05D:F5:78`. Every dungeon tile below
`$F5` — which is essentially all of them — now reads as walkable. No other PRG
bank holds `$78` at that `$8000`-window offset.

**Caveat — the underworld twin of the existing water-walking code.** The
published overworld code patches byte 4 of `ObjectRoomBoundsOW` (`$B058`).
This is the same field in the underworld row; the two are independent and
stack.

**Caveat — applies to everything, not just Link.** `SetupObjRoomBounds` fills
the shared bound variables for the whole room, so monsters walk through walls
too. Room transitions still happen only at real doorways, so walking into
solid wall leaves Link inside the wall graphics until he walks back out or
reaches a doorway.

**Not live-verified:** derived from reading `SetupObjRoomBounds` and
`ObjectRoomBoundsUW` (`src/Z_05.asm`), not from observing it in-game.

## Objects can move further into the underworld screen's left edge

**Code:** `PASUPAPZ`

**Effect:** In dungeons, Link and every other object can move further past the
left edge of the play area than normal before the bound clamp stops them.

**How it works:** Byte 0 of each `ObjectRoomBounds*` row is `RoomBoundLeft`,
copied into the live bound variables by `SetupObjRoomBounds`
(`src/Z_05.asm:6444`) on every room entry; `BoundDirectionHorizontally`
(`src/Z_01.asm:3360`) compares each object's X against it:

```
ObjectRoomBoundsUW:
    .BYTE $21, $D0, $5E, $BD, $78
...
@Left:
    LDA $00
    CMP RoomBoundLeft
    BCC BoundDirectionReturn
```

This patches `ObjectRoomBoundsUW` byte 0 at bank 5 CPU `$B059` (originally
`$21`) to `$01`. Raw form: `$B059:01:21`.

**Caveat — NOT bank-unique.** Bank 4 also holds `$21` at this `$8000`-window
offset, so the patch fires in two banks. Expect unrelated side effects while
bank 4 (object AI) is mapped in over `$B059`.

**Caveat — the underworld counterpart of the published overworld code.** The
existing "Objects can move further into the overworld screen edges" code
patches `ObjectRoomBoundsOW` byte 0 at `$B054`. Same field, other world row.

**Not live-verified:** derived from reading `SetupObjRoomBounds` and
`ObjectRoomBoundsUW` (`src/Z_05.asm`), not from observing it in-game.

## Objects can move further into the overworld's right edge

**Code:** `EYSLIAEV`

**Effect:** On the overworld, Link and every other object can walk further
past the right edge of the play area than normal.

**How it works:** Byte 1 of each `ObjectRoomBounds*` row is `RoomBoundRight`
(`src/Z_05.asm:6438`), copied by `SetupObjRoomBounds` and checked in
`BoundDirectionHorizontally` (`src/Z_01.asm:3403`):

```
@Right:
    ; Check right boundary.
    ; If X coordinate is within (<) right bound, return and leave direction alone.
    LDY #$01
    LDA $00
    CMP RoomBoundRight
    BCC L6825_Exit
```

This patches `ObjectRoomBoundsOW` byte 1 at bank 5 CPU `$B055` (originally
`$E0`) to `$F8`. Raw form: `$B055:F8:E0`. No other PRG bank holds `$E0` at
that `$8000`-window offset.

**Caveat — applies to everything, not just Link.** Enemies and projectiles get
the same widened right edge.

**Caveat — screen transitions are unaffected.** Room scrolling is triggered by
`CheckWarps`/mode 7 logic, not by these bounds, so walking further right only
pushes Link into the screen-edge tiles, it does not scroll early.

**Not live-verified:** derived from reading `SetupObjRoomBounds` and
`ObjectRoomBoundsOW` (`src/Z_05.asm`), not from observing it in-game.

## Objects can move up into the overworld status bar

**Code:** `GGSLTETG`

**Effect:** On the overworld, Link and every other object can move about 10
pixels higher than normal, overlapping the bottom of the status bar.

**How it works:** Byte 2 of each `ObjectRoomBounds*` row is `RoomBoundUp`
(`src/Z_05.asm:6438`), copied into the live bound variables by
`SetupObjRoomBounds` (`src/Z_05.asm:6444`) and checked by
`BoundDirectionVertically` (`src/Z_01.asm:3428`). The overworld row's value is
`$4E`, just under the `$40` top of the play area:

```
ObjectRoomBoundsOW:
    .BYTE $11, $E0, $4E, $CD, $89
```

This patches byte 2 at bank 5 CPU `$B056` (originally `$4E`) to `$44`. Raw
form: `$B056:44:4E`. No other PRG bank holds `$4E` at that `$8000`-window
offset.

**Caveat — sprites, not tiles.** Only the movement clamp changes; the status
bar is drawn from the nametable, so Link's sprite will overlap it rather than
scroll it.

**Caveat — applies to everything, not just Link.** Monsters get the same
raised ceiling.

**Not live-verified:** derived from reading `SetupObjRoomBounds` and
`ObjectRoomBoundsOW` (`src/Z_05.asm`), not from observing it in-game.

## Link barely steps out of dungeon doorways

**Code:** `AANLYEAX`

**Effect:** When Link leaves a dungeon room through a wall-level doorway, the
automatic walk that carries him out to the edge of the play area is much
shorter, so the room transition starts almost at once.

**How it works:** `InitMode6` (`src/Z_05.asm:6466`) picks how far Link has to
walk before the room actually changes, from a 3-byte table:

```
LeavingRoomRelativePositions:
    .BYTE $28, $D8, $00
...
    LDA LeavingRoomRelativePositions, Y
    STA ObjGridOffset
```

The header comment states the meaning outright: index 2 is `$00` for "open",
"key" and "shutter" doors, where Link already stands at the play-area edge;
indexes 0 and 1 are `$28` and `-$28` for wall-level doorways, the distance
Link must cover in the increasing or decreasing direction. This patches byte 0
at bank 5 CPU `$B077` (originally `$28`) to `$08`. Raw form: `$B077:08:28`.
No other PRG bank holds `$28` at that `$8000`-window offset.

**Caveat — one direction only.** Byte 0 is the decreasing direction (left/up).
Doorways heading right or down use byte 1 (`$D8`, at `$B078`) and are
unchanged, so exits become asymmetric.

**Not live-verified:** derived from reading `InitMode6` and
`LeavingRoomRelativePositions` (`src/Z_05.asm`), not from observing it
in-game.

## The dungeon map shows the rooms you have not visited

**Code:** `EIOUYTEY`

**Effect:** The dungeon map in the pause submenu inverts: rooms Link has never
entered are drawn with their door layout, and rooms he has already visited are
drawn blank.

**How it works:** `Submenu_WriteScanningMapRoomMark` (`src/Z_05.asm:7688`)
writes one map cell per call. It defaults the cell to the blank mark, then
tests the scanned room's visit flag and only builds a door mask if the room
has been visited:

```
    ; Set OpenDoorMask to $13, in case the room has not been
    ; visited. $E2 will be added, yielding $F5, which is the blank
    ; map mark tile.
    LDA #$13
    STA OpenDoorwayMask
    ...
    ; Get the currently scanned room's visit state.
    LDY RoomId
    LDA ($00), Y
    AND #$20                    ; Visit state
    ...
    BEQ @WriteMapTile
```

This patches the `BEQ @WriteMapTile` opcode at bank 5 CPU `$B61F` (originally
`$F0`, `BEQ`) to `$D0` (`BNE`) — a plain branch-sense flip, with the branch
offset untouched. Raw form: `$B61F:D0:F0`. Visited rooms now take the branch
and get the blank `$F5` mark; unvisited rooms fall through to the
`FindDoorTypeByDoorBit`/`CalcOpenDoorwayMask` loop and get a real layout.

**Caveat — NOT bank-unique.** Bank 1 also holds `$F0` at this `$8000`-window
offset, so the patch fires in two banks. `$F0` is a common `BEQ` opcode byte;
expect a second, unrelated branch in bank 1 to invert while this code is on.

**Caveat — the unexplored layout is partly a guess.** `CalcOpenDoorwayMask`
reads the room's *door flags* for key doors, shutters and bomb holes. For a
room Link has never been in those flags are clear, so those doorways show as
walls; only permanently-open doorways draw as openings. The revealed map is
therefore the room's minimum layout, not its full one.

**Caveat — needs the map item.** The submenu only scans and draws rooms when
`HasMap` (`src/Z_05.asm:7664`) returns nonzero for the current level. Without
the level's map, nothing is drawn either way.

**Not live-verified:** derived from reading
`Submenu_WriteScanningMapRoomMark` and `CalcOpenDoorwayMask`
(`src/Z_05.asm`), not from observing it in-game.

## Mountain stairs no longer slow Link down

**Code:** `ATNUZLAL`

**Effect:** The overworld staircase tiles that normally halve Link's walking
speed let him move at full speed.

**How it works:** `InitLinkSpeed` (`src/Z_05.asm:7123`) sets Link's quarter-
speed fraction each time his direction is (re)established, with a documented
special case for stairs:

```
InitLinkSpeed:
    LDA #$60                    ; Link gets a quarter speed (QSpeed) of $60 by default (1.5 pixels a frame).
    STA $00
    LDA CurLevel
    BNE @SetSpeed               ; If in UW, go use this speed.

    ; In OW. If standing on mountain stairs, then
    ; use a lower quarter speed of $30.
    LDA ObjCollidedTile
    CMP #$74
    BEQ :+
    CMP #$75
    BNE @SetSpeed
:
    LDA #$30
    STA $00
```

`ObjQSpeedFrac` is applied four times a frame by `MoveObject`, so `$60` is 1.5
pixels/frame and `$30` is 0.75. This patches the `LDA #$30` immediate at bank
5 CPU `$B37A` (originally `$30`) to `$60`. Raw form: `$B37A:60:30`. Stairs now
load the same speed as flat ground. No other PRG bank holds `$30` at that
`$8000`-window offset.

**Caveat — distinct from the published default-speed code.** The existing
"Link walks faster" code patches the `LDA #$60` at `$B367`. If both are on,
this one should be set to match whatever the other one uses, or stairs will be
*faster* than flat ground.

**Caveat — the position-fraction reset still runs.** The `CMP ObjQSpeedFrac /
BEQ` that follows compares against the new value, so with both speeds equal
the `ObjPosFrac` reset is skipped on stairs. That only affects sub-pixel
alignment.

**Not live-verified:** derived from reading `InitLinkSpeed` (`src/Z_05.asm`),
not from observing it in-game.

## The B button swings the sword too

**Code:** `EKXULZEA`

**Effect:** Pressing B swings the sword *and* uses the selected item. A still
swings the sword on its own.

**How it works:** `Link_HandleInput` (`src/Z_05.asm:6921`) tests the two
action buttons in sequence while Link is in state 0:

```
    ; If the sword is not blocked, then handle the sword if A is pressed.
    LDA SwordBlockedLongTimer
    ORA SwordBlocked
    BNE :+
    LDA ButtonsPressed
    AND #$80
    BEQ :+
    JSR WieldSword
:
    ; If B is pressed, handle the item.
    LDA ButtonsPressed
    AND #$40
    BEQ @CheckMovement
    JSR WieldItem
```

`$80` is the A bit of `ButtonsPressed` and `$40` is the B bit. This patches the
sword test's mask at bank 5 CPU `$B2AB` (originally `$80`) to `$C0`. Raw form:
`$B2AB:C0:80`. The `AND` now leaves a nonzero result for A *or* B, so B
reaches `WieldSword` and then falls through to the untouched `AND #$40` and
also reaches `WieldItem`.

**Caveat — B does both at once.** The item test is a separate, unmodified
comparison, so a single B press fires `WieldSword` and `WieldItem` in the same
frame. Whether the second one takes effect depends on the slots `WieldSword`
leaves occupied; this is unexplored behaviour.

**Caveat — the sword-blocked guard still applies.** `SwordBlockedLongTimer` /
`SwordBlocked` gate the whole block, so B will not swing while the sword is
blocked.

**Not live-verified:** derived from reading `Link_HandleInput`
(`src/Z_05.asm`), not from observing it in-game.

## The second raft dock moves to the corner of the overworld

**Code:** `AAKEEPII`

**Effect:** The raft dock that normally sits in overworld room `$55` is gone
from there and appears in room `$00`, the north-west corner screen, instead.

**How it works:** `SetupTileObjectOW` (`src/Z_05.asm:1842`) hard-codes the two
overworld screens that carry a dock, and puts the dock object type in the room
tile-object slot for them:

```
SetupTileObjectOW:
    ; If this is a room with a dock ($3F and $55), then
    ; set the dock object type ($61) in tile object slot ($B).
    LDA RoomId
    CMP #$3F
    BEQ :+
    CMP #$55
    BNE @PlaceTileObj
:
    LDA #$61
    JMP @SetType
```

This patches the second comparison's immediate at bank 5 CPU `$8948`
(originally `$55`) to `$00`. Raw form: `$8948:00:55`. Room `$3F` keeps its
dock; room `$55` now falls through to the ordinary tile-object path, and room
`$00` gets the dock object. No other PRG bank holds `$55` at that
`$8000`-window offset.

**Caveat — the dock object, not the dock graphics.** Only the object in slot
`$B` moves. The dock tiles are part of each room's layout data and stay where
they are, so room `$00` gets an invisible dock and room `$55` keeps a dock
you cannot use.

**Caveat — placement in the new room is whatever the object defaults to.**
The `@SetType` path skips the `RoomTileObjX`/`RoomTileObjY` stores, so the
dock object keeps whatever coordinates slot `$B` last held. Where it actually
lands in room `$00` is unexplored behaviour.

**Not live-verified:** derived from reading `SetupTileObjectOW`
(`src/Z_05.asm`), not from observing it in-game.

## The overworld heart container moves to the corner screen

**Code:** `AEOUXEYI`

**Effect:** The overworld heart container that normally sits in room `$5F`
appears in room `$00`, the north-west corner screen, instead.

**How it works:** `CreateRoomObjects` (`src/Z_05.asm:8191`) has a dedicated
overworld branch for the single loose heart container:

```
@MakeHeartContainerOW:
    ; Try to make the heart container in OW.
    LDA #$1A                    ; Heart container
    STA RoomItemId

    ; Load the coordinates of the heart container in
    ; OW room $5F.
    LDA #$C0
    LDY #$90

    ; If in mode 5, and in room $5F, then go store the coordinates
    ; in the object slot.
    LDX GameMode
    CPX #$05
    BNE :+
    LDX RoomId
    CPX #$5F
    BEQ @StoreLocation
:
    ; Else deactivate the object.
    DEC ObjState+19
```

This patches the room comparison at bank 5 CPU `$B89A` (originally `$5F`) to
`$00`. Raw form: `$B89A:00:5F`. Room `$5F` now takes the deactivate path and
room `$00` activates the item object at `($C0, $90)`. No other PRG bank holds
`$5F` at that `$8000`-window offset.

**Caveat — the coordinates are unchanged.** `LDA #$C0 / LDY #$90` is the
position that suits room `$5F`; in room `$00` the heart container appears at
those same screen coordinates whatever terrain is there.

**Caveat — mode 5 only.** The `CPX #$05` guard is untouched, so the object is
still only created while the overworld play mode is running.

**Not live-verified:** derived from reading `CreateRoomObjects`
(`src/Z_05.asm`), not from observing it in-game.

## The pushable dungeon block detaches from its tile

**Code:** `NYOXOAEU`

**Effect:** In dungeon rooms flagged as having a movable block, the block
*object* Link can push is no longer placed on the block tile — it always ends
up at the right-hand end of the row instead, leaving the drawn block inert and
an invisible pushable block elsewhere.

**How it works:** `FindAndCreatePushBlockObject` (`src/Z_05.asm:5470`) scans
row `$A` of the play-area tile map for the block tile and derives the object's
X coordinate from the column it was found in:

```
    ; Look for a block tile in row $A of play area, starting in column 4.
    LDX #$08
    LDY #$0A

@LoopColumn:
    LDA PlayAreaColumnAddrs, X
    ...
    LDA ($00), Y
    CMP #$B0
    BEQ @Found
    INX
    INX
    INX
    INX
    CPX #$34
    BNE @LoopColumn

@Found:
    ; The block was found in a column with an address at
    ; offset %X in column table. So the column number would
    ; be (%X/2), and X coordinate ((%X/2)*8). That means
    ; multiplying %X by 4.
    TXA
    ASL
    ASL
    STA ObjX+11
```

This patches the tile comparison at bank 5 CPU `$A819` (originally `$B0`, the
block tile) to `$FF`. Raw form: `$A819:FF:B0`. `$FF` is never a play-area
tile, so the scan never matches; the loop instead runs to its `CPX #$34`
terminator and falls straight into `@Found` with `X = $34`, giving
`ObjX+11 = $D0` — the far right of the row — and the routine's hard-coded
`ObjY+11 = $90`.

**Caveat — the block graphic does not move.** The block tile is written by the
room layout, not by this routine, so the visible block stays put while the
pushable object sits somewhere else.

**Caveat — only rooms flagged for a push block.** `CreateRoomObjects`
(`src/Z_05.asm:8236`) calls this routine only when `LevelBlockAttrsD` bit
`$40` is set for the room. It also has a separate hard-coded case for unique
room `$21`, which returns before the scan and is unaffected. No other PRG bank
holds `$B0` at that `$8000`-window offset.

**Not live-verified:** derived from reading `FindAndCreatePushBlockObject` and
`CreateRoomObjects` (`src/Z_05.asm`), not from observing it in-game.

## Any name beginning with Z starts the second quest

**Code:** `PAVPXYIA`

**Effect:** Registering a name whose first letter is `Z` — not just "ZELDA" —
flags the new file as a second-quest file.

**How it works:** `UpdateModeERegister` (`src/Z_02.asm:1683`) compares the
freshly registered name against a 5-byte literal and sets the file's quest
number if all five characters match:

```
ZeldaString:
    .BYTE $23, $0E, $15, $0D, $0A
...
    LDX #$00                    ; Compare the name to "ZELDA".

@CompareToZelda:
    LDA Names, Y
    CMP ZeldaString, X
    BNE @FlagBReady             ; If there's any mismatch, then skip the rest.
    INY
    INX
    CPX #$05
    BCC @CompareToZelda         ; Go check the next character until the end of "ZELDA".
    ...
    LDY #$00                    ; Set second quest in file B.
    LDA #$01
    STA ($CC), Y
```

This patches the loop's terminator at bank 2 CPU `$9F62` (originally `$05`) to
`$01`. Raw form: `$9F62:01:05`. After the first character is compared, `X` is
already 1, so `CPX #$01` sets carry, the `BCC` is not taken, and the routine
falls straight through to the quest-number store — one matching character is
now the whole test.

**Caveat — NOT bank-unique.** Bank 0 also holds `$05` at this `$8000`-window
offset, so the patch fires in two banks. Expect unrelated side effects while
bank 0 (the audio engine) is mapped in over `$9F62`.

**Caveat — the first letter must still be Z.** The first `CMP ZeldaString, X`
runs before the loop terminator is reached, so `$23` (the character code for
`Z`) still has to match. See the companion code below for changing which
letter that is.

**Not live-verified:** derived from reading `UpdateModeERegister` and
`ZeldaString` (`src/Z_02.asm`), not from observing it in-game.

## The second-quest magic name becomes "AELDA"

**Code:** `ZEVOUTLX`

**Effect:** Registering the name "ZELDA" no longer starts the second quest;
"AELDA" does instead.

**How it works:** `ZeldaString` (`src/Z_02.asm:1612`) is the 5-byte literal
`UpdateModeERegister` compares a newly registered name against, in the game's
own character encoding:

```
ZeldaString:
    .BYTE $23, $0E, $15, $0D, $0A
```

`$23` is `Z`, `$0E` is `E`, `$15` is `L`, `$0D` is `D` and `$0A` is `A` — the
same encoding `ModeE_CharMap` (`src/Z_02.asm:1423`) uses to build the name
entry board. This patches byte 0 at bank 2 CPU `$9EEB` (originally `$23`) to
`$0A`, the code for `A`. Raw form: `$9EEB:0A:23`. No other PRG bank holds `$23`
at that `$8000`-window offset.

**Caveat — fires at name registration only.** Like the other register-screen
codes, the effect is baked into the save file when the name is committed;
existing files keep whatever quest number they already have.

**Not live-verified:** derived from reading `ZeldaString` and
`UpdateModeERegister` (`src/Z_02.asm`), not from observing it in-game.

## Starting the second quest grants 16 heart containers

**Code:** `NYNXKYZX`

**Effect:** When a profile flips over to the second quest, it is reset with 16
full heart containers instead of the usual 3.

**How it works:** `SwitchProfileToSecondQuest` (`src/Z_02.asm:4037`) wipes the
world flags and the whole `Items` block, then writes back the small set of
values a second-quest run starts with:

```
    ; Set 3 full hearts and heart containers.
    LDA #$22
    STA HeartValues
    DEC HeartPartial
    LDA #$08
    STA MaxBombs
    LDY CurSaveSlot
    LDA #$01
    STA QuestNumbers, Y
```

`HeartValues` (`$066F`) packs the container count in the high nibble and the
filled-heart count in the low nibble, both stored one less than displayed, so
`$22` is 3 containers with 3 full. This patches the `LDA #$22` immediate at
bank 2 CPU `$AF7C` (originally `$22`) to `$FF`. Raw form: `$AF7C:FF:22`. The
`DEC HeartPartial` on the next line is untouched, so the partial heart still
wraps to full. No other PRG bank holds `$22` at that `$8000`-window offset.

**Caveat — a different routine from the new-file seed.** The published "New
files start with 16 full heart containers" code patches `$9F41` in
`UpdateModeERegister`, which runs at name registration. This one runs when an
*existing* profile is switched to the second quest, and the two never fire on
the same event.

**Caveat — the switch still wipes everything else.** The routine clears the
world flags and the entire `Items` block first, so the 16 containers arrive on
an otherwise empty inventory.

**Not live-verified:** derived from reading `SwitchProfileToSecondQuest`
(`src/Z_02.asm`), not from observing it in-game.

## Starting the second quest grants a bomb capacity of 255

**Code:** `NNEZKNAE`

**Effect:** When a profile flips over to the second quest, its bomb capacity is
set to 255 instead of 8.

**How it works:** In the same `SwitchProfileToSecondQuest` block quoted above
(`src/Z_02.asm:4067`), the line after the heart seed sets the bomb ceiling:

```
    LDA #$08
    STA MaxBombs
```

This patches the immediate at bank 2 CPU `$AF84` (originally `$08`) to `$FF`.
Raw form: `$AF84:FF:08`. `MaxBombs` (`$067C`) is the clamp `TakeItem`
(`src/Z_01.asm`) applies to bomb pickups with `CMP MaxBombs / BCC /
LDA MaxBombs`, so bomb drops now fill toward 255. No other PRG bank holds
`$08` at that `$8000`-window offset.

**Caveat — the status bar only has two digits.** The bomb count is drawn as a
two-digit number, so counts above 99 are unexplored territory for the display
code even though the clamp itself is a plain byte compare.

**Caveat — capacity, not stock.** Only the ceiling changes; Link still has to
pick bombs up to fill it. The in-game bomb upgrade's `ADC #$04` still stacks on
top and will wrap past `$FF`.

**Not live-verified:** derived from reading `SwitchProfileToSecondQuest`
(`src/Z_02.asm`), not from observing it in-game.

## The game starts in the underworld

**Code:** `PEVZIIAA`

Tags: `play-start`

**Effect:** Choosing a save slot and starting a game puts Link in level 1's
underworld instead of the overworld.

**How it works:** `UpdateMode1Menu_Sub1` (`src/Z_02.asm:2795`) is the file-select
menu's "Start was pressed" handler. Before it copies the chosen file into the
live profile it resets the world state:

```
UpdateMode1Menu_Sub1:
    LDA #$00
    STA Tune1
    LDA #$00
    STA CurLevel                ; Begin in OW.
    STA SelectedItemSlot        ; Reset item index.
```

`CurLevel` (`$0010`) is the variable every world routine branches on —
`SetupObjRoomBounds`, `LayoutRoomOW` vs `LayoutUWFloor`, `IsDarkRoom_Bank5`,
`InitLinkSpeed` and the scroll code all test `CurLevel` for zero to mean
"overworld". This patches the `LDA #$00` immediate at bank 2 CPU `$A5E5`
(originally `$00`) to `$01`. Raw form: `$A5E5:01:00`. No other PRG bank holds
`$00` at that `$8000`-window offset.

**Caveat — the same `LDA` also feeds `SelectedItemSlot`.** The very next
instruction stores the same accumulator to `SelectedItemSlot` (`$0656`), so the
B-button item cursor starts on slot 1 rather than slot 0 as well.

**Caveat — the room the game loads is unexplored.** `RoomId` comes from the
save file, which for a fresh file is 0, and level 1's info block is loaded on
the strength of `CurLevel`. Whether that lands Link in a sensible level-1 room,
in a mismatched one, or somewhere the layout code has to improvise is not
determined by this routine and has not been established.

**Caveat — only the level number changes.** Nothing here loads a dungeon's map
or compass state; the status bar and submenu read those from the profile as
usual.

**Not live-verified:** derived from reading `UpdateMode1Menu_Sub1`
(`src/Z_02.asm`), not from observing it in-game.

## "Register your name" runs the ending instead

**Code:** `AONXASLA`

**Effect:** Selecting REGISTER YOUR NAME on the file-select menu and pressing
Start jumps straight to the game's win/ending sequence.

**How it works:** `UpdateMode1Menu_Sub1` (`src/Z_02.asm:2802`) treats
`CurSaveSlot` as a menu index — 0-2 are the three save slots, 3 is "register"
and 4 is "eliminate" — and turns the two option indexes into a game mode by
adding a base:

```
    LDA CurSaveSlot
    CMP #$03
    BCC @ChoseSlot              ; If not a save slot,
    LDA CurSaveSlot             ; Go to the mode for each option (register, eliminate).
    CLC
    ADC #$0B
    STA GameMode
    JMP EndGameMode
```

Index 3 + `$0B` is mode `$E` (`InitModeEandF_Full`, register) and index 4 + `$0B`
is mode `$F` (eliminate). This patches the `ADC #$0B` immediate at bank 2 CPU
`$A5F8` (originally `$0B`) to `$10`. Raw form: `$A5F8:10:0B`. Index 3 now
becomes mode `$13`, which is `InitMode13_Full` — the win-game/ending mode that
runs the Zelda rescue, the "PEACE RETURNS TO HYRULE" text and the credits. No
other PRG bank holds `$0B` at that `$8000`-window offset.

**Caveat — ELIMINATION MODE breaks.** The same add serves both options, so
index 4 becomes mode `$14`, which is past the end of the mode jump table.
Selecting ELIMINATION MODE with this code on is unexplored behaviour — avoid
it, or turn the code off first.

**Caveat — the ending runs on whatever state is loaded.** Mode `$13` normally
follows a completed game. Reached from the menu, it draws from a profile that
was never loaded, so the sprites and text it composes may not match a real
victory.

**Not live-verified:** derived from reading `UpdateMode1Menu_Sub1` and
`InitMode13_Full` (`src/Z_02.asm`), not from observing it in-game.

## Cave items can be picked up from much further away

**Code:** `AVUEEATA`

Tags: `play-start`

**Effect:** In caves where Link chooses or touches an item (give-away items,
shops, hint caves, the money game), he no longer has to stand almost right on
top of the item to take it — he can grab it from much further up or down the
screen, as long as he's still in the right column.

**How it works:** `UpdateCavePersonState_TalkOrShopOrDoorCharge`
(`src/Z_01.asm:739`) loops over the cave's items and only accepts a pickup
once Link is both in the right column and close enough vertically:

```
    ; If Link's X <> item's X, then loop again.
    LDA ObjX
    CMP CaveWareXs, X
    BNE @NextWare

    ; If the vertical distance between Link and the item < 6, then
    ; go try to take it.
    LDA ObjY
    SEC
    SBC #$98
    JSR Abs
    CMP #$06
    BCC @PickedUp
```

This patches the vertical-distance threshold at bank 1 CPU `$88B8`
(originally `$06`) to `$60`. Raw form: `$88B8:60:06`. `Abs` (`src/Z_01.asm`)
returns an unsigned distance, so the `BCC` now takes for any vertical gap
under 96 pixels instead of 6 — Link can be almost anywhere in the room
vertically and still pick the item up. No other PRG bank holds `$06` at that
`$8000`-window offset.

**Caveat — the column test is untouched.** The `CMP CaveWareXs, X` / `BNE`
check just above is an exact match against the item's X coordinate. Widening
only the vertical test still means Link has to be standing in the item's
column; he can't grab it from an arbitrary diagonal.

**Caveat — this widens pickup for every cave-item type at once.** The same
loop handles give-away items, shop purchases, hint payments and the money
game wager, since they all share `CaveItemIds` / `CaveWareXs`. There's no way
to widen just one item type with this single-byte patch.

**Not live-verified:** derived from reading
`UpdateCavePersonState_TalkOrShopOrDoorCharge` (`src/Z_01.asm`), not from
observing it in-game.

## The life-or-money money option is free

**Code:** `AAEESGZL`

**Effect:** In the life-or-money cave, choosing the money option pays out
without costing any rupees — and works even with an empty wallet.

**How it works:** `UpdateUnderworldPersonLifeOrMoneyState_2`
(`src/Z_01.asm:1423`) checks affordability and posts the debit using the same
value in the accumulator:

```
    ; The player chose the money.
    ; But if he doesn't have enough, then return.
    LDA #$32
    CMP InvRupees
    BEQ @PayWithMoney
    BCS @Exit

@PayWithMoney:
    ; Post 50 rupees more to subtract, and go flag this offer taken.
    CLC
    ADC RupeesToSubtract
    STA RupeesToSubtract
    JMP @EndLifeOrMoney
```

The same register both gates the offer and supplies the amount to debit —
the same shape as the already-published bomb-capacity-upgrade code. This
patches it at bank 1 CPU `$8C0D` (originally `$32`) to `$00`. Raw form:
`$8C0D:00:32`. With `$00`, `CMP InvRupees` either matches (0 rupees, takes
the `BEQ`) or leaves the carry clear (any rupees, so `BCS` isn't taken) — the
check always falls through to `@PayWithMoney` — and the amount added to
`RupeesToSubtract` is zero. No other PRG bank holds `$32` at that
`$8000`-window offset.

**Caveat — one offer per room.** `@EndLifeOrMoney` still runs
`L_Person_FlagItemTakenAndAdvanceState`, so the offer is still marked taken
after it's claimed for free; it won't pay out twice.

**Not live-verified:** derived from reading
`UpdateUnderworldPersonLifeOrMoneyState_2` (`src/Z_01.asm`), not from
observing it in-game.

## Armos and Flying Ghini fade in almost instantly

**Code:** `PEKXAXYL`

**Effect:** When an Armos statue or gravestone releases its monster, the
fade-in that normally takes it a moment to complete instead finishes almost
immediately.

**How it works:** `CheckPassiveTileObjects` (`src/Z_01.asm:2359`) picks the
object type for the tile Link collided with and then sets how long it takes
to fade in:

```
@ChooseObjType:
    ; Choose the right object type for the tile.
    LDA #$1E                    ; Armos
    LDY $02                     ; [02] collided tile
    CPY #$C0
    BCS :+                      ; If tile >= $C0, then instantiate an armos.
    LDA #$22                    ; Flying Ghini
:
    STA ObjType, X
    JSR ResetObjMetastate
    LDA #$3F                    ; Fade in for $3F frames.
    STA ObjTimer, X
```

This patches the fade duration at bank 1 CPU `$A2C8` (originally `$3F`) to
`$01`. Raw form: `$A2C8:01:3F`. This applies to both branches of the type
choice, so it shortens the fade for Armos and Flying Ghini alike. No other
PRG bank holds `$3F` at that `$8000`-window offset.

**Caveat — this is the same byte for both monster types.** There's no way to
shorten the fade for just Armos or just Flying Ghini with this single-byte
patch; both tile ranges (`$BC`-`$BF` gravestones, `$C0`-`$C3` Armos squares)
share the one `ObjTimer` initialization.

**Not live-verified:** derived from reading `CheckPassiveTileObjects`
(`src/Z_01.asm`), not from observing it in-game.

## The Power Triforce fanfare is much shorter

**Code:** `AXUZIPEG`

**Effect:** Taking the Power Triforce halts Link for a much shorter time
before the fanfare ends and the song resumes.

**How it works:** `TakePowerTriforce` (`src/Z_01.asm:2116`) halts Link for a
fixed number of frames when the Triforce of Power is taken:

```
TakePowerTriforce:
    INC TriforceFanfareActive

    ; Halt Link for $C0 frames.
    LDA #$C0
    STA ObjTimer
    LDA #$40
    STA ObjState
    RTS
```

This patches the halt duration at bank 1 CPU `$A1B5` (originally `$C0`) to
`$20`. Raw form: `$A1B5:20:C0`. `CheckPowerTriforceFanfare`
(`src/Z_01.asm:2066`) counts `ObjTimer` down every frame while
`TriforceFanfareActive` is set and ends the fanfare the instant it reaches
zero, so this cuts the halt from 192 frames (~3.2 seconds) to 32 (~0.5
seconds). No other PRG bank holds `$C0` at that `$8000`-window offset.

**Caveat — hearts are never refilled through this timer, patched or not.**
`CheckPowerTriforceFanfare` looks like it should fill Link's hearts when the
timer expires:

```
    ; When Link's timer expires, go finish up the fanfare.
    LDA ObjTimer
    BEQ @EndFanfare

    ; While Link's timer is counting down, every 4 frames, switch
    ; between the level palette and the white palette.
    LDY #$18

    ; Redundant check of Link's timer that won't branch.
    LDA ObjTimer
    BEQ @FillHearts
```

But the first check already sends `ObjTimer == 0` straight to `@EndFanfare`,
so the second `BEQ @FillHearts` — already flagged in the source as
"redundant... that won't branch" — can never fire, at any timer duration.
`@FillHearts` (`src/Z_01.asm:2091`) is marked as unverified/uncovered code
for exactly this reason. This patch doesn't change that: hearts were not
filled by this routine before the patch, and aren't after it either. `@EndFanfare`
still runs unconditionally, restoring the palette, requesting the level song,
and clearing `TriforceFanfareActive` and Link's halted state, which is the
entire visible effect of shortening this timer.

**Not live-verified:** derived from reading `TakePowerTriforce` and
`CheckPowerTriforceFanfare` (`src/Z_01.asm`), not from observing it in-game.

## Link walks much further into a cave on entering

**Code:** `ATOXTTAL`

**Effect:** Stepping into a cave makes Link walk automatically much further
inward before control returns to the player, instead of the normal short
walk-in.

**How it works:** `InitModeB_EnterCave_Bank5` (`src/Z_01.asm:3018`) places
Link at the cave entrance and arms an automatic walk-in distance:

```
    ; Get Link ready to move automatically this number of pixels.
    LDA #$30
    STA ObjGridOffset
```

`InitMode_WalkCave` (`src/Z_05.asm:6687`) then moves Link one step per frame
for as long as `ObjGridOffset` is nonzero, and `MoveObject`'s helpers
(`AddQSpeedToPositionFraction` / `SubQSpeedFromPositionFraction`,
`src/Z_01.asm:3518`/`3557`) count `ObjGridOffset` down by exactly 1 each time
Link's fractional position crosses a whole pixel, so any starting value
counts cleanly down to 0 — it just takes proportionally longer. This patches
the value at bank 1 CPU `$A61E` (originally `$30`) to `$60`. Raw form:
`$A61E:60:30`. This doubles the walk-in from 48 pixels to 96. No other PRG
bank holds `$30` at that `$8000`-window offset.

**Caveat — this byte is copied into Save RAM before it runs, and the code
must be switched on at boot.** `InitModeB_EnterCave_Bank5` is part of the
`BANK_01_CODE` segment (`src/Z.cfg`), stored in ROM at `$A500`+ but *run* from
Save RAM at `$6C90`+ — this instruction executes at `$6DAE`
(`$6C90` + (`$A61E` - `$A500`)). `CopyCommonCodeToRam`
(`src/Z_01.asm:1569`, bank 1 CPU `$8D00`) copies the whole block through the
cartridge bus from ROM `$A500`+ to Save RAM `$6C90`+ at boot, so the
substitution has to be in effect during that copy — the code must be on at
boot, not just when Link enters a cave.

**Evidence — the exact operand address.** `$A61D` is the `LDA` opcode itself
(`$A9`); the immediate operand — the byte that actually needs patching — is
the next byte, `$A61E`. Verified against the ROM directly:
`$A61D`=`$A9`, `$A61E`=`$30`, followed by `$8D $94 $03`
(`STA $0394`, i.e. `STA ObjGridOffset` — `Variables.inc:103` defines
`ObjGridOffset := $394`), which matches the source exactly. This entry uses
the corrected address, `$A61E`.

**Caveat — how far Link walks past where a room's graphics/collision expect
him to stop is untested.** 96 pixels is double the vanilla distance but still
well short of a typical room's height; larger values were avoided since
there's no confirmation, short of live play, of what's beyond that point.

**Not live-verified:** derived from reading `InitModeB_EnterCave_Bank5`
(`src/Z_01.asm`), `InitMode_WalkCave` (`src/Z_05.asm`), and
`CopyCommonCodeToRam` (`src/Z_01.asm`), not from observing it in-game.

## Bait disappears almost instantly after being thrown

**Code:** `AXUYTKNY`

**Effect:** Link's Bait item, once thrown, disappears in about half a second
instead of lasting several seconds — nowhere near enough time to lure a
monster over to it.

**How it works:** `UpdateBoomerangOrFood` (`src/Z_07.asm:3763`) handles both
weapon-slot object types that share this update routine, branching on the
high bit of `ObjState`; when that bit is set, the object is Bait:

```
    ; The object is food.
    ;
    ; Once the timer has expired, increment the state and set timer to $FF.
    ; If we reach state $83, then go deactivate the object.
    ;
    ; Nothing changes between the states. So, they are used as
    ; a way to extend the timer. $2FD screen frames in total.
    LDA ObjTimer, X
    BNE @CheckMonsterType
    INC ObjState, X
    LDA ObjState, X
    AND #$0F
    CMP #$03
    BEQ @Deactivate
    LDA #$FF
    STA ObjTimer, X
```

`ObjTimer, X` is the per-object countdown that gates each of Bait's
sub-states — as opposed to the sub-state count itself, compared against
`$03` two instructions earlier (bank 7 CPU `$F4B2`). Every time the timer
reaches 0, the low nibble of `ObjState` is bumped and the timer is re-armed
to `$FF` (255 frames, about 4.25 seconds) — until the low nibble reaches
`$03`, at which point `@Deactivate` (`JMP ResetObjState`) removes the
object. This patches the `LDA #$FF` immediate at bank 7 CPU `$F4B6`
(originally `$FF`) to `$20` (32 frames, about half a second). Raw form:
`$F4B6:20:FF`.

One-byte patch. CPU `$F4B6` falls in bank 7, the fixed bank permanently
mapped to `$C000`-`$FFFF` under this ROM's MMC1 setup — unlike the
switchable `$8000`-`$BFFF` window, this address is unambiguous on hardware
no matter which of the other banks is switched in, so no cross-bank check
applies here; the disassembler itself confirms the bank argument is ignored
above `$C000`.

**Caveat — the sub-state count is untouched.** The `CMP #$03` check at
`$F4B2` still requires the low nibble of `ObjState` to reach `$03` before
the object deactivates, so Bait still cycles through its sub-states — it
just blows through each one in `$20` frames instead of up to `$FF`.

**Not live-verified:** derived from reading `UpdateBoomerangOrFood`
(`src/Z_07.asm`), not from observing it in-game.

## Candle and Book-triggered flames deal nearly a full heart of damage per touch

**Code:** `NYEYNPEE`

**Effect:** Touching a fire object — the Candle's flame, or the flame a
blocked Magic Rod shot turns into when Link owns the Book of Magic — now
costs Link close to a full heart instead of half a heart.

**How it works:** `UpdateFire` (`src/Z_07.asm:4658`) drives both the
Candle's flame and, via `WieldCandle` (`src/Z_01.asm:3991`), the flame that
`HandleShotBlocked` (`src/Z_07.asm:3547`) creates when a blocked magic shot
is converted to fire (gated on `InvBook`). Near the end of `UpdateFire`,
once a collision with Link is detected:

```
    ; The player and the fire collide.
    ;
    ; Make the fire shove the player.
    LDX $00
    LDY #$00
    STY $00
    JSR BeginShove

    ; Harm the player $80 points.
    LDA #$00
    STA $0D
    LDA #$80
    STA $0E
    JMP Link_BeHarmed
```

`Link_BeHarmed` (`src/Z_01.asm:5742`) treats `[$0D:$0E]` as a 16-bit damage
amount — `$0D` in whole hearts, `$0E` as the partial-heart fraction — and
subtracts it from `HeartPartial`/`HeartValues`, borrowing a full heart if
the partial component underflows. This patches the `LDA #$80` immediate at
bank 7 CPU `$F907` (originally `$80`) to `$FF`. Raw form: `$F907:FF:80`.
With `$0D` still `$00`, the damage becomes `$00FF` — one unit short of a
full heart (a full `HeartPartial` is `$FF`, not `$100`), so nearly every
touch either drains almost all of the current partial heart or borrows a
whole one.

One-byte patch. CPU `$F907` falls in bank 7, the fixed bank permanently
mapped to `$C000`-`$FFFF` under this ROM's MMC1 setup — unlike the
switchable `$8000`-`$BFFF` window, this address is unambiguous on hardware
no matter which of the other banks is switched in, so no cross-bank check
applies here; the disassembler itself confirms the bank argument is ignored
above `$C000`.

**Caveat — rings still halve it.** `Link_BeHarmed` divides `[$0D:$0E]` by 2
for each ring level Link owns before applying it, so the blue and red rings
still soften this hit proportionally, exactly as they do for the original
`$80`.

**Caveat — doesn't touch enemy fireballs.** Wizzrobe and Aquamentus
projectiles run through the separate `UpdateFireball` routine, not
`UpdateFire`, so this patch has no effect on them — only the Candle's own
flame and the Book-triggered blocked-magic-shot flame are affected.

**Not live-verified:** derived from reading `UpdateFire` (`src/Z_07.asm`),
`WieldCandle`/`HandleShotBlocked` (`src/Z_01.asm`/`src/Z_07.asm`), and
`Link_BeHarmed` (`src/Z_01.asm`), not from observing it in-game.

## The boomerang doesn't slow down before it turns back

**Code:** `EGONLTAG`

**Effect:** When a thrown boomerang (Link's or a Goriya's) reaches the end
of its outward flight, it normally visibly slows to a crawl for a moment
before turning back toward the thrower. With this code, it keeps moving at
a brisk pace right up until it snaps into its return leg — no more hang.

**How it works:** `UpdateArrowOrBoomerang` (`src/Z_07.asm:3857`) tracks a
boomerang's major state in the high nibble of `ObjState`. During state
`$1x` (outward flight), once the traveled distance reaches
`ObjMovingLimit`, the code sets state `$20` — a comment there notes it
"will become `$30` below in `HandleArrowOrBoomerangBlocked`"
(`src/Z_07.asm:4050`), which adds `$10` to the state. `CheckState30`
(`src/Z_07.asm:4092`) then handles that state:

```
CheckState30:
    ; If major state <> $30, go check other states.
    CMP #$30
    BNE @CheckOtherStates

    ; State $3x. Slow down.
    ;
    ; Reset grid offset for movement.
    LDA #$00
    STA ObjGridOffset, X

    ; Go slow at q-speed fraction $40 (1 pixel a frame).
    LDA #$40
    STA ObjQSpeedFrac, X
```

The boomerang moves at this reduced speed until `ObjMovingLimit` (reloaded
to `$10` when state `$20` was set) counts down to 0, at which point
`@SetState40` switches it into state `$40` — the actual return-to-thrower
leg, driven separately further down by `@CheckOtherStates`. This patches
the `LDA #$40` immediate at bank 7 CPU `$F61B` (originally `$40`) to `$C0`.
Raw form: `$F61B:C0:40`. `$C0` is the same "full speed" q-speed-fraction
constant `SetUpWeaponWithState` (`src/Z_07.asm:4590`) uses for a sword
shot — 3 pixels a frame instead of 1.

One-byte patch. CPU `$F61B` falls in bank 7, the fixed bank permanently
mapped to `$C000`-`$FFFF` under this ROM's MMC1 setup — unlike the
switchable `$8000`-`$BFFF` window, this address is unambiguous on hardware
no matter which of the other banks is switched in, so no cross-bank check
applies here; the disassembler itself confirms the bank argument is ignored
above `$C000`.

**Caveat — only this one phase changes.** The outbound flight (state `$10`,
which uses the `BoomerangQSpeedFracsX`/`Y` deceleration tables) and the
actual return leg (states `$40`/`$50`) are untouched; only the brief pause
at maximum range speeds up.

**Caveat — affects monsters' boomerangs too.** `UpdateArrowOrBoomerang` is
shared by Link's boomerang and any monster's (Goriyas'), so a Goriya's
boomerang loses its hang at max range as well.

**Not live-verified:** derived from reading
`UpdateArrowOrBoomerang`/`CheckState30`/`SetUpWeaponWithState`
(`src/Z_07.asm`), not from observing it in-game.

## Goriyas can rethrow their boomerang almost immediately

**Code:** `AEEYPTAN`

**Effect:** After a Goriya's boomerang returns to it, the Goriya is normally
idle for a while (up to about 1.9 seconds) before it can throw again. With
this code, on the majority of throws — any random roll landing in the
`$70`-or-higher band, more than half the possible range — that wait drops
to a handful of frames, so Goriyas rethrow almost immediately.

**How it works:** `@CatchBoomerang` (`src/Z_07.asm:4194`), reached when a
monster's own boomerang makes it back to it, arms a timer on the thrower
before destroying the boomerang object:

```
@CatchBoomerang:
    ; A monster caught the boomerang that it threw.
    ;
    ; Set a timer for the thrower based on a random value:
    ; < $30: $30
    ; < $70: $50
    ; Else:  $70
    LDY #$30
    LDA Random, X
    CMP #$30
    BCC @SetThrowerTimer
    LDY #$50
    CMP #$70
    BCC @SetThrowerTimer
    LDY #$70

@SetThrowerTimer:
    TYA
    LDY ObjRefId, X
    STA a:ObjTimer, Y
```

The three loaded values live at bank 7 CPU `$F673` (`LDY #$30`), `$F67B`
(`LDY #$50`), and `$F681` (`LDY #$70`), and become the thrower's
`ObjTimer` — its cooldown before it starts acting (and throwing) again.
`Random, X` is compared as an unsigned byte, so `Else: $70` covers values
`$70`-`$FF`, 143 of the 256 possible rolls (about 56%) — the widest of the
three bands, and therefore the byte that gives the clearest, most
frequently observed effect. This patches the `LDY #$70` immediate at
`$F681` (originally `$70`) to `$08` (8 frames). Raw form: `$F681:08:70`.

One-byte patch. CPU `$F681` falls in bank 7, the fixed bank permanently
mapped to `$C000`-`$FFFF` under this ROM's MMC1 setup — unlike the
switchable `$8000`-`$BFFF` window, this address is unambiguous on hardware
no matter which of the other banks is switched in, so no cross-bank check
applies here; the disassembler itself confirms the bank argument is ignored
above `$C000`.

**Caveat — the other two bands are untouched.** Rolls under `$30` (about
19% of throws) still get the original `$30`-frame cooldown, and rolls
`$30`-`$6F` (about 25%) still get `$50` frames, so roughly 44% of rethrows
still use their original, longer timers. To shorten every band, also apply
these optional companion codes: `$F673:08:30` (`AANYLTAU`) for the `< $30`
case, and `$F67B:08:50` (`AANNLTAS`) for the `< $70` case.

**Not live-verified:** derived from reading `@CatchBoomerang`
(`src/Z_07.asm`), not from observing it in-game.

## Sword and magic-rod shots always spawn, even right at the screen edge

**Codes:** `AAUNXAGP` `NYUNVEKV`

**Effect:** Firing the sword beam (at full health) or the Magic Rod
horizontally while standing very close to the left or right edge of the
screen normally fails silently — the shot is created and instantly
destroyed before it ever appears. With this pair of codes, that
suppression never triggers, so horizontal shots always spawn no matter how
close Link is to the edge.

**How it works:** `SetUpWeaponWithState` (`src/Z_07.asm:4570`) is the
shared setup routine both `MakeSwordShot` (`src/Z_07.asm:4616`) and the
magic/rod shot path (`src/Z_07.asm:4562`) fall into once a shot is ready to
activate. Right after placing the shot at Link's position, it checks his
position:

```
SetUpWeaponWithState:
    STA ObjState, X
    LDA #$10
    JSR PlaceWeapon

    ; If the direction is horizontal, and X < $14 or >= $EC, then
    ; deactivate the shot object.
    LDA ObjDir, X
    AND #$03
    BEQ @ChooseSpeed
    LDA ObjX, X
    CMP #$14
    BCC ResetObjState
    CMP #$EC
    BCS ResetObjState
```

If `ObjDir, X` has either of its low two bits set (a horizontal direction,
per this comment), and Link's `ObjX` is below `$14` or at/above `$EC`,
`ResetObjState` zeroes the shot's state before it ever draws or does
anything else — this is a spawn-time gate, not something that kills a shot
already in flight. This patches both immediate operands: the `CMP #$14` at
bank 7 CPU `$F83A` (originally `$14`) to `$00`, and the `CMP #$EC` at bank 7
CPU `$F83E` (originally `$EC`) to `$FF`. Raw forms: `$F83A:00:14` and
`$F83E:FF:EC`. With the low bound at `$00`, the unsigned `CMP`/`BCC` never
takes (`ObjX` is never less than 0); with the high bound at `$FF`, `BCS` is
only taken when `ObjX` is exactly `$FF`, which is effectively never in
practice — so the edge check never fires either way.

Two one-byte patches, both in bank 7, the fixed bank permanently mapped to
`$C000`-`$FFFF` under this ROM's MMC1 setup — unlike the switchable
`$8000`-`$BFFF` window, these addresses are unambiguous on hardware no
matter which of the other banks is switched in, so no cross-bank check
applies to either.

**Caveat — either code alone gives an asymmetric effect.** Applying only
`$F83A:00:14` removes the suppression near the left edge while the
right-edge check still fires; applying only `$F83E:FF:EC` does the reverse.
Both together are needed for shots to spawn near either edge.

**Caveat — vertical shots were never affected.** The `AND #$03` /
`BEQ @ChooseSpeed` skips this whole check when `ObjDir, X` is a vertical
direction, so shots fired up or down were never suppressed near the
top/bottom edges and are unchanged by this code.

**Not live-verified:** derived from reading
`SetUpWeaponWithState`/`MakeSwordShot` (`src/Z_07.asm`), not from observing
it in-game.

## Room scrolling runs at half speed

**Code:** `PASATZZA`

**Effect:** Halves the screen-scroll animation's horizontal speed (used when
walking left or right between rooms) from 2 to 1 pixel/frame in dungeons, and
from 4 to 2 pixels/frame in the overworld. Unlike the published speed-*up*
code above, this one needs no companion patch — the room transition still
completes cleanly on its own.

**How it works:** `ScrollWorldH` (`src/Z_05.asm:650`) picks the scroll speed
and, alongside it, a reference scroll position used later to switch the base
nametable:

```
ScrollWorldH:
    LDA #$02                    ; Use the default scroll speed: 2 pixels a frame.
    LDX #$FE
    LDY CurLevel
    BNE :+
    ASL                         ; Scroll twice as fast if in the overworld.
    LDX #$FC
:
    STA $00                     ; [00] holds the speed.
    STX $01                     ; [01] holds the X position where we must start using NT 1.
```

This is the same immediate the published "Scrolling: Horizontal scroll speed
increased to 4/8 pixels per frame" code touches, just moved the other
direction. This patches CPU `$8256` (bank 5, originally `$02`) to `$01`. Raw
form: `$8256:01:02`. Bank-unique: no other PRG bank holds `$02` at that
`$8000`-window offset (checked against all 8 banks with `romcheck.py`).

**Caveat — why no NT-1 sync patch is needed.** `$01` (stashed in `X`/`$01`
via `LDX #$FE`) is a reference scroll position that `CurHScroll` must land on
exactly for `SwitchToNT1` to fire, and `CurHScroll` must also land on exactly
0 for the scroll to stop (`BEQ IncSubmode`). Both landings only happen if the
speed evenly divides `$100`. `$01` does (as does its overworld double, `$02`
after the `ASL`), so `CurHScroll` steps through every value on the way down
and is guaranteed to hit both the `$FE`/`$FC` reference and final 0 exactly —
unlike an arbitrary speed that doesn't divide `$100` evenly, which can step
past 0 and leave the scroll stuck.

**Not live-verified:** derived from reading `ScrollWorldH` (`src/Z_05.asm`),
not from observing it in-game.

## Objects can move further down into the overworld's bottom edge

**Code:** `ETSLYESK`

**Effect:** On the overworld, Link and every other object can walk further
past the bottom edge of the play area than normal before the bound clamp
stops them.

**How it works:** Byte 3 of each `ObjectRoomBounds*` row is `RoomBoundDown`
(`src/Z_05.asm:6438`, `Variables.inc:94`), copied into the live bound
variable by `SetupObjRoomBounds` (`src/Z_05.asm:6444`) and checked by
`BoundDirectionVertically` (`src/Z_01.asm:3428`):

```
ObjectRoomBoundsOW:
    .BYTE $11, $E0, $4E, $CD, $89
...
@Down:
    ; Check down boundary.
    ; If Y coordinate is within (<) down bound, return and leave direction alone.
    LDY #$04
    LDA $00
    CMP RoomBoundDown
    BCS BoundDirectionReturn    ; If Y coordinate crosses (>=) right boundary, go reset target direction.
```

This patches `ObjectRoomBoundsOW` byte 3 at bank 5 CPU `$B057` (originally
`$CD`) to `$E8`. Raw form: `$B057:E8:CD`. No other PRG bank holds `$CD` at
that `$8000`-window offset.

**Caveat — applies to everything, not just Link.** Enemies and projectiles
get the same lowered floor.

**Caveat — same family as three already-published `ObjectRoomBounds*` codes.**
"Objects can move further into the underworld screen's left edge" patches
`ObjectRoomBoundsUW` byte 0 (`$B059`); "...the overworld's right edge"
patches `ObjectRoomBoundsOW` byte 1 (`$B055`); "...up into the overworld
status bar" patches `ObjectRoomBoundsOW` byte 2 (`$B056`). This code adds
`ObjectRoomBoundsOW` byte 3 (down). The OW-left and UW-right/up/down bytes in
this same table remain unpublished.

**Not live-verified:** derived from reading `SetupObjRoomBounds` and
`ObjectRoomBoundsOW` (`src/Z_05.asm`), not from observing it in-game.

## Link barely steps out of dungeon doorways heading right or down

**Code:** `EYNUAEES`

**Effect:** When Link leaves a dungeon room through a wall-level doorway to
the right or downward, the automatic walk that carries him out to the edge of
the play area is much shorter, so the room transition starts almost at once.
Paired with the already-published left/up code, exits become symmetric again
(both short instead of one short and one full-length).

**How it works:** `InitMode6` (`src/Z_05.asm:6466`) picks how far Link has to
walk before the room actually changes, from a 3-byte table, with the header
comment stating the sign convention outright:

```
LeavingRoomRelativePositions:
    .BYTE $28, $D8, $00
...
    ; If walking in a decreasing direction (left or up), then
    ; Link's relative position is $28 and has to decrease to 0.
    ;
    ; If walking in an increasing direction (right or down), then
    ; Link's relative position is -$28 and has to increase to 0.
...
    LDA LeavingRoomRelativePositions, Y
    STA ObjGridOffset
```

This patches byte 1 at bank 5 CPU `$B078` (originally `$D8`, i.e. `-$28`) to
`$F8` (`-$08`). Raw form: `$B078:F8:D8`. No other PRG bank holds `$D8` at
that `$8000`-window offset.

**Caveat — pairs with the published left/up code.** The existing "Link barely
steps out of dungeon doorways" code shortens byte 0 (`$B077`, `$28`&rarr;`$08`,
the decreasing/left-up direction) but leaves byte 1 unchanged, so right/down
exits stayed full-length until now. Applying both makes every wall-level
doorway exit short.

**Not live-verified:** derived from reading `InitMode6` and
`LeavingRoomRelativePositions` (`src/Z_05.asm`), not from observing it
in-game.

## The fade to black entering a dark room is shorter

**Code:** `ZKOAALAG`

**Effect:** When Link walks from a lit room into a dark one, the screen fades
to black in roughly a third of the normal time instead of running the full
4-step cycle.

**How it works:** `InitMode7_Sub5`'s `@DarkenRoom` (`src/Z_05.asm:927`) kicks
off the fade by writing a start index into `FadeCycle`:

```
@DarkenRoom:
    ; Going from room with light to a dark room.
    LDA #$00                    ; The next room will not be lit yet.
    STA CandleState
    LDA #$40                    ; Start a fade-to-black cycle.
    STA FadeCycle
    INC GameSubmode
    RTS
```

`AnimateWorldFading` (`src/Z_01.asm:4743`) reads `FadeCycle` as two hex
digits `XY`: `X` selects which cycle's palette row to use, `Y` (0-3) is the
step within it. Each call maps the current value to an offset `X0 + Y*8` into
`LevelInfo_PaletteCycles`, transfers 8 bytes of palette from there, then
increments `FadeCycle` and checks whether its low nibble has reached `4`
(done):

```
    INC FadeCycle
    LDA FadeCycle
    AND #$0F
    CMP #$04
    BEQ @ReturnDone
```

This patches the `LDA #$40` operand at bank 5 CPU `$8390` (originally `$40`)
to `$42`. Raw form: `$8390:42:40`. No other PRG bank holds `$40` at that
`$8000`-window offset. Starting at step 2 instead of step 0 means only 2 of
the normal 4 palette steps run before the low-nibble-4 check ends the cycle,
so the room reaches full darkness in about a third of the normal ~30-frame
span (steps are 10 frames apart) instead of the full span. Offset `$50`
(step 2) is a step this same cycle already visits on the way to `$58` (the
final, darkest step also used as the starting point for the reverse
fade-to-light cycle below), so it's a palette entry the game already treats
as valid mid-cycle data, not an out-of-table read.

**Caveat — the fade-to-light twin is untouched.** `InitMode4`
(`src/Z_05.asm:1510`) starts the reverse cycle the same way, with `LDA #$C0`
feeding the same `SetFadeCycleAndAdvanceSubmode` routine (CPU `$87B2`, not
patched by this code) when brightening a room after leaving a dark one. That
fade still runs at full length; only darkening is shortened.

**Not live-verified:** derived from reading `InitMode7_Sub5` and
`AnimateWorldFading` (`src/Z_05.asm`, `src/Z_01.asm`), not from observing it
in-game.

## The push block search scans a higher row of the dungeon

**Code:** `IAEXUEZA`

**Effect:** When a dungeon room is set up to have a pushable block object,
the game looks for the block tile in a different row of the room than
normal (row 5 of the play area instead of row 10), so the block that gets
made interactive is a different one than the room's layout intends.

**How it works:** `FindAndCreatePushBlockObject` (`src/Z_05.asm:5470`) scans
across a fixed row of the play area's column data, looking for a block tile
(`$B0`); the row number is set at `src/Z_05.asm:5495`:

```
    ; Look for a block tile in row $A of play area, starting in column 4.
    LDX #$08
    LDY #$0A

@LoopColumn:
    LDA PlayAreaColumnAddrs, X
    STA $00
    LDA PlayAreaColumnAddrs+1, X
    STA $01
    LDA ($00), Y
    CMP #$B0
    BEQ @Found
```

This patches the `LDY #$0A` operand at bank 5 CPU `$A80B` (originally `$0A`)
to `$05`. Raw form: `$A80B:05:0A`. No other PRG bank holds `$0A` at that
`$8000`-window offset.

**Caveat — the object detaches vertically, not horizontally.** Once a block
tile is found, `@Found` computes `ObjX+11` dynamically from the column the
match was found in, so the X placement always lines up with whichever column
matched. But `ObjY+11` is hard-coded to `$90` (the pixel Y of row `$A`)
regardless of which row was actually searched:

```
@Found:
    TXA
    ASL
    ASL
    STA ObjX+11
    LDA #$90                    ; Row $A is at $90 from the top of the screen.
    STA ObjY+11
```

With the search row changed to `$05`, the block object's X still lines up
with the matched tile, but its Y is still planted at row `$A`'s pixel
position — the interactive block object appears vertically detached from the
tile that was actually found.

**Caveat — one room bypasses the scan entirely.** Unique room ID `$21` skips
straight to a hard-coded `($40, $80)` position (the "Begin/End unverified
code" block just above the scan), so this patch has no effect in that room.

**Not live-verified:** derived from reading `FindAndCreatePushBlockObject`
(`src/Z_05.asm`), not from observing it in-game.

## Link's walk-out from a cave or dungeon entrance is shorter

**Code:** `AAUEYTAO`

Tags: `utility`

**Effect:** When Link re-emerges onto the overworld after leaving a cave or
dungeon, the walking-up animation that carries him from off-screen back into
view is about half as long.

**How it works:** `InitMode10` (`src/Z_05.asm:1394`) runs when Link steps
onto a cave/dungeon entrance tile (`$24`) and records a target Y position
`$10` pixels below his current one:

```
InitMode10:
    LDX #$00                    ; Get the tile the player is standing on (on the hotspot).
    JSR GetCollidableTileStill
    CMP #$24
    BNE :+                      ; If player touched any stairs tile instead of a cave or dungeon entrance, go start updating.
    LDA #$00                    ; TODO: ?
    STA SongEnvelopeSelector
    LDA #$08                    ; Stairs effect
    STA EffectRequest

    ; Set the target Y coordinate $10 pixels below current one.
    LDA ObjY
    CLC
    ADC #$10
    STA StairsTargetY
```

That `StairsTargetY` is consumed later, in `StepOutside` (`src/Z_07.asm:1782`),
when Link comes back out of the underground onto this same overworld
entrance: he starts hidden behind the background and is walked up 1 pixel
every 4 frames until his Y matches the recorded target:

```
    ; We're entering the OW room from a cave or dungeon.
    LDA #$05
    JSR SwitchBank
    JSR AnimateAndDrawLinkBehindBackground

    ; Every 4 frames, move Link up 1 pixel.
    LDA FrameCounter
    AND #$03
    BNE @Exit
    DEC ObjY
    LDA ObjY
    CMP StairsTargetY
    BEQ GoToNextModePlayLevelSong    ; If Link has reached the target position, go finish the mode.
```

This patches the `ADC #$10` operand at bank 5 CPU `$863F` (originally `$10`)
to `$08`. Raw form: `$863F:08:10`. No other PRG bank holds `$10` at that
`$8000`-window offset. Halving the offset halves how far below the doorway
Link starts when climbing back into view, so the walk-out animation takes
about half as many frames.

**Caveat — "Stairs" is the game's internal name for this transition**, per
the `EffectRequest` comment ("Stairs effect") in `InitMode10`, even though
the code path is specifically for cave/dungeon entrance tiles (`$24`), not
literal in-room staircases.

**Not live-verified:** derived from reading `InitMode10` (`src/Z_05.asm`) and
`StepOutside` (`src/Z_07.asm`), not from observing it in-game.

## Link flashes longer before the death spin starts

**Codes:** `AZSANZAP` + `PGSEKZPZ`

**Effect:** After Link's last heart is lost, he flashes (invincibility
flicker) for noticeably longer before the death spin animation kicks in,
instead of the flash and the wait ending together almost immediately.

**How it works:** `InitMode11` submode 0 (`src/Z_05.asm:2046`) sets up two
timers when Link dies — `ObjInvincibilityTimer` and `ObjTimer` — and its own
comment states they're meant to measure the same span, since one counts down
every 2 frames and the other every frame:

```
    INC GameSubmode
    LDA #$10                    ; Set the invincibility timer, so that Link will flash for a fixed amount of time.
    STA ObjInvincibilityTimer

    ; Invincibility timers count down every 2 frames, while
    ; object timers count every frame. So, these 2 timers measure
    ; about the same amount of time.
    LDA #$21
    STA ObjTimer
```

`InitMode11_Sub1` (`src/Z_05.asm:2067`) only starts the death spin once
`ObjTimer` hits 0 — that's the timer that actually gates "before the death
spin starts." But the flashing itself is driven separately, by
`Anim_WriteSpritePair` (`src/Z_01.asm:5198`), which only patches in the
flicker while `ObjInvincibilityTimer` is nonzero:

```
    ; If not currently invincible, then leave the attributes alone.
    LDY ObjInvincibilityTimer, X
    BEQ Anim_WriteSpritePairNotFlashing
```

and `DecrementInvincibilityTimer` (`src/Z_07.asm:5782`) counts it down
independently of `ObjTimer`. Because of that split, raising only one of the
two timers doesn't give the effect its name promises: raising `ObjTimer`
alone delays the spin, but the flash (paced by the unchanged, smaller
`ObjInvincibilityTimer`) still runs out first, leaving Link standing still
and fully visible for the rest of the wait; raising `ObjInvincibilityTimer`
alone extends how long the flash *could* last, but the spin still cuts it off
at the original, shorter `ObjTimer`. Both reads best — the two codes need to
be applied together, scaled by the same factor (`$10`&rarr;`$20`,
`$21`&rarr;`$41`, preserving the original `ObjTimer = 2*ObjInvincibilityTimer + 1`
relationship), so the flash and the wait still end at essentially the same
moment, just later.

**Code 1 (`AZSANZAP`)** patches the `LDA #$10` operand at bank 5 CPU `$8A57`
(originally `$10`) to `$20`. Raw form: `$8A57:20:10`.

**Code 2 (`PGSEKZPZ`)** patches the `LDA #$21` operand at bank 5 CPU `$8A5C`
(originally `$21`) to `$41`. Raw form: `$8A5C:41:21`.

**Caveat — `$8A57` is NOT bank-unique.** Bank 4 also holds `$10` at this
`$8000`-window offset, so Code 1 fires whenever either bank is mapped in;
expect unrelated side effects while bank 4 (object AI) is active. `$8A5C`
(Code 2) is bank-unique: no other PRG bank holds `$21` at that offset.

**Caveat — applying only one code.** See "How it works" above: alone, either
code produces a different, less coherent effect than "flashes longer" (a
longer static wait with the same flash, or a flash that's cut short by an
unchanged spin start).

**Not live-verified:** derived from reading `InitMode11`
(`src/Z_05.asm`), `Anim_WriteSpritePair` (`src/Z_01.asm`), and
`DecrementInvincibilityTimer` (`src/Z_07.asm`), not from observing it
in-game.

## Link uses monster-sized movement cells

**Codes:** `AOENTEAA` + `ENOYAEEY`

**Effect:** Link's movement now uses the same "grid cell" limit the engine
normally reserves for monsters. His walking speed itself is unchanged, but
the point at which his fractional movement stops accumulating extra offset
from his last grid-aligned position doubles from 8 pixels to 16 in every
direction, matching the +-16 limit non-player objects already use.

**How it works:** `MoveObject` (`src/Z_07.asm:2768`) sets up two limits
before moving any object, based on whether the object is Link (object
index 0):

```
MoveObject:
    LDA #$08                    ; Positive limit is 8 for Link.
    LDY #$F8                    ; Negative limit is -8 for Link.
    CPX #$00
    BEQ :+                      ; If the object isn't Link,
    LDA #$10                    ; then use $10 and -$10.
    LDY #$F0
:
    STA PositiveGridCellSize    ; Store the limits that we determined.
    STY NegativeGridCellSize
```

`BEQ :+` branches away from the override only when `X` = 0, i.e. only for
Link — so the top two immediates are Link's own values, and the `LDA
#$10`/`LDY #$F0` pair a few lines down is what every other object falls
through to. `PositiveGridCellSize`/`NegativeGridCellSize` are then read by
`AddQSpeedToPositionFraction` and `SubQSpeedFromPositionFraction`
(`src/Z_01.asm:3518`, `3557`), which apply the object's fractional q-speed
to its position every quarter-step:

```
    ; Don't let positions go past the limits
    ; If we're at a limit, then clear carry.
    LDA ObjGridOffset, X
    CMP PositiveGridCellSize
    BEQ @ClearCarry
    CMP NegativeGridCellSize
    BNE :+
```

Once `ObjGridOffset` (the object's pixel offset from its last grid-aligned
position) reaches the limit, the carry that would advance it further is
cleared — movement in that direction stops accumulating into
`ObjGridOffset` even though whole-pixel position (`ObjX`/`ObjY`) keeps
moving. `ObjGridOffset` returning to exactly 0 is itself a gate elsewhere —
`Walker_CheckTileCollision` (`src/Z_07.asm:2857`), called immediately
before `MoveObject` every frame (`src/Z_07.asm:2755`), only re-evaluates
blocked directions and tile collisions when `ObjGridOffset` = 0
(`src/Z_07.asm:2874`) — and the room-to-room scroll transition
(`UpdateMode4and6EnterLeave`, `src/Z_07.asm:1753`) advances the game mode
specifically when `ObjGridOffset` reads `$00`, `$08`, or `$F8`.

**Code 1 (`AOENTEAA`)** patches the positive-limit immediate at bank 7 CPU
`$F08E` (originally `$08`) to `$10`. **Code 2 (`ENOYAEEY`)** patches the
matching negative-limit immediate at bank 7 CPU `$F090` (originally `$F8`)
to `$F0`. Raw forms: `$F08E:10:08` and `$F090:F0:F8`. Both bytes are
needed together for a symmetric +-16 change — patching only one gives Link
mismatched positive and negative limits. Neither byte's compare collides
with anything: bank 7 is the fixed `$C000`-`$FFFF` window, so no other
bank can ever be mapped there regardless. (The non-player pair the branch
falls through to lives a few bytes later, at bank 7 CPU `$F096`/`$F098` —
already `$10`/`$F0` and untouched by this patch.)

**Caveat — every walking monster already uses this limit.** `MoveObject`
is the shared movement routine for every object, so this doesn't add a new
mechanic to Link; it just gives him the same grid tolerance monsters
already had.

**Caveat — the room-transition trigger checks for exactly `$08`/`$F8`, and
appears unaffected.** `UpdateMode4and6EnterLeave`'s own check tests
`ObjGridOffset` against `$00`/`$08`/`$F8` every frame and changes game mode
(resetting `ObjGridOffset` to 0) the instant one of those values shows up,
before `ObjGridOffset` would ever have a chance to climb toward the new
16-pixel ceiling during that specific transition. What isn't traced here
is every other place — ordinary in-room walking, doorway alignment, corner
turning — that depends on how far `ObjGridOffset` can climb before
returning to 0; those are read here only as far as confirming they gate on
`ObjGridOffset`, not as a full model of how the extra travel plays out.

**Not live-verified:** derived from reading `MoveObject`
(`src/Z_07.asm`), `AddQSpeedToPositionFraction`/
`SubQSpeedFromPositionFraction`, and their `ObjGridOffset` consumers
(`src/Z_01.asm`, `src/Z_07.asm`), not from observing it in-game.

## Link's walk cycle animates every frame

**Code:** `PASNKZTA`

Tags: `play-start`

**Effect:** Link's (and every walking monster's) leg-animation frame now
advances every single frame instead of once every 6 frames — a much
faster-flickering walk cycle. Pure cosmetic change; movement speed itself
is untouched.

**How it works:** `AnimateObjectWalking` (`src/Z_07.asm:5078`) ticks a
per-object animation counter down and only advances the walk frame once it
rolls over:

```
AnimateObjectWalking:
    DEC ObjAnimCounter, X
    BNE SetUpWalkingSprites

    ; Once the counter reaches 0, and if object is the player,
    ; animate Link's object state.
    CPX #$00
    BNE :+
    JSR AnimateLinkObjState
:
    ; Roll over the counter (6 frames).
    LDA #$06
    STA $00
    JSR RollOverAnimCounter
```

`RollOverAnimCounter` reloads `ObjAnimCounter` from `[$00]`, so the `LDA
#$06` immediate sets how many frames elapse between animation ticks. This
patches that immediate at bank 7 CPU `$FA5C` (originally `$06`) to `$01`.
Raw form: `$FA5C:01:06`. No other PRG bank holds `$06` at that offset
(bank 7 is the fixed `$C000`-`$FFFF` window, so no other bank can ever be
mapped there regardless).

**Caveat — applies to every walking object, not just Link.**
`AnimateObjectWalking` is the shared per-object walk-animation routine;
every walking monster on screen gets the same 1-frame roll-over.

**Not live-verified:** derived from reading `AnimateObjectWalking`
(`src/Z_07.asm`), not from observing it in-game.

## The file-select menu cycles through fewer options

**Code:** `GEUZAIIA`

**Effect:** On the file-select screen, pressing Select to cycle the cursor
through the three save slots, REGISTER YOUR NAME, and ELIMINATE MODE now
skips ELIMINATE MODE entirely — Select can no longer land the cursor on
it.

**How it works:** `UpdateMode1Menu_Sub0` (`src/Z_02.asm:2749`) treats
`CurSaveSlot` as a 0-4 menu index (0-2 are save slots, 3 is REGISTER, 4 is
ELIMINATE) and wraps it back to 0 once it goes out of range:

```
@ChangeSelection:
    LDA #$01                    ; Request to play the selection change SFX (same as rupee taken).
    STA Tune1Request
    INC CurSaveSlot             ; Select the next slot or option.
    LDA CurSaveSlot
    CMP #$05
    BNE :+                      ; If the index is out of bounds,
    LDA #$00                    ; then wrap around to zero.
    STA CurSaveSlot
:
    LDY CurSaveSlot

    ; Since CurSaveSlot is used to index menu choices, which
    ; includes register and eliminate in addition to save slots;
    ; the IsSaveSlotActive array includes elements at the end
    ; for these options.
    LDA IsSaveSlotActive, Y
    BEQ @ChangeSelection        ; If option or save slot isn't active, then go advance the index.
```

`IsSaveSlotActive` (`$633`) is only 3 bytes long (one per save slot); the
next two RAM addresses are separately named `IsRegisterSaveFileOptionEnabled`
(`$636`) and `IsEliminateSaveFileOptionEnabled` (`$637`)
(`src/Variables.inc:232-233`) — confirming index 3 and index 4 of this
`, Y`-indexed read land on real, documented "is this option enabled" flags
for REGISTER and ELIMINATE respectively, not undocumented memory.

This patches the wrap-point immediate `CMP #$05` at bank 2 CPU `$A5B0`
(originally `$05`) to `$04`. Raw form: `$A5B0:04:05`. Since `INC
CurSaveSlot` runs before the compare, changing the wrap target to 4 means
the very increment that would have produced index 4 (ELIMINATE) is
immediately wrapped back to 0 instead — `IsEliminateSaveFileOptionEnabled`
is never even read, and the cursor cycles through slots 0-2 and REGISTER
(index 3) only. No other PRG bank holds `$05` at that `$8000`-window
offset.

**Caveat — ELIMINATE MODE isn't removed, only unreachable by cycling.**
Nothing about `InitModeEandF_Full` (the shared register/eliminate handler)
or `GameMode` changes; if some other path still sets `CurSaveSlot` to 4,
ELIMINATE MODE would presumably still run. This patch only removes
Select's ability to land the cursor there.

**Not live-verified:** derived from reading `UpdateMode1Menu_Sub0`
(`src/Z_02.asm`) and the `IsSaveSlotActive`/`IsRegisterSaveFileOptionEnabled`/
`IsEliminateSaveFileOptionEnabled` layout (`src/Variables.inc`), not from
observing it in-game.

## Saving zeroes out Link's hearts instead of refilling them

**Code:** `AENZYTEY`

**Effect:** Choosing SAVE from the pause/continue menu (game mode `$0D`,
`UpdateModeDSave`) no longer heals Link to full hearts as a side effect.
Instead, the live heart value that drives the rest of the current play
session — and the file-select screen's heart icons — is forced to zero:
both Link's heart-container count and his current hearts read as empty
until a fresh profile is loaded.

**How it works:** `HeartValues` packs heart-container count and Link's
current hearts into one byte (high nibble = container count, low nibble =
current hearts) — confirmed independently by the damage-handling code in
`src/Z_01.asm:5779` (`LDA HeartValues / AND #$0F / CMP $0D`, testing
current hearts) and by the cave heart-requirement check in
`src/Z_01.asm:813` (`CPY HeartValues`, comparing against values like `$40`
and `$B0` that only make sense as container counts sitting in the high
nibble).

`UpdateModeDSave_Sub0` (`src/Z_02.asm:2978`) rebuilds this byte into a
"full hearts" value right before the save screen advances:

```
    LDA HeartValues             ; Put in [$0A] a full hearts value for the profile's heart containers.
    AND #$F0
    PHA
    LSR
    LSR
    LSR
    LSR
    STA $0A
    PLA
    ORA $0A
    STA HeartValues
```

`AND #$F0` isolates the container-count nibble; `LSR` x4 copies that same
value down into `[$0A]` as a low-nibble number; `ORA $0A` then rejoins the
untouched high nibble with that copy in the low nibble, so the byte
written back to `HeartValues` has current hearts equal to container
count — a full heal.

This patches the `AND` mask at bank 2 CPU `$A6F7` (originally `$F0`) to
`$00`. Raw form: `$A6F7:00:F0`. With the mask zeroed, the value pushed to
the stack, the value shifted into `[$0A]`, and the final `ORA` are all
zero, so `STA HeartValues` writes `$00` — zero containers, zero current
hearts — instead of a full heal. The compare byte (`F0`) pins this to bank
2's `$8000`-window offset; bank 7 also holds `$F0` at that offset, but
bank 7 is the fixed top bank at `$C000` and is never mapped into the
`$8000` window, so it can't collide.

**Caveat — the save file itself is unaffected.** `HeartValues` is byte 24
of the 40-byte `Items` block (`Items` = `$657`, `HeartValues` = `$66F`),
and that whole block is copied into file B earlier in this same routine
(`LDA Items, Y / STA ($C0), Y`, a few lines above), before this rebuild
ever runs. So the bytes actually written to the save file keep whatever
hearts Link had at the moment SAVE was chosen; only the live in-RAM value
(and therefore the current session's gameplay and the file-select heart
icons) gets zeroed.

**Caveat — the next hit likely reads as fatal.** With current hearts (the
low nibble) already at zero, both branches of the damage-handling code
treat that as "Link died": the main path
(`src/Z_01.asm:5779-5782`, `LDA HeartValues / AND #$0F / CMP $0D / BCC
@HandleDied`) takes the death branch whenever full hearts are less than
the damage amount, which zero always is for any nonzero hit; the borrow
path (`src/Z_01.asm:5802-5804`, `LDA HeartValues / AND #$0F / BEQ
@HandleDied`) checks for exactly zero and takes the same branch. Whether
this fires immediately on saving or only on Link's next hit is not traced
here — only that the byte pattern this patch produces is the exact one
both paths already treat as death.

**Not live-verified:** derived from reading `UpdateModeDSave_Sub0`
(`src/Z_02.asm`) and the `HeartValues` consumers in `src/Z_01.asm`, not
from observing it in-game.

## Formatted files get a different blank-name character

**Code:** `ZAVZALGX`

**Effect:** After ELIMINATE FILE clears a save slot (or the game
reformats a corrupt/blank file at boot), the file-select screen shows the
name filled with a repeated letter instead of blank spaces.

**How it works:** `FormatFileA` (`src/Z_02.asm:2374`) clears a file's
8-character name by writing the same fill byte 8 times:

```
FormatFileA:
    LDY #$07
    LDA #$24                    ; Make the name 8 spaces.

@ClearName:
    STA ($04), Y
    DEY
    BPL @ClearName
```

`$24` is the space character in this game's tile-index character
encoding — the same encoding `ModeE_CharMap` (`src/Z_02.asm:1423`) maps,
where index 0 is `$0A` ('A'), confirmed by the already-published
"second-quest magic name becomes AELDA" entry in this document, which
uses that identical `$0A` = 'A' mapping. `FormatFileA` is called from
three real, player-reachable places: clearing inactive slots at boot
(`src/Z_02.asm:256`), `DeleteSlot` — the ELIMINATE FILE handler
(`src/Z_02.asm:1787`) — and reformatting a file that fails its checksum
check at boot (`src/Z_02.asm:2308`).

This patches the immediate at bank 2 CPU `$A360` (originally `$24`) to
`$0A`. Raw form: `$A360:0A:24`. No other PRG bank holds `$24` at that
`$8000`-window offset. Formatted/eliminated names now read as
`AAAAAAAA` instead of eight blank spaces.

**Caveat — `FormatFileB` carries the identical immediate but isn't
patched here.** `FormatFileB` (`src/Z_02.asm:2511`) does the same
`LDA #$24` fill for file B (the staging buffer written during a normal
SAVE, before it's committed to file A) at bank 2 CPU `$A43A`. Bank 6 also
holds `$24` at that same `$8000`-window offset, and bank 6 *is* a real
switchable bank at `$8000`-`$BFFF` — unlike the fixed bank-7 case
elsewhere in this document, a Game Genie compare byte here would also
match live bank-6 code/data, corrupting whatever's there whenever bank 6
is mapped in during normal play. One code (on `FormatFileA`, which covers
every player-visible formatting path — boot cleanup, ELIMINATE FILE, and
checksum-failure recovery) is judged to cover the effect without adding
that risk.

**Not live-verified:** derived from reading `FormatFileA`/`FormatFileB`
(`src/Z_02.asm`) and their call sites, not from observing it in-game.

## Overworld rock walls are pushed aside instead of bombed open

**Code:** `ZTNZOPLT`

**Effect:** The bombable rock walls in the overworld stop being bombable and
become pushable rocks, like the stones that slide aside to uncover a
staircase. Walk up to a wall with the Power Bracelet, line up under (or over)
it, and hold into it: the wall slides one square, leaving gray floor behind,
the "secret found" tune plays, and the room's hidden staircase appears.

**How it works:** While laying out an overworld room, `CheckTileObject`
(`src/Z_05.asm:5924`) recognises the marker squares `$E5`-`$EA` in the room
data and, for each one, pairs a *type* with the square that actually gets
drawn:

```
TileObjectTypes:
    .BYTE $62, $63, $64, $65, $66, $67
TileObjectPrimarySquaresOW:
    .BYTE $C8, $D8, $C4, $BC, $C0, $C0
...
    LDA TileObjectPrimarySquaresOW, X
    PHA                         ; Save primary square.
    LDA TileObjectTypes, X
    STA RoomTileObjType
```

Index 1 is the rock wall: marker square `$E6`, drawn as square `$D8`, object
type `$63`. `UpdateObject_JumpTable` (`src/Z_07.asm:5321`) sends type `$63` to
`UpdateRockWall` (`src/Z_04.asm:3716`), which waits for a bomb in state `$13`
to collide with it, and type `$62` (rock) to `UpdateRockOrGravestone`
(`src/Z_04.asm:3569`), which is the push handler:

```asm
    ; If this is not a gravestone (but it's a rock), and there is no
    ; bracelet, then return.
    LDA ObjType, X
    CMP #$65
    BEQ @CheckQuest
    LDA InvBracelet
    BEQ @Exit
...
    ; The gravestone and rocks can only be pushed vertically.
    ; Return, if X's don't match.
```

This patches `TileObjectTypes` byte 1 at bank 5 CPU `$A971` (originally `$63`,
rock wall) to `$62`, rock. Raw form: `$A971:62:63`. The paired entry in
`TileObjectPrimarySquaresOW` is untouched, so the square still *looks* like a
rock wall; only the object driving it changes. On the push,
`UpdateRockOrGravestone` writes the gray floor tile `$26` at the wall's old
square, slides a rock sprite one square, writes the rock square `$C8` where it
lands, calls `MarkRoomVisited` for the room, then places the stairs tile `$70`
at `GetShortcutOrItemXYForRoom`'s position and plays the secret tune.

**Caveat — it needs the Power Bracelet, exactly like a real push rock.**
The `InvBracelet` test above is only skipped for the gravestone type (`$65`).
Without the bracelet these walls can no longer be opened at all: the bomb path
is gone and the push path returns immediately. For a bracelet-free variant,
`ITNZOPLT` (`$A971:65:63`) makes them gravestones instead — pushable with no
item, at the cost of landing as a gravestone square (`$BC`) and taking the
gravestone's ghost palette row (`$20`) in `InitMode5Play`.

**Caveat — the staircase appears at the room's shortcut position, not where
the wall was.** A bombed wall becomes a black cave mouth at the wall itself
(`UpdateRockWall` → `RevealAndFlagSecretTileObj`, tile `$24`); the rock path
instead reveals stairs wherever `GetShortcutOrItemXYForRoom`
(`src/Z_01.asm:4050`) says, from the room's 2-bit shortcut/item position
attribute. In rooms built around a bombable wall that attribute may point
somewhere unrelated, so the staircase can land in an odd spot.

**Caveat — the secret is flagged as a shortcut, not as "secret found".**
The rock path calls `MarkRoomVisited` (`src/Z_07.asm:783`), which sets room
flag bit `$20`, rather than the bit `$80` that `RevealAndFlagSecretTileObj`
sets. That is the bit `CheckShortcut` (`src/Z_05.asm:6071`) tests when
redrawing the room later, and its rock-wall case explicitly asks for
`RoomTileObjType` = `$62`:

```
    CMP #$D8
    BNE @WriteStairs            ; If it's not a rock wall, then go prepare a stairs square.
    LDA RoomTileObjType
    CMP #$62
    BEQ @WriteStairs            ; If the room's tile object is a rock, go prepare a stairs square.
```

With this patch that test now passes in these rooms, so the revealed stairs
should persist across visits.

**Caveat — the room's sprite palette changes.** `InitMode5Play`
(`src/Z_07.asm:1499`) picks a palette row from the tile object's type on every
overworld room entry. Type `$63` falls through to the red Armos row (`$7A`);
type `$62` takes the rock branch and selects brown (`$24`) or green (`$22`)
from the room's inner-palette attribute. Sprite colours in rock-wall rooms
will shift.

**Caveat — bank-unique.** No other PRG bank holds `$63` at that
`$8000`-window offset.

**Caveat — adjacent to a published code.** "Swap which tile object type
appears first" patches byte 0 of this same table at `$A970`. The two codes are
independent bytes and can be used together, but both alter `TileObjectTypes`.

**Not live-verified:** derived from reading `CheckTileObject`,
`UpdateRockOrGravestone`, `UpdateRockWall`, `CheckShortcut` and
`InitMode5Play` (`src/Z_04.asm`, `src/Z_05.asm`, `src/Z_07.asm`), not from
observing it in-game.

## Every overworld screen gets one pushable wall

**Codes:** `KSKZEXXV` + `ZTNZOPLT` (both needed)

**Effect:** Ordinary mountain walls — the plain scenery kind, not the six real
bombable ones — become pushable. One wall per overworld screen turns into a
push-rock object that looks exactly like a wall: line up under it with the
Power Bracelet, hold into it, and it slides one square aside, plays the
"secret found" tune and uncovers a staircase. With `KSKZEXXV` alone the same
walls become *bombable* instead of pushable.

**How it works:** A tile object exists only where `LayoutRoomOrCaveOW`
(`src/Z_05.asm:5842`) hands `CheckTileObject` (`src/Z_05.asm:5924`) a primary
square inside a six-value window. `CheckTileObject` walks that window
downwards from a single immediate:

```asm
CheckTileObject:
    ; Find the index X corresponding to the primary square: $E5  => 0; $EA => 5.
    LDX #$EA
    STX $0A
    LDX #$05
:
    CMP $0A
    BEQ :+                      ; If we found the primary, go handle it.
    DEC $0A
    DEX
    BPL :-
    BMI L16AF0_Exit             ; If the primary isn't between $E5 to $EA, then return.
:
    LDA TileObjectPrimarySquaresOW, X
    PHA                         ; Save primary square.
    LDA TileObjectTypes, X
    STA RoomTileObjType
```

The matched index picks both the object type and the square that is actually
drawn in place of the marker, so ordinary scenery can be moved into the window
by changing where the window sits. Ordinary walls are primary square `$D8` —
the same square `TileObjectPrimarySquaresOW` index 1 draws for the real
bombable wall, which is why a bombable wall is indistinguishable from scenery.

This patches the window's top value at bank 5 CPU `$AAC0` (originally `$EA`)
to `$DC`. Raw form: `$AAC0:DC:EA`. The window becomes `$D7`-`$DC`, which puts
`$D8` at index 1 — the rock-wall slot. Index 1 draws square `$D8`, exactly what
was there, so the wall's appearance is unchanged; its type becomes `$63`
(rock wall, bombable). Adding `ZTNZOPLT` ("Overworld rock walls are pushed
aside instead of bombed open", `$A971:62:63`) turns index 1's type into `$62`,
routing it to `UpdateRockOrGravestone` (`src/Z_04.asm:3569`) — the push
handler — instead of `UpdateRockWall`.

Counting the square descriptors in `ColumnHeapOW0`-`ColumnHeapOWF`
(`src/Z_05.asm:4235`-`4392`), square `$D8` is used 199 times across the
overworld — the most common non-ground square in the game — so almost every
screen with a mountain edge qualifies.

**Caveat — one wall per screen, and you don't choose which.**
`RoomTileObjType`/`RoomTileObjX`/`RoomTileObjY` are single variables that
`CheckTileObject` overwrites on every match, and `InitMode_EnterRoom`
(`src/Z_05.asm:1854`) copies them into object slot 11 once. Layout runs
left-to-right by column and top-to-bottom within a column, so the *last*
matching square wins: the pushable wall is the bottom-most wall square of the
right-most column that has one.

**Caveat — it disables every real overworld secret.** Moving the window off
`$E5`-`$EA` means the actual marker squares stop matching. The six bombable
walls (`$E6`), three burnable trees (`$E7`), two secret rocks (`$E5`) and one
gravestone (`$E8`) in the shipped room data no longer become tile objects, and
worse, `CheckTileObject` no longer substitutes a real square for them, so
`WriteSquareOW` draws raw tiles `$E5`-`$E8` where those secrets used to be.
Expect visibly wrong squares on those screens.

**Caveat — square `$DC` is redrawn as an armos.** `$DC` (13 uses) also falls
in the new window, at index 5, whose drawn square is `$C0` — the armos square —
and whose type `$67` goes to `UpdateRockWall`. Those squares will change
appearance.

**Caveat — where the staircase leads was never designed.** After the push,
`UpdateRockOrGravestone` writes the stairs tile `$70` at
`GetShortcutOrItemXYForRoom`'s position (`src/Z_01.asm:4050`) and calls
`MarkRoomVisited`. On a screen with no real secret, both the position and
whatever the stairs open into come from room attributes that were never
authored for this, so results there are unpredictable.

**Caveat — quest-gated screens are skipped.** `IsQuestSecretMismatch`
(`src/Z_04.asm:3829`) still runs first; it passes when the room's quest-secret
attribute is 0, which is the ordinary case, but a screen whose secret belongs
to the other quest refuses the push.

**Caveat — bank-unique.** No other PRG bank holds `$EA` at that
`$8000`-window offset.

**Not live-verified:** derived from reading `CheckTileObject`,
`LayoutRoomOrCaveOW`, `InitMode_EnterRoom` and `UpdateRockOrGravestone`
(`src/Z_04.asm`, `src/Z_05.asm`) and counting square usage in the overworld
column heaps, not from observing it in-game.

## Every overworld screen gets one pushable bush

**Codes:** `NKKZEXXT` + `ZTNZXPGT` (both needed)

**Effect:** Ordinary trees and bushes — not the three real burnable ones —
become pushable. One bush per overworld screen turns into a push-rock object
that still looks like a bush: shove it vertically with the Power Bracelet and
it slides aside, plays the "secret found" tune and uncovers a staircase. With
`NKKZEXXT` alone those bushes become *burnable* by the candle instead.

**How it works:** Same mechanism as "Every overworld screen gets one pushable
wall" above — `CheckTileObject` (`src/Z_05.asm:5924`) only builds a tile object
for primary squares inside the six-value window that starts at its `LDX #$EA`
immediate, and the matched index selects both the drawn square and the type.
Ordinary trees and bushes are primary square `$C4`, the same square
`TileObjectPrimarySquaresOW` index 2 draws for the real burnable tree.

This patches the window's top value at bank 5 CPU `$AAC0` (originally `$EA`)
to `$C7`. Raw form: `$AAC0:C7:EA`. The window becomes `$C2`-`$C7`, which puts
`$C4` at index 2 — the tree slot, drawn as `$C4`, so appearance is unchanged —
with type `$64`, `UpdateTree` (`src/Z_04.asm:3746`), the candle-fire handler.
`ZTNZXPGT` then patches `TileObjectTypes` byte 2 at bank 5 CPU `$A972`
(originally `$64`, tree) to `$62`, rock. Raw form: `$A972:62:64`. Type `$62`
goes to `UpdateRockOrGravestone` (`src/Z_04.asm:3569`), so the bush is pushed
rather than burned. Square `$C4` is used 63 times across
`ColumnHeapOW0`-`ColumnHeapOWF` (`src/Z_05.asm:4235`-`4392`).

Nothing else in the shipped overworld data falls inside `$C2`-`$C7`, so unlike
the wall version this window catches bushes and nothing else. Both window
codes patch the *same* byte, so the wall and bush versions cannot be used at
the same time.

**Caveat — it needs the Power Bracelet.** `UpdateRockOrGravestone` skips its
`InvBracelet` test only for the gravestone type. `ITNZXPGT` (`$A972:65:64`)
substitutes `$65`, gravestone, instead: pushable with no item at all, at the
cost of the bush landing as a gravestone square (`$BC`) and taking the ghost
palette row in `InitMode5Play` (`src/Z_07.asm:1499`).

**Caveat — the pushed bush lands as a rock.** `UpdateRockOrGravestone`'s
`@ReplaceTiles` picks the destination square from the object type: `$C8` for a
rock, `$BC` for a gravestone. Either way the square it ends on stops looking
like a bush.

**Caveat — one bush per screen, real secrets break, staircases lead
somewhere unplanned, quest-gated screens are skipped.** All four apply exactly
as described for the wall version above — same single `RoomTileObjType`
slot, same loss of the `$E5`-`$EA` markers, same
`GetShortcutOrItemXYForRoom` placement, same `IsQuestSecretMismatch` gate.

**Caveat — bank-unique.** No other PRG bank holds `$EA` at the `$AAC0`
window offset, nor `$64` at the `$A972` window offset.

**Not live-verified:** derived from reading `CheckTileObject`,
`LayoutRoomOrCaveOW`, `UpdateTree` and `UpdateRockOrGravestone`
(`src/Z_04.asm`, `src/Z_05.asm`) and counting square usage in the overworld
column heaps, not from observing it in-game.

## Ordinary bushes can be burned away with the candle

**Code:** `NKKZEXXT`

**Effect:** Ordinary trees and bushes — the plain scenery kind, not the three
real burnable ones — can be burned with the candle. One bush per overworld
screen becomes a burnable secret: light it, wait for the standing fire to burn
down, and the bush is replaced by a staircase.

**How it works:** A tile object exists only where `LayoutRoomOrCaveOW`
(`src/Z_05.asm:5842`) hands `CheckTileObject` (`src/Z_05.asm:5924`) a primary
square inside a six-value window, and that whole window comes from one
immediate:

```asm
CheckTileObject:
    ; Find the index X corresponding to the primary square: $E5  => 0; $EA => 5.
    LDX #$EA
```

The matched index picks both the object type and the square that gets drawn,
so ordinary scenery becomes a tile object by moving the window onto it.
Ordinary bushes are primary square `$C4` — the same square
`TileObjectPrimarySquaresOW` index 2 draws for the real burnable tree, which is
why a real one is indistinguishable from scenery.

This patches the window's top value at bank 5 CPU `$AAC0` (originally `$EA`) to
`$C7`. Raw form: `$AAC0:C7:EA`. The window becomes `$C2`-`$C7`, putting `$C4`
at index 2 — the tree slot. Index 2 draws square `$C4`, exactly what was there,
and its type `$64` goes to `UpdateTree` (`src/Z_04.asm:3746`), the candle-fire
handler:

```asm
UpdateTree:
    ; If the secret in this room does not apply to the current quest,
    ; then return.
    JSR IsQuestSecretMismatch
    BCS L10F3E_Exit

    ; If there is no standing fire (state $22) in slots $10 and $11,
    ; then return.
```

It then requires the standing fire's timer to be below 2 and the fire to
collide with the tile object, and calls `RevealAndFlagSecretStairsObj`
(`src/Z_04.asm:3779`), writing the stairs tile `$70` where the bush stood.
Square `$C4` is used 63 times across `ColumnHeapOW0`-`ColumnHeapOWF`
(`src/Z_05.asm:4235`-`4392`), and nothing else in the shipped overworld data
falls inside `$C2`-`$C7`, so this window catches bushes and nothing else.

This is the same byte as the first half of "Every overworld screen gets one
pushable bush"; adding `ZTNZXPGT` to it retypes the object from tree to rock,
which trades burning for pushing. Use this code alone to keep burning.

**Caveat — one bush per screen, and you don't choose which.**
`RoomTileObjType`/`RoomTileObjX`/`RoomTileObjY` are single variables that
`CheckTileObject` overwrites on every match, and `InitMode_EnterRoom`
(`src/Z_05.asm:1854`) copies them into object slot 11 once. Layout runs
left-to-right by column, top-to-bottom within a column, so the last matching
square wins: the burnable bush is the bottom-most bush square of the
right-most column that has one.

**Caveat — it disables every real overworld secret.** Moving the window off
`$E5`-`$EA` means the shipped marker squares stop matching, so the six bombable
walls (`$E6`), three burnable trees (`$E7`), two secret rocks (`$E5`) and one
gravestone (`$E8`) no longer become tile objects — and `CheckTileObject` no
longer substitutes a real square for them either, so `WriteSquareOW` draws raw
tiles `$E5`-`$E8` in their place.

**Caveat — the staircase does not persist.** `RevealAndFlagSecretStairsObj`
sets the room's secret-found bit `$80`, but the redraw path in
`LayoutRoomOrCaveOW` only converts a square to stairs when it is marker `$E7`
(or `$EA`). An ordinary `$C4` bush is not, so on re-entering the screen the
bush is drawn again — and, being still inside the window, becomes a fresh
burnable object.

**Caveat — where the staircase leads was never designed.** On a screen with no
real secret, whatever those stairs open into comes from room attributes that
were never authored for it.

**Caveat — quest-gated screens are skipped.** `IsQuestSecretMismatch`
(`src/Z_04.asm:3829`) still runs first; it passes when the room's quest-secret
attribute is 0, the ordinary case, but a screen whose secret belongs to the
other quest refuses to burn.

**Caveat — bank-unique.** No other PRG bank holds `$EA` at that
`$8000`-window offset.

**Not live-verified:** derived from reading `CheckTileObject`,
`LayoutRoomOrCaveOW` and `UpdateTree` (`src/Z_04.asm`, `src/Z_05.asm`) and
counting square usage in the overworld column heaps, not from observing it
in-game.

## Ordinary bushes can be crossed with the stepladder

**Code:** `EKXNZXOO` (add `EYVNIZEI` to make it work on every screen)

**Effect:** The stepladder can be laid across ordinary bushes and trees, the
same way it is laid across water. Walk into a bush holding the ladder and Link
steps over it, one square at a time.

**How it works:** `Link_EndMoveAndAnimate` (`src/Z_07.asm:3269`) decides where
the ladder may be placed by testing the tile Link is walking into against a
range:

```asm
    ; If in OW and tile is not water (as in < $8D or >= $99), then
    ; go check warps and animate.
    ; If in UW, and tile <> $F4, go check warps and animate.
    LDY CurLevel
    BEQ @CheckWaterOW
    CMP #$F4
    BEQ @SetUpLadder
    BNE @CheckWarps

@CheckWaterOW:
    CMP #$8D
    BCC @CheckWarps
    CMP #$99
    BCS @CheckWarps
```

This patches the upper bound at bank 7 CPU `$F2AA` (originally `$99`) to
`$C8`. Raw form: `$F2AA:C8:99`. The accepted range becomes tiles `$8D`-`$C7`,
which now contains `$C4`-`$C7` — the four tiles of the ordinary bush square
`$C4`. Everything downstream is tile-agnostic: `@SetUpLadder` places a ladder
object of type `$5F` one square ahead, and `CheckLadder` (`src/Z_05.asm:3217`)
overrides Link's moving direction so he is not stopped — its own comment says
"This lets Link step onto the ladder. Otherwise he would have been blocked by
the water." Nothing in that path is specific to water.

**Caveat — vanilla only allows the ladder on six overworld screens.**
Before any of this, the routine checks the room against a list:

```asm
    ; If in OW and we're not in this list of 6 rooms, go check warps and animate.
    LDA CurLevel
    BNE @CheckLadder
    LDA RoomId
    LDY #$05

@LoopLadderRoom:
    CMP LadderRoomsOW, Y
```

`LadderRoomsOW` (`src/Z_07.asm:3175`) is `$17, $18, $19, $27, $4F, $5F`. With
`EKXNZXOO` alone, bushes are only crossable on those six screens. Adding
`EYVNIZEI` — bank 7 CPU `$F26D`, the `BNE` opcode (`$D0`) of that `LDA CurLevel`
test flipped to `BEQ` (`$F0`), raw form `$F26D:F0:D0` — makes the overworld
branch straight to `@CheckLadder`, skipping the room list, so bushes (and
water) work on every overworld screen.

**Caveat — `EYVNIZEI` costs the ladder in dungeons.** With the branch flipped,
the underworld now falls into the room-list loop instead of skipping it, so the
ladder is only set up in a dungeon room whose id happens to be one of
`$17/$18/$19/$27/$4F/$5F`. Level 4's ladder crossings will generally stop
working while this code is on.

**Caveat — it widens more than bushes.** The added range `$99`-`$C7` covers
every square whose tiles fall in it, not just `$C4`: squares `$9A`, `$9C`,
`$A0`, `$A2`, `$A6`, `$AA`, `$AC`, `$B0`, `$B4`, `$B8`, `$BC` (gravestone) and
`$C0` (armos) — 37 uses across the overworld column heaps, against 63 for the
bush square itself. Rocks (`$C8`) and walls (`$D8`) sit above the new bound and
stay solid. For bushes and nothing else, add `KKXYTXSA` (`$F2A6:C4:8D`), which
raises the lower bound to `$C4` — but that drops water out of the range, so the
ladder stops working on water entirely.

**Caveat — the ladder still needs the item and grid alignment.** The
`InvLadder` check, the "not in a doorway" check and the grid-offset-zero
requirement are all upstream of the patched byte and are unchanged.

**Caveat — fixed bank.** `$F2AA` and `$F26D` are both in the `$C000`-`$FFFF`
window, which always maps bank 7 on this cart, so no other bank can match the
compare byte.

**Not live-verified:** derived from reading `Link_EndMoveAndAnimate`
(`src/Z_07.asm`) and `CheckLadder` (`src/Z_05.asm`), not from observing it
in-game.

## The Bow on its own fires the Magical Rod's beam

**Code:** `NGXEKTVZ`

**Effect:** The Bow occupies its own inventory slot next to the Arrow, and
selecting it normally does nothing at all — the arrow is what you shoot. With
this code, pressing B with the *Bow* selected fires the Magical Rod's beam
instead. No rod is needed, no arrow is needed, and no rupee is spent.

**How it works:** `WieldItem` (`src/Z_05.asm:2883`) dispatches on
`SelectedItemSlot`, which is an index into the inventory bytes starting at
`Items` (`$0657` in `src/Variables.inc`): 0 boomerang, 1 bombs, 2 arrow,
3 bow, 4 candle, 5 flute, 6 food, 7 potion, 8 rod.

```asm
WieldItem:
    ; If the letter slot is selected, return.
    LDA SelectedItemSlot
    CMP #$0F
    BEQ L14E71_Exit
    JSR TableJump

WieldItem_JumpTable:
    .ADDR WieldBoomerang
    .ADDR WieldBomb
    .ADDR WieldArrow
    .ADDR WieldNothing          ; Slot 3: the bow
    ...
```

`WieldNothing` (`src/Z_05.asm:3000`) is a bare `RTS` — that is why the bow
does nothing. This patches the *low byte of the fourth table entry*, at bank 5
CPU `$8E2C`, from `$A6` (`WieldNothing`, `$8EA6`) to `$C7` (`WieldRod`,
`$8EC7`). Raw form: `$8E2C:C7:A6`. Both handlers live in page `$8E`, so the
high byte of the entry is already correct and one byte moves the dispatch.

The handler it now reaches checks no inventory byte whatsoever:

```asm
WieldRod:
    ; Switch to the rod slot.
    ; If it's already in use, then return.
    LDX #$12
    LDA ObjState, X
    BNE L14EC6_Exit

    ; The first state lasts 5 frames.
    LDA #$05
    STA ObjAnimCounter, X

    ; The initial state is $31.
    LDA #$31
    JMP WieldWeapon
```

`WieldWeapon` sets the object's state, gives it q-speed `$C0` (3 pixels a
frame) and calls `PlaceWeaponForPlayerStateAndAnim`, so the shot leaves Link's
hands in his facing direction exactly as a real rod shot would.

**Caveat — object slot `$12` is shared with the arrow.** `WieldArrow`
(`src/Z_05.asm:2954`) also does `LDX #$12`, and both handlers return early
when `ObjState` for that slot is non-zero. A rod shot in flight therefore
blocks an arrow shot and vice versa; you get one or the other on screen, never
both.

**Caveat — the Magic Book still applies.** Whether the shot bursts into flame
where it lands is decided by the rod-shot object itself, not by `WieldRod`, so
owning `InvBook` changes this code's shots the same way it changes real ones.

**Caveat — `WieldNothing` is still reachable.** `WieldArrow` branches to it
(`BEQ WieldNothing`) when there is no bow, no rupee, or a shot already out.
Those are branches inside the routine, not table entries, so they are
untouched — only the bow *slot* is redirected.

**Caveat — compare byte.** `$8E2C` is in the `$8000`-`$BFFF` switchable
window. `$A6` appears at that window offset in bank 5 only (checked across all
eight 16 KB banks of `bin/Z.nes`), so the patch cannot fire in another bank.

**Not live-verified:** derived from reading `WieldItem`, `WieldNothing` and
`WieldRod` (`src/Z_05.asm`), not from observing it in-game.

## Dungeon shutters never block Link

**Code:** `PLUPLZPS`

**Effect:** Shutter doors stop holding Link in. Walk into a shutter that has
slammed shut — the ones that trap you until the room is cleared, and the ones
guarding a boss — and Link walks straight through it into the next room. The
door still *looks* shut; only its ability to stop him is gone.

**How it works:** When Link is standing in a doorway,
`CheckDoorway` (`src/Z_05.asm:3747`) looks up the door type for that
direction and dispatches on it (`src/Z_05.asm:3850`):

```asm
    JSR FindDoorTypeByDoorBit
    STA $0D                     ; [0D] holds the door type.
    JSR TouchDoor               ; Can set [0E] to $FF, if a door blocks the way.

TouchDoor:
    AND #$07
    JSR TableJump

TouchDoor_JumpTable:
    .ADDR TouchDoorOpen
    .ADDR TouchDoorWall
    .ADDR TouchDoorFalse
    .ADDR TouchDoorFalse
    .ADDR TouchDoorBombable
    .ADDR TouchDoorKey
    .ADDR TouchDoorKey
    .ADDR TouchDoorShutter      ; Type 7
```

Blocking is done by writing `$FF` into `[0E]`, which every "no" path reaches
through `TouchDoorWall`; `TouchDoorOpen` is the `RTS` immediately after it:

```asm
TouchDoorWall:
    LDY #$FF
    STY $0E

TouchDoorOpen:
    RTS
```

This patches the low byte of the *eighth* table entry, at bank 5 CPU `$9233`,
from `$51` (`TouchDoorShutter`, `$9251`) to `$39` (`TouchDoorOpen`, `$9239`).
Raw form: `$9233:39:51`. All the handlers in this table live in page `$92`, so
one byte moves the dispatch. `TouchDoorShutter`'s three tests — a door command
in progress (`TriggeredDoorCmd`), this door not being in `CurOpenedDoors`, and
the timed re-entry block through `BlockUntilTime` — are all skipped, and the
caller sees `[0E]` unblocked.

**Caveat — the door still draws closed.** Door tiles come from the room's
door-drawing code, which this does not touch. Expect Link to walk through
what looks like a solid shutter.

**Caveat — type 7 only.** Locked doors (types 5 and 6) and bombable walls
(type 4) have their own entries and are unaffected. Shutters that a *room
secret* would have opened still open normally; this only removes the block
while they are shut.

**Caveat — the routine's own bookkeeping is skipped.** `TouchDoorShutter`
writes the door bit into `$0519`, an unnamed variable the disassembly marks
`; TODO: ?`. It is read and written nowhere else in the source
(`src/Z_05.asm:3962-3968`), so skipping it stays inside the routine that was
bypassed — but it is the one effect of this code that cannot be explained from
the annotations.

**Caveat — compare byte.** `$9233` is in the `$8000`-`$BFFF` switchable
window. `$51` appears at that window offset in bank 5 only (checked across all
eight 16 KB banks of `bin/Z.nes`).

**Not live-verified:** derived from reading `TouchDoor` and its handlers
(`src/Z_05.asm`), not from observing it in-game.

## Bombable dungeon walls are open doorways

**Code:** `PLXOIXZK`

**Effect:** The cracked walls that normally need a bomb stop being walls.
Walk into one and Link passes through it into the room beyond, exactly as if
he had blown it open — no bomb, no explosion, no waiting for the smoke.

**How it works:** `CheckDoorway` (`src/Z_05.asm:3747`) dispatches the door
type Link is standing in through `TouchDoor` (`src/Z_05.asm:3908`), whose
table has one entry per door type. Entry 4 is the bombable wall:

```asm
TouchDoorBombable:
    ; Block movement, if this door's direction is not in the open door mask.
    LDA $0C
    AND CurOpenedDoors
    BEQ TouchDoorWall
    RTS
```

Until the wall is bombed its direction bit is not in `CurOpenedDoors`, so it
falls into `TouchDoorWall`, which writes `$FF` into `[0E]` and blocks Link.
This patches the low byte of the *fifth* table entry, at bank 5 CPU `$922D`,
from `$4A` (`TouchDoorBombable`, `$924A`) to `$39` (`TouchDoorOpen`, `$9239`)
— the bare `RTS` that follows `TouchDoorWall`. Raw form: `$922D:39:4A`. Every
handler in this table is in page `$92`, so one byte moves the dispatch.

What makes this a *pass-through* rather than a plain doorway walk is the code
right after the call. `CheckDoorway` re-reads the door type and, for types 2,
3 and 4 — the two false-wall types and the bombable one — leaves the room
immediately instead of walking the doorway:

```asm
    ; Movement was not blocked at a doorway.
    ; If we're at a false wall or bombable, then go pass thru it
    ; and leave the room.
    LDA $0D
    AND #$07
    CMP #$02
    BEQ :+
    CMP #$03
    BEQ :+
    CMP #$04
    BEQ :+

@Exit:
    RTS
:
    JMP GoToNextModeFromPlay
```

The type byte is unchanged, so a bombable wall still takes that branch — the
only thing removed is the `CurOpenedDoors` test that used to stop Link first.

**Variant — walled-up doorways are passable too:** `PLXPYZIU`
(`$9227:39:35`) does the same thing to entry 1, `TouchDoorWall`. Door type 1
is a doorway position that was walled off; with this variant Link walks
through it — through what is drawn as solid wall. Type 1 is *not* in the
pass-through list above, so he takes the normal doorway walk. Note this
reaches only doorway positions, not arbitrary room walls: `TouchDoor` is
called only after `CheckDoorway` has confirmed Link is inside a doorway's
bounds.

**`PLXPYZIU` needs a companion to actually go anywhere.** Door type 1 is also
the type that `CalculateNextRoom_JumpTable` (bank 7 `$E6A6`) maps to
`CalculateNoNextRoom`, so the scroll starts but `NextRoomId` is never
recomputed and Link arrives back in the room he left. Pair it with
`ZXXVATYP` (`$E6A8:22:17`), documented under "Walled-up doorways lead to the
next room" below, to make the destination come out right.

**Caveat — the wall still looks cracked and unbroken.** Nothing here writes
tiles or sets `CurOpenedDoors`; the wall is drawn exactly as before and stays
that way after Link walks through it.

**Caveat — one-way opening is now two-way.** A bombable wall bombed from one
side normally records its direction bit; with this code the block is gone in
both rooms whether or not either side was ever opened.

**Caveat — compare byte.** `$922D` and `$9227` are in the `$8000`-`$BFFF`
switchable window. `$4A` and `$35` each appear at their window offset in bank
5 only (checked across all eight 16 KB banks of `bin/Z.nes`).

**Not live-verified:** derived from reading `CheckDoorway`, `TouchDoor` and
its handlers (`src/Z_05.asm`), not from observing it in-game.

## The life-or-money shutters open the moment you walk in

**Code:** `ZONAVLTN`

**Effect:** In the rooms where an old man blocks the way and demands rupees or
a heart container, the shutters open by themselves as soon as Link enters. He
can walk on past without paying anything and without touching the old man at
all; the offer is never made and never marked taken.

**How it works:** `CheckUnderworldSecrets` (`src/Z_05.asm:2337`) runs every
frame in a dungeon room. It takes the room's secret trigger — the low three
bits of `LevelBlockAttrsByteF` — and dispatches it:

```asm
CheckUnderworldSecrets:
    JSR CheckHasLivingMonsters

    ; If there's no secret in this room, return.
    LDA LevelBlockAttrsByteF
    AND #$07                    ; Secret trigger
    BEQ CheckSecretTriggerNone

    ; If the secret was not triggered, return.
    JSR CheckSecretTrigger
    BCC CheckSecretTriggerNone

CheckSecretTrigger_JumpTable:
    .ADDR CheckSecretTriggerNone
    .ADDR CheckSecretTriggerAllDead
    .ADDR CheckSecretTriggerRingleader
    .ADDR CheckSecretTriggerLastBoss
    .ADDR CheckSecretTriggerBlockDoor
    .ADDR CheckSecretTriggerBlockStairs
    .ADDR CheckSecretTriggerMoneyOrLife     ; Trigger 6
    .ADDR CheckSecretTriggerAllDead
```

Trigger 6 waits for the old man to be gone before opening the shutters:

```asm
CheckSecretTriggerMoneyOrLife:
    ; If the money-or-life man is gone, then
    ; go trigger shutters to open, and return C=1.
    LDA ObjType+1
    BEQ TriggerShutters
    CLC
    RTS
```

This patches the low byte of the *seventh* table entry, at bank 5 CPU
`$8BF6`, from `$76` (`CheckSecretTriggerMoneyOrLife`, `$8C76`) to `$1A`
(`CheckSecretTriggerAllDead`, `$8C1A`). Raw form: `$8BF6:1A:76`. Entries 1-7
of this table all live in page `$8C`, so one byte moves the dispatch.

The redirected handler opens the shutters as soon as the room counts as
cleared:

```asm
CheckSecretTriggerAllDead:
    ; If there are still monsters, not counting bubbles, then return C=0.
    LDA RoomAllDead
    BEQ ReturnFalse

TriggerShutters:
    ; No monsters are left. Trigger shutters to open, and return C=1.
    LDA #$01
    STA ShutterTrigger
    SEC
    RTS
```

and the old man does not count. `CheckHasLivingMonsters` (`src/Z_05.asm:2387`)
— called at the top of `CheckUnderworldSecrets`, before the dispatch — scans
the object slots and treats only types below `$2B` and `$2E`-`$48` as living
monsters; everything from `$49` up, which is where the underworld persons sit,
is skipped. A life-or-money room holds the old man and nothing else, so
`RoomAllDead` is already set on the first frame and `ShutterTrigger` fires
immediately.

**Caveat — the old man stays put, and so does his text.** Nothing here
removes him or his message; he simply becomes scenery you can ignore. He can
still be paid the normal way if you want the offer marked taken.

**Caveat — this is a different mechanism from the existing free-payment
codes.** "The life-or-money money option is free" and "'Take any one you want'
costs no heart container" patch
`UpdateUnderworldPersonLifeOrMoneyState_2` (`src/Z_01.asm`), which runs when
Link actually walks into the old man. This code never reaches that routine at
all — it changes which secret rule the *room* uses. Stacking them is
harmless but pointless.

**Caveat — trigger 6 only.** Rooms opened by killing everything (trigger 1),
by pushing a block (4 and 5), by the ringleader (2), by the last boss (3), or
that give an item for clearing the room (7) all keep their own entries.

**Caveat — compare byte.** `$8BF6` is in the `$8000`-`$BFFF` switchable
window. `$76` appears at that window offset in bank 5 only (checked across all
eight 16 KB banks of `bin/Z.nes`).

**Not live-verified:** derived from reading `CheckUnderworldSecrets`,
`CheckSecretTrigger` and `CheckHasLivingMonsters` (`src/Z_05.asm`), not from
observing it in-game.

## Select refills Link's hearts instead of pausing

**Code:** `LTKTOGET`

Tags: `play-start`

**Effect:** Select stops being the pause button. Press it and Link's hearts
start filling — the same refill the fairy pond and the potion give, with the
same repeating "heart taken" chime — except the game keeps running while it
happens. It works anywhere, any number of times, and costs nothing.

**How it works:** `UpdateMode5Play` (`src/Z_07.asm:1811`) handles Select at
the top of every play frame:

```asm
    ; Not paused or paused voluntarily.
    ; Check Select button.
    LDA ButtonsPressed
    AND #$20
    BEQ @CheckPaused            ; If pressed Select,
    LDA Paused                  ; then toggle pause.
    EOR #$01
    STA Paused
    BNE @CheckPaused            ; If not paused,
    LDA #$0F                    ; then enable sound.
    STA ApuStatus_4015
```

`Paused` is `$E0` — a zero-page variable — so `STA Paused` assembles as the
two-byte instruction `85 E0` and its operand reaches *any* zero-page address
in one byte. This patches that operand, at bank 7 CPU `$EC41`, from `$E0`
(`Paused`) to `$63` (`World_IsFillingHearts`). Raw form: `$EC41:63:E0`.

Because the game is not paused when the check runs, `LDA Paused / EOR #$01`
always leaves `A = 1`, so each press writes `1` into `World_IsFillingHearts`.
That is the flag `World_FillHearts` (`src/Z_05.asm:6763`) watches, and
`World_FillHearts` runs every frame of normal play — `@FinishUpdatePlay`
(`src/Z_07.asm:2060`) falls straight through into `UpdateHeartsAndRupees`,
which calls it:

```asm
World_FillHearts:
    LDA World_IsFillingHearts
    BEQ @Exit                   ; If not filling hearts, then return.
    LDA #$10                    ; Play the "heart taken" tune.
    STA Tune0Request
    LDA HeartPartial
    CMP #$F8
    BCS @CompleteHeart          ; If HeartPartial >= $F8, go complete a heart.
    CLC                         ; else add 6.
    ADC #$06
    STA HeartPartial
    RTS
```

It stops itself: when hearts reach heart containers it clears `SwordBlocked`,
`World_IsFillingHearts` and `Paused` and returns. Since `Paused` was already
zero, that final store changes nothing.

**Caveat — it fills in real time, not frozen time.** The potion path sets
`Paused` to `$02` so the world freezes while the hearts tick up
(`WieldPotion`, `src/Z_05.asm:3019`). This code sets only the flag, so
monsters keep moving and hitting Link while he refills, at `$06` of
`HeartPartial` per frame — roughly 43 frames per heart. Pair it with "Hearts
refill almost instantly" (`AVNUAPTA`, `$B1F8:60:06`) to make the refill nearly
immediate.

**Caveat — the chime repeats.** `World_FillHearts` writes `Tune0Request` every
frame it runs, exactly as it does during a normal refill.

**Caveat — the game can no longer be paused.** Select was the only thing
writing `Paused` here. Start still opens the subscreen (`INC MenuState`,
further down the same routine), and the involuntary pause used by the potion
is untouched.

**Caveat — `SwordBlocked` gets cleared.** The completion path clears it along
with the flag. That is the normal end-of-refill behaviour, just reachable at
will now.

**Caveat — compare byte.** `$EC41` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play`
(`src/Z_07.asm`) and `World_FillHearts` (`src/Z_05.asm`), not from observing
it in-game.

## Select opens the subscreen instead of pausing

**Code:** `OTKTOGET`

**Effect:** Select no longer pauses. Instead it scrolls the inventory
subscreen down, exactly as Start does — and once the subscreen is up, Select
goes back to its usual job of moving the item cursor. Start still opens and
closes it as well, so this is Select becoming a second, one-handed way in.

**How it works:** Both buttons are handled by `UpdateMode5Play`
(`src/Z_07.asm:1811`), a few instructions apart. Select toggles `Paused`;
Start, further down, starts the subscreen scrolling:

```asm
    LDA ButtonsPressed
    AND #$20
    BEQ @CheckPaused            ; If pressed Select,
    LDA Paused                  ; then toggle pause.
    EOR #$01
    STA Paused
...
@NotInMenu:
    ; Not in submenu.
    LDA ButtonsPressed
    AND #$10
    BEQ BeginUpdateWorld        ; If Start not pressed, go update the world.
    INC MenuState               ; Else set menu state 1 to start scrolling.
    RTS
```

`Paused` (`$E0`) and `MenuState` (`$E1`) are adjacent zero-page variables, so
`STA Paused` (`85 E0`) needs one byte changed to become `STA MenuState`. This
patches that operand at bank 7 CPU `$EC41`, `$E0` → `$E1`. Raw form:
`$EC41:E1:E0`.

The value stored is always `1`: the check is only reached while the game is
running, so `LDA Paused / EOR #$01` leaves `A = 1` — which is precisely the
state Start's `INC MenuState` produces from zero. Control then reaches
`@CheckMenu`, sees a non-zero `MenuState`, and hands off to
`UpdateMenuAndMeters` in bank 5, the same as if Start had been pressed.

**Caveat — no conflict with Select's role inside the menu.** The pause check
sits behind `LDA MenuState / BNE @CheckMenu` at the top of the routine, so
once the subscreen is up this code is unreachable and Select is read only by
the submenu's own cursor handling (`src/Z_05.asm:2211`).

**Caveat — the game can no longer be paused.** This was the only write to
`Paused` from the Select check. The involuntary pause the potion uses
(`Paused = $02`) is untouched.

**Caveat — mutually exclusive with `LTKTOGET`.** "Select refills Link's
hearts instead of pausing" patches the same byte to `$63`; only one of the two
can be active.

**Caveat — compare byte.** `$EC41` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play`
(`src/Z_07.asm`), not from observing it in-game.

## Hold Select for half-speed play

**Code:** `XYUTNKEN`

Tags: `play-start`

**Effect:** Tapping Select still pauses and unpauses, but *holding* it makes
the game run at about half speed: the world advances on every other frame
while the button is down. Let go and it snaps back to full speed, in whatever
pause state the last frame left it.

**How it works:** The Select check in `UpdateMode5Play` (`src/Z_07.asm:1811`)
reads the newly-pressed buttons, so a press toggles `Paused` exactly once:

```asm
    ; Not paused or paused voluntarily.
    ; Check Select button.
    LDA ButtonsPressed
    AND #$20
    BEQ @CheckPaused            ; If pressed Select,
    LDA Paused                  ; then toggle pause.
    EOR #$01
    STA Paused
    BNE @CheckPaused            ; If not paused,
    LDA #$0F                    ; then enable sound.
    STA ApuStatus_4015
```

`ButtonsPressed` (`$F8`) holds the buttons that went down *this* frame;
`ButtonsDown` (`$FA`) holds the ones currently held — the distinction the same
routine relies on a few lines later, where movement is read with `LDA
ButtonsDown / AND #$0F / STA ObjInputDir`. Both are zero page, so `LDA
ButtonsPressed` (`A5 F8`) becomes `LDA ButtonsDown` with one byte. This
patches that operand at bank 7 CPU `$EC37`, `$F8` → `$FA`. Raw form:
`$EC37:FA:F8`.

With the held state feeding the check, `Paused` is toggled on *every* frame
Select is down. The two outcomes alternate: on a paused frame the routine
takes `@CheckPaused`, which switches to bank 5 and jumps to
`UpdateHeartsAndRupees` without ever reaching `BeginUpdateWorld`, so no object
in the room is updated; on the next frame `Paused` is zero again and the full
world update runs. The net effect is one world frame per two hardware frames.

**Caveat — the sound status register is rewritten constantly.** Every
unpausing frame stores `$0F` to `ApuStatus_4015`, so while Select is held that
write happens ~30 times a second.

**Caveat — you can end up in either state.** Which way the toggle lands when
you release Select depends on the parity of how long you held it, so a long
hold can leave the game paused (tap Select again to clear it).

**Caveat — half speed is not slow motion for everything.** Only what
`BeginUpdateWorld` drives is skipped. Hearts and rupees still tick on paused
frames, since `@CheckPaused` jumps straight to `UpdateHeartsAndRupees`.

**Caveat — compare byte.** `$EC37` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play`
(`src/Z_07.asm`), not from observing it in-game.

## Select makes monsters chase where you stood

**Code:** `ATKTOGET`

**Effect:** Select stops pausing and becomes a decoy button. Tap it and every
monster that homes in on Link keeps walking toward the spot he occupied the
instant before the press, ignoring where he actually is — long enough to walk
out of a corner or slip past a Goriya. The game's own timer pulls their
attention back to him after up to about a second, and another tap sets the
decoy again.

**How it works:** Monsters do not read Link's position directly. They read
`ChaseTargetX`/`ChaseTargetY` (`$61`/`$62`), the "observed player" position
that `UpdateMode5Play` (`src/Z_07.asm:1811`) refreshes once a frame — but only
while `ChaseOtherTarget` is clear:

```asm
@CheckChaseTarget:
    ; If Link can be chased, then set his coordinates as the target.
    LDA ChaseOtherTarget
    BNE @UpdateWeapons
    LDA ObjX
    STA ChaseTargetX
    LDA ObjY
    STA ChaseTargetY
```

`Paused` is `$E0`, a zero-page variable, so the Select handler's `STA Paused`
is the two-byte instruction `85 E0` and its operand reaches any zero-page
address. This patches that operand, at bank 7 CPU `$EC41`, from `$E0`
(`Paused`) to `$60` (`ChaseOtherTarget`). Raw form: `$EC41:60:E0`.

The check is only reached while the game is running, so `LDA Paused / EOR
#$01` always leaves `A = 1` and each press writes `1` into `ChaseOtherTarget`.
The Select handler sits at the *top* of `UpdateMode5Play`, ahead of
`@CheckChaseTarget`, so on the very frame Select is pressed the refresh is
already suppressed: the target keeps the coordinates stored on the previous
frame — where Link stood one frame earlier.

Everything downstream follows from that one pair of bytes. `Wanderer_TargetPlayer`
(`src/Z_04.asm:313`) steers walking monsters by the horizontal and vertical
distance from `ChaseTargetX`/`Y` to the monster; `TurnTowardsPlayer8`
(`src/Z_04.asm:11693`) builds a direction toward "observed player X/Y" for
flyers; `UpdateGoriya` (`src/Z_04.asm:434`), `UpdateTektiteOrBoulder`
(`src/Z_04.asm:2250`), `UpdateBoulderSet` (`src/Z_04.asm:2167`) and
`InitWalker` (`src/Z_04.asm:216`) all read the same two bytes.

**Caveat — it wears off on its own, in under about a second.** The flag is
not yours alone; the game toggles it on a timer a few instructions later:

```asm
    ; If it's not time to change the chase target, then
    ; skip this and go update objects.
    LDA ChaseLongTimer
    BNE @LoopObject

    ; Set the chase long-timer to a random value between 0 and 7.
    LDA Random+1
    AND #$07
    STA ChaseLongTimer

    ; Switch the flag indicating whether Link is the target.
    LDA ChaseOtherTarget
    EOR #$01
    STA ChaseOtherTarget
```

`ChaseLongTimer` (`$4A`) is one of the long timers, decremented only when the
stun cycle wraps every ten frames (`@UpdateTimers`, `src/Z_07.asm:481`), and
it is reseeded to a random 0-7. So a press holds the decoy for at most ~70
frames before the toggle flips the flag back to zero and Link becomes the
target again. Tapping Select repeatedly keeps re-arming it.

**Caveat — this is the "chase elsewhere" phase the game already has, minus
the mirroring.** When the timer flips the flag the normal way *and* Link's X
has not changed since the previous frame, the routine reflects the target
across the room with `EOR #$FF` "so that monsters chase away from him". This
code never runs that path — it only freezes the target — so monsters walk
toward the stale point rather than fleeing the mirrored one.

**Caveat — it does not stop monsters that ignore the chase target.** Anything
steering by its own rules (Wizzrobes teleporting, Peahats, projectiles already
in flight) is unaffected; only the routines listed above read these bytes.

**Caveat — the game can no longer be paused,** and this patches the same byte
as `LTKTOGET` ("Select refills Link's hearts") and `OTKTOGET` ("Select opens
the subscreen"), so only one of the three can be active at a time.

**Caveat — compare byte.** `$EC41` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play`
(`src/Z_07.asm`), `Wanderer_TargetPlayer` and `TurnTowardsPlayer8`
(`src/Z_04.asm`), not from observing it in-game.

## Select turns the room's item into something else

**Codes:** `UZKTOGEV` + `LAUVNGPE` (Magic Key)

**Effect:** Select stops pausing. Press it in a dungeon room whose item is
still lying on the floor and the item *changes on the spot* — the sprite on
screen becomes a different item, and picking it up grants that item instead.
The second code chooses which one; `LAUVNGPE` makes it the Magic Key, so the
first dungeon item you find opens every locked door in the game forever.

**How it works:** Two bytes in the Select handler of `UpdateMode5Play`
(`src/Z_07.asm:1811`) do the work:

```asm
    LDA ButtonsPressed
    AND #$20
    BEQ @CheckPaused            ; If pressed Select,
    LDA Paused                  ; then toggle pause.
    EOR #$01
    STA Paused
```

`Paused` is `$E0`, a zero-page variable, so `STA Paused` is `85 E0` and its
one-byte operand reaches any zero-page address. `UZKTOGEV` retargets it at
bank 7 CPU `$EC41`, `$E0` → `$AB` (`RoomItemId`). Raw form: `$EC41:AB:E0`.
With the store redirected, `Paused` is never written, so it stays `0` and the
value stored is whatever `EOR #$01` produces — which is why the second code matters:
`LAUVNGPE` patches that immediate at `$EC3F`, `$01` → `$0B`. Raw form:
`$EC3F:0B:01`. Any item id can go there; the table below lists them.

One byte covers both halves of "the item" because they are the same byte.
`RoomItemId` is `$AB`, and `ObjDir` is `$98` with the room item in object slot
`$13` — `$98 + $13 = $AB`. The disassembly says so at the pickup site:

```asm
    ; Pass RoomItemId, also known as [98][$13] and ObjDir[$13],
    ; to try to take the item.
    LDA ObjRoomItemId, X
```

So `MoveAndDrawRoomItem` (`src/Z_07.asm:819`), which re-reads `RoomItemId`
every frame and passes it to `AnimateItemObject` for drawing, and
`TryTakeRoomItem` (`src/Z_01.asm:4386`), which passes it to `TakeItem`, both
follow the new value. `TakeItem` (`src/Z_01.asm:4457`) looks the id up in two
documented tables and writes the result into the inventory:

```asm
    ; Look up the item slot and sprite attributes by the item type.
    TAX
    LDA ItemIdToSlot, X
    TAY
    LDA ItemIdToDescriptor, X
...
    ; Finally, this is a simple item. Put the item value in the item slot.
    LDA $0A

SetItemValue:
    STA Items, Y
```

**Choosing the item.** `ItemIdToSlot` and `ItemIdToDescriptor`
(`src/Z_01.asm:4318`, `4341`) give every id's inventory slot and its class —
high nibble `0` unique, `1` an amount to add, `2` a grade that only upgrades.
Slot `N` is `Items + N`, so each row below is the named variable at that
address in `src/Variables.inc`. Replace the `$0B` in `$EC3F:0B:01` with:

| id | becomes | slot written | class |
|----|---------|--------------|-------|
| `$03` | Magic Sword — `LAUVNGPA` | `Items` | grade 3 |
| `$0B` | Magic Key — `LAUVNGPE` | `InvMagicKey` | unique |
| `$13` | Red Ring — `LPUVNGPA` | `InvRing` | grade 2 |
| `$14` | Power Bracelet — `GPUVNGPA` | `InvBracelet` | unique |
| `$19` | a Key — `PPUVNGPE` | `InvKeys` | amount +1 |
| `$1C` | Magic Shield — `GPUVNGPE` | `InvMagicShield` | unique |
| `$1E` | Magic Boomerang — `TPUVNGPE` | `InvMagicBoomerang` | unique |
| `$21` | Clock — `PZUVNGPA` | `InvClock` | unique |

**Caveat — it only transforms an item that is already there.** All three of
`MoveAndDrawRoomItem`'s early exits still apply: the room flag says the item
was taken (`GetRoomFlagUWItemState`), the room item object is inactive
(`ObjState+19` negative), or the id is `$3F`, "none". Pressing Select in a
room with nothing on the floor writes the byte and nothing reads it; the next
room load overwrites it (`src/Z_05.asm:8219`, `8265`).

**Caveat — grades only ever upgrade.** For a class-2 id the header comment is
explicit: "Picking up an item with a lower grade won't change the inventory."
Turning an item into the Red Ring is worthless if you already have it.

**Caveat — with `UZKTOGEV` alone the item becomes a Wood Sword.** The
untouched `EOR #$01` stores `1`, and id `$01` is grade 1 of the sword slot —
which does nothing for a Link who already has any sword. The second code is
what makes this worth using.

**Caveat — the two complex ids behave differently.** `$1B` (Triforce piece)
and `$0E` (Triforce of Power, whose slot is `LastBossDefeated`) are routed to
`TakeClass0Complex` rather than the simple store above, along with the map
(`$17`) and compass (`$16`). Their effects are not the plain "write the value
into the slot" this writeup describes.

**Caveat — the game can no longer be paused,** and `$EC41` is the same byte
patched by `LTKTOGET`, `OTKTOGET` and `ATKTOGET`, so only one of those Select
codes can be active at a time. This one needs two of your three code slots.

**Caveat — compare bytes.** `$EC3F` and `$EC41` are both in the
`$C000`-`$FFFF` window, which always maps bank 7 on this cart, so no other
bank can match either compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play`
(`src/Z_07.asm`), `MoveAndDrawRoomItem` (`src/Z_07.asm`), `TryTakeRoomItem`
and `TakeItem` with `ItemIdToSlot`/`ItemIdToDescriptor` (`src/Z_01.asm`), not
from observing it in-game.

## Select turns the picture black and white

**Code:** `VYKTOGEV`

**Effect:** Select stops pausing. Tap it and the whole screen — room, Link,
monsters, status bar — drops to greyscale and stays that way for the rest of
the room. It is the same washed-out look a bomb blast flashes for a few
frames, held indefinitely. Tapping Select again does not undo it; opening the
subscreen with Start does, and so does leaving the room.

**How it works:** The Select check in `UpdateMode5Play` (`src/Z_07.asm:1811`,
bank 7 CPU `$EC36`) toggles `Paused` with a zero-page store:

```asm
    ; Not paused or paused voluntarily.
    ; Check Select button.
    LDA ButtonsPressed
    AND #$20
    BEQ @CheckPaused            ; If pressed Select,
    LDA Paused                  ; then toggle pause.
    EOR #$01
    STA Paused
```

`Paused` is `$E0`, so `STA Paused` assembles as `85 E0` and its operand byte
reaches any zero-page variable. This patches that operand at `$EC41`, `$E0` →
`$FE` (`CurPpuMask_2001`). Raw form: `$EC41:FE:E0`. Nothing writes
`Paused` any more, so it stays `0` and `LDA Paused / EOR #$01` always leaves
`A = 1`, and the
patched store writes `1` into the PPUMASK shadow — bit 0, the greyscale bit.

The bit survives because of how `IsrNmi` (`src/Z_07.asm:388`) builds the
register value each frame:

```asm
    ; Set PPUMASK.
    ; Start with curren mask value, but ...
    LDA CurPpuMask_2001
    LDY IsSprite0CheckActive    ; If checking for sprite 0,
    BNE @EnableAllVideo
    LDY TileBufSelector
    BNE @SetPpuMask
    LDY $17
    BNE @SetPpuMask

@EnableAllVideo:
    ORA #$1E                    ; then make sure all video is on.

@SetPpuMask:
    STA PpuMask_2001
    STA CurPpuMask_2001
```

`ORA #$1E` turns the rendering bits back on but leaves bit 0 alone, and the
result is written straight back into `CurPpuMask_2001`, so once bit 0 is set
every later frame re-reads it and re-sets it. This is exactly the mechanism
`UpdateBombFlashEffect` (`src/Z_01.asm:4088`) uses for the explosion flash,
which rotates the same bit in and out at `ObjTimer` values `$16`/`$11` and
`$12`/`$0D`.

**Caveat — the game can no longer be paused.** `$EC41` is the byte that stores
into `Paused`, so nothing sets it any more.

**Caveat — several things clear it.** `MaskCurPpuMaskGrayscale`
(`src/Z_05.asm:7529`) is `LDA CurPpuMask_2001 / AND #$FE / STA
CurPpuMask_2001`, and it runs whenever the submenu is being drawn and from
`SetTargetMode` (`src/Z_05.asm:7317`) when the room changes. Detonating a bomb
also clears it, because the flash's `@Clear` path (`ASL`) shifts the bit out at
timer `$12` and `$0D`.

**Caveat — one frame can go black instead.** If `TileBufSelector` or `$17` is
non-zero on the frame the NMI runs, `ORA #$1E` is skipped and the raw `$01`
reaches PPUMASK with the rendering bits off. That happens on the odd frame the
status-bar map is cued, and it self-corrects the next frame.

**Caveat — `$EC41` is shared.** `LTKTOGET`, `OTKTOGET`, `ATKTOGET`, `UZKTOGEV`
and `VTKTOGEV` all patch this same byte, so only one of them can be active at a
time.

**Caveat — compare byte.** `$EC41` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play` and `IsrNmi`
(`src/Z_07.asm`), `MaskCurPpuMaskGrayscale` (`src/Z_05.asm`) and
`UpdateBombFlashEffect` (`src/Z_01.asm`), not from observing it in-game.

## Select opens every door in the dungeon room

**Codes:** `VTKTOGEV` + `YAUVNGPE`

**Effect:** In a dungeon room, Select stops pausing and becomes a skeleton key.
Tap it and all four of the room's doorways count as already open: locked doors
let Link through without spending a key, bombable walls let him through without
a bomb, and shutters that have not been earned yet stop blocking him. The doors
still *look* shut — the code only flips the "is it open" bitmask, it does not
redraw anything. The effect lasts until Link walks into the next room.

**How it works:** `CurOpenedDoors` (`$EE`) is a four-bit mask of which of the
room's doorways are currently passable, one bit per direction. Every door type
that can refuse Link tests it the same way, in `TouchDoor*`
(`src/Z_05.asm:3935` onwards, dispatched through `TouchDoor_JumpTable`):

```asm
TouchDoorBombable:
    ; Block movement, if this door's direction is not in the open door mask.
    LDA $0C
    AND CurOpenedDoors
    BEQ TouchDoorWall
    RTS

TouchDoorShutter:
    ; If a door is triggered or this door wasn't already opened,
    ; then block movement.
    LDA TriggeredDoorCmd
    BNE TouchDoorWall
    LDA $0C
    AND CurOpenedDoors
    BEQ TouchDoorWall
```

and `TouchDoorKey` returns immediately — without charging a key — when the bit
is already set. `[0C]` is the bit for the doorway Link is touching, so setting
every bit satisfies all four.

Two bytes of the Select handler in `UpdateMode5Play` (`src/Z_07.asm:1811`) do
the work. `Paused` is `$E0`, so `STA Paused` is `85 E0` and its operand reaches
any zero-page variable:

- `$EC41`, `$E0` → `$EE` (`CurOpenedDoors`) — raw `$EC41:EE:E0`, code
  `VTKTOGEV`. This is what makes Select write the door mask.
- `$EC3F`, `$01` → `$0F` — raw `$EC3F:0F:01`, code `YAUVNGPE`. The handler is
  redirected away from `Paused`, so `Paused` stays `0` and `LDA Paused /
  EOR #imm` leaves `A = imm`; this sets the stored value to all four direction bits instead of `1`.

`VTKTOGEV` on its own writes `$01`, which opens only the doorway whose bit is
`$01`. The second code is what makes it open all of them.

**Caveat — the doors do not change appearance.** `LayOutDoors`
(`src/Z_05.asm:5300` region) is only called from `UpdateDoors` when a door
command is triggered, and this patch never triggers one. A locked door keeps
its lock and a bombable wall keeps its wall; Link simply walks through.

**Caveat — it is overwritten on every room change.**
`SetEnteringDoorwayAsCurOpenedDoors` (`src/Z_05.asm:972`) rewrites the mask with
just the doorway Link came in by, so the effect has to be re-triggered in each
new room.

**Caveat — the door flags are not saved.** Only the live mask is patched, not
the per-room door flags in save RAM that `SetDoorFlag` writes, so a door opened
this way is shut again when the room is re-entered normally.

**Caveat — overworld and caves are unaffected.** `TouchDoor*` only runs for
underworld doorways.

**Caveat — the game can no longer be paused,** and `$EC41` is shared with
`LTKTOGET`, `OTKTOGET`, `ATKTOGET`, `UZKTOGEV` and `VYKTOGEV`, so only one of
those Select codes can be active at a time. This one needs two of your three
code slots.

**Caveat — compare bytes.** `$EC3F` and `$EC41` are both in the `$C000`-`$FFFF`
window, which always maps bank 7 on this cart, so no other bank can match
either compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play`
(`src/Z_07.asm`) and the `TouchDoor*` handlers, `UpdateDoors` and
`SetEnteringDoorwayAsCurOpenedDoors` (`src/Z_05.asm`), not from observing it
in-game.

## Select freezes the world the way the Recorder does

**Codes:** `GLKTOGEV` + `NYUVNGPE`

**Effect:** Select stops pausing and becomes a stopwatch. Tap it and the room
locks solid for about four seconds — monsters, projectiles, Link, everything —
while the music keeps playing and the picture keeps being drawn. It is the same
freeze the Recorder holds the room in while its tune plays, without the tune or
the whirlwind. When the timer runs out play resumes exactly where it left off.

**How it works:** `UpdateMode5Play` (`src/Z_07.asm:1811`) opens with the flute
check, before anything in the room is touched:

```asm
UpdateMode5Play:
    ; While the flute timer has not expired, return.
    LDA FluteTimer
    BNE L1EBF8_Exit
```

`WieldFlute` (`src/Z_05.asm:7317` region) is the only routine that normally
sets it — `LDA #$98 / STA FluteTimer`, 152 frames. The timer is counted down by
the frame loop's `@UpdateTimers` (`src/Z_07.asm:481`), which walks zero page
downward from `$3C` to `$27` decrementing every non-zero byte, so the freeze
ends on its own.

Two bytes of the Select handler point that machinery at the button. `Paused` is
`$E0`, so `STA Paused` is `85 E0` and its operand byte reaches any zero-page
variable:

- `$EC41`, `$E0` → `$3C` (`FluteTimer`) — raw `$EC41:3C:E0`, code `GLKTOGEV`.
- `$EC3F`, `$01` → `$FF` — raw `$EC3F:FF:01`, code `NYUVNGPE`. The handler is
  redirected away from `Paused`, so `Paused` stays `0` and `LDA Paused /
  EOR #imm` leaves `A = imm`; this makes the freeze 255 frames instead of 1.

For a shorter, 96-frame freeze use `ATUVNGPA` (`$EC3F:60:01`) as the second code
instead.

**Caveat — `GLKTOGEV` alone does nothing you can see.** The untouched `EOR #$01`
stores `1`, and `@UpdateTimers` decrements it to zero on the very next frame, so
the freeze lasts a single frame. The second code is what makes this worth using.

**Caveat — Link freezes too.** The early return is above `BeginUpdateWorld`, so
the player is as stuck as the monsters. This is a "stop the world" code, not an
invincibility trick.

**Caveat — you cannot cancel it.** The Select check sits *below* the flute
check, so while the timer is running the button is not read at all. You have to
wait it out.

**Caveat — the status bar stops too.** Hearts and rupees are updated from
`@FinishUpdatePlay`, which the early return skips, so the meters do not tick
during the freeze either.

**Caveat — the game can no longer be paused,** and `$EC41` is shared with
`LTKTOGET`, `OTKTOGET`, `ATKTOGET`, `UZKTOGEV`, `VYKTOGEV` and `VTKTOGEV`, so
only one of those Select codes can be active at a time. This one needs two of
your three code slots.

**Caveat — compare bytes.** `$EC3F` and `$EC41` are both in the `$C000`-`$FFFF`
window, which always maps bank 7 on this cart, so no other bank can match
either compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play` and
`@UpdateTimers` (`src/Z_07.asm`) and `WieldFlute` (`src/Z_05.asm`), not from
observing it in-game.

## Select stamps "GAME OVER" across the room

**Codes:** `GPKTOGET` + `TGUVNGPA`

**Effect:** Select stops pausing and becomes a graffiti button. Tap it during
play and the "GAME OVER" banner the death sequence uses is drawn straight into
the middle of the room, on top of whatever is there — and the game carries on
underneath it. The letters stay in the background until the room is redrawn.

**How it works:** `TileBufSelector` (`$14`) names which of the game's 64
canned PPU transfer buffers the next NMI should send. `TransferCurTileBuf`
(`src/Z_06.asm:557`) is called from `IsrNmi` every frame and reads it as a byte
offset into `TransferBufAddrs` (`src/Z_06.asm:491`):

```asm
TransferCurTileBuf:
    LDX TileBufSelector
    LDA TransferBufAddrs, X
    STA $00
    LDA TransferBufAddrs+1, X
    STA $01
    JSR TransferTileBuf
    ...
    LDX #$00
    STX TileBufSelector
```

Entry 35 of that table is `GameOverTransferBuf` (`src/Z_06.asm:826`), whose
records write the attribute bytes at `$23E3` and the "GAME OVER" tiles at
`$224C`, in the middle of the play area. The routine clears the selector after
each transfer, so one press means exactly one transfer.

Two bytes of the Select handler in `UpdateMode5Play` (`src/Z_07.asm:1811`) aim
it. `Paused` is `$E0`, so `STA Paused` is `85 E0` and its operand reaches any
zero-page variable:

- `$EC41`, `$E0` → `$14` (`TileBufSelector`) — raw `$EC41:14:E0`, code
  `GPKTOGET`.
- `$EC3F`, `$01` → `$46` — raw `$EC3F:46:01`, code `TGUVNGPA`. The handler is
  redirected away from `Paused`, so `Paused` stays `0` and `LDA Paused /
  EOR #imm` leaves `A = imm`; `$46` is `2 × 35`, the byte offset of the `GAME OVER` entry.

**Choosing the buffer.** Any even value picks a different entry of
`TransferBufAddrs`; the offset is twice the entry number. A few worth trying in
place of `$46`:

| offset | entry | what it sends | code |
|--------|-------|---------------|------|
| `$10` | 8 | `GameTitleTransferBuf` — the title logo tiles | `APUVNGPA` |
| `$36` | 27 | `GanonPaletteRow7TransferBuf` — Ganon's colours | `TLUVNGPA` |
| `$46` | 35 | `GameOverTransferBuf` — the "GAME OVER" banner | `TGUVNGPA` |
| `$4E` | 39 | `TriforceTextTransferBuf` — the Triforce caption | `TGUVNGPE` |

**Caveat — `GPKTOGET` alone does almost nothing.** The untouched `EOR #$01`
stores `1`, an *odd* offset, so `TransferCurTileBuf` builds its pointer from
`TransferBufAddrs+1` and `TransferBufAddrs+2` — the high byte of one entry and
the low byte of the next. That is a garbage pointer and the transfer it runs is
undefined; expect corruption rather than a clean effect. Always pair this with
an even-valued second code.

**Caveat — the game is still playing.** Nothing about this triggers the death
sequence. The letters are background tiles sitting over a live room, and Link
can walk behind them.

**Caveat — it is wiped by the next redraw.** Scrolling to another room, opening
the subscreen, or anything else that lays out the play area overwrites the
tiles.

**Caveat — it can collide with the game's own transfers.** `TileBufSelector` is
also set during play when the status-bar map is cued (`src/Z_07.asm:2057`,
value `$44`). If both happen on the same frame the last write wins.

**Caveat — the game can no longer be paused,** and `$EC41` is shared with
`LTKTOGET`, `OTKTOGET`, `ATKTOGET`, `UZKTOGEV`, `VYKTOGEV`, `VTKTOGEV` and
`GLKTOGEV`, so only one of those Select codes can be active at a time. This one
needs two of your three code slots.

**Caveat — compare bytes.** `$EC3F` and `$EC41` are both in the `$C000`-`$FFFF`
window, which always maps bank 7 on this cart, so no other bank can match
either compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play` (`src/Z_07.asm`)
and `TransferCurTileBuf` with `TransferBufAddrs` and `GameOverTransferBuf`
(`src/Z_06.asm`), not from observing it in-game.

## Select swaps the screen to the other name table

**Code:** `GIKTOGEV`

**Effect:** Select stops pausing and becomes a channel switch. Tap it and the
picture jumps to the NES's other name table — normally the off-screen half the
game scrolls rooms in and out of, so what appears is the room Link scrolled
away from, a half-built room, or blank tiles, with the live sprites still
running around on top. Tap it again to jump back. Gameplay is unaffected
throughout; only what is drawn changes.

**How it works:** `SwitchNameTablesReq` (`$5C`) is a one-shot request flag that
`IsrNmi` (`src/Z_07.asm:388`) consumes at the top of every frame:

```asm
IsrNmi:
    LDA CurPpuControl_2000
    LDX SwitchNameTablesReq
    BEQ :+                      ; If need to switch name tables,
    EOR #$02                    ; Switch to the other name table ($2000 <-> $2800).
:
    AND #$7F                    ; Disable NMI.
    STA CurPpuControl_2000
```

The flipped value is stored *back* into `CurPpuControl_2000`, so a single frame
with the flag set changes the base name table permanently, not just for that
frame. `TransferCurTileBuf` (`src/Z_06.asm:557`) clears the flag at the end of
the same NMI, which is what makes it one-shot.

This patches the Select handler's store in `UpdateMode5Play`
(`src/Z_07.asm:1811`). `Paused` is `$E0`, so `STA Paused` is `85 E0`; the
operand at `$EC41` becomes `$5C` (`SwitchNameTablesReq`). Raw form:
`$EC41:5C:E0`. Nothing writes `Paused` any more, so it stays `0` and
`LDA Paused / EOR #$01` always leaves `A = 1` — exactly the non-zero the flag wants, and the same value
the game's own `INC SwitchNameTablesReq` sites (`src/Z_02.asm:525`, `568`,
`635`) produce.

**Caveat — what you see is undefined by design.** The contents of the other
name table depend on where the last scroll left off, so the same press gives a
different picture in different rooms.

**Caveat — the game's own scrolling will fight it.** Walking to the next room
runs the mode-7 scroll submodes, which set the flag themselves
(`src/Z_05.asm:205`, `413`) and put the base name table back where they expect
it. Scrolling once is the reliable way to undo a stuck flip.

**Caveat — the status bar moves with it.** The whole background comes from the
switched name table, so the meters go too.

**Caveat — the game can no longer be paused,** and `$EC41` is shared with
`LTKTOGET`, `OTKTOGET`, `ATKTOGET`, `UZKTOGEV`, `VYKTOGEV`, `VTKTOGEV`,
`GLKTOGEV` and `GPKTOGET`, so only one of those Select codes can be active at a
time.

**Caveat — compare byte.** `$EC41` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play` and `IsrNmi`
(`src/Z_07.asm`) and `TransferCurTileBuf` (`src/Z_06.asm`), not from observing
it in-game.

## Pause with a different button — or never

**Codes:** `APUVOGAZ` (Start) · `AGUVOGAZ` (B) · `EAUVOGAZ` (A) ·
`AAUVOGAZ` (no pause at all)

**Effect:** Moves the pause toggle off Select and onto another button, or
removes it entirely. Use exactly one of these codes:

| code | raw | pause button |
|------|-----|--------------|
| `APUVOGAZ` | `$EC39:10:20` | Start |
| `AGUVOGAZ` | `$EC39:40:20` | B |
| `EAUVOGAZ` | `$EC39:80:20` | A |
| `AAUVOGAZ` | `$EC39:00:20` | nothing — the game can never be paused |

Select becomes an inert button in all four cases.

**How it works:** The Select check in `UpdateMode5Play` (`src/Z_07.asm:1811`,
bank 7 CPU `$EC36`) is a plain mask against the newly-pressed buttons:

```asm
    ; Not paused or paused voluntarily.
    ; Check Select button.
    LDA ButtonsPressed
    AND #$20
    BEQ @CheckPaused            ; If pressed Select,
    LDA Paused                  ; then toggle pause.
    EOR #$01
    STA Paused
    BNE @CheckPaused            ; If not paused,
    LDA #$0F                    ; then enable sound.
    STA ApuStatus_4015
```

`$20` is the Select bit of the standard NES button byte (`$80` A, `$40` B,
`$20` Select, `$10` Start, `$08`-`$01` the d-pad — the same layout the routine
relies on a few lines later with `LDA ButtonsDown / AND #$0F / STA
ObjInputDir`). This patches the `AND` operand at `$EC39` to a different bit, so
a different button drives the same toggle. With `$00` the `AND` always produces
zero, the `BEQ` is always taken, and the toggle is unreachable.

**Caveat — the button keeps its old job, but only on every second press.**
These codes do not take the button away from whatever else reads it — `A` still
swings the sword and `B` still uses the B-slot item, both read out of the same
`ButtonsPressed` byte by `Link_HandleInput` (`src/Z_05.asm:6931`, `6937`; bank 5
`$B2A8` and `$B2B1`). What decides whether that read happens is *which way the
toggle landed*. On the press that pauses, `UpdateMode5Play` takes `@CheckPaused`
and returns before the world update, so the sword or item is swallowed. On the
press that unpauses, `Paused` is zero when `@CheckPaused` tests it, execution
falls through to the world update, and nothing has cleared `ButtonsPressed` in
between — so that press both unpauses *and* swings. With `EAUVOGAZ` you keep the
sword at half rate, alternating swing and freeze.

**Caveat — Start is a special case.** Start is read again further down the same
routine, at `@NotInMenu`, to open the subscreen. On the frame Start pauses, the
paused branch is taken first and the subscreen check is skipped; on the frame
that *unpauses*, execution falls through to `@NotInMenu` with Start still in
`ButtonsPressed`, so unpausing also opens the subscreen. Expect Start to pause,
then unpause into the inventory screen.

**Caveat — `AAUVOGAZ` also strands the sound-enable write.** `LDA #$0F / STA
ApuStatus_4015` only runs on the unpause path, so it never executes. Nothing
disables the channels either, so in practice this is harmless.

**Caveat — the involuntary pause is untouched.** `Paused = $02`, which the
routine tests before this check, is set and cleared elsewhere; these codes do
not affect it.

**Caveat — compare byte.** `$EC39` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play`
(`src/Z_07.asm`), not from observing it in-game.

## Select makes Link untouchable

**Codes:** `ILKTOGEV` + `NYUVNGPE`

**Effect:** Select stops pausing and becomes a panic button. Tap it and nothing
can hurt Link for about forty seconds — monsters, their projectiles, Wallmasters
— while he still walks, swings and shoots exactly as normal. He passes through
enemies rather than being knocked back by them. No flashing, no visible cue; the
timer just runs out and contact starts hurting again. Tap Select to top it up.

**How it works:** `ObjStunTimer` is the per-object stun timer array, and slot 0
of it — `$3D` — belongs to Link. `CheckLinkCollision` (`src/Z_01.asm:5598`),
the routine every monster goes through to find out whether it has touched the
player, rejects the collision outright while it is set:

```asm
    ; If Link is invincible, or we have the magic clock,
    ; or Link is stunned, or the monster is stunned;
    ; then return no collision.
    LDA ObjInvincibilityTimer
    ORA InvClock
    ORA ObjStunTimer
    ORA ObjStunTimer, X
    BNE L73A9_Exit
```

The `ORA ObjStunTimer` with no index is Link's own slot; `ORA ObjStunTimer, X`
is the monster's. Either one non-zero means "no collision".

What makes this a cheat rather than a self-inflicted freeze is that Link is
specifically exempted from the *other* half of the stun mechanic. `MoveObject`
(`src/Z_07.asm:2635`) refuses to move a stunned object — but skips the check
for object 0:

```asm
@CheckStunned:
    CPX #$00
    BEQ @FilterInput
    LDA InvClock
    ORA ObjStunTimer, X
    BNE L1EFCF_Exit
```

So Link keeps his stun timer's protection without paying its price.

Two bytes of the Select handler in `UpdateMode5Play` (`src/Z_07.asm:1811`) do
this. `Paused` is `$E0`, so `STA Paused` is `85 E0` and its operand reaches any
zero-page variable:

- `$EC41`, `$E0` → `$3D` (`ObjStunTimer`) — raw `$EC41:3D:E0`, code `ILKTOGEV`.
- `$EC3F`, `$01` → `$FF` — raw `$EC3F:FF:01`, code `NYUVNGPE` (the same second
  code the Recorder-freeze entry uses). The handler is only reached while
  unpaused, so `LDA Paused / EOR #imm` leaves `A = imm`.

`$3D` sits in the stun-timer half of zero page, which `@UpdateTimers`
(`src/Z_07.asm:481`) only walks when the ten-frame `StunCycle` wraps, so each
count is ten frames: `$FF` is 2550 frames, about forty-two seconds.

**Caveat — `ILKTOGEV` alone lasts a sixth of a second.** The untouched
`EOR #$01` stores `1`, which is one ten-frame tick. The second code is what
makes this worth using.

**Caveat — it is cleared when you change rooms.** Room entry
(`src/Z_05.asm:1819`) does `LDA #$00 / STA ObjStunTimer` for Link's slot along
with his shove state, so walking into the next room ends it early.

**Caveat — it is not full invincibility.** Only what goes through
`CheckLinkCollision` is blocked. Damage the game applies without a collision
test — traps and room hazards that write Link's health directly — is not
covered, and neither is falling into water or a pit.

**Caveat — it works on the monster's side of the test.** Since the routine
returns "no collision", Link also cannot *shove* enemies by walking into them,
and anything that keyed off contact simply does not happen.

**Caveat — the game can no longer be paused,** and `$EC41` is shared with every
other `$EC41` Select code, so only one of them can be active at a time. This one
needs two of your three code slots.

**Caveat — compare bytes.** `$EC3F` and `$EC41` are both in the `$C000`-`$FFFF`
window, which always maps bank 7 on this cart, so no other bank can match
either compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play`, `MoveObject` and
`@UpdateTimers` (`src/Z_07.asm`), `CheckLinkCollision` (`src/Z_01.asm`) and the
room-entry reset (`src/Z_05.asm`), not from observing it in-game.

## Select guarantees the next kill drops an item

**Codes:** `AIKTOGET` + `ZAUVNGPE`

**Effect:** Select stops pausing and becomes a loot button. Tap it, then kill
anything — the drop is guaranteed instead of rolled for, and it is five rupees.
One press buys one guaranteed drop; the game resets the counter as it hands the
item over, so tap again before the next kill.

**How it works:** The game runs a pity timer on item drops. `HandleMonsterDied`
(`src/Z_01.asm:5996`) counts kills into `HelpDropCount` (`$50`), capping at
`$0A`:

```asm
HandleMonsterDied:
    ; Handle the monster dying.
    INC WorldKillCount

    ; Increase the help drop counter, if not at max ($A).
    LDA HelpDropCount
    CMP #$0A
    BCS @SetDyingMetastate
    INC HelpDropCount
```

and `SetUpDroppedItem` (`src/Z_04.asm:11070`) checks it when deciding what, if
anything, the corpse leaves behind:

```asm
    ; If help drop counter < $A, then use the dropped item ID as is.
    ; But there is a random chance that the item drop will be canceled.
    LDA HelpDropCount
    CMP #$0A
    BCC @RandomlyCancel

    ; Otherwise, the item will be guaranteed to be made.
    ; [51] HelpDropValue determines which kind:
    ; - 0:     5 rupees
    ; - other: bomb
    LDA #$0F
    LDY HelpDropValue
    BEQ @SetHelpItem
    LDA #$00                    ; Bomb
```

Below `$0A` the drop goes through `@RandomlyCancel`, which rolls `Random`
against the monster group's drop rate. At `$0A` the roll is skipped entirely.

Two bytes of the Select handler in `UpdateMode5Play` (`src/Z_07.asm:1811`) push
the counter straight to the cap. `Paused` is `$E0`, so `STA Paused` is `85 E0`
and its operand reaches any zero-page variable:

- `$EC41`, `$E0` → `$50` (`HelpDropCount`) — raw `$EC41:50:E0`, code
  `AIKTOGET`.
- `$EC3F`, `$01` → `$0A` — raw `$EC3F:0A:01`, code `ZAUVNGPE`. The handler is
  redirected away from `Paused`, so `Paused` stays `0` and `LDA Paused /
  EOR #imm` leaves `A = imm`.

**Making it drop a bomb instead.** `HelpDropValue` (`$51`) picks which help item
is given: zero means five rupees, anything else means a bomb. The game only sets
it when the tenth kill was itself a bomb kill. `PIKTOGET` (`$EC41:51:E0`) points
the Select store at `$51` instead, storing `1` — so once the counter reaches
`$0A` on its own, ten kills later, the guaranteed drop is a bomb. `AIKTOGET` and
`PIKTOGET` patch the same byte and cannot both be active, so this is a choice
between "guarantee the drop now" and "make the guaranteed drop a bomb".

**Caveat — `AIKTOGET` alone does nothing useful.** The untouched `EOR #$01`
stores `1`, which just resets the pity counter to near the bottom and makes
drops *rarer*. The second code is what makes this work.

**Caveat — one press, one drop.** `SetUpDroppedItem`'s `@SetHelpItem` path ends
with `LDA #$00 / STA HelpDropCount / STA HelpDropValue`, so the counter is spent
on the item it grants.

**Caveat — the monster still has to be droppable.** Bosses, room objects and
anything that does not run `SetUpDroppedItem` are unaffected, and the global
`WorldKillCount == $10` fairy case is tested before the counter and wins.

**Caveat — five rupees, not a heart.** Item `$0F` is the five-rupee pile. This
code cannot choose a different item; only the rupee/bomb switch above.

**Caveat — the game can no longer be paused,** and `$EC41` is shared with every
other `$EC41` Select code, so only one of them can be active at a time. This one
needs two of your three code slots.

**Caveat — compare bytes.** `$EC3F` and `$EC41` are both in the `$C000`-`$FFFF`
window, which always maps bank 7 on this cart, so no other bank can match
either compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play` (`src/Z_07.asm`),
`HandleMonsterDied` (`src/Z_01.asm`) and `SetUpDroppedItem` (`src/Z_04.asm`),
not from observing it in-game.

## Select switches on one of the room's long-timer behaviours

**Codes:** `LGKTOGEV` (no monsters from the edges) · `GGKTOGEV` (sword blocked)
· `IGKTOGEV` (no red Leevers) — each paired with `NYUVNGPE`

**Effect:** Three separate codes, each turning one of the game's "long timers"
on at will for about forty seconds. Use one at a time, with `NYUVNGPE` as the
second code:

| code | raw | what the press does |
|------|-----|---------------------|
| `LGKTOGEV` | `$EC41:4B:E0` | monsters stop walking in from the screen edges |
| `GGKTOGEV` | `$EC41:4C:E0` | Link's sword stops working, as if a Bubble had touched him |
| `IGKTOGEV` | `$EC41:4D:E0` | red Leevers stop surfacing |

**How it works:** `$4A`-`$4D` are a small block of *long* timers — counters the
game decrements once every ten frames rather than every frame, because
`@UpdateTimers` (`src/Z_07.asm:481`) only extends its downward walk of zero page
past `$3C` when the ten-frame `StunCycle` wraps. Each one gates a behaviour
while it is non-zero:

- `MonstersFromEdgesLongTimer` (`$4B`) throttles edge spawns. In
  `@UninitMonsterFromEdge` (`src/Z_07.asm:5522`) a monster due to walk in from
  the screen border is put back to uninitialized while the timer runs, and the
  spawn path arms it again with a random 2-5 (`src/Z_07.asm:5555`) so the
  monsters trickle in rather than arriving at once.
- `SwordBlockedLongTimer` (`$4C`) is the flashing Bubble's curse.
  `Link_HandleInput` (`src/Z_05.asm:6921`) does `LDA SwordBlockedLongTimer /
  ORA SwordBlocked / BNE :+` around its `JSR WieldSword`, so A does nothing
  while it runs. The Bubble itself sets `$10` — 160 frames
  (`src/Z_04.asm:1161`).
- `RedLeeverLongTimer` (`$4D`) paces red Leevers. `UpdateRedLeever`
  (`src/Z_04.asm:2753`) returns from state 0 without bursting out of the ground
  while it is set, and re-arms it to 2 after each surfacing
  (`src/Z_04.asm:2881`).

All three are reached the same way: the `STA Paused` in `UpdateMode5Play`
(`src/Z_07.asm:1811`) is `85 E0`, and its operand byte at `$EC41` can name any
zero-page variable. `NYUVNGPE` (`$EC3F:FF:01`) changes the value stored from `1`
to `$FF`, which at ten frames a count is 2550 frames — about forty-two seconds.

**Caveat — without `NYUVNGPE` each press lasts a sixth of a second.** The
untouched `EOR #$01` stores `1`, a single ten-frame tick. All three of these
need the second code.

**Caveat — `GGKTOGEV` is a handicap, not a cheat.** It is included because it
completes the set; a press costs you your sword for forty seconds.

**Caveat — the game re-arms these timers itself.** Each behaviour writes its own
value back when it fires, so what a press really buys is a long delay before the
game's own pacing resumes, not a permanent switch.

**Caveat — `IGKTOGEV` only matters where red Leevers live**, which is a handful
of overworld screens; elsewhere the press does nothing visible. `LGKTOGEV` only
affects monsters that walk in from the border — the ones that appear in a cloud
in the middle of the screen are spawned by a different path and are unaffected.

**Caveat — the game can no longer be paused,** and `$EC41` is shared with every
other `$EC41` Select code, so only one of them can be active at a time. Each of
these needs two of your three code slots.

**Caveat — compare bytes.** `$EC3F` and `$EC41` are both in the `$C000`-`$FFFF`
window, which always maps bank 7 on this cart, so no other bank can match
either compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play`,
`@UpdateTimers` and `@UninitMonsterFromEdge` (`src/Z_07.asm`),
`Link_HandleInput` (`src/Z_05.asm`) and `UpdateRedLeever` and the Bubble's
sword-block (`src/Z_04.asm`), not from observing it in-game.

## Select plays the second save file's world

**Code:** `TPKTOGET`

**Effect:** Select stops pausing and switches which saved profile the game is
consulting. From the press on, everything the game looks up per-file — whether
this is a First or Second Quest, which rooms and secrets have been dealt with,
the death count — comes from save file 2 instead of the one you are playing.
Link, his hearts and his inventory do not change; the world around him quietly
becomes someone else's. Pressing Select again does nothing (it stores the same
value), and the room you are standing in is unaffected until it is reloaded.

**How it works:** `CurSaveSlot` (`$16`) is the index of the profile in play.
Save data is not copied into working RAM wholesale; instead, routines index it
by this byte whenever they need it. `FetchFileAAddressSet` (`src/Z_01.asm:3063`)
walks `$0E` bytes per slot to build the pointers to the current profile's death
count, quest number and world flags, and the quest number in particular is
re-read constantly during play:

```asm
InitRope:
    ; Rope has $10 HP in quest 1, $40 HP in quest 2.
    LDA #$10
    STA ObjHP, X
    LDY CurSaveSlot
    LDA QuestNumbers, Y
    BEQ :+
    LDA #$40
    STA ObjHP, X
```

The same `LDY CurSaveSlot / LDA QuestNumbers, Y` appears in `UpdateStalfos`
(`src/Z_04.asm:4670`, whether Stalfos can shoot), the Rope draw routine
(`src/Z_04.asm:4636`, whether Ropes flash), `IsQuestSecretMismatch`
(`src/Z_04.asm:3829`, whether a room's secret belongs to this quest) and
`WieldFlute` (`src/Z_07.asm:2500`). Bank 6's level loader picks the level's
block from `LevelBlockAddrsQ1` or the Second Quest table the same way
(`src/Z_06.asm:64`).

This patches the Select handler's store in `UpdateMode5Play`
(`src/Z_07.asm:1811`). `Paused` is `$E0`, so `STA Paused` is `85 E0`; the
operand at `$EC41` becomes `$16` (`CurSaveSlot`). Raw form: `$EC41:16:E0`. Nothing
writes `Paused` any more, so it stays `0` and `LDA Paused / EOR #$01` always
leaves `A = 1` — slot index 1, the second save file.

**Caveat — it writes as well as reads.** Anything that records progress —
killed-room flags, secrets found, the death count, and saving on the Continue
screen — will now write into file 2. Do not use this on a cartridge whose
second file you care about; on an emulator, keep a backup of the save.

**Caveat — what you see depends entirely on what is in file 2.** If it is a
Second Quest file, Ropes gain HP and flash, Stalfos start shooting, and dungeons
reload with Second Quest layouts. If file 2 is empty, the quest number and flags
read as a blank profile — rooms you had cleared fill up again.

**Caveat — the current room does not change under you.** The room was laid out
before the press; the switch shows up as you move to new rooms and levels.

**Caveat — it always selects slot 1.** The stored value is fixed at `1` by the
untouched `EOR #$01`, so this is specifically "switch to file 2", and it cannot
be pressed to cycle. Starting a game on file 2 makes the press a no-op.

**Caveat — the game can no longer be paused,** and `$EC41` is shared with every
other `$EC41` Select code, so only one of them can be active at a time.

**Caveat — compare byte.** `$EC41` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play` and `WieldFlute`
(`src/Z_07.asm`), `FetchFileAAddressSet` (`src/Z_01.asm`), `InitRope`,
`UpdateStalfos` and `IsQuestSecretMismatch` (`src/Z_04.asm`) and
`InitMode2_Sub0` (`src/Z_06.asm`), not from observing it in-game.

## The game permanently runs at half speed

**Codes:** `EIUVXGEY` — or `PAUVEKPX` for the uninterruptible version

Tags: `demo-ready` `play-start` `curated`

**Effect:** Everything in the room — Link, monsters, weapons, scrolling
animations — moves at half its normal rate, all the time, with no button held
and nothing to switch it off. The picture still refreshes at the usual sixty
frames a second, so it is genuine slow motion rather than a slideshow.

With `EIUVXGEY`, tapping Select skips one toggle and flips the phase; the speed
is unaffected either way, and Select no longer pauses. With `PAUVEKPX` the
button does nothing at all.

**How it works:** The Select check in `UpdateMode5Play` (`src/Z_07.asm:1811`,
bank 7 CPU `$EC36`) is a mask, a branch, and a toggle:

```asm
    ; Not paused or paused voluntarily.
    ; Check Select button.
    LDA ButtonsPressed
    AND #$20
    BEQ @CheckPaused            ; If pressed Select,
    LDA Paused                  ; then toggle pause.
    EOR #$01
    STA Paused
```

Below it, `@CheckPaused` reads `Paused` and — when it is set — switches to bank
5 and jumps to `UpdateHeartsAndRupees` without ever reaching
`BeginUpdateWorld`, so no object in the room is updated that frame. The toggle
normally fires once per press, because `ButtonsPressed` holds only the buttons
that went down this frame. Make it fire every frame and `Paused` alternates
0-1-0-1, which means one world frame per two hardware frames.

Two different bytes get there:

- `EIUVXGEY` patches the branch opcode at `$EC3A`, `$F0` (`BEQ`) → `$D0`
  (`BNE`). Raw form: `$EC3A:D0:F0`. The branch now skips the toggle on the one
  frame Select goes down and runs it on every other frame.
- `PAUVEKPX` patches the mask opcode at `$EC38`, `$29` (`AND #imm`) → `$09`
  (`ORA #imm`). Raw form: `$EC38:09:29`. `ORA #$20` can never produce zero, so
  the `BEQ` is never taken and the toggle runs unconditionally, Select or no
  Select.

This is the always-on relative of `XYUTNKEN`, which gets the same alternation
by pointing the load at `ButtonsDown` so it only happens while the button is
held.

**Caveat — use one, not both.** They are different bytes, so both can be
active at once, but the second one adds nothing.

**Caveat — the game can no longer be paused.** The toggle no longer answers to
the button in any usable way.

**Caveat — the sound status register is rewritten thirty times a second.**
Every unpaused frame runs `LDA #$0F / STA ApuStatus_4015`, the write that
normally happens once per unpause.

**Caveat — half speed is not slow motion for everything.** Only what
`BeginUpdateWorld` drives is skipped. Hearts and rupees still tick on the
paused frames, since `@CheckPaused` jumps straight to `UpdateHeartsAndRupees`,
and the music runs from the audio driver at full speed.

**Caveat — the involuntary pause still works normally.** `Paused = $02`, set
while hearts refill (`src/Z_05.asm:3027`), is tested before this check and is
unaffected.

**Caveat — compare bytes.** `$EC38` and `$EC3A` are both in the `$C000`-`$FFFF`
window, which always maps bank 7 on this cart, so no other bank can match
either compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play`
(`src/Z_07.asm`), not from observing it in-game.

## Time moves only while a button is held (3-code version)

**Codes:** `XYKVXGEV` + `EIKVUGEY` + `AAUVOGAZ`

Tags: `play-start`

**Effect:** When no button is held, the room freezes: Link, monsters and
weapons stop. Hold any button (a direction, A, B, Start or Select) and the
game runs at normal speed. Select no longer pauses. Unlike the 5-code version
("Time moves only while a button is held", in
`zelda_1_long_game_genie.md`), the music keeps playing while the room is frozen, and some timers keep
counting down (see the caveats).

**How it works:** The 5-code version sets `Paused` from the buttons. This
version leaves `Paused` at 0 and changes the test that reads it. In
`UpdateMode5Play` (`src/Z_07.asm:1811`, bank 7), `@CheckPaused` skips the
world update when `Paused` is set:

```asm
@CheckPaused:
    LDA Paused                  ; A5 E0   $EC49
    BEQ @CheckMenu              ; F0 0B   $EC4B
    LDA #$05                    ; paused: update hearts and rupees only
    ...
```

- `XYKVXGEV` patches `$EC4A`, `$E0` → `$FA`, so `LDA Paused` becomes `LDA
  ButtonsDown`. Raw form: `$EC4A:FA:E0`.
- `EIKVUGEY` patches `$EC4B`, `$F0` → `$D0`, so `BEQ` becomes `BNE`. Raw form:
  `$EC4B:D0:F0`.

Now any held button goes to `@CheckMenu` and the world updates. With no
button held, the code falls into the paused path, which skips the world
update.

- `AAUVOGAZ` patches the Select mask at `$EC39`, `$20` → `$00` (`AND #$00`).
  The result is always zero, so the Select toggle never runs and `Paused` stays
  0. Raw form: `$EC39:00:20`. Without this code, Select would still set
  `Paused`, which mutes the music and stops the timers while the world keeps
  running.

**Caveat — the music keeps playing while time is stopped.** `DriveAudio`
(`src/Z_00.asm:105`) mutes only when `Paused` is set.

**Caveat — timers keep counting down while time is stopped.** The timer code
in the NMI (`src/Z_07.asm:484`) skips the timers only when `MenuState` or
`Paused` is set. So object timers keep running during a freeze: monster wait
timers, Link's invincibility, and dropped-item timers. After a long freeze, a
monster may act at once, an item may vanish, or Link's flashing may already be
over.

**Caveat — holding a button during a heart refill lets the world run.** While
a potion or fairy refills hearts, `Paused = $02`. That path jumps straight to
`@CheckPaused`, so a held button now runs the world during the refill. In the
original game the world stays frozen until the refill ends.

**Caveat — why this can't match the 5-code version in 3 codes.** That version
needs three changes at the Select check: read the held buttons, test all 8
buttons, and turn "no buttons" into `Paused` = 1 and "any button" into
`Paused` = 0. The last step needs a branch to two different values, and the
existing code has no spare byte for it.

**Caveat — compare bytes.** `$EC39`, `$EC4A` and `$EC4B` are in the
`$C000`-`$FFFF` window, which always maps bank 7 on this cart, so no other
bank can match the compare bytes.

**Live-verified** in fceumm, in a Level 9 room with monsters: with no buttons
for 120 frames, the monster positions (`$71`-`$73`, `$85`-`$87`) did not change
and `Paused` stayed 0. From the same state with A held for 120 frames, the
monsters moved. The timer caveat comes from reading the code. The test room
had no active timers to watch.

## Select slides the screen sideways

**Codes:** `SYKTOGEV` + `EAUVNGPA`

**Effect:** Select stops pausing and becomes a camera shove. Tap it and the
whole picture jumps half a screen to the left, so you are looking at the seam
between this room and the off-screen name table beside it — half of the room
you are in, half of whatever the scrolling engine last left next door. Link
does not move; only the view does. The game keeps playing normally at his real
position, which is now partly or wholly off the visible area. Scrolling to
another room puts it right.

**How it works:** `CurHScroll` (`$FD`) is the shadow copy of the PPU's
horizontal scroll. The frame loop writes it to the hardware every frame, for
the modes that scroll (`src/Z_07.asm:471`):

```asm
@SetScroll:
    LDA PpuStatus_2002
    LDA CurHScroll
    STA PpuScroll_2005
    LDA CurVScroll
    STA PpuScroll_2005
```

During play it is left alone — it is written by the mode-7 scroll submodes as a
room slides past (`src/Z_05.asm:672`, `709`, `1060`) and by
`ResetPpuRegisters` (`src/Z_07.asm:553`), and by nothing else. So a value
stored into it during mode 5 simply stays there and is pushed at the PPU sixty
times a second.

Two bytes of the Select handler in `UpdateMode5Play` (`src/Z_07.asm:1811`)
supply it. `Paused` is `$E0`, so `STA Paused` is `85 E0` and its operand
reaches any zero-page variable:

- `$EC41`, `$E0` → `$FD` (`CurHScroll`) — raw `$EC41:FD:E0`, code `SYKTOGEV`.
- `$EC3F`, `$01` → `$80` — raw `$EC3F:80:01`, code `EAUVNGPA`. The handler is
  redirected away from `Paused`, so `Paused` stays `0` and `LDA Paused /
  EOR #imm` leaves `A = imm`; `$80` is 128 pixels, half the screen width. Use `AGUVNGPA` (`$EC3F:40:01`)
  for a quarter-screen nudge instead.

**Caveat — `SYKTOGEV` alone shifts by one pixel.** The untouched `EOR #$01`
stores `1`. The second code is what makes the shift visible.

**Caveat — you cannot shove it back.** Every press stores the same value, so
the view stays where the first press put it until a room transition rewrites
`CurHScroll`.

**Caveat — the status bar goes with it.** The split that keeps the meters still
re-applies the same scroll value, so the whole picture moves, not just the play
area.

**Caveat — what is next door is not guaranteed to be anything.** The adjacent
name table holds whatever the last scroll left in it, which may be a previous
room, a half-built one, or blanks.

**Caveat — the game can no longer be paused,** and `$EC41` is shared with every
other `$EC41` Select code, so only one of them can be active at a time. This one
needs two of your three code slots.

**Caveat — compare bytes.** `$EC3F` and `$EC41` are both in the `$C000`-`$FFFF`
window, which always maps bank 7 on this cart, so no other bank can match
either compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play` and the frame
loop's `@SetScroll` (`src/Z_07.asm`) and the mode-7 scroll submodes
(`src/Z_05.asm`), not from observing it in-game.

## Unpausing sprays a page of RAM over the sprites

**Code:** `GPKTNGIP`

**Effect:** Pausing still works normally. *Un*pausing, instead of switching the
sound channels back on, dumps 256 bytes of the game's working memory straight
into sprite memory — so the frame you unpause on is covered in a field of junk
sprites at junk positions. The game repairs it on the very next frame and play
continues as though nothing happened, which makes this a one-frame glitch flash
you can fire at will by tapping Select twice.

**How it works:** The tail of the Select handler in `UpdateMode5Play`
(`src/Z_07.asm:1811`) re-enables the APU when the toggle lands on "not paused":

```asm
    STA Paused
    BNE @CheckPaused            ; If not paused,
    LDA #$0F                    ; then enable sound.
    STA ApuStatus_4015
```

`STA ApuStatus_4015` assembles as `8D 15 40` at `$EC46`. This patches the low
byte of that address at `$EC47`, `$15` → `$14`. Raw form: `$EC47:14:15`. The
instruction becomes `STA $4014` — the NES's OAM DMA register — and the byte in
`A` at that moment is the `$0F` that was meant for the sound register. Writing
`$0F` to `$4014` tells the hardware to copy CPU page `$0F00` into sprite
memory: 256 bytes, read as 64 sprites of Y, tile, attribute and X.

The repair is automatic. `IsrNmi` (`src/Z_07.asm:388`) does the game's real OAM
DMA every frame from the sprite buffer at `$0200`:

```asm
    ; Copy all our sprites to OAM.
    LDA #$00
    STA OamAddr_2003
    LDA #$02
    STA SpriteDma_4014
```

so the junk survives exactly one frame.

**Caveat — the sound channels are never re-enabled.** The write that did that
job now goes somewhere else. In practice the bank 0 audio driver stores `$0F`
to `ApuStatus_4015` in seven places of its own (`src/Z_00.asm:116`, `225`,
`530`, `569`, `571`, `833`, `835`), so the channels come back on their own.

**Caveat — page `$0F00` is not documented in this disassembly.** The NES mirrors
CPU RAM every `$0800` bytes, so `$0F00` is really `$0700`, past the last named
variable in `src/Variables.inc` (`WorldFlags`, `$67F`). What appears on screen
is therefore genuinely arbitrary — the effect is "a screenful of garbage
sprites", not any particular picture.

**Caveat — the DMA happens mid-frame.** It stalls the CPU for 513 cycles
outside vblank, so expect the scanline it lands on to tear as well.

**Caveat — the other two neighbours are worse.** `$16` and `$17` would reach the
controller strobe and the APU frame counter instead; neither is published here.

**Caveat — compare byte.** `$EC47` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play` and `IsrNmi`
(`src/Z_07.asm`) and the audio driver's `ApuStatus_4015` writes
(`src/Z_00.asm`), not from observing it in-game.

## Select keeps working while the game has paused itself

**Code:** `NYUTUGZE`

**Effect:** On its own this does almost nothing — it is an enabler. The game
pauses *itself* while your hearts refill, after a heart container or a potion,
and during that refill the Select button is deliberately ignored. This code
removes that exception, so Select is read during the refill too. Paired with
any of the other Select codes it lets you fire their effect at a moment the
game would normally lock you out of.

**How it works:** `UpdateMode5Play` (`src/Z_07.asm:1811`) gates its own Select
check on the pause state:

```asm
    LDA Paused
    CMP #$02
    BEQ @CheckPaused            ; If involuntarily paused, skip checking Select button here. But go do pause actions.
```

`Paused = $02` is the involuntary pause. `World_FillHearts`
(`src/Z_05.asm:3027`) sets it — "Flag that we're filling hearts and
involuntarily paused" — alongside `World_IsFillingHearts`, and clears both when
the meter is full (`src/Z_05.asm:6788`).

This patches the `CMP` operand at `$EC33`, `$02` → `$FF`. Raw form:
`$EC33:FF:02`. `Paused` only ever holds `0`, `1` or `2`, so the comparison can
no longer succeed and the `BEQ` never skips the Select check.

**Caveat — by itself it only makes the pause state odd.** With the handler
untouched, pressing Select during a refill runs `LDA Paused / EOR #$01` on the
value `2`, storing `3`. That is still non-zero, so the game stays paused, and
`World_FillHearts` clears it to `0` when the refill finishes. Pressing again
takes it back to `2`. Nothing breaks; nothing much happens either.

**Caveat — its value is as a second code.** Combined with a `$EC41` code —
`ILKTOGEV`, `LTKTOGET`, `VYKTOGEV` and the rest — it widens the window in which
that code's effect can be triggered.

**Caveat — it does not affect the submenu lockout.** The separate `LDA MenuState
/ BNE @CheckMenu` test above it is untouched, so Select still does nothing while
the inventory screen is open.

**Caveat — compare byte.** `$EC33` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play` (`src/Z_07.asm`)
and `World_FillHearts` (`src/Z_05.asm`), not from observing it in-game.

## Select slides the screen upward

**Codes:** `KYKTOGEV` + `EAUVNGPA`

**Effect:** The vertical twin of `SYKTOGEV`. Select stops pausing and shoves the
camera up instead: tap it and the whole picture — status bar included — jumps
128 pixels, so the top half of the screen shows the bottom half of the room you
were looking at and the bottom half shows whatever sits in the name table below
it. Link keeps playing at his real position, which is now off the visible area.
Unlike the horizontal version, nothing in normal play puts it back; you have to
open and close the inventory.

**How it works:** `CurVScroll` (`$FC`) is the shadow copy of the PPU's vertical
scroll, written to the hardware every frame alongside `CurHScroll` by the frame
loop's `@SetScroll` (`src/Z_07.asm:472`):

```asm
@SetScroll:
    LDA PpuStatus_2002
    LDA CurHScroll
    STA PpuScroll_2005
    LDA CurVScroll
    STA PpuScroll_2005
```

During mode 5 nothing writes it. Room-to-room scrolling does *not* use it, even
when the scroll is vertical — `ScrollWorldDownOrH` (`src/Z_05.asm:618`) walks a
VRAM address (`VScrollAddrHi`/`VScrollAddrLo`) a tile row at a time instead. The
only writers in bank 5 are the inventory submenu: `UpdateMenuCommon1`
(`src/Z_05.asm:193`), `UpdateMenuScrollDownOW`/`UW` (`:269`, `:273`) and
`UpdateMenuScrollUp` (`:399`), the last of which stores `$00` when the submenu
finishes retracting. Outside the menu, a value stored into `CurVScroll` simply
stays there.

Two bytes of the Select handler in `UpdateMode5Play` (`src/Z_07.asm:1811`)
supply it. `Paused` is `$E0`, so `STA Paused` is `85 E0` and its operand reaches
any zero-page variable:

- `$EC41`, `$E0` → `$FC` (`CurVScroll`) — raw `$EC41:FC:E0`, code `KYKTOGEV`.
- `$EC3F`, `$01` → `$80` — raw `$EC3F:80:01`, code `EAUVNGPA`. The handler is
  redirected away from `Paused`, so `Paused` stays `0` and `LDA Paused /
  EOR #imm` leaves `A = imm`; `$80` is 128 pixels, half a screen. `AGUVNGPA` (`$EC3F:40:01`) gives a
  quarter-screen nudge instead. This is the same second code the horizontal
  version uses.

**Caveat — `KYKTOGEV` alone shifts by one scanline.** The untouched `EOR #$01`
stores `1`. The second code is what makes the shift visible.

**Caveat — don't go past `$EF`.** The PPU's vertical scroll is only defined up
to 239. A value of `$F0` or more makes it render the attribute table as tiles
for the first few rows — which is a fine oddity if you want it, but it is
garbage, not a view of another room.

**Caveat — the inventory puts it back.** `UpdateMenuScrollUp` stores `$00` when
the submenu finishes retracting, so pressing Start twice clears the shift. That
is also the only way to clear it, since every Select press stores the same value.

**Caveat — the game can no longer be paused,** and `$EC41` is shared with every
other `$EC41` Select code, so only one of them can be active at a time. This one
needs two of your three code slots.

**Caveat — compare bytes.** `$EC3F` and `$EC41` are both in the `$C000`-`$FFFF`
window, which always maps bank 7 on this cart, so no other bank can match either
compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play` and the frame
loop's `@SetScroll` (`src/Z_07.asm`), and the submenu scroll routines and
`ScrollWorldDownOrH` (`src/Z_05.asm`), not from observing it in-game.

## Select moves you to another room without moving you

**Code:** `UTKTOGEV`

**Effect:** Select stops pausing and instead overwrites the game's idea of which
room you are standing in. Nothing changes on screen — the tiles in front of you
are already drawn and stay drawn — but from that moment the engine is reading
another room's record. Walk off any edge and you scroll into that room's
neighbour rather than your own, so one tap of Select relocates you on the world
map. Everything that is looked up per room follows: which secrets this screen
has, which palette the rocks take, what the flute does here.

**How it works:** `RoomId` (`$EB`) is the index of the room the player occupies.
It is written in exactly two places — on level entry (`src/Z_07.asm:1453`) and
by the mode-7 scroll submodes when a transition completes (`InitMode7_Finish`,
`src/Z_05.asm:949`) — and read by everything. `GetUniqueRoomId`
(`src/Z_07.asm:1134`) indexes the level block with it:

```asm
GetUniqueRoomId:
    LDY RoomId
    LDA LevelBlockAttrsD, Y
    AND #$3F                    ; Unique room ID in both OW and UW.
    RTS
```

`ChangeTileObjTiles` uses it to pick the rock/Armos palette from
`LevelBlockAttrsB` (`src/Z_07.asm:1554`), the secret-tune check compares it to
`$0F` (`:1529`), the flute searches `FluteRoomSecretsOW` with it (`:2524`), and
`CalculateNextRoomForDoor` (`src/Z_05.asm:7491`) and `CalcNextRoomByDir`
(`:7541`) add a direction offset to it to work out where an edge leads. Change `RoomId` and all of that changes at once.

The Select handler in `UpdateMode5Play` (`src/Z_07.asm:1811`) supplies the
write. `Paused` is `$E0`, so `STA Paused` is `85 E0` and its operand reaches any
zero-page variable — raw `$EC41:EB:E0`.

The value stored is whatever the untouched `EOR #$01` leaves in A, which is `1`
(nothing writes `Paused` any more, so it stays `0`): overworld room `$01`,
near the top-left of the map. Add a `$EC3F` code to choose a different one —
`YYUVNGPA` (`$EC3F:77:01`) sets room `$77`, the screen you start the game on.

**Caveat — the screen does not redraw.** You keep looking at the old room until
you scroll. The effect is entirely in what happens next.

**Caveat — objects already on screen keep their old identity.** They were
created from the old room's record by `CreateRoomObjects`; only things looked up
again after the press change.

**Caveat — underground it is rougher.** In a dungeon `RoomId` also drives door
state, the map cursor and the room-history list (`src/Z_07.asm:1603`), so a
press mid-room can leave the doors you can see disagreeing with the doors the
engine will honour.

**Caveat — the game can no longer be paused,** and `$EC41` is shared with every
other `$EC41` Select code, so only one of them can be active at a time.

**Caveat — compare bytes.** `$EC3F` and `$EC41` are both in the `$C000`-`$FFFF`
window, which always maps bank 7 on this cart, so no other bank can match either
compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play`,
`GetUniqueRoomId`, `ChangeTileObjTiles` and the flute handler (`src/Z_07.asm`),
and `CalculateNextRoomForDoor` and the mode-7 scroll submodes (`src/Z_05.asm`), not from
observing it in-game.

## Select tells the game you are in a dungeon

**Code:** `APKTOGET`

Tags: `interesting`

**Effect:** Select stops pausing and sets the current level number to 1 while
leaving you exactly where you are. Every overworld-versus-underground test in
the engine flips at once. Link is drawn two pixels higher, the frame's
per-room work starts running the dungeon jobs — statues firing, the triforce
position marker, door handling — and the flute, the secrets and the palette
choices all take their underground branch. Press it standing in a field and the
field starts behaving like a dungeon room.

**How it works:** `CurLevel` (`$10`) is `0` on the overworld and `1`-`9` in a
dungeon. It is not a copy of anything — it is the flag the whole engine branches
on. `UpdateMode5Play`'s own per-frame work tests it (`src/Z_07.asm:2010`):

```asm
@CheckUW:
    ; If in UW, check statues, doors, secrets, and the power triforce.
    LDA CurLevel
    BEQ @CheckOW
    LDA #$04
    JSR SwitchBank
    JSR UpdateStatues           ; Update statues.
    JSR UpdateTriforcePositionMarker
```

`DrawLink` shifts the sprite when it is zero ("In OW, draw Link 2 pixels down",
`src/Z_07.asm:3365`), the flute handler branches on it (`:2510`), the submenu
scroll branches on it (`src/Z_05.asm:293`, `:418`), and the room scroll speed
doubles on the overworld because of it (`ScrollWorldH`, `src/Z_05.asm:650`).

The Select handler in `UpdateMode5Play` (`src/Z_07.asm:1811`) supplies the
write. `Paused` is `$E0`, so `STA Paused` is `85 E0` and its operand reaches any
zero-page variable — raw `$EC41:10:E0`. The value stored is whatever the
untouched `EOR #$01` leaves in A, which is `1`: level 1. A `$EC3F` code picks a
different level, but `1` is the useful one — anything above `9` indexes past the
end of `LevelInfoAddrs`.

**Caveat — the level data is not reloaded.** `InitMode2_Sub0`/`Sub1`
(`src/Z_06.asm:62`, `:91`) are what actually copy a level's block and info into
RAM, and they only run when you enter a level. So you get dungeon *behaviour*
over overworld *data*: the rooms, tiles and objects are still the overworld's.

**Caveat — the room scroll halves in speed.** `ScrollWorldH` reads `CurLevel` to
pick 4 pixels a frame outdoors and 2 indoors, so transitions get noticeably
slower after the press.

**Caveat — expect the status bar to disagree with itself.** The map and
compass area is drawn from level state that was never loaded, so what it shows
after the press is not meaningful.

**Caveat — pressing it again does not undo it.** Every press stores the same
`1`. Walking into a cave or a dungeon and back out is what resets `CurLevel`.

**Caveat — the game can no longer be paused,** and `$EC41` is shared with every
other `$EC41` Select code, so only one of them can be active at a time.

**Caveat — compare byte.** `$EC41` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play`, `DrawLink` and
the flute handler (`src/Z_07.asm`), `ScrollWorldH` and the submenu scroll
(`src/Z_05.asm`), and `InitMode2_Sub0`/`Sub1` (`src/Z_06.asm`), not from
observing it in-game.

## The pause button is a coin flip

**Code:** `IPUVSGET`

**Effect:** Select still pauses and unpauses, but only about half the time.
Press it and the game freezes, or does not, depending on which frame you
happened to catch. Press it again and you get another 50/50. Nothing is ever
stuck — you just have to mash Select until it takes.

**How it works:** the toggle reads the current pause state, flips the low bit,
and stores it back (`src/Z_07.asm:1836`):

```asm
    LDA Paused                  ; then toggle pause.
    EOR #$01
    STA Paused
```

`LDA Paused` assembles as `A5 E0`, and its operand reaches any zero-page
variable. Retarget it at `FrameCounter` (`$15`): raw `$EC3D:15:E0`. The store
still goes to `Paused`, so the instruction now means `Paused = FrameCounter ^ 1`
— the pause state is decided by the parity of the frame you pressed on, not by
what it was before.

`FrameCounter` is incremented once per frame by the NMI handler
(`src/Z_07.asm:535`) and is used everywhere as a free-running clock, so its low
bit alternates every frame and there is no way to time a press against it.

**Caveat — it cannot lock you up, and that is not an accident.** Any zero-page
variable whose parity is *fixed* while the game is frozen would be a soft-lock
instead of a coin flip: it would decide the same way on every press, and if that
decision is "paused" you could never get out. `FrameCounter` keeps counting
during the pause — the NMI runs regardless — which is exactly what makes this
one safe. `ObjX` (`$70`) and `ObjState` (`$AC`) are not, so do not substitute
them.

**Caveat — one press in two is wasted,** including the press that turns the
sound back on. The `LDA #$0F / STA ApuStatus_4015` branch below the store only
runs when the result is zero, so the audio channels get re-enabled on exactly
the presses that unpause. That part is unchanged.

**Caveat — mode 5 only,** and the involuntary heart-refill pause (`Paused` =
`$02`) still skips this check entirely.

**Caveat — `$EC3D` conflicts with nothing else published,** but the value it
loads feeds the same `EOR` operand at `$EC3F` that several other codes patch, so
combining it with one of those changes what gets stored in a way neither writeup
describes.

**Caveat — compare byte.** `$EC3D` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play` and `IsrNmi`
(`src/Z_07.asm`), not from observing it in-game.

## Select swings the sword instead of A

**Code:** `AXXULZEA` (pair it with `AAUVOGAZ`)

**Effect:** The sword moves off A and onto Select. A becomes an inert button —
it no longer attacks — and every Select press swings instead. Everything else
about the sword is unchanged: the beam still fires at full health, the
sword-blocked guard still applies, and B still uses your item.

**How it works:** `Link_HandleInput` (`src/Z_05.asm:6921`) tests the two action
buttons in sequence, but only while Link is in state 0:

```asm
    ; If the sword is not blocked, then handle the sword if A is pressed.
    LDA SwordBlockedLongTimer
    ORA SwordBlocked
    BNE :+
    LDA ButtonsPressed
    AND #$80
    BEQ :+
    JSR WieldSword
```

`$80` is the A bit of `ButtonsPressed`; `$20` is the Select bit. This patches
the mask at `src/Z_05.asm:6932`, bank 5 CPU `$B2AB`, `$80` → `$20`. Raw form:
`$B2AB:20:80`.

**Caveat — take the companion code.** Without it, Select is still the pause
button, and `UpdateMode5Play`'s pause check runs *before* the world update. So
the press that pauses returns before `Link_HandleInput` is ever reached and the
swing is swallowed; only the press that unpauses swings. `AAUVOGAZ`
(`$EC39:00:20`) makes the pause mask zero, Select stops pausing, and every press
swings. Two codes, one mechanic.

**Caveat — Link's state gates it, as it always did.** The whole block is behind
`LDA ObjState / BNE @CheckMovement`, so pressing Select does nothing while Link
is already swinging, hurt, or in a transition.

**Caveat — this is the mask, not the button.** Anything else that reads the A
bit — the title screen, the file-select screen, the submenu — is untouched, and
A still works there.

**Caveat — compare byte.** `$B2AB` is in the switched `$8000`-`$BFFF` window.
Checked against every bank of `zelda1.nes`: bank 5 is the only one holding `$80`
at that offset, so the compare byte cannot fire anywhere else.

**Not live-verified:** derived from reading `Link_HandleInput` (`src/Z_05.asm`)
and `UpdateMode5Play` (`src/Z_07.asm`), not from observing it in-game.

## Select uses your item instead of B

**Code:** `AXULGZAG` (pair it with `AAUVOGAZ`)

**Effect:** The B-slot item moves off B and onto Select. B stops doing anything;
Select throws the boomerang, fires the arrow, drops the bomb, plays the
Recorder — whatever is in the slot. The sword stays on A.

**How it works:** the item test sits directly below the sword test in
`Link_HandleInput` (`src/Z_05.asm:6937`):

```asm
    ; If B is pressed, handle the item.
    LDA ButtonsPressed
    AND #$40
    BEQ @CheckMovement
    JSR WieldItem
```

`$40` is the B bit; `$20` is Select. This patches the mask at
`src/Z_05.asm:6938`, bank 5 CPU `$B2B4`, `$40` → `$20`. Raw form:
`$B2B4:20:40`.

**Caveat — take the companion code,** for the same reason as the sword version:
without `AAUVOGAZ` (`$EC39:00:20`) the pause check eats every other press, so
the item only comes out on the presses that unpause.

**Caveat — combining it with `AXXULZEA` puts both on one button.** Select would
then pass both masks in the same frame and fire `WieldSword` and `WieldItem`
back to back. That is the same untested double-fire the B-swings-the-sword code
warns about; treat it as unexplored.

**Caveat — Link's state gates it,** exactly as it gates the sword: the block
runs only at `ObjState` 0.

**Caveat — compare byte.** `$B2B4` is in the switched `$8000`-`$BFFF` window.
Checked against every bank of `zelda1.nes`: bank 5 is the only one holding `$40`
at that offset.

**Not live-verified:** derived from reading `Link_HandleInput` (`src/Z_05.asm`)
and `UpdateMode5Play` (`src/Z_07.asm`), not from observing it in-game.

## Select opens the subscreen — or nobody does

**Codes:** `AZNTKGAP` (Select opens it) · `AANTKGAP` (nothing opens it)

**Effect:** `AZNTKGAP` moves the inventory screen off Start and onto Select.
Start becomes inert. `AANTKGAP` removes the inventory screen from the game
entirely — no button opens it, so you are stuck with whatever B item you had
when you enabled the code and you cannot see the map, the compass or your
triforce pieces.

**How it works:** this is the *real* menu entry point, distinct from the
published "Select opens the subscreen" code, which reaches `MenuState` through
the redirected store at `$EC41`. `UpdateMode5Play` tests Start here
(`src/Z_07.asm:1868`):

```asm
@NotInMenu:
    ; Not in submenu.
    LDA ButtonsPressed
    AND #$10
    BEQ BeginUpdateWorld        ; If Start not pressed, go update the world.
    INC MenuState               ; Else set menu state 1 to start scrolling.
    RTS
```

`$10` is the Start bit. The mask at `src/Z_07.asm:1871`, bank 7 CPU `$EC74`,
becomes `$20` for Select (`$EC74:20:10`, `AZNTKGAP`) or `$00` for nothing at all
(`$EC74:00:10`, `AANTKGAP` — the `AND` can never be non-zero, so the `BEQ`
always falls through to `BeginUpdateWorld`).

**Caveat — `AZNTKGAP` wants `AAUVOGAZ` too.** `@NotInMenu` is downstream of the
pause check, so an unaccompanied Select press pauses first and never arrives
here; the menu would open only on the presses that unpause. `AAUVOGAZ`
(`$EC39:00:20`) clears that up.

**Caveat — `INC MenuState` is only reached at `MenuState` 0.** Once the submenu
is up, `@CheckMenu` routes to `UpdateMenuAndMeters` instead, so neither code can
drive `MenuState` past its valid range.

**Caveat — closing it is unchanged.** The submenu's own Start handling lives in
bank 5 (`src/Z_05.asm:2206`) and is not patched, so with `AZNTKGAP` you open
with Select and still close with Start.

**Caveat — `AANTKGAP` is a difficulty code, and a harsh one.** Whatever is in
your B slot when you switch it on is what you keep. It also hides the dungeon
map and compass for the rest of the run.

**Caveat — compare byte.** `$EC74` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateMode5Play` (`src/Z_07.asm`)
and the submenu update routines (`src/Z_05.asm`), not from observing it in-game.

## Every button auto-repeats

**Code:** `IPNTPTIL`

**Effect:** One byte in the controller reader turns every "was just pressed"
test in the game into "is being held". Hold A and Link swings the sword as fast
as his animation allows; hold B and the arrows, bombs or boomerangs pour out
until the rupees or bombs run dry; hold Select and the game drops to half speed;
hold a direction on the file-select screen and the cursor runs away. Menus you
used to tap through become things you have to feather.

**How it works:** `ReadOneController` (`src/Z_07.asm:687`) polls the pad into
`ButtonsPressed`, where it temporarily means "down now", then converts that into
a rising edge (`src/Z_07.asm:729`):

```asm
    PHA
    EOR ButtonsDown, X
    AND ButtonsPressed, X
    STA ButtonsPressed, X       ; Now ButtonsPressed means "down now instead of before".
    PLA
    STA ButtonsDown, X
```

`EOR ButtonsDown, X` produces the bits that *changed* since last frame, and
`AND ButtonsPressed, X` keeps only the changes that are currently down — the
newly-pressed bits. Verified unique in bank 7 at `$E66E`:
`48 55 FA 35 F8 95 F8 68 95 FA 60`. `AND zp,X` is `35`; `ORA zp,X` is `15`. Raw
form: `$E671:15:35`.

With `ORA`, the result is `changed | down now`, which is every button currently
held plus the ones released this frame. `ButtonsDown` is still written correctly
from the stacked copy, so held-state readers — Link's movement, which uses
`LDA ButtonsDown / AND #$0F / STA ObjInputDir` (`src/Z_07.asm:1856`) — behave
exactly as before. Only the edge readers change.

**Caveat — releasing a button fires it one last time.** The released bits are in
`changed` but not in `down now`, so `ORA` lets them through for a single frame.
Let go of A and you get one extra swing.

**Caveat — this is the root of the input system, and it touches everything at
once.** The pause toggle, the sword, the B item, the shop Letter, the submenu
cursor, the title and file-select screens all read `ButtonsPressed`. Expect
every one of them to repeat.

**Caveat — Link's state machine is what stops it being infinite.** The sword and
item block in `Link_HandleInput` runs only at `ObjState` 0, so holding A gives
you the fastest swing rate the animation permits, not one swing per frame.

**Caveat — the submenu is safe, the wallet is not.** `INC MenuState` is only
reachable at `MenuState` 0, so Start cannot run the menu state past its range.
Arrows, bombs and bait have no such guard — holding B will empty you out.

**Caveat — compare byte.** `$E671` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `ReadOneController`,
`UpdateMode5Play` (`src/Z_07.asm`) and `Link_HandleInput` (`src/Z_05.asm`), not
from observing it in-game.

## Darknuts and Pols Voice trade movement

**Codes:** `XXKNXULG` (blue Darknuts hop) · `XXKNKULG` (red Darknuts hop) ·
`LKVYELXX` (Pols Voice march)

**Effect:** `XXKNXULG` makes blue Darknuts stop marching in straight lines and
start hopping across the room the way Pols Voice does, arcing over gaps and
bouncing off blocks. `XXKNKULG` does the same for the red ones. `LKVYELXX` is
the reverse: Pols Voice stop hopping and patrol the room like Darknuts —
including the part where they can no longer be stunned. Use them separately or
together.

**How it works:** every object's per-frame behaviour is a `TableJump` through
`UpdateObject_JumpTable` (`src/Z_07.asm:5321`), indexed by object type. The
caller (`UpdateObject`, `src/Z_07.asm:5266`) maps bank 4 first, so the table's
handlers all live there:

```asm
@NormalObject:
    ; Else call the object update routine.
    JSR TableJump

UpdateObject_JumpTable:
    .ADDR DoNothing
    .ADDR UpdateLynel
    ...
```

Each entry is two bytes, so entry *n*'s low byte sits at `$FBB4 + 2n`.
`UpdateDarknut` is at bank 4 `$9B4B` (`src/Z_04.asm:6475`) and `UpdatePolsVoice`
at `$9BA2` (`src/Z_04.asm:6533`) — the same 256-byte page, so a single byte
repoints one at the other:

| code | raw | entry | type |
|------|-----|-------|------|
| `XXKNXULG` | `$FBCA:A2:4B` | `$0B` | blue Darknut → `UpdatePolsVoice` |
| `XXKNKULG` | `$FBCC:A2:4B` | `$0C` | red Darknut → `UpdatePolsVoice` |
| `LKVYELXX` | `$FBE0:4B:A2` | `$16` | Pols Voice → `UpdateDarknut` |

The substitution is well-behaved because both routines drive the same standard
object fields. `UpdateDarknut` calls `UpdateCommonWanderer` and reads `ObjDir`;
`UpdatePolsVoice` reads `ObjState` (tested for zero, never used as an index),
`ObjRemDistance` and `ObjDir`. Neither indexes a jump table with a field the
other does not maintain, so there is no way to land on a garbage address.

**Caveat — the creature keeps its own sprites.** `DrawObjectNotMirrored`
(`src/Z_01.asm:5037`) takes the animation set from `ObjType, X`
(`src/Z_01.asm:5043`) and only the *frame image number* from the caller. So a
hopping Darknut is still drawn as a Darknut — but with the frame numbers Pols
Voice picks, which are not the same range. Expect wrong-looking or repeated
animation frames, not a Pols Voice sprite.

**Caveat — `LKVYELXX` makes Pols Voice unstunnable.** `UpdateDarknut` clears
`ObjStunTimer` on every call ("Darknuts are never stunned",
`src/Z_04.asm:6481`), so the boomerang stops working on them.

**Caveat — `XXKNXULG` gives Darknuts a weakness they did not have.**
`UpdatePolsVoice` honours `ObjStunTimer` instead of clearing it, so a hopping
Darknut *can* be stunned. It also skips its move on odd frames, so it covers
ground more slowly than it used to.

**Caveat — nothing about toughness changes.** Hit points come from
`ObjectTypeToHpPairs` (`src/Z_07.asm:5256`), indexed by object type, and the
weapon-damage rules are keyed to type as well. Swapping the update handler
changes how a creature *moves*, never how hard it is to kill.

**Caveat — compare bytes.** `$FBCA`, `$FBCC` and `$FBE0` are all in the
`$C000`-`$FFFF` window, which always maps bank 7 on this cart, so no other bank
can match their compare bytes.

**Not live-verified:** derived from reading `UpdateObject` and
`UpdateObject_JumpTable` (`src/Z_07.asm`), `UpdateDarknut` and
`UpdatePolsVoice` (`src/Z_04.asm`) and `DrawObjectNotMirrored`
(`src/Z_01.asm`), not from observing it in-game.

## Red Leevers never burrow again

**Code:** `NNSYKUPE`

**Effect:** The red Leevers in the desert stop being ambushers. Instead of
lurking underground, rising in front of you and sinking away, they stay above
ground permanently and behave like fast Octoroks — wandering, turning toward
Link, and spitting rocks at him. There is no longer any warning-free lunge,
but there is a lot more incoming fire.

**How it works:** the same one-byte lever on `UpdateObject_JumpTable`
(`src/Z_07.asm:5321`). Entry `$10` is the red Leever, and its low byte sits at
`$FBB4 + 2 × $10` = `$FBD4`. `UpdateRedLeever` is at bank 4 `$8B09`
(`src/Z_04.asm:2744`) and `UpdateOctorock` at `$8BFF` (`src/Z_04.asm:2969`) —
same page, one byte apart in the table. Raw form: `$FBD4:FF:09`.

`UpdateOctorock` decides its own parameters from the object's type rather than
from any state the Leever failed to set up:

```asm
UpdateOctorock:
    ; If the monster is a fast octorock, use turn rate $A0.
    ; Else use turn rate $70.
    LDA #$A0
    LDY ObjType, X
    CPY #$09                    ; Blue octorock (fast and slow)
    BCS :+
    LDA #$70
```

A red Leever is type `$10`, which is above every Octorok id, so it takes the
fast turn rate and the doubled q-speed. That is why the substitution needs no
companion code: the handler configures itself.

**Caveat — the Leever population cap stops applying.** `UpdateRedLeever`'s state
0 is what enforces "only two red Leevers at a time" via `ActiveRedLeeverCount`
and gates on `RedLeeverLongTimer`. With the handler gone, neither is consulted,
so however many the room spawns are all active at once.

**Caveat — they still look like Leevers.** `DrawObjectNotMirrored` picks the
animation set from `ObjType`, so you get Leever sprites doing Octorok things,
with the frame numbers `UpdateOctorock` chooses.

**Caveat — blue Leevers are a separate entry** (`$0F`, `UpdateBlueLeever`) and
are untouched. This code is only the red ones.

**Caveat — the rocks are real.** `UpdateOctorock` shoots object type `$53`,
flying rocks, through `_TryShooting`. They come out of a creature that never
had a projectile before.

**Caveat — compare byte.** `$FBD4` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateObject_JumpTable`
(`src/Z_07.asm`) and `UpdateRedLeever` and `UpdateOctorock` (`src/Z_04.asm`),
not from observing it in-game.

## Moblins sink into the ground and never come back

**Codes:** `EOUNXUNU` (blue Moblins) · `EOUNKUNU` (red Moblins)

**Effect:** Moblins stop wandering and shooting arrows. Instead they run the
Zora's cycle: they surface, spit a fireball, and submerge — and when the cycle
comes back around they delete themselves. So a Moblin room clears itself after
one pass, at the cost of one fireball per Moblin. As a side effect the overworld
stops producing Zoras entirely for the rest of the session.

**How it works:** entries `$03` and `$04` of `UpdateObject_JumpTable`
(`src/Z_07.asm:5321`) are the blue and red Moblin, at `$FBBA` and `$FBBC`.
`UpdateMoblin` is at bank 4 `$87BF` (`src/Z_04.asm:1950`) and `UpdateZora` at
`$8798` (`src/Z_04.asm:1915`) — same page. Raw forms: `$FBBA:98:BF` and
`$FBBC:98:BF`.

`UpdateZora` delegates the surfacing to `UpdateBurrower` (`src/Z_04.asm:2606`),
which is type-agnostic — it cycles `ObjState` 0 → 5 with a bounds check and
indexes two six-entry speed/timer tables, so a Moblin cannot land out of range.
The one type-specific branch inside it tests for `$11` (Zora) and a Moblin
simply skips it.

What makes this a *disappearing* code is the tail of `UpdateZora`:

```asm
@DestroyWhenDone:
    ; If state = 0, then destroy zora object.
    ; Also flag it inactive, so that the object update loop will try
    ; to make another one.
    LDA ObjState, X
    BNE L10797_Exit
    DEC ZoraActive
    JMP DestroyMonster
```

Every time the state cycle wraps back to 0, the object is destroyed and
`ZoraActive` is decremented. A Moblin never incremented it, so the counter goes
to `$FF`.

**Caveat — that is why the Zoras stop.** The spawn check is `LDA ZoraActive /
BNE @Exit` (`src/Z_04.asm:1765`), so a non-zero counter means "a Zora is already
out." Once the first Moblin has wrapped, no Zora will ever spawn again until you
reset. Whether you count that as a bonus or a loss is up to you.

**Caveat — it is a kill code, not a stealth code.** The Moblins really are
destroyed, which means they do not count as kills for the room's dropped item.

**Caveat — they still look like Moblins,** drawn from the `ObjType` animation
set, with `UpdateZora`'s frame numbers.

**Caveat — Lynels are a separate pair of entries** (`$01`/`$02`) and keep their
own behaviour, so the dangerous half of the overworld roster is unaffected.

**Caveat — compare bytes.** `$FBBA` and `$FBBC` are in the `$C000`-`$FFFF`
window, which always maps bank 7 on this cart, so no other bank can match their
compare bytes.

**Not live-verified:** derived from reading `UpdateObject_JumpTable`
(`src/Z_07.asm`) and `UpdateMoblin`, `UpdateZora`, `UpdateBurrower` and the Zora
spawn check (`src/Z_04.asm`), not from observing it in-game.

## Vires teleport and throw magic

**Code:** `UVSNELYI`

**Effect:** Vires stop being the two-legged hoppers that split into a pair of
red Keese when you cut them down. Instead they behave like blue Wizzrobes:
they walk a few squares, fade out, reappear somewhere else in the room, and
throw magic at Link. The splitting is gone entirely, because splitting is
something the Vire handler did and the Wizzrobe handler does not.

**How it works:** entry `$12` of `UpdateObject_JumpTable` (`src/Z_07.asm:5321`)
is the Vire; its low byte sits at `$FBB4 + 2 × $12` = `$FBD8`. `UpdateVire` is
at bank 4 `$9D57` (`src/Z_04.asm:6915`) and `UpdateBlueWizzrobe` at `$9DE3`
(`src/Z_04.asm:7034`) — the same 256-byte page. Raw form: `$FBD8:E3:57`.

`UpdateBlueWizzrobe` is one of the safe substitutes: it drives `ObjTimer`,
`ObjRemDistance` and `ObjDir`, all standard fields, and it never uses an object
field as a jump-table index.

```asm
UpdateBlueWizzrobe:
    LDA InvClock
    BNE L_Wizzrobe_DrawAndCheckCollisions
    JSR BlueWizzrobe_WalkOrTeleport
    JSR BlueWizzrobe_TryShooting
```

The timer decides the phase — at `$10` and above it walks, at 1 it picks a
teleport target, at 0 it fades across — so a Vire, whose timer is set by the
generic monster init, drops straight into the cycle.

**Caveat — do not try this in reverse.** Pointing a Wizzrobe at `UpdateVire`
(`$FBFA:57:E3`) is exactly the unsafe shape: `UpdateVireState` does
`LDA ObjState, X / JSR TableJump` into a *two-entry* table with no bounds
check, so any object whose state ever exceeds 1 jumps to whatever address the
following bytes happen to form.

**Caveat — the splitting stops, and so does the Keese supply.** `UpdateVire`'s
state ≥ 2 branch is what calls `FindEmptyMonsterSlot` twice and shoots two red
Keese. With this code no Vire ever produces one.

**Caveat — they still look like Vires,** drawn from the `ObjType` animation set
by `DrawObjectNotMirrored` (`src/Z_01.asm:5043`), with the frame numbers the
Wizzrobe handler picks. Expect the fade-out to look wrong, since a Vire has no
translucent frames.

**Caveat — hit points are unchanged.** They come from `ObjectTypeToHpPairs`
(`src/Z_07.asm:5256`), indexed by type.

**Caveat — compare byte.** `$FBD8` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateObject_JumpTable`
(`src/Z_07.asm`) and `UpdateVire`, `UpdateVireState` and `UpdateBlueWizzrobe`
(`src/Z_04.asm`), not from observing it in-game.

## Dungeon traps throw you out of the dungeon

**Codes:** `AGKYVGAT` + `AGKNEGAT`

**Effect:** The spike blocks that sit in the corners of dungeon rooms stop
lunging. They drift steadily to the right instead, and the moment one touches
Link it grabs him, hides him, and carries him off the right edge of the
screen — the Recorder whirlwind's entire routine, running on a trap. When it
leaves the screen the game changes mode and deposits Link outside a level
entrance on the overworld. It is a one-way exit from any trapped room, on
contact, whether you wanted it or not.

**How it works:** entries `$49` and `$4A` of `UpdateObject_JumpTable`
(`src/Z_07.asm:5321`) are the two trap types, at `$FC46` and `$FC48`. Both
handlers are bank-7 trampolines that switch to bank 1 (`src/Z_07.asm:5724` and
`:5744`), so they sit in the same page and swap in one byte each:

| code | raw | entry |
|------|-----|-------|
| `AGKYVGAT` | `$FC46:40:60` | trap type 1 → `UpdateWhirlwind` |
| `AGKNEGAT` | `$FC48:40:60` | trap type 2 → `UpdateWhirlwind` |

`UpdateWhirlwind_Full` (`src/Z_01.asm:1768`) adds 2 to the object's X every
frame, calls `CheckLinkCollision`, and on a hit halts Link (state `$40`), hides
his sprites, picks a destination from `TeleportingLevelIndex`, and sets
`WhirlwindTeleportingState`. When the object's X reaches `$F0`:

```asm
    JSR DestroyWhirlwind
    LDA WhirlwindTeleportingState
    BEQ @Draw
    TXA
    PHA
    JSR GoToNextModeFromPlay
```

It has no jump-table index on any object field, so it is safe to point anything
at it.

**Caveat — the destination is whatever the flute last chose.**
`TeleportingLevelIndex` is masked with `#$07` and used to look up
`WhirlwindPrevRoomIdList`. It is advanced by the Recorder's own whirlwind
logic, so if you have not used the Recorder this run you get whatever value it
happens to hold — repeatable, but not predictable from the writeup.

**Caveat — use both codes or neither.** The two trap types are separate table
entries. A room laid out with the type you did not patch still has ordinary
traps in it.

**Caveat — traps are not monsters you can kill,** and this does not change that.
The whirlwind handler has no collision-damage path of its own, so a patched trap
neither hurts you nor can be destroyed; it only carries you away.

**Caveat — it fires once per trap.** The object destroys itself at the right
edge, so each patched trap is a single use per room visit.

**Caveat — they still look like traps,** since `DrawWhirlwind` goes through the
same `ObjType`-indexed animation lookup. You do get the whirlwind's palette
flash, which cycles on the frame counter.

**Caveat — compare bytes.** `$FC46` and `$FC48` are in the `$C000`-`$FFFF`
window, which always maps bank 7 on this cart, so no other bank can match their
compare bytes.

**Not live-verified:** derived from reading `UpdateObject_JumpTable` and the
bank-7 trampolines (`src/Z_07.asm`) and `UpdateWhirlwind_Full` and
`UpdateTrap_Full` (`src/Z_01.asm`), not from observing it in-game.

## The rupees in the cave lunge at you

**Code:** `ATONVGAI`

**Effect:** The piles of rupees you walk over to collect in a money cave stop
being pickups. They become traps: each one senses Link along its row or column
and shoots across the room at him. Walking into one no longer adds a rupee — it
runs the trap's collision handling instead.

**How it works:** entry `$35` of `UpdateObject_JumpTable` (`src/Z_07.asm:5321`)
is the rupee stash, at `$FC1E`. `UpdateRupeeStash` and `UpdateTrap` are both
bank-7 trampolines into bank 1 (`src/Z_07.asm:5734` and `:5744`), sixteen bytes
apart in the same page. Raw form: `$FC1E:60:50`.

What you give up is `UpdateRupeeStash_Full` (`src/Z_01.asm:2608`), which is the
whole pickup:

```asm
    ; Else Link is close enough. Add 1 rupee, and destroy this object.
    JSR TakeOneRupee
    JSR DestroyMonster

    ; Once you've taken one, it counts as taking them all
    ; once you leave the room.
    LDA #$00
    STA RoomObjCount
```

What you get is `UpdateTrap_Full` (`src/Z_01.asm:2459`), a two-state machine:
state 0 senses Link within `$0E` pixels on one axis, sets `ObjDir` toward him,
and advances to state 1 at q-speed `$70`.

**Caveat — the allowed-direction table is indexed by slot, not by type.**
`UpdateTrap_Full` does `AND TrapAllowedDirs-1, X` (`src/Z_01.asm:2496`) against
a six-byte table meant for the six trap slots. A rupee stash in a higher slot
reads past the table into the following instruction bytes. That is a data read,
not a jump, so it cannot crash — it just gives that stash an arbitrary set of
directions it is willing to move in.

**Caveat — the room does not think it is empty.** `RoomObjCount` is cleared by
the pickup path, which no longer runs, so the "you took them all" shortcut is
gone.

**Caveat — this makes the money cave a losing proposition,** which is the
point, but it also means the cave's own logic still expects you to be able to
collect. Treat the cave's exit behaviour as unexplored.

**Caveat — they still look like rupees.** `DrawObjectNotMirrored` picks the
animation set from `ObjType` (`src/Z_01.asm:5043`).

**Caveat — compare byte.** `$FC1E` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match the compare byte.

**Not live-verified:** derived from reading `UpdateObject_JumpTable` and the
bank-7 trampolines (`src/Z_07.asm`) and `UpdateRupeeStash_Full` and
`UpdateTrap_Full` (`src/Z_01.asm`), not from observing it in-game.

## The old man's invisible wall covers the whole room

**Code:** `NNUXPVVE`

**Effect:** The opposite of `AEUXPVVA` above. Normally a person in the room
only stops Link from walking up while he is in the *upper* part of it — below
that line the veto is switched off. This code removes the line, so for as long
as a person or a Grumble Moblin is in the room, Link cannot walk upward
anywhere in it. He can still move down, left and right, so caves are still
enterable and leavable; he simply can never make northward progress in a room
that has one of these characters in it.

**How it works:** same byte as `AEUXPVVA`, taken the other way.
`CheckPersonBlocking` (`src/Z_01.asm:3144`) opens with a Y test:

```asm
CheckPersonBlocking:
    LDA ObjY
    CMP #$8E
    BCS :-                      ; Return if Y coordinate >= $8E.
    LDA $0F
    AND #$08
    BEQ :-                      ; If not moving up, then return.
    JMP ResetMovingDir
```

The compare operand at bank 1 CPU `$A6B9` goes from `$8E` to `$FF`. Link's Y
never reaches `$FF`, so the early return never fires and the direction test
runs at every position. Raw form: `$A6B9:FF:8E`.

**Caveat — mutually exclusive with `AEUXPVVA`.** Both patch `$A6B9`.

**Caveat — this byte is copied into Save RAM before it runs.**
`CheckPersonBlocking` is inside the `BANK_01_CODE` block that
`CopyCommonCodeToRam` (`src/Z_01.asm:1569`) copies from ROM `$A500`+ to
`$6C90`+; the instruction executes at `$6E48`. The Game Genie sees the read
that the copy loop makes, so the patched byte is what lands in RAM — but the
code has to be switched on before the copy, which `UpdateMode*` triggers at
`src/Z_07.asm:1262` and `:1346`.

**Caveat — bank-unique.** A scan of all eight PRG banks found `$8E` at this
`$8000`-window offset only in bank 1.

**Caveat — Level 7's Grumble Moblin still lets you through once fed.**
`UpdateGrumble3` (`src/Z_01.asm`) clears `ObjType+1` after the feeding
animation, and the whole check is gated on that byte, so the wall lifts with
him. This code makes the room harder to cross, not impossible.

**Not live-verified:** derived from reading `CheckPersonBlocking` and
`CopyCommonCodeToRam` (`src/Z_01.asm`) and `Walker_Move` (`src/Z_07.asm`), not
from observing it in-game.

## The hungry Goriya stops blocking the way (but shopkeepers still do)

**Code:** `AAXNYEAA`

**Effect:** The Grumble Moblin in Level 7 no longer stands in your way. You
walk straight past him without the food, and the Bait stays in your inventory.
Every other person — shopkeepers, the old men, the door-repair charger — keeps
blocking exactly as it always did.

**How it works:** `Walker_Move` (`src/Z_07.asm:2600`) decides whether to
consult `CheckPersonBlocking` by looking at what is in object slot 1. The
Grumble is checked separately from the person range:

```asm
    LDA ObjType+1
    CMP #$36                    ; Grumble moblin
    BEQ @CheckBlocked
    CMP #$4B                    ; Person1
    BCC @CheckSubroomOrDoorways
    CMP #$53                    ; Person8
    BCS @CheckSubroomOrDoorways

@CheckBlocked:
    JSR CheckPersonBlocking
```

The `BEQ`'s displacement at `$F02F` goes from `$08` to `$00`. A branch of zero
lands on the very next instruction, `CMP #$4B` — so type `$36` now falls into
the range test, fails it (`$36 < $4B`), and takes the `BCC` past the blocking
call. Raw form: `$F02F:00:08`.

**Caveat — this is the surgical half of `AEUXPVVA`.** That code disables the
blocking routine outright and frees you from persons *and* the Grumble. This
one leaves persons alone. Its companion `LGUYIALS` below does the reverse.

**Caveat — knockback is unaffected.** There is a second copy of the same type
test in `ShoveMoveMin` (`src/Z_07.asm:2427`), which decides whether a shoved
object can be pushed past a person. This code only patches the `Walker_Move`
copy, so being knocked back into the Grumble still stops at him.

**Caveat — you can still feed him.** Nothing about the Bait handling changes;
walking past is simply now an option.

**Caveat — compare byte.** `$F02F` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match it.

**Not live-verified:** derived from reading `Walker_Move` (`src/Z_07.asm`) and
`CheckPersonBlocking` (`src/Z_01.asm`), not from observing it in-game.

## Shopkeepers stop blocking the way (but the hungry Goriya still does)

**Code:** `LGUYIALS`

**Effect:** The mirror image of `AAXNYEAA`. All eight person types — cave
shopkeepers, the old men with the hint text, the "leave your life or your
money" pair, the door-repair charger — stop vetoing Link's upward movement, so
he can step behind their counters. The Grumble Moblin in Level 7 still blocks
until you feed him.

**How it works:** the same `Walker_Move` type test. The person range is a pair
of compares, `CMP #$4B / BCC skip` then `CMP #$53 / BCS skip`, so types `$4B`
through `$52` fall through to `JSR CheckPersonBlocking`. Lowering the upper
bound at `$F035` from `$53` to `$4B` makes the range empty: any type that
survives the first compare (`>= $4B`) now also satisfies the second (`>= $4B`)
and branches away. Raw form: `$F035:4B:53`.

**Caveat — mutually compatible with `AAXNYEAA`.** Different bytes, and using
both is equivalent to `AEUXPVVA` at the cost of a second code slot; the
difference is that this pair leaves `CheckPersonBlocking` itself intact, so
the `ShoveMoveMin` caller still behaves normally.

**Caveat — knockback is unaffected,** for the same reason as above: the second
copy of the test in `ShoveMoveMin` (`src/Z_07.asm:2427`) is not patched.

**Caveat — buying still works.** The block is only a movement veto;
`UpdateUnderworldPerson` and its collision handling are untouched, so the
wares, the text and the purchase all behave as usual.

**Caveat — compare byte.** `$F035` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match it.

**Not live-verified:** derived from reading `Walker_Move` (`src/Z_07.asm`) and
`CheckPersonBlocking` (`src/Z_01.asm`), not from observing it in-game.

## The hungry Goriya lunges at you

**Code:** `ATXYEGEP`

**Effect:** The Grumble Moblin stops being a character you can talk to and feed.
He becomes a spike trap: he sits still until Link lines up with him, then
charges. He still blocks the way north — that veto does not depend on where he
is standing — and because the feeding logic is gone, he blocks it forever.

**How it works:** entry `$36` of `UpdateObject_JumpTable` (`src/Z_07.asm:5321`)
is the Grumble, at `$FC20`. `UpdateGrumble` and `UpdateTrap` are both bank-7
trampolines into bank 1 (`src/Z_07.asm:5774` and `:5744`), sixteen bytes apart
in page `$FE`, so the swap is one byte and trivially bank-safe. Raw form:
`$FC20:60:90`.

What is lost is `UpdateGrumble_Full` (`src/Z_01.asm:1482`), which draws the
Grumble, runs `Person_CheckCollisions`, and dispatches on `ObjState+1` through
a four-state machine — the last state of which, `UpdateGrumble3`, is the one
that consumes the Bait and does `STA ObjType+1` with A = 0 to clear his type.
That store is what lifts the wall in the ordinary game, so with this code
nothing ever lifts it.

**Caveat — Level 7 becomes impassable unless you pair this with `AAXNYEAA`.**
The blocking test in `Walker_Move` reads `ObjType+1` and compares it to `$36`;
without the feeding path there is no longer anything that clears it. Use the
two codes together if you want the room to be crossable at all.

**Caveat — he can only lunge right or down.** `UpdateTrap_Full`
(`src/Z_01.asm:2459`) masks its chosen direction with `TrapAllowedDirs-1, X`
(`src/Z_01.asm:2456`, `.BYTE $05, $09, $06, $0A, $01, $02`). A person always
occupies slot 1, so X = 1 selects the first entry, `$05` — right plus down. Any
lunge he would otherwise make upward or to the left is discarded and he stays
put.

**Caveat — do not point anything else at the Grumble.**
`UpdateGrumble_Full` ends with `LDA ObjState+1 / JSR TableJump` into a
four-entry table with no bounds check, and reads slot 1 by hard-coded address
rather than through X. It is safe as a source entry, never as a destination.

**Caveat — he still looks like a Moblin.** `DrawObjectNotMirrored`
(`src/Z_01.asm:5043`) takes the animation set from `ObjType`, and the trap
handler does draw him, so he stays visible with the frame numbers the trap
picks.

**Caveat — compare byte.** `$FC20` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match it.

**Not live-verified:** derived from reading `UpdateObject_JumpTable` and the
bank-7 trampolines (`src/Z_07.asm`) and `UpdateGrumble_Full` and
`UpdateTrap_Full` (`src/Z_01.asm`), not from observing it in-game.

## Buy the bomb-capacity upgrade over and over

**Code:** `AAUEUXYG`

**Effect:** The old man who sells you four more bomb slots for 100 rupees stops
being a one-time offer. He is still gone for the rest of the visit once you pay
him, but leave the room and come back and he is there again, offering the same
deal. Every purchase costs another 100 rupees and adds another four to your
maximum bomb count.

**How it works:** the purchase itself never checks whether you have already
made it. `UpdateUnderworldPersonComplexState_SenseLink` (`src/Z_01.asm:1265`)
tests only that the man is type `$4F`, that Link is standing at X `$78` within
six pixels of the rupee at Y `$98`, and that `InvRupees` is at least `$64`:

```asm
@CheckCanPay:
    LDA #$64
    CMP InvRupees
    BEQ :+
    BCS @Exit
:
    CLC
    ADC RupeesToSubtract
    STA RupeesToSubtract
    ...
    LDA MaxBombs
    CLC
    ADC #$04
    STA MaxBombs
    STA InvBombs
```

The one-time-ness comes from somewhere else entirely — the *init*. When the
room is loaded, `InitUnderworldPersonA` (`src/Z_01.asm:1023`) singles out this
one type and removes him if the room's item flag is already set:

```asm
    LDA ObjType+1
    CMP #$4F
    BNE L_PlayCharacterSfx
    BEQ UnderworldPerson_DestroyIfTaken
```

The compare operand at bank 1 CPU `$8A3B` goes from `$4F` to `$00`. Persons are
types `$4B` through `$52`, so `ObjType+1` never equals `$00` here; the `BNE` is
always taken and `UnderworldPerson_DestroyIfTaken` is never reached. Raw form:
`$8A3B:00:4F`.

**Caveat — you still have to leave and re-enter.** Paying runs
`L_Person_FlagItemTakenAndAdvanceState`, which walks the man through his exit
states; `UpdateUnderworldPersonComplexState_DelayAndQuit` clears `ObjType+1`
and he vanishes for that visit. This code only stops him being deleted at load
time on the *next* visit.

**Caveat — `MaxBombs` is a single byte with no ceiling.** `ADC #$04` with no
clamp means enough purchases roll it past `$FF` and back to a small number.
The HUD digit display is also not built for three-digit counts.

**Caveat — no other old man is affected.** Every other person type took the
`BNE` before this code and still does; only the `$4F` branch changes.

**Caveat — bank-unique.** A scan of all eight PRG banks found `$4F` at this
`$8000`-window offset only in bank 1.

**Not live-verified:** derived from reading `InitUnderworldPersonA`,
`UnderworldPerson_DestroyIfTaken` and
`UpdateUnderworldPersonComplexState_SenseLink` (`src/Z_01.asm`), not from
observing it in-game.

## Level 3's old men give Level 1's advice

**Code:** `LZEESXPT`

**Effect:** The old men in Level 3 say the wrong lines — specifically, the
lines that belong to the old men of Levels 1, 2, 5 and 7. Each person type has
an entry in two parallel tables, and this swaps which table Level 3 reads from.

**How it works:** `InitUnderworldPerson_Full` (`src/Z_01.asm:1011`) is a
`TableJump` on `CurLevel`, not on the object:

```asm
InitUnderworldPerson_Full:
    LDA TextboxLineAddrsLo+2
    STA PersonTextPtr
    LDA CurLevel
    JSR TableJump

InitUnderworldPerson_Full_JumpTable:
    .ADDR InitUnderworldPerson_DoNothing   ; level 0
    .ADDR InitUnderworldPersonA            ; levels 1, 2, 5, 7
    ...
    .ADDR InitUnderworldPersonB            ; levels 3, 4, 6, 8
    .ADDR InitUnderworldPersonC            ; level 9
```

Level 3's entry sits at bank 1 `$8A0D` and holds `$69`, the low byte of
`InitUnderworldPersonB` (`$8A69`). Changing it to `$23` points the entry at
`InitUnderworldPersonA` (`$8A23`) — same page, one byte. Raw form:
`$8A0D:23:69`.

The two routines are nearly identical. Both place the person at (`$78`, `$80`),
both subtract `$4B` from the object type to get an index, and both look up a
text selector. The only differences are the table they read —
`UnderworldPersonTextSelectorsA` (`.BYTE $28, $26, $2E, $30, $32, $3E, $3E,
$34`) versus `UnderworldPersonTextSelectorsB` (`.BYTE $2A, $38, $3A, $2C, $40,
$42, $42, $3C`) — and one extra check in A, described below.

**Caveat — Level 3 also inherits the bomb-man check.**
`InitUnderworldPersonA` ends with the `CMP #$4F` test that deletes the
bomb-capacity man if his offer was already taken. If Level 3 has a type-`$4F`
person, he now disappears on a second visit where before he did not.

**Caveat — one byte per level.** The same swap works on `$8A0F` (Level 4),
`$8A13` (Level 6) and `$8A17` (Level 8) to send them to table A, or on `$8A09`
/ `$8A0B` / `$8A11` / `$8A15` with `$69` to send Levels 1, 2, 5 and 7 to
table B. Each is an independent code.

**Caveat — nothing about the room changes.** The person still stands in the
same place, the shutters and item logic are untouched; only the text selector
differs.

**Caveat — bank-unique.** A scan of all eight PRG banks found `$69` at this
`$8000`-window offset only in bank 1.

**Not live-verified:** derived from reading `InitUnderworldPerson_Full`,
`InitUnderworldPersonA` and `InitUnderworldPersonB` (`src/Z_01.asm`), not from
observing it in-game.

## The Level 9 doorman won't open the door

**Code:** `LZOEOZKA`

**Effect:** The old man at the entrance to Level 9 becomes an ordinary dungeon
old man. He no longer counts your Triforce pieces and no longer opens the
shutters, so the eight-piece check that lets you in is simply gone. This is a
lock-yourself-out code — use it as a handicap, not on a run you care about.

**How it works:** Level 9's entry in `InitUnderworldPerson_Full_JumpTable`
(`src/Z_01.asm:1017`) is at bank 1 `$8A19` and holds `$84`, the low byte of
`InitUnderworldPersonC` (`$8A84`). Changing it to `$23` points Level 9 at
`InitUnderworldPersonA` (`$8A23`) instead — same page, one byte. Raw form:
`$8A19:23:84`.

`InitUnderworldPersonC` is the only one of the three that does anything beyond
looking up a line of text:

```asm
    ; Return, if this is not the man at the entrance of Level 9,
    ; or Link has not gotten all the triforce pieces.
    CMP #$4B
    BNE @Exit
    LDA InvTriforce
    CMP #$FF
    BNE @Exit

    ; Otherwise, open the shutters, and destroy this object.
    LDA #$01
    STA ShutterTrigger
```

**Caveat — this is the opposite of the `$8AA5` code.** Patching the
`CMP #$FF` operand in `InitUnderworldPersonC` makes the entrance open with *no*
Triforce pieces; this code removes the routine from the level entirely, so it
never opens.

**Caveat — Level 9's old men also change what they say.**
`InitUnderworldPersonA` reads `UnderworldPersonTextSelectorsA`, not
`UnderworldPersonTextSelectorsC`, so every person in Level 9 draws a line from
the Level 1/2/5/7 set.

**Caveat — `UnderworldPersonTextSelectorsC` is only four bytes long**
(`.BYTE $44, $46, $48, $4A`) while the index it is read with runs `$00` to
`$07`. That is a pre-existing quirk of the original code, not something this
patch introduces, but it is the reason pointing an *early* level at
`InitUnderworldPersonC` is a worse idea than it looks: a person of type `$4F`
or above reads past the table into the routine's own opcodes.

**Caveat — bank-unique.** A scan of all eight PRG banks found `$84` at this
`$8000`-window offset only in bank 1.

**Not live-verified:** derived from reading `InitUnderworldPerson_Full`,
`InitUnderworldPersonA` and `InitUnderworldPersonC` (`src/Z_01.asm`), not from
observing it in-game.

## The first dungeon old man lunges at you

**Code:** `ATKNXGEA` + `AEUAZTAG` — **both are required.**

**Effect:** Person type `$4B` — the first entry in every level's text table, and
the man who stands at the entrance to Level 9 — stops talking and starts
charging. He sits still until Link lines up with him and then rushes across the
room like a spike trap. There is no textbox and no interaction; the other seven
person types are untouched.

**`ATKNXGEA` alone locks the game up.** Entering the old man's room halts Link
permanently: he vanishes and stops responding to the controller, with the music
still playing. `AEUAZTAG` ("Old men don't freeze Link while they talk", the
next entry) is the other half of the code and must be entered alongside it.
See the first caveat for why.

**How it works:** entry `$4B` of `UpdateObject_JumpTable` (`src/Z_07.asm:5321`)
is at `$FC4A` and holds `$80`, the low byte of `UpdateUnderworldPerson`
(`$FE80`). `UpdateTrap` is at `$FE60`, thirty-two bytes away in the same page —
both are bank-7 trampolines into bank 1 (`src/Z_07.asm:5764` and `:5744`), so
the swap is one byte and trivially bank-safe. Raw form: `$FC4A:60:80`.

Entries `$4C` through `$50` and `$52` still point at `$FE80`, and `$51` still
points at `UpdateUnderworldPersonLifeOrMoney` at `$FE88`.

**Caveat — his initialization still runs, and that is what needs the second
code.** `InitObject_JumpTable` is a separate table, so `InitUnderworldPersonA`
(or `B`/`C`, by level) still fires — meaning the Triforce check and the shutter
opening happen exactly as usual, at load time, before he ever starts moving.
But every one of those init routines calls `SetUpCommonCaveObjects`
(`src/Z_01.asm:278`), which **halts Link**:

```asm
    ; Halt Link.
    LDA #$40
    STA ObjState
```

`UpdatePlayer` (`src/Z_07.asm:2079`) returns immediately while
`ObjState & $C0 == $40`, so a halted Link is neither moved nor drawn. The only
thing that ever lifts the halt for an underworld person is the `JSR UnhaltLink`
at the tail of `UpdatePersonState_Textbox` (`src/Z_01.asm:576`, the call at
`:673`), reached when the text runs off its third line — and
`UpdatePersonState_Textbox` is
downstream of `UpdateUnderworldPerson_Full`, which is exactly the routine this
code swaps out. Replacing the person handler with `UpdateTrap` therefore
deletes the only exit from the halt, and Link stays frozen for good. (The
`LDA #$00 / STA ObjState` in `InitUnderworldPersonB` and `InitUnderworldPersonC`
does not save you: it runs only on the paths that *destroy* the person outright
— item already taken, or all eight Triforce pieces in hand.)

`AEUAZTAG` patches the `#$40` operand to `#$00`, so the halt never happens and
the trap-old-man behaves as intended.

**Caveat — he can only lunge right or down.** `UpdateTrap_Full`
(`src/Z_01.asm:2459`) masks its chosen direction with `TrapAllowedDirs-1, X`
(`src/Z_01.asm:2456`, `.BYTE $05, $09, $06, $0A, $01, $02`). A person always
occupies slot 1, so X = 1 selects `$05` — right plus down — and any leftward or
upward lunge is discarded.

**Caveat — he still blocks the way.** `CheckPersonBlocking` is driven by the
type in slot 1, not by the handler or by where the person is standing, so the
invisible wall stays exactly where it was even as he charges around. Pair with
`LGUYIALS` if you want it gone.

**Caveat — he still looks like an old man.** `DrawObjectNotMirrored`
(`src/Z_01.asm:5043`) takes the animation set from `ObjType`, and the trap
handler does draw the object, so he stays visible with the frame numbers the
trap picks.

**Caveat — compare byte.** `$FC4A` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match it.

**Partly live-verified:** the single-code form was played and *fails* — the
Level 1 old man's room locks up, which is the observation that turned up the
missing `UnhaltLink`. The paired form and the lunge behaviour itself are still
derived from reading `UpdateObject_JumpTable` and the bank-7 trampolines
(`src/Z_07.asm`) and `UpdateUnderworldPerson_Full`, `UpdateTrap_Full` and
`SetUpCommonCaveObjects` (`src/Z_01.asm`), not from observing them in-game.

## The "eastmost peninsula" old man lunges at you

**Code:** `ATGNKGEA` + `AEUAZTAG` — **both are required.**

**Effect:** Person type `$4C` — the old man who gives the
"EASTMOST PENNINSULA IS THE SECRET" hint — stops talking and starts charging,
exactly like the `$4B` entry above. `$4C` is `UnderworldPersonTextSelectorsA`
index 1 (`src/Z_01.asm:1030`, `.BYTE $28, $26, $2E, $30, $32, $3E, $3E, $34`
— text selector `$26` decodes, via `PersonTextAddrs` entry 19 into
`PersonText` at `+641`, to `EASTMOST PENNINSULA|    IS THE SECRET,`), so it
lunges wherever that hint is placed by whichever level's `OverworldCaveTypes`
puts a `$4C` person in a cave, and inside any dungeon room that spawns a
`$4C` old man directly.

**How it works:** identical mechanism to the `$4B` code, one table entry
over. Entry `$4C` of `UpdateObject_JumpTable` (`src/Z_07.asm:5321`) is at
`$FC4C` — two bytes past the `$4B` entry at `$FC4A` — and holds `$80`, the
low byte of `UpdateUnderworldPerson` (`$FE80`). Patching it to `$60` points
the entry at `UpdateTrap` (`$FE60`) instead, the same bank-7-to-bank-1
trampoline swap as the `$4B` code. Raw form: `$FC4C:60:80`.

**Caveat — `AEUAZTAG` is mandatory for the same reason as the `$4B` code.**
`InitUnderworldPersonA` (the init routine for person types `$4B`-`$52`,
including `$4C`) still runs and still calls `SetUpCommonCaveObjects`
(`src/Z_01.asm:278`), which halts Link via `LDA #$40 / STA ObjState`. With
only `ATGNKGEA` applied, the only routine that ever lifts that halt —
`UnhaltLink`, called from `UpdatePersonState_Textbox` — is exactly the code
this patch removes, so Link locks up permanently. `AEUAZTAG` patches that
halt's `#$40` operand to `#$00` so it never happens; see "Old men don't
freeze Link while they talk" below for the full mechanism. It is the same
shared routine for every person type, so the existing code needs no changes
to pair with this one.

**Caveat — every other `UnderworldPersonTextSelectorsA` caveat applies
unchanged:** he can only lunge right or down (`TrapAllowedDirs-1, X`), he
still blocks the way (`CheckPersonBlocking` reads slot 1's type, not the
handler), and he still draws as an old man (`DrawObjectNotMirrored` takes the
animation set from `ObjType`).

**Not live-verified:** derived from reading `UpdateObject_JumpTable`
(`src/Z_07.asm`), `UnderworldPersonTextSelectorsA` and `InitUnderworldPersonA`
(`src/Z_01.asm`), and decoding `PersonText`/`PersonTextAddrs` — the same
mechanism already partly verified in-game for the `$4B` code above, not from
observing person type `$4C` directly.

## Old men don't freeze Link while they talk

**Code:** `AEUAZTAG`

Tags: `utility` `play-start`

**Effect:** Link keeps walking, and stays on screen, while a dungeon old man or
a cave dweller delivers his line. Normally the room takes the controller away
until the text has finished printing; with this on, the text prints in the
background and Link is free the whole time. Useful on its own, and *required*
alongside `ATKNXGEA`.

**How it works:** every person init routine — `InitUnderworldPersonA`, `B` and
`C`, `InitUnderworldPersonLifeOrMoney_Full`, `InitGrumble_Full`, and the cave
paths — funnels through `SetUpCommonCaveObjects` (`src/Z_01.asm:278`), which
positions the person, lights the two bonfires, and freezes Link:

```asm
    ; Halt Link.
    LDA #$40
    STA ObjState
```

The `#$40` operand sits at `$86B2`. Zeroing it stores Link's ordinary idle
state instead of the halted state, so `UpdatePlayer` (`src/Z_07.asm:2079`),
which bails out on `ObjState & $C0 == $40`, keeps running him normally. Raw
form: `$86B2:00:40`.

Nothing else depends on the halt: the matching `UnhaltLink` (`src/Z_01.asm:105`)
just stores `#$00` to the same variable, which is what the patched instruction
now stores up front, so the state machine's later `JSR UnhaltLink` is a no-op
rather than a conflict.

**Caveat — it covers caves too.** The same routine sets up overworld cave
persons, so shopkeepers, the hint-givers, the Moblin with the free rupees and
the "It's a secret to everybody" man all stop holding Link still as well. Their
purchase and hint logic runs off `ObjState+1`, which this does not touch, so
the transactions themselves are unaffected — you can just walk out mid-sentence.

**Caveat — you can walk out of a textbox.** Leaving the room while the text is
still printing is now possible. The person object is torn down with the room
like any other, so this is untidy rather than dangerous, but a line you walk
away from is simply never finished.

**Caveat — compare byte.** `$86B2` is in the `$8000`-`$BFFF` window, which is
bank-switched on this MMC1 cart. A scan of all eight PRG banks found `$40` at
this window offset only in bank 1 (the others hold `$FF`, `$01`, `$18`, `$95`,
`$13`, `$00` and `$90`), so the compare byte pins the patch to the intended
instruction.

**Not live-verified:** derived from reading `SetUpCommonCaveObjects` and the
person init routines (`src/Z_01.asm`) and `UpdatePlayer` (`src/Z_07.asm`), not
from observing it in-game.

## Everything in the shops is free

**Code:** `AEVAKAZA`

**Effect:** Walk into any item in any cave shop and it is yours. Nothing is
deducted, and — because the affordability test lives inside the same block that
this code switches off — you can take things you could never have paid for, on
zero rupees.

**How it works:** `UpdateCavePersonState_TalkOrShopOrDoorCharge`
(`src/Z_01.asm:678`) reaches `@PickedUpWare` once Link is standing on one of
the three wares. Whether that costs anything is decided by one bit of
`CaveFlags`:

```asm
@PickedUpWare:
    ; This is a shop, or something is being given away.
    ;
    ; If "pay" cave flag is missing, then go try to take the item.
    LDA CaveFlags
    AND #$02
    BEQ @TryToTake

    ; If rupees < price, then return.
    LDA InvRupees
    CMP CavePrices, X
    BCC Exit

    ; Pass the price to pay for the item.
    LDA CavePrices, X
    JSR PostDebit
```

The mask at bank 1 CPU `$88E4` goes from `$02` to `$00`. `AND #$00` is always
zero, so the `BEQ` is always taken and the whole paying block — price check and
`PostDebit` alike — is jumped over. Raw form: `$88E4:00:02`.

**Caveat — the price is still displayed.** Nothing here touches
`WritePricesToDynamicTransferBuf` or the price list, so the shop still shows
what it thinks it is charging. It just never collects.

**Caveat — hints and the money game are unaffected.** Those take a different
branch much earlier, on the `AND #$30` test at `$88C6`; `@PickedUpWare` is only
reached when neither flag is set. See `AEKEXAAP` below for the hint half.

**Caveat — the heart-container gate still applies.** The White Sword and
Magical Sword caves are checked further down, after `@TryToTake`, against a
different `CaveFlags` bit (`AND #$40`). Free does not mean unconditional.

**Caveat — bank-unique.** A scan of all eight PRG banks found `$02` at this
`$8000`-window offset only in bank 1.

**Not live-verified:** derived from reading
`UpdateCavePersonState_TalkOrShopOrDoorCharge` (`src/Z_01.asm`), not from
observing it in-game.

## The old men's hints are free

**Code:** `AEKEXAAP`

**Effect:** The old men who charge you to talk — the ones who make you pay
before they will say anything useful — stop charging. Step onto the ware, the
hint appears, and your rupees are untouched.

**How it works:** the same routine, one branch earlier. `@PickedUp` sorts the
three paying-cave kinds apart using two `CaveFlags` bits, `$10` for a hint cave
and `$20` for the money game:

```asm
@PickedUp:
    STX CaveChosenIndex
    LDA CaveFlags
    AND #$30                    ; Cave flags: Hint and Money game
    BEQ @PickedUpWare

    ; If have cave flag "money game", then go to state 5 and return.
    AND #$10
    BEQ @MadeWager

    ; Else have "hint" cave flag.
    ;
    ; If rupees < price, then return.
    LDA InvRupees
    CMP CavePrices, X
    BCC Exit

    ; Pass the price to pay for the hint.
    LDA CavePrices, X
    JSR PostDebit
```

The second mask, at bank 1 CPU `$88CA`, goes from `$10` to `$00`. A hint cave
now takes the money-game branch to `@MadeWager`, which does nothing but set
`ObjState+1` to 5 — so the hint still runs, it is simply no longer paid for.
Raw form: `$88CA:00:10`.

**Caveat — the hint text itself is chosen in state 5, not here.**
`UpdateCavePersonState_HintOrMoneyGame` (`src/Z_01.asm:864`) re-tests
`CaveFlags AND #$10` from scratch to decide between the hint and the money
game, and that copy is not patched, so you still get the hint and not a wager.

**Caveat — the "can't afford it" gate goes too.** The `CMP CavePrices, X /
BCC Exit` pair is inside the skipped block, so a hint that used to be
unreachable on low rupees is now available immediately.

**Caveat — independent of `AEVAKAZA`.** Different bytes, different branches;
the two can be used together, and neither covers the other's caves.

**Caveat — bank-unique.** A scan of all eight PRG banks found `$10` at this
`$8000`-window offset only in bank 1.

**Not live-verified:** derived from reading
`UpdateCavePersonState_TalkOrShopOrDoorCharge` (`src/Z_01.asm`), not from
observing it in-game.

## You always win the money game

**Code:** `AESASOAA`

**Effect:** The three-doors gambling game stops being a gamble. Whichever
amount you pick is added to your rupees instead of taken from them, including
the ones displayed with a minus sign. Ten rupees still buys the round, so each
play is a guaranteed profit.

**How it works:** the payout at the end of
`UpdateCavePersonState_HintOrMoneyGame` (`src/Z_01.asm:864`) decides win from
loss by comparing the chosen amount against the only two winning values:

```asm
    ; If the amount chosen = 20 or 50, then add it;
    ; else subtract it.
    LDX CaveChosenIndex
    LDA MoneyGameAmounts, X
    CMP #$14
    BEQ PostCredit
    CMP #$32
    BNE PostDebit

PostCredit:
    CLC
    ADC RupeesToAdd
    STA RupeesToAdd
    RTS
```

`PostCredit` sits at bank 1 `$89D6` and is eight bytes long, so `PostDebit`
begins at `$89DE` and the `BNE` at `$89D4` carries a displacement of `$08`.
Changing that displacement at `$89D5` to `$00` makes the branch land on the
very next instruction — which is `PostCredit`. Both the taken and the not-taken
paths now credit. Raw form: `$89D5:00:08`.

**Caveat — the signs on screen still tell the truth about the round.**
`PrependSignToPrice` (`src/Z_01.asm`) picks "+" or "−" from the same `$14`/`$32`
test, in its own copy of the comparison, which this code does not touch. A
door showing "−40" pays you 40.

**Caveat — `PostDebit` still works everywhere else.** Only the branch
displacement inside the money-game payout changes; the `JSR PostDebit` calls
from the shop and hint paths reach the routine normally.

**Caveat — you still need ten rupees to play.** The entry test is
`LDA InvRupees / CMP #$0A / BCC` at `$8995`, a separate byte.

**Caveat — bank-unique.** A scan of all eight PRG banks found `$08` at this
`$8000`-window offset only in bank 1.

**Not live-verified:** derived from reading
`UpdateCavePersonState_HintOrMoneyGame`, `PostCredit` and `PostDebit`
(`src/Z_01.asm`), not from observing it in-game.

## The White Sword needs twelve heart containers

**Code:** `EUNESAAG`

**Effect:** The opposite of the usual sword codes. The old man in the first
cave, who normally hands over the White Sword at five heart containers, now
holds out for twelve — the Magical Sword's requirement. Since he is also the
sword you are meant to get early, this pushes the whole first half of the game
onto the wooden sword.

**How it works:** the heart-container gate in
`UpdateCavePersonState_TalkOrShopOrDoorCharge` (`src/Z_01.asm:797`) picks one
of two thresholds by cave type:

```asm
    ; Check heart container requirements.
    ;
    ; 5 is the minimum for cave type $6C (white sword)
    ; $C is the minimum otherwise
    LDY #$40
    LDA ObjType+1
    CMP #$6C
    BEQ :+
    LDY #$B0
:
    CPY HeartValues
```

`HeartValues` packs the container count into its high nibble, so `$40` is five
containers and `$B0` is twelve. Raising the White Sword's threshold at bank 1
CPU `$88FD` from `$40` to `$B0` gives both caves the same requirement. Raw
form: `$88FD:B0:40`.

**Caveat — this is the counterpart of `$88FD:00:40`,** the published code that
lowers the same byte to zero and hands the White Sword over at one heart. They
patch the same address and cannot be combined.

**Caveat — the Magical Sword's own threshold is a separate byte** at `$8906`,
already published as `AAEAVPEL` in its zeroed form. Using that alongside this
one inverts the two swords entirely: the Magical Sword becomes the early one.

**Caveat — the gate is `CPY HeartValues / BEQ / BCC`,** a comparison against
the *current* container count, not the maximum ever held. Losing containers to
Ganon's chip damage does not apply here, but the count is read fresh on every
touch of the ware.

**Caveat — bank-unique.** A scan of all eight PRG banks found `$40` at this
`$8000`-window offset only in bank 1.

**Not live-verified:** derived from reading
`UpdateCavePersonState_TalkOrShopOrDoorCharge` (`src/Z_01.asm`), not from
observing it in-game.

## The money cave is full of spike traps

**Code:** `ASVNKSAK`

**Effect:** Walk into a cave expecting a pile of rupees on the floor and find
four spike blocks instead. There is no money in the room at all — the object
that normally scatters ten rupees now scatters traps, at the trap positions,
and they behave like real traps because they are given the real trap type.

**How it works:** this is the *init* table, not the update table.
`InitObject_JumpTable` (bank 7 `$FD82`) has a separate entry per object type,
and entry `$35` — the rupee stash — sits at `$FDEC` holding `$48`, the low byte
of `InitRupeeStash` (`$FE48`). `InitTrap` is at `$FE58`, sixteen bytes away in
the same page; both are bank-7 trampolines into bank 1. Raw form: `$FDEC:58:48`.

Both routines are generators — they use the object they are called on to create
a set of new objects and then hand over:

```asm
InitTrap_Full:
    LDA ObjAttr, X
    STA $01

    ; Assume we're initializing trap object type $49 that makes 6 traps.
    LDY #$05

    ; The individual trap objects to make will be of type $49.
    LDA #$49
    STA $00

    ; If the object type we're initializing is not $49 (as in it's $4A),
    ; then we'll make 4 traps.
    CMP ObjType, X
    BEQ @LoopTrap
    LDY #$03
```

The generator's own type is `$35`, not `$49`, so the `BEQ` fails and `LDY #$03`
runs: **four** traps, placed from `TrapXs` / `TrapYs`
(`.BYTE $20, $20, $D0, $D0, $40, $B0`) — the room's four corners. Each one is
stamped with type `$49`, so it dispatches through the ordinary trap entries and
lunges normally.

**Caveat — this is not the same as `ATONVGAI`.** That code repoints the rupee
stash's *update* handler, so type-`$35` objects still exist and behave like
traps. This one stops them being created at all. Using both is harmless but
redundant: with this code active there is never a type-`$35` object for
`ATONVGAI` to act on.

**Caveat — the room's own bookkeeping is untouched.** `RoomObjCount` and the
cave's secret flag are set by code that never runs now, so treat the cave's
exit and revisit behaviour as unexplored.

**Caveat — ten becomes four.** `InitRupeeStash_Full` loops `LDX #$0A` over
`RupeeStashXs-1, X`; the trap generator loops over a six-entry table and stops
at four. The extra six object slots are simply never filled.

**Caveat — compare byte.** `$FDEC` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match it.

**Not live-verified:** derived from reading `InitObject_JumpTable` and the
bank-7 trampolines (`src/Z_07.asm`) and `InitTrap_Full` and
`InitRupeeStash_Full` (`src/Z_01.asm`), not from observing it in-game.

## Dungeon traps are replaced by rupees

**Codes:** `AGOYKVAS` + `AGOYVVAS`

**Effect:** The exact inverse of `ASVNKSAK`. Every room that would have been
laid out with spike blocks gets ten collectible rupees instead, arranged in the
money cave's layout. The traps never exist, so nothing in the room can lunge at
you; you just walk in and pick up money.

**How it works:** entries `$49` and `$4A` of `InitObject_JumpTable` are the two
trap generator types, at `$FE14` and `$FE16`. Both hold `$58`
(`InitTrap`, `$FE58`); pointing them at `$48` gives `InitRupeeStash`
(`$FE48`), sixteen bytes away in the same page:

| code | raw | entry |
|------|-----|-------|
| `AGOYKVAS` | `$FE14:48:58` | trap generator type 1 → `InitRupeeStash` |
| `AGOYVVAS` | `$FE16:48:58` | trap generator type 2 → `InitRupeeStash` |

```asm
InitRupeeStash_Full:
    LDA ObjAttr, X
    STA $01                     ; [01] holds object attributes
    LDA #$35
    STA $00                     ; [01] holds object type $35 (rupee stash)

    ; Loop over $A rupee stash objects to make
    ; -- each one now representing an individual rupee
    LDX #$0A

@LoopRupee:
    JSR InitOneSimpleObject
    LDA RupeeStashXs-1, X
    STA ObjX, X
    ...
```

It writes type `$35` into every object it creates regardless of what the parent
was, so the results are genuine rupee stashes that run
`UpdateRupeeStash_Full` and add a rupee each when Link touches them.

**Caveat — use both codes or neither.** A room laid out with the generator
type you did not patch still has ordinary traps in it.

**Caveat — the coordinates come from the money cave, not the room.**
`RupeeStashXs` / `RupeeStashYs` are fixed tables sized for a cave's rupee
layout. In a dungeon room the ten rupees land wherever those tables say, which
may well be inside walls or on top of doorways.

**Caveat — ten rupees, then the room thinks it is done.**
`UpdateRupeeStash_Full` (`src/Z_01.asm:2608`) zeroes `RoomObjCount` after the
first pickup, on the assumption that taking one rupee counts as taking them
all. Whether the rest stay collectible after that is unexplored.

**Caveat — compare bytes.** `$FE14` and `$FE16` are in the `$C000`-`$FFFF`
window, which always maps bank 7 on this cart, so no other bank can match them.

**Not live-verified:** derived from reading `InitObject_JumpTable` and the
bank-7 trampolines (`src/Z_07.asm`) and `InitRupeeStash_Full` and
`InitTrap_Full` (`src/Z_01.asm`), not from observing it in-game.

## The "life or money" old man never leaves

**Code:** `ATXYKTAN`

**Effect:** The old man who makes you choose between a heart container and 50
rupees stops being a one-time toll. Pay him, leave the room, come back, and he
is there again with the same two items on the floor — and touching one charges
you again. He also greets you with an ordinary old man's line instead of his
own.

**How it works:** the one-time-ness is not in the payment code. `Init`, not
`Update`, is what removes him — `InitUnderworldPersonLifeOrMoney_Full`
(`src/Z_01.asm:1056`) falls straight through into
`UnderworldPerson_DestroyIfTaken`:

```asm
InitUnderworldPersonLifeOrMoney_Full:
    LDA #$78
    LDY #$80
    JSR SetUpCommonCaveObjects

    ; Set text selector for "life or money".
    LDA #$36
    STA PersonTextSelector

    LDA TextboxLineAddrsLo+2
    STA PersonTextPtr

UnderworldPerson_DestroyIfTaken:
    JSR GetRoomFlagUWItemState
    BEQ L_PlayCharacterSfx
    LDA #$00
    STA ObjState
    JMP DestroyMonster
```

Entry `$51` of `InitObject_JumpTable` sits at bank 7 `$FE24` and holds `$70`,
the low byte of `InitUnderworldPersonLifeOrMoney` (`$FE70`). Changing it to
`$68` points it at `InitUnderworldPerson` (`$FE68`) — eight bytes away, same
page. Raw form: `$FE24:68:70`.

`InitUnderworldPerson_Full` never reaches `UnderworldPerson_DestroyIfTaken` for
type `$51`: the A path only tests it for the bomb-capacity man (`CMP #$4F`),
the B path has no such test at all, and the C path exits on `CMP #$4B`. So the
room flag stops mattering and he loads every visit.

**Caveat — the payment is genuinely repeatable, and it costs you.**
`UpdateUnderworldPersonLifeOrMoneyState_2` (`src/Z_01.asm:1391`) checks only
Link's position against `LifeOrMoneyItemXs` and a six-pixel vertical window
before charging; there is no room-flag test anywhere in it. This is a code that
makes the game harder, not easier.

**Caveat — his update handler is unchanged.** Entry `$51` of
`UpdateObject_JumpTable` still points at `UpdateUnderworldPersonLifeOrMoney`,
so the two items are still drawn and the "−1  −50" price line still appears —
that comes from `UpdateUnderworldPersonLifeOrMoneyState_0`'s own transfer-buf
selector (`LDA #$76`), which is a different mechanism from `PersonTextSelector`.

**Caveat — the greeting depends on the level.** `InitUnderworldPersonA` and
`InitUnderworldPersonB` index their text tables with `type − $4B` = 6, giving
`$3E` and `$42` respectively. If a level 9 room ever held this type, the C path
would index `UnderworldPersonTextSelectorsC`, which is only four bytes long,
and read past it into the routine's own opcodes — a garbage selector, not a
crash.

**Caveat — compare byte.** `$FE24` is in the `$C000`-`$FFFF` window, which
always maps bank 7 on this cart, so no other bank can match it.

**Not live-verified:** derived from reading `InitObject_JumpTable`
(`src/Z_07.asm`) and `InitUnderworldPersonLifeOrMoney_Full`,
`UnderworldPerson_DestroyIfTaken` and
`UpdateUnderworldPersonLifeOrMoneyState_2` (`src/Z_01.asm`), not from observing
it in-game.

## Walled-up doorways lead to the next room

**Codes:** `ZXXVATYP` + `PLXPYZIU`

**Effect:** The dungeon doorway positions that have been bricked up become real
doors. Link walks into what is drawn as solid wall and comes out in the room
next door. `PLXPYZIU` is what lets him move into the wall; `ZXXVATYP` is what
makes the game work out where he ends up.

**How it works:** door type 1 is "wall" — a doorway position that the level
layout filled in. It is handled twice, in two different tables, and both have
to be redirected.

`TouchDoor_JumpTable` (bank 5 `$9225`) decides whether Link is blocked.
`PLXPYZIU` (`$9227:39:35`) repoints its entry 1 from `TouchDoorWall` to
`TouchDoorOpen`, and is documented in full under "Bombable walls open without
bombs" above.

`CalculateNextRoom_JumpTable` (bank 7 `$E6A6`) decides where he goes. It is
indexed by the same door type, and entry 1 is the only wall type that does not
compute a destination:

```asm
CalculateNextRoom_JumpTable:
    .ADDR CalculateNextRoomForDoor      ; 0 open
    .ADDR CalculateNoNextRoom           ; 1 wall
    .ADDR CalculateNextRoomForDoor      ; 2 false wall
    .ADDR CalculateNextRoomForDoor      ; 3 false wall 2
    .ADDR CalculateNextRoomForDoor      ; 4 bombable
    .ADDR CalculateNextRoomForDoor      ; 5 key
    .ADDR CalculateNextRoomForDoor      ; 6 key 2
    .ADDR CalculateNextRoomForDoor      ; 7 shutter
    .ADDR CalculateNoNextRoom           ; 8 invalid direction
```

(The type-to-meaning list is spelled out in `src/Z_05.asm:4811`.)
`CalculateNoNextRoom` writes zero to `[E7]` and returns without touching
`NextRoomId`:

```asm
CalculateNoNextRoom:
    LDA #$00
    STA $E7
    RTS
```

`ZXXVATYP` changes the low byte of entry 1 at `$E6A8` from `$17`
(`CalculateNoNextRoom`, `$B517`) to `$22` (`CalculateNextRoomForDoor`,
`$B522`) — same page, one byte. Raw form: `$E6A8:22:17`.

**Caveat — `ZXXVATYP` on its own does nothing you can see.** `TouchDoor` still
blocks Link at a type-1 wall, so the entry is never reached. It is only useful
alongside `PLXPYZIU`.

**Caveat — without `ZXXVATYP` you arrive back where you started.**
`NextRoomId` retains whatever the previous transition put there, which is the
ID of the room Link is currently standing in, so `PLXPYZIU` alone scrolls him
into a second copy of the same room.

**Caveat — doorway positions only.** `TouchDoor` runs only after
`CheckDoorway` has confirmed Link is inside a doorway's bounds, so this is not
a walk-through-anything code; a room with no doorway on that side is still
sealed.

**Caveat — the wall is still drawn.** Nothing writes tiles or sets
`CurOpenedDoors`, so the bricked-up doorway looks exactly the same before and
after Link walks through it.

**Caveat — compare bytes.** `$E6A8` is in the `$C000`-`$FFFF` window, which
always maps bank 7, so nothing else can match it. `$9227` is in the switchable
window and holds `$35` at that offset in bank 5 only.

**Not live-verified:** derived from reading `CalculateNextRoom`,
`CalculateNoNextRoom`, `CalculateNextRoomForDoor`, `CheckDoorway` and
`TouchDoor` (`src/Z_05.asm`) and `CalculateNextRoom_JumpTable`
(`src/Z_07.asm`), not from observing it in-game.

## Going south puts you back in the same room

**Code:** `AAOLGIAP`

**Effect:** Every southward transition — a dungeon door, or walking off the
bottom edge of an overworld screen — scrolls normally and then delivers Link
into the room he just left. You can still travel north, east and west; south
is a treadmill.

**How it works:** `NextRoomIdOffsets` (`src/Z_05.asm:7474`) is the four-byte
table that turns a direction into a room-ID delta:

```asm
NextRoomIdOffsets:
    .BYTE $F0, $10, $FF, $01
...
    LDA NextRoomIdOffsets, X    ; Look up offset used to calculate next room ID from current one.
    CLC
    ADC RoomId
    STA NextRoomId
```

Room IDs are laid out sixteen to a row, so `$F0` is north, `$10` south, `$FF`
west and `$01` east. Per the mapping comment above `CalculateNextRoomForDoor`
("1:3, 2:2, 4:1, 8:0"), byte 1 is direction bit `4` — south. Setting it to
`$00` at bank 5 CPU `$B514` makes `NextRoomId` equal `RoomId`. Raw form:
`$B514:00:10`.

**Caveat — this is the room-transition table, not the door-flagging table.**
`DoorNextRoomIdOffsets` holds the same four values in a different order and is
read only by `UpdateDoors`, to mark the opposite door in the next room as open.
It is untouched, so shutter bookkeeping still points at the room to the south
that Link never reaches.

**Caveat — overworld and dungeon alike.** Both `CalculateNextRoomForDoor` and
`CalcNextRoomByDir` (`src/Z_05.asm:7541`) read this table, and the second is
what handles walking off a screen edge, so the effect is not confined to
dungeons.

**Caveat — it does not lock you in.** The transition completes normally; the
room simply reloads. North still works, so nothing here is a dead end on its
own.

**Caveat — bank-unique.** A scan of all eight PRG banks found `$10` at this
`$8000`-window offset only in bank 5.

**Not live-verified:** derived from reading `NextRoomIdOffsets`,
`CalculateNextRoomForDoor` and `CalcNextRoomByDir` (`src/Z_05.asm`), not from
observing it in-game.

## Going east takes you west

**Code:** `NYOLTIPE`

**Effect:** Walking east — through a dungeon door or off the right-hand edge of
an overworld screen — moves Link one room *west* instead. Combined with the
normal westward transition, the two directions become a two-room shuttle: go
east and you land where going west would have taken you, and going west from
there brings you back.

**How it works:** the same `NextRoomIdOffsets` table, byte 3. The mapping
comment above `CalculateNextRoomForDoor` gives "1:3", so direction bit `1`
(east) reads index 3, which holds `$01`. Changing it to `$FF` at bank 5 CPU
`$B516` makes the eastward delta identical to the westward one. Raw form:
`$B516:FF:01`.

**Caveat — the screen still scrolls the way you walked.** Only the destination
room ID changes; mode 7 draws the transition in the direction of travel, so the
scroll goes right while the map goes left.

**Caveat — row edges wrap.** `NextRoomId` is a plain 8-bit add with no column
check, so leaving the west edge of a row lands in the previous row's east end —
already true of the original westward offset, and now true of eastward travel
too.

**Caveat — the same shared-table notes apply** as for `AAOLGIAP` above:
`DoorNextRoomIdOffsets` is a separate table and is not patched, and
`CalcNextRoomByDir` means overworld screen edges are affected as well as
dungeon doors.

**Caveat — bank-unique.** A scan of all eight PRG banks found `$01` at this
`$8000`-window offset only in bank 5.

**Not live-verified:** derived from reading `NextRoomIdOffsets`,
`CalculateNextRoomForDoor` and `CalcNextRoomByDir` (`src/Z_05.asm`), not from
observing it in-game.

## Dying skips the death sequence and ends the dungeon instead

**Code:** `VASVKLVE`

**Effect:** When Link runs out of hearts there is no spinning-death animation
and no "GAME OVER" screen. Instead the game plays the *end-of-dungeon*
sequence: the screen flashes, the hearts refill, the curtain closes, and Link
is put back on the overworld outside the dungeon he just died in — alive, with
a full life bar.

**How it works:** `UpdateMode` (`src/Z_07.asm:1649`) selects a bank and then
dispatches on `GameMode` through `UpdateMode_JumpTable` (bank 7 `$EB3A`), a
20-entry `.ADDR` table:

```
UpdateMode_JumpTable:
    ...
    .ADDR UpdateMode10Stairs     ; entry $10, $EB7E
    .ADDR UpdateMode11Death      ; entry $11, $EB86  <- patched
    .ADDR UpdateMode12EndLevel   ; entry $12, $EB8E
    .ADDR UpdateMode13WinGame
```

Entry `$11` (death) and entry `$12` (end of level) both live on page `$EB`, so
one byte moves death onto the end-of-level handler. This patches the low byte
of entry `$11` at CPU `$EB5C` from `$86` to `$8E`. Raw form: `$EB5C:8E:86`.

The two targets are three-instruction trampolines with identical shapes —
`LDA #$05 / JSR SwitchBank / JMP UpdateMode11Death_Full` and the same for
`UpdateMode12EndLevel_Full` (`src/Z_07.asm:1700` and `:1705`) — so the
caller's contract (bank 5 mapped in on entry) is satisfied either way.

Mode `$11`'s *init* is untouched: `InitMode11` (`src/Z_05.asm:2039`) still runs
its two submodes, and `InitMode11_Sub1` ends with `STA GameSubmode` (zero) and
`INC IsUpdatingMode`. So the redirected update starts at submode 0, which is a
valid index into `UpdateMode12EndLevel_Full_JumpTable` (5 entries) —
submode 0 sets `ObjTimer`, submode 1 flashes and sets `World_IsFillingHearts`,
submode 2 refills the life bar, submode 3 runs the curtain, and submode 4
falls into `EndGameMode12` (`src/Z_05.asm:7519`), which sets `CurLevel` to 0,
`GameMode` to `$02` and `UndergroundExitType` to 2 — the overworld reload that
puts Link outside a dungeon entrance.

**Caveat — `InitMode12` never runs, so the sequence is visually broken.** The
death mode's init sets up death, not the end-of-level presentation. That leaves
`ObjX+12`/`ObjX+13` (the curtain's two column counters), `ItemTypeToLift` and
the "End Level" `SongRequest` at whatever the room left behind. Expect no
fanfare, a garbled curtain, and `DrawLinkLiftingItem` drawing a stale item
above Link's head every frame. Submode 3 still terminates — the curtain
routine drives `ObjX+12` down each frame until it drops below `$11` — but how
long that takes depends on what object slot 12's X coordinate happened to be.

**Caveat — you can never save again.** The Continue/Save/Retry menu (mode `$08`)
is reached only from the end of the death sequence, and mode `$0D` (save and
quit) is reached only from that menu. With death rerouted, neither is
reachable in normal play.

**Caveat — dying on the overworld does this too.** `CurLevel` is already 0
there, so `EndGameMode12` reloads the overworld with `UndergroundExitType` 2
and Link steps out as if leaving a dungeon.

**Caveat — the death count stops rising.** `DeathCounts` is incremented in
`UpdateMode11Death_SubC`, which this code never reaches.

**Caveat — fixed bank.** `$EB5C` is in the `$C000`-`$FFFF` window, which on
this ROM is always bank 7, so the compare byte cannot match a different bank's
data.

**Not live-verified:** derived from reading `UpdateMode_JumpTable` and the mode
trampolines (`src/Z_07.asm`), `InitMode11`/`InitMode11_Sub1`,
`UpdateMode12EndLevel_Full` and `EndGameMode12` (`src/Z_05.asm`), not from
observing it in-game.

## "GAME OVER" revives you and throws you out of the dungeon

**Code:** `ZPVEUSAA`

**Effect:** The whole death sequence plays normally — Link spins, the screen
fades, the spark flashes, "GAME OVER" appears — and then, instead of the
Continue/Save/Retry menu, the end-of-dungeon sequence takes over: the
"End Level" song plays, the hearts refill, Link holds up a Triforce piece, and
he is put back on the overworld outside the dungeon, alive.

**How it works:** `UpdateMode11Death_SubC` (`src/Z_05.asm:2704`, bank 5
`$8D63`) is the last submode of the death sequence. Once the "GAME OVER" delay
expires it hands off to the next game mode:

```
UpdateMode11Death_SubC:
    LDA ObjTimer+11
    BNE :+
    JSR EndGameMode
    LDA #$08                    ; Go to the Continue Question mode.
    STA GameMode
```

This patches the `LDA #$08` operand at bank 5 CPU `$8D6B` from `$08` to `$12`.
Raw form: `$8D6B:12:08`. Mode `$12` is `EndLevel` — the sequence that normally
runs when a dungeon's Triforce piece is taken.

Unlike `VASVKLVE` above, this hand-off is clean: `JSR EndGameMode` has just
zeroed `GameSubmode` and `IsUpdatingMode` on the line before, so mode `$12`
starts from the top. `InitMode12` (`src/Z_05.asm:5529`) therefore does run —
it requests the "End Level" song, seeds the curtain columns `ObjX+12`/`ObjX+13`,
sets `ObjTimer`, blanks the tile map and sets `ItemTypeToLift` to `$1B` (the
Triforce) — and `UpdateMode12EndLevel_Full` then plays the flash, the heart
refill and the curtain before `EndGameMode12` drops Link on the overworld with
`CurLevel` 0 and `UndergroundExitType` 2.

No other PRG bank holds `$08` at that same `$8000`-window offset (gg.py
checked all 8 banks), so this is bank-unique.

**Caveat — you can never save again,** for the same reason as `VASVKLVE`: the
Continue/Save/Retry menu is the only route to the save-and-quit mode.

**Caveat — the Game Over music still fires.** The two instructions after the
patched store still request tune `$40` (Game Over), and `InitMode12` then
requests song `$04` (End Level) on the next frame, so the two overlap.

**Caveat — the death count still rises.** `INC DeathCounts, X` sits below the
patched store and is unaffected.

**Caveat — dying on the overworld does this too,** with `CurLevel` already 0,
so the overworld simply reloads with Link stepping out of a dungeon entrance.

**Not live-verified:** derived from reading `UpdateMode11Death_SubC`,
`InitMode12`, `UpdateMode12EndLevel_Full` and `EndGameMode12`
(`src/Z_05.asm`), not from observing it in-game.

## Finishing any dungeon rolls the ending

**Code:** `LPKUYIZA`

**Effect:** Taking the Triforce piece at the end of *any* dungeon runs the
end-of-level sequence as usual — flash, heart refill, curtain — and then, in
place of the return trip to the overworld, the game goes straight into its
win sequence.

**How it works:** `EndGameMode12` (`src/Z_05.asm:7519`, bank 5 `$B547`) is what
the last submode of the end-of-level sequence falls into:

```
EndGameMode12:
    JSR EndGameMode
    STA $E7
    STA CurLevel                ; Set OW (level 0).
    LDA #$02
    STA GameMode
    STA UndergroundExitType     ; Set to type 2: dungeon level.
```

`GameMode` `$02` is the level loader, which combined with `CurLevel` 0 is how
the game returns you to the overworld. This patches the `LDA #$02` operand at
bank 5 CPU `$B54F` from `$02` to `$13`. Raw form: `$B54F:13:02`. Mode `$13` is
the last entry in both mode tables — `InitMode13` (`src/Z_07.asm:1388`) and
`UpdateMode13WinGame` — the sequence that normally plays after Ganon.

No other PRG bank holds `$02` at that same `$8000`-window offset (gg.py
checked all 8 banks), so this is bank-unique.

**Caveat — `UndergroundExitType` gets `$13` too.** The same `A` is stored to
both variables, so it also becomes `$13` instead of 2. That value is only ever
read by `UpdateMode3Unfurl` and `UpdateMode4and6EnterLeave` (`src/Z_07.asm`),
neither of which the win sequence passes through, so it should not matter —
but it is a second, unintended write.

**Caveat — Zelda's sprite comes from object slot 1.** `InitMode13_Sub0`
(`src/Z_02.asm:3214`) draws her with `LDX #$01 / JMP Person_Draw`. Reaching the
ending from Ganon's room means slot 1 really holds Zelda; reaching it from an
ordinary dungeon means it holds whatever was left there, so expect a wrong
sprite or none at all.

**Caveat — the ending's opening curtain is already open.** `InitMode13_Sub0`
advances once `ObjX+12` falls below `$11`, and mode `$12`'s curtain has just
driven it there, so that step passes immediately instead of animating.

**Caveat — this is a shortcut, not a completed game.** Nothing about the save
file changes: the Triforce pieces you have not collected are still missing, so
whatever the ending displays about your quest reflects the real save state.

**Not live-verified:** derived from reading `EndGameMode12`,
`UpdateMode12EndLevel_Full` (`src/Z_05.asm`), the mode jump tables
(`src/Z_07.asm`) and `InitMode13_Full` (`src/Z_02.asm`), not from observing it
in-game.

## Every cave is laid out like a secret shortcut passage

**Code:** `NPUVOPEA`

Tags: `play-start`

**Effect:** Walking into any ordinary overworld cave — shop, hint room, old
man's chamber, heart-container cave — gets you the bare rock passage that the
overworld's secret shortcut caves use, instead of the usual cave interior. The
occupant and the wares still appear; they are just standing in the wrong room.

**How it works:** `InitMode_JumpTable` (bank 7 `$E923`, `src/Z_07.asm:1279`) is
the 20-entry `.ADDR` table `InitMode` dispatches through on `GameMode`. Entries
`$0B` and `$0C` are the two ways into an overworld subroom:

```
    .ADDR InitModeB              ; entry $0B, $9080  <- patched
    .ADDR InitModeC              ; entry $0C, $9097
```

`HandleWarpOW` (`src/Z_05.asm:7345`) is what picks between them: it reads the
room's cave-index attribute and uses mode `$0B` for a regular cave, bumping it
to `$0C` only when the index is `$14`, the shortcut caves. Both targets are on
page `$90`, so one byte sends regular caves down the shortcut path. This
patches the low byte of entry `$0B` at CPU `$E939` from `$80` to `$97`. Raw
form: `$E939:97:80`.

`InitModeB` and `InitModeC` (`src/Z_05.asm:3507` and `:3522`) are jump tables
of nine submodes that are **identical except for submode 3**:

```
InitModeB_JumpTable: ... .ADDR LayoutCaveAndAvanceSubmode      ...
InitModeC_JumpTable: ... .ADDR LayoutShortcutAndAdvanceSubmode ...
```

and those two differ only in an index (`src/Z_05.asm:6041`):

```
LayoutCaveAndAvanceSubmode:
    LDX #$00                    ; Usual cave
LayoutShortcutAndAdvanceSubmode:
    LDX #$02                    ; Offset of address of column directory of shortcut cave
```

`X` selects between `RoomLayoutOWCave0` and `RoomLayoutOWCave1` in
`SubroomLayoutAddrs` (`src/Z_05.asm:6035`) before `LayoutRoomOrCaveOW` draws
the room. Everything else about entering the cave — including submode 7,
`InitModeB_EnterCave_Bank5`, which spawns the person and the items — is shared
by both tables.

**Caveat — `GameMode` is still `$0B`.** Only the init routine changes.
`UpdateMode_JumpTable` maps modes `$09`-`$0C` all to `UpdateMode5Play`, so the
running game is unaffected and nothing is mismatched.

**Caveat — the exit still works.** Leaving a cave is driven by
`UndergroundExitType`, which is set to 1 when Link walks in
(`src/Z_01.asm:3023`), not by the room's tiles.

**Caveat — real shortcut caves are unchanged.** They enter through mode `$0C`,
whose table entry is not patched.

**Caveat — fixed bank.** `$E939` is in the `$C000`-`$FFFF` window, which on
this ROM is always bank 7, so the compare byte cannot match a different bank's
data.

**Not live-verified:** derived from reading `InitMode_JumpTable`
(`src/Z_07.asm`), `InitModeB`/`InitModeC`, `LayoutCaveAndAvanceSubmode`,
`LayoutShortcutAndAdvanceSubmode`, `SubroomLayoutAddrs` and `HandleWarpOW`
(`src/Z_05.asm`), not from observing it in-game.

## Link cannot die — an empty life bar just restarts the room

**Code:** `IAXUZGPP`

**Effect:** Running out of hearts no longer starts the death sequence. Link's
life bar empties and stays empty, and instead of dying he keeps playing in the
same room. Every further hit re-runs the same "you died" path, so the empty
life bar is permanent until a fairy, a heart drop or a potion refills it.

**How it works:** `Link_BeHarmed` (`src/Z_01.asm:5742`) subtracts damage and,
when it can no longer borrow from the filled hearts, falls into `@HandleDied`:

```
@HandleDied:
    ; Link died.
    LDA HeartValues
    AND #$F0
    STA HeartValues
    JSR EndGameMode
    STA HeartPartial
    STA ObjState
    LDA #$11
    STA GameMode
```

This is the only place in the ROM that sets `GameMode` to `$11`. Patching the
`LDA #$11` operand to `$05` sends Link into the ordinary play mode instead of
the death mode. The hand-off is clean: `JSR EndGameMode` on the line above has
already zeroed `GameSubmode` and `IsUpdatingMode`, so mode `$05` starts from
its own init.

**The address needs the relocation rule.** `Link_BeHarmed` lives in segment
`BANK_01_CODE`, which `src/Z.cfg` declares as `load = ROM_01, run =
RAM_01_CODE` — the block `CopyCommonCodeToRam` (`src/Z_01.asm:1569`) copies
into Save RAM at load time. `bin/Z.map` gives `__BANK_01_CODE_LOAD__ = $A500`
and `__BANK_01_CODE_RUN__ = $6C90`, so the disassembly's addresses are *run*
addresses: `@HandleDied` is listed at `$7BA9` and the `LDA #$11` operand at
`$7BBA`. A code aimed there would do nothing — `$7BBA` is Save RAM, not
cartridge. The load address is `$A500 + ($7BBA - $6C90)` = `$B42A`, which is
what the copy loop reads through the cartridge bus. Raw form: `$B42A:05:11`.

Bank 1 at `$B419` reads `AD 6F 06 29 F0 8D 6F 06 20 A3 EB 8D 70 06 85 AC A9 11
85 12 A9 04`, matching the source instruction for instruction, with the `11`
at `$B42A`. No other PRG bank holds `$11` at that same `$8000`-window offset
(gg.py checked all 8 banks), so this is bank-unique.

**Caveat — the room repopulates every time you would have died.**
`InitMode5Play` (`src/Z_07.asm:1499`) is not a no-op: it falls through to
`RunCrossRoomTasksAndBeginUpdateMode`, which calls `CreateRoomObjects` — the
same routine that populates a room when you walk into it. So each would-be
death re-creates the room's monsters around you.

**Caveat — expect a visible hitch.** The same init re-cues a palette transfer
buffer and calls `DrawSpritesBetweenRooms`, and `@HandleDied` sets `ObjDir` to
down, so Link snaps to facing down and the screen blinks on each save.

**Caveat — other ways to die are untouched.** This patches the heart-depletion
path only. Nothing else in the ROM writes `$11` to `GameMode` as shipped —
but `POKPIPLA` below adds one, and the two combine into "only a Wallmaster can
kill you".

**Not live-verified:** derived from reading `Link_BeHarmed` (`src/Z_01.asm`),
`InitMode5Play` (`src/Z_07.asm`), the segment definitions in `src/Z.cfg` and
the load/run addresses in `bin/Z.map`, not from observing it in-game.

## A Wallmaster's grab is fatal

**Code:** `POKPIPLA`

**Effect:** When a Wallmaster grabs Link and carries him off, it no longer
drops him at the dungeon's entrance room — it kills him. The death sequence
plays out from a full life bar.

**How it works:** `UpdateWallmaster` (`src/Z_04.asm:4128`) checks, at the end
of each trip across the room, whether Link was captured:

```
    ; At the end of a trip where Link was captured:
    ; 1. hide the special sprites used by Wallmaster
    ; 2. go to mode 3 "unfurl" to go the level's entrance
    ; 3. reset Link's state, so he's idle
    JSR HideSpritesOverLink
    LDA #$03
    STA GameMode
    LDA #$00
    STA ObjState
    STA IsUpdatingMode
    STA GameSubmode
```

Mode `$03` is the curtain-unfurl that redraws the level at its entrance. This
patches the `LDA #$03` operand at bank 4 CPU `$91C5` to `$11`, the death mode.
Raw form: `$91C5:11:03`. The three stores immediately after the patched one
zero `ObjState`, `IsUpdatingMode` and `GameSubmode`, so mode `$11` starts from
`InitMode11` (`src/Z_05.asm:2039`) with a clean submode — the same entry
conditions it gets on a normal death.

No other PRG bank holds `$03` at that same `$8000`-window offset (gg.py checked
all 8 banks), so this is bank-unique.

**Caveat — you die at full health.** Nothing here touches `HeartValues`;
`InitMode11` does not look at Link's hearts, it just runs the sequence. The
life bar is still full behind the fade.

**Caveat — the capture animation still plays in full.** The patched store runs
only after `Wallmaster_ObjTilesCrossed` reaches 7, so the Wallmaster still
drags Link the whole way across the room first.

**Caveat — combines with `IAXUZGPP`.** With Link's heart-depletion death
rerouted into normal play, this becomes the only route to the death mode left
in the ROM.

**Not live-verified:** derived from reading `UpdateWallmaster`
(`src/Z_04.asm`) and `InitMode11` (`src/Z_05.asm`), not from observing it
in-game.

## Taking a Triforce piece opens the save menu instead

**Code:** `AEUZNGZO`

**Effect:** Picking up a dungeon's Triforce piece no longer plays the
end-of-level fanfare and no longer sends Link back to the overworld. The
Continue/Save/Retry menu comes up instead — a save point at the end of every
dungeon, with the Triforce piece already recorded.

**How it works:** `TakeClass0Complex` (`src/Z_01.asm:4604`) handles the
complex underworld items. After OR-ing the level's bit into the item slot it
checks whether the slot taken was `$1A`, the per-level Triforce-pieces slot:

```
    ; If the item taken was a triforce piece, then go to mode $12.
    CPY #$1A
    BNE @Exit
    JSR EndGameMode
    LDA #$12
    STA GameMode
```

Mode `$12` is the end-of-level sequence. This patches the `LDA #$12` operand to
`$08`, the Continue Question mode. As with `IAXUZGPP`, `JSR EndGameMode` on the
line above has just zeroed `GameSubmode` and `IsUpdatingMode`, so `InitMode8`
(`src/Z_05.asm:1369`) runs properly — video off, palettes patched, room
history cleared, mode-8 text cued — and the menu is drawn correctly rather
than over a half-torn play screen.

**This address needs the relocation rule too.** `TakeClass0Complex` is in the
`BANK_01_CODE` segment that runs from Save RAM (see `IAXUZGPP` above for the
`src/Z.cfg` / `bin/Z.map` derivation). The operand's run address is `$7447`;
the cartridge address a Game Genie code has to name is
`$A500 + ($7447 - $6C90)` = `$ACB7`. Raw form: `$ACB7:08:12`. Bank 1 at
`$ACAF` reads `C0 1A D0 07 20 A3 EB A9 12 85 12 60`, matching the source, with
the `12` operand at `$ACB7`. No other PRG bank holds `$12` at that same
`$8000`-window offset (gg.py checked all 8 banks), so this is bank-unique.

**Caveat — the piece is still credited.** `LDA Items, Y / ORA LevelMasks, X /
STA Items, Y` runs before the patched instruction, so the Triforce piece is
recorded whichever mode follows.

**Caveat — "Continue" knocks you back to three hearts.**
`UpdateMode8ContinueQuestion_Full` (`src/Z_05.asm:2199`) forces `HeartValues`
through `AND #$F0 / ORA #$02` on every selection, so resuming from this menu
costs you all but three filled hearts. It also means the heart refill that mode
`$12` would have given you never happens.

**Caveat — you stay in the dungeon.** Choosing "Continue" goes to mode `$03`,
the unfurl at the level entrance, instead of the trip back to the overworld —
so you have to walk out.

**Caveat — Ganon's Triforce of Power is unaffected.** That is item slot `$1B`,
handled earlier in the same routine by `L_TakePowerTriforce`, which never
reaches the patched instruction.

**Not live-verified:** derived from reading `TakeClass0Complex`
(`src/Z_01.asm`), `InitMode8` and `UpdateMode8ContinueQuestion_Full`
(`src/Z_05.asm`), the segment definitions in `src/Z.cfg` and the load/run
addresses in `bin/Z.map`, not from observing it in-game.

## The death sequence ends at the fade — no spark, no "GAME OVER"

**Code:** `LVOAKGPA`

**Effect:** Dying still plays Link's four turns and the screen fade, but that
is where it stops: no grey Link, no flashing spark, no "GAME OVER" text. The
Continue/Save/Retry menu comes up as soon as the fade finishes.

**How it works:** `UpdateMode11Death_Full` (`src/Z_05.asm:2523`) dispatches on
`GameSubmode` through a 13-entry table at bank 5 `$8C82`:

```
UpdateMode11Death_Full_JumpTable:
    ...
    .ADDR UpdateMode11Death_Sub8_AnimateFade   ; entry 8,  $8CFB
    .ADDR UpdateMode11Death_Sub9               ; entry 9,  $8D01  <- patched
    .ADDR UpdateMode11Death_SubA               ; entry $A, $8D0D
    .ADDR UpdateMode11Death_SubB               ; entry $B, $8D56
    .ADDR UpdateMode11Death_SubC               ; entry $C, $8D63
```

Submode 9 cues the grey "dead Link" palette row and arms the spark timer;
submodes `$A` and `$B` draw the spark and cue the "GAME OVER" text; submode
`$C` hands off to the Continue Question mode. Entries 9 through `$C` all live
on page `$8D`, so one byte skips straight to the end. This patches the low
byte of entry 9 at CPU `$8C94` from `$01` to `$63`. Raw form: `$8C94:63:01`.

`UpdateMode11Death_SubC` (`src/Z_05.asm:2704`) waits for `ObjTimer+11` and then
runs `JSR EndGameMode / LDA #$08 / STA GameMode`. `ObjTimer+11` is left at most
5 frames by submode 7's turn timer, so the hand-off happens almost at once.

No other PRG bank holds `$01` at that same `$8000`-window offset (gg.py checked
all 8 banks), so this is bank-unique.

**Caveat — the death count still rises.** `INC DeathCounts, X` is part of
submode `$C`, which this code jumps straight into.

**Caveat — the "heart taken" tune never plays.** It is requested by submode
`$A` at the end of the spark, which is skipped; the Game Over music requested
by submode `$C` still plays.

**Caveat — submodes 9 through `$B` become unreachable,** so the grey palette
row (`TileBufSelector` `$2C`) is never cued and Link's sprite keeps its normal
colours through the fade.

**Not live-verified:** derived from reading `UpdateMode11Death_Full_JumpTable`
and submodes 7 through `$C` (`src/Z_05.asm`), not from observing it in-game.

## Shops pay you instead of charging you

**Code:** `VSNAUEVI`

**Effect:** Buying an item in an overworld cave shop credits you the price
instead of debiting it. Pick up the 100-rupee blue ring and you come out 100
rupees richer than you went in — and the shop still hands over the item.

**How it works:** `UpdateCavePersonState_TalkOrShopOrDoorCharge`
(`src/Z_01.asm:678`) reaches `@PickedUpWare` (`:779`) when Link steps onto one
of the three wares in a paying shop:

```
    ; If rupees < price, then return.
    LDA InvRupees
    CMP CavePrices, X
    BCC Exit

    ; Pass the price to pay for the item.
    LDA CavePrices, X
    JSR PostDebit
```

`PostDebit` and `PostCredit` (`src/Z_01.asm:979` and `:968`) are the game's own
matched pair — same one-argument convention, same three instructions, opposite
destination:

```
PostCredit:
    CLC
    ADC RupeesToAdd
    STA RupeesToAdd
    RTS

PostDebit:
    CLC
    ADC RupeesToSubtract
    STA RupeesToSubtract
    RTS
```

`PostCredit` sits at bank 1 `$89D6` and `PostDebit` at `$89DE`, so the shop's
`JSR PostDebit` (`20 DE 89` at `$88F2`) becomes `JSR PostCredit` by changing
its low operand byte. This patches bank 1 CPU `$88F3` from `$DE` to `$D6`.
Raw form: `$88F3:D6:DE`. The calling convention is known to match because the
money-game payout at `$89D4` already falls through to one or the other with the
same `A`.

**Caveat — you still have to be able to afford it.** The `CMP CavePrices, X /
BCC Exit` test above the patched call is untouched, so a 255-rupee item is
still unreachable on 200 rupees. You just get paid rather than charged when
you can.

**Caveat — a compare-byte collision in bank 2 alters one pixel of one tile.**
Bank 2 also holds `$DE` at this `$8000`-window offset, at
`CommonBackgroundPatterns + $174` (`src/Z_02.asm:151`) — byte 4 of the 24th
common background tile. While bank 2 is mapped, that byte uploads to the PPU as
`$D6` instead, clearing one pixel in one bitplane row of that tile. Cosmetic
and confined to that tile.

**Caveat — hints and the money game use their own call.** The hint path has a
separate `JSR PostDebit` at `$88D8`; see `VSSEOEVI` below. The money game
decides credit-versus-debit at `$89D4` and is covered by `AESASOAA`.

**Caveat — this is not the same as `AEVAKAZA`.** That code switches off the
paying block entirely (items become free); this one keeps the block and
reverses its direction (items become profitable). Using both means the block
is skipped, so `VSNAUEVI` would have nothing to do.

**Not live-verified:** derived from reading
`UpdateCavePersonState_TalkOrShopOrDoorCharge`, `PostCredit` and `PostDebit`
(`src/Z_01.asm`), not from observing it in-game.

## Hint caves pay you for the hint

**Code:** `VSSEOEVI`

**Effect:** The old man who charges for a hint pays you his fee instead of
taking it. Walk into the hint, and your rupee count goes up by the price on
the wall.

**How it works:** the same `PostDebit`/`PostCredit` pair, reached from the
hint branch of `UpdateCavePersonState_TalkOrShopOrDoorCharge`
(`src/Z_01.asm:748`, `@PickedUp`):

```
    ; Else have "hint" cave flag.
    ;
    ; If rupees < price, then return.
    LDA InvRupees
    CMP CavePrices, X
    BCC Exit

    ; Pass the price to pay for the hint.
    LDA CavePrices, X
    JSR PostDebit
```

That `JSR PostDebit` is `20 DE 89` at bank 1 `$88D8`; this patches its low
operand byte at `$88D9` from `$DE` to `$D6`, making it `JSR PostCredit`.
Raw form: `$88D9:D6:DE`. No other PRG bank holds `$DE` at that same
`$8000`-window offset (gg.py checked all 8 banks), so unlike `VSNAUEVI` this
one is bank-unique.

**Caveat — you still need the price in hand.** The affordability test above the
call is unpatched, so a hint you could not afford stays unreachable.

**Caveat — one payout per visit.** `@PickedUp` runs when Link steps onto the
chosen ware and then sets `ObjState+1` to 5; you have to leave and re-enter the
cave to collect again.

**Caveat — the shop and money game are separate.** See `VSNAUEVI` for the shop
half and `AESASOAA` for the money game.

**Not live-verified:** derived from reading
`UpdateCavePersonState_TalkOrShopOrDoorCharge`, `PostCredit` and `PostDebit`
(`src/Z_01.asm`), not from observing it in-game.

## Every item's class and amount come from its inventory slot number

**Code:** `KZEZNKEG`

**Effect:** Items still look right and still land in the right inventory slot,
but what you *get* changes completely: keys arrive seven at a time, a heart
restores nine, a bomb pickup sets your bomb count to exactly 1 instead of
adding 4, and picking up the wooden sword sets your sword to "none".

**How it works:** `TryTakeItem` (`src/Z_01.asm:4483`) looks up two parallel
36-byte tables with the same index, the item type:

```
    ; Look up the item slot and sprite attributes by the item type.
    TAX
    LDA ItemIdToSlot, X
    TAY
    LDA ItemIdToDescriptor, X
```

`ItemIdToSlot` (`src/Z_01.asm:4318`) gives the inventory slot; the parallel
`ItemIdToDescriptor` (`:4341`) gives a packed byte whose high nibble is the
item's *class* and whose low nibble is its *value*:

```
; 0x - individuals ... value is boolean: you have it or you don't
; 1x - amounts ...... value is an amount to add
; 2x - grades ....... value is a grade
```

The two tables run at `$72A4` and `$72C8` — the same page — so one byte makes
either read the other. This patches the low byte of the `LDA
ItemIdToDescriptor, X` operand so the descriptor is fetched from
`ItemIdToSlot`: each item's class and value now come from its own slot number.
Raw form: `$AC07:A4:C8`.

**This is a relocated address.** The instruction is inside `BANK_01_CODE`,
which `src/Z.cfg` declares `load = ROM_01, run = RAM_01_CODE`; `bin/Z.map`
gives load `$A500` and run `$6C90`. The operand's run address is `$7397`, so
the cartridge address is `$A500 + ($7397 - $6C90)` = `$AC07`. Bank 1 at `$AC02`
reads `BD A4 72 A8 BD C8 72 48 29 0F 85 0A`, matching the source, with the
`$C8` at `$AC07`. No other PRG bank holds `$C8` at that same `$8000`-window
offset (gg.py checked all 8 banks), so this is bank-unique.

Because every entry of `ItemIdToSlot` is `$00`-`$1F`, the substituted class is
always 0 or 1 — both of which the taking code handles — so nothing is thrown at
an unhandled class. Worked examples, reading the two tables side by side:

- **Bomb** (type 0): slot `$01`, so the descriptor becomes `$01` — class 0,
  value 1. Class 0 ends at `STA Items, Y` (`SetItemValue`, `:4516`), so the
  bomb count is *set* to 1 instead of `$14`'s "add 4".
- **Wooden sword** (type 1): slot `$00`, descriptor `$00` — class 0, value 0.
  Taking the sword stores 0 in the sword slot, i.e. removes it.
- **Key** (type `$19`): slot `$17`, descriptor `$17` — class 1, value 7.
  `CheckClass1` (`:4531`) special-cases slot `$17` to play the key tune and
  then adds the value: seven keys per key.
- **Heart** (type `$22`): slot `$19`, descriptor `$19` — class 1, value 9,
  so `TakeHearts` is handed 9 instead of 1.
- **Triforce piece** (type `$1B`): slot `$1A`, descriptor `$1A` — class **1**
  rather than class 0. The class-0 special case that routes slots `$10`, `$11`,
  `$1A` and `$1B` to `TakeClass0Complex` is never reached, so the piece is
  added arithmetically to the bitmask and the end-of-dungeon mode never starts.

**Caveat — the item still looks normal.** The sprite and the "you got it"
display are drawn by `AnimateItemObject` (`src/Z_07.asm:852`), which reads its
own copy of the same two tables from Save RAM through a different instruction
in bank 7. That instruction is not patched, so the picture and the printed
value are unchanged; only what lands in the inventory differs.

**Caveat — finishing a dungeon stops working.** With Triforce pieces taking the
class-1 path, `TakeClass0Complex` never fires and mode `$12` never starts: no
fanfare, no heart refill, no trip back to the overworld. The map and compass
lose their per-level bit handling for the same reason.

**Caveat — this is chaos by design.** Thirty-six item types are affected at
once; the five above are worked examples, not the whole list. Read the two
tables together to predict any other item.

**Not live-verified:** derived from reading `TryTakeItem`, `ItemIdToSlot`,
`ItemIdToDescriptor`, `SetItemValue` and `CheckClass1` (`src/Z_01.asm`),
`AnimateItemObject` (`src/Z_07.asm`), the segment definitions in `src/Z.cfg`
and the load/run addresses in `bin/Z.map`, not from observing it in-game.

## A blue rupee is worth 128

**Code:** `YYXXXGGE`

**Effect:** The blue "5 rupees" pickup credits 128 rupees instead of 5. One of
them nearly fills the purse.

**How it works:** the blue rupee is the only item the taking code implements as
a loop — it simply performs the single-rupee action five times
(`src/Z_01.asm:4522`):

```
Take5Rupees:
    ; For 5 Rupees, perform the action for 1 rupee 5 times.
    LDY #$04
:
    JSR TakeOneRupee
    DEY
    BPL :-
    RTS
```

`TakeOneRupee` (`src/Z_01.asm:4722`) requests the "rupee taken" tune and does
`INC RupeesToAdd`. With `BPL` as the loop test the body runs `Y+1` times, so
`$04` means five. This patches the `LDY` operand to `$7F`, giving 128
iterations and `RupeesToAdd += 128` in a single frame — still inside one byte,
so nothing overflows. Raw form: `$AC2A:7F:04`.

**This is a relocated address,** on the same basis as `KZEZNKEG` above:
`Take5Rupees` runs at `$73B9`, so the operand's run address is `$73BA` and the
cartridge address is `$A500 + ($73BA - $6C90)` = `$AC2A`. Bank 1 at `$AC29`
reads `A0 04 20 A3 74 88 10 FA 60`, matching the source instruction for
instruction.

**Caveat — a compare-byte collision in bank 4 breaks Patra's children.** Bank 4
holds `$04` at this same `$8000`-window offset, and there it is not inert data:
it is the high byte of the absolute operand in `ADC Flyer_ObjOffsetY+1`
(`6D 79 04` at `$AC28`) inside `PatraChild_State1` (`src/Z_04.asm:10207`). With
this code active that instruction reads `$7F79` — an unrelated Save RAM byte —
instead of `$0479`, so Patra's orbiting children pick up a wrong vertical
offset each frame. Patra appears in only a couple of rooms in the game, but in
those rooms expect the ring of children to drift away from its body.

**Caveat — the tune fires once, not 128 times.** `TakeOneRupee` stores `$01`
into `Tune1Request` on every pass, but all 128 passes happen in the same frame,
so the sound driver sees a single request.

**Caveat — the counter still ticks up one rupee at a time.**
`World_ChangeRupees` drains `RupeesToAdd` gradually, so the rupee count climbs
for a while (with the usual counting sound) after the pickup.

**Caveat — only the blue rupee changes.** The orange rupee and the single
rupee take other branches of `CheckClass1` and are unaffected.

**Not live-verified:** derived from reading `Take5Rupees`, `TakeOneRupee` and
`CheckClass1` (`src/Z_01.asm`), `PatraChild_State1` (`src/Z_04.asm`), the
segment definitions in `src/Z.cfg` and the load/run addresses in `bin/Z.map`,
not from observing it in-game.

## Hold A to swing the sword again and again with no delay

**Code:** `XNXUPXEN`

Tags: `play-start`

**Optional, shorter swings too:** `PANNZNAA`

**Effect:** Holding A swings the sword over and over. A new swing starts as
soon as the last one ends, with no need to let go of A. With the optional
code, each swing is also shorter, so there are more swings per second.

**How it works:** `Link_HandleInput` (`src/Z_05.asm:6921`) only starts a swing
on the frame A is first pressed:

```
    ; If the sword is not blocked, then handle the sword if A is pressed.
    LDA SwordBlockedLongTimer
    ORA SwordBlocked
    BNE :+
    LDA ButtonsPressed
    AND #$80
    BEQ :+
    JSR WieldSword
```

`ButtonsPressed` (`$F8`) has the buttons pressed this frame, and
`ButtonsDown` (`$FA`) has the buttons held. This patches the `LDA` operand at
bank 5 CPU `$B2A9` (originally `$F8`) to `$FA`. Raw form: `$B2A9:FA:F8`. The
item test after it still reads `ButtonsPressed`, so B does not change. This
block only runs while Link's state is 0, and `WieldSword` returns if the sword
is still out, so each swing still plays to the end before the next one starts.

The optional code is the opposite of "Sword and rod stay extended much
longer": it patches the immediate at bank 7 CPU `$F77A` in `UpdateSwordOrRod`
(originally `$08`) to `$01`, so the fully extended state lasts 1 frame instead
of 8. Raw form: `$F77A:01:08`.

**Evidence:** `ext/original.nes` has `A5 F8 29 80 F0 03 20 00 8E A5 F8 29 40`
at bank 5 CPU `$B2A8`, and that `A5 F8 29 80 F0` run appears only once.
`nes_gg.py` finds no other bank with `$F8` at `$B2A9`. Bank 7 is fixed, so
`$F77A` is unambiguous.

**Caveat — the doorway and screen-edge block is gone.** `Link_FilterInput`
clears the A bit only in `ButtonsPressed` when Link is near the edge of the
room or in a doorway (`MaskInputInBorder`). `ButtonsDown` is not cleared, so
holding A swings there too. What the sword does in those spots was not
checked.

**Caveat — sword beams.** At full hearts each swing tries to fire a beam. Only
one beam can be out at a time, as before.

**Caveat — the optional code is shared.** `UpdateSwordOrRod` also runs the
Magical Rod, so the rod's thrust is shorter too. It changes the same byte as
"Sword and rod stay extended much longer" (`AGNNZNAA`), so don't use both.

**Not tested:** derived from reading `Link_HandleInput` and `UpdateSwordOrRod`,
not from observing it in-game.

## The overworld plays the title-screen music

**Code:** `EEVTELPA`

Tags: `demo-ready` `play-start` `curated` `video-ready`

**Effect:** The overworld music is replaced by the title-screen theme, the one
that plays over the waterfall and the story scroll. It plays every time the
overworld song would start, for example when a game starts and when you come
back out of a dungeon.

**How it works:** This is the Zelda version of the SMW and SMB1 codes that swap
level songs for event tunes. `GoToNextModePlayLevelSong` (`src/Z_07.asm`)
picks the song for the current level from a table and asks the sound engine to
play it:

```
LevelSongIds:
    .BYTE $01, $40, $40, $40, $40, $40, $40, $40
    .BYTE $40, $20

GoToNextModePlayLevelSong:
    LDY CurLevel
    LDA LevelSongIds, Y
    STA SongRequest             ; Play the song for the level.
```

Byte 0 is the overworld (level 0). Song `$01` is the overworld song and song
`$80` is the title song. This patches byte 0 at bank 7 CPU `$EBE0`
(originally `$01`) to `$80`. Raw form: `$EBE0:80:01`. `DriveSong`
(`src/Z_00.asm`) sees bit 7 set, starts at phrase `$19` as it does on the title
screen, and loops phrases `$1A`-`$23` forever, so the song never ends.
`LevelSongIds` byte 0 is the only place that requests song `$01`.

**Evidence:** `ext/original.nes` has `01 40 40 40 40 40 40 40 40 20` at bank 7
CPU `$EBE0`. Bank 7 is fixed at `$C000`, so the address is unambiguous.

**Caveat — the title song also uses the noise channel.** On the title screen
the song plays drums on the noise channel. The overworld song has none, so with
this code the drums can cut into sword and bomb noises, or the other way round.

**Caveat — the dungeons are not changed.** The dungeon bytes are the other 9
entries of the table. Changing all of them would take 9 codes.

**Tested by the user:** works.

## All music plays with a thin, nasal instrument

**Code:** `AOOPEYEP`

Tags: `demo-ready` `play-start` `curated` `video-ready`

**Optional, a softer, hollow instrument instead:** `ASOPEYEP`

**Effect:** Both square-wave channels of every song play with a thin, buzzy
tone instead of the normal full one. The triangle bass and the sound effects
sound the same as before. With the optional code instead, the tone is less
thin.

**How it works:** This is the Zelda version of the SMB1 code "All music uses
the water music's instrument". Every frame, for both square channels,
`DriveSong` calls `ShapeSongVolume` (`src/Z_00.asm`) and writes the result to
the channel's duty/volume register (`Sq0Duty_4000`, `Sq1Duty_4004`):

```
ShapeSongVolume:
    ...
@ReturnValue:
    ORA #$90
    RTS
```

The low 4 bits are the volume from the envelope. `$90` sets the duty bits to
`%10` (50% pulse, the full "square" sound) and the constant-volume bit. This
patches the `ORA` operand at bank 0 CPU `$9F90` (originally `$90`) to `$10`
(12.5% pulse). Raw form: `$9F90:10:90`. The optional code uses `$50` (25%
pulse) instead. Raw form: `$9F90:50:90`. The constant-volume bit stays set in
both, so the volume envelopes work as before.

**Evidence:** `ext/original.nes` has `4A 4A 4A 09 90 60` at bank 0 CPU
`$9F8C`. `nes_gg.py` finds no other bank with `$90` at `$9F90`.

**Caveat — only songs.** The short tunes (item fanfare, secret found, low
health) and sound effects set their own duty, so they sound as before.

**Tested by the user:** works. The optional code was not tested.

## Three notes of the music play out of place (C4, F4 and C5)

**Codes:** `IPOONNUX` + `KGXOOYAG` + `VYUPNYSS`

Tags: `play-start` `interesting`

**Effect:** Three of the most-used notes play at the wrong pitch everywhere
they occur. C4 plays as G4, F4 plays as B3, and C5 plays as A4. The songs keep
their rhythm, but the melodies sound wrong in a way that is hard to place.

**How it works:** This is the Zelda version of the SMB1 code "Three notes of
the music play out of place". Every song note is an offset into
`NotePeriodTable` (`src/Z_00.asm`, bank 0 CPU `$9F00`), a table of big-endian
16-bit APU periods. `EmitSquareNote0`, `EmitSquareNote1` and
`EmitTriangleNote` copy the two bytes of the entry to the channel's timer
registers. These codes change the low byte of three entries:

- Note `$1E` (C4, period `$01AB`): `$9F1F` from `$AB` to `$1D`, so the period
  is `$011D` (G4). Raw form: `$9F1F:1D:AB`.
- Note `$28` (F4, period `$0140`): `$9F29` from `$40` to `$C4`, so the period
  is `$01C4` (B3). Raw form: `$9F29:C4:40`.
- Note `$36` (C5, period `$00D5`): `$9F37` from `$D5` to `$FE`, so the period
  is `$00FE` (A4). Raw form: `$9F37:FE:D5`.

A count of the note bytes in all 36 song phrases puts these three notes among
the four most used, after rests (C4 217 times, F4 204, C5 198).

**Evidence:** `ext/original.nes` has `01 AB` at `$9F1E`, `01 40` at `$9F28` and
`00 D5` at `$9F36`, as in the source. `nes_gg.py` finds no other bank with
these bytes at these addresses.

**Caveat — the triangle plays an octave lower.** The triangle channel uses the
same table, so its moved notes are the same note names an octave lower.

**Caveat — the short tunes change too.** The item fanfare and other short
tunes use the same table, so some of their notes move too.

**Tested by the user:** works.

## Moblins throw rocks

**Code:** `LSKEANLI`

Tags: `demo-ready` `play-start` `video-ready`

**Effect:** Moblins spit the round rocks that Octoroks shoot, instead of
arrows. The rocks fly in a straight line the way the Moblin is facing, and
break on walls, trees and rocks the way an Octorok's rock does.

**How it works:** This is the rock version of "Moblins throw boomerangs
instead of arrows". `UpdateMoblin` (`src/Z_04.asm`) passes the shot's object
type to `_TryShooting` in Y:

```
    LDY #$5B                    ; Arrow object type
    JMP :+
```

The code patches the immediate at bank 4 CPU `$87C8` (originally `$5B`) to
`$53`, the flying rock that `UpdateOctorock` passes (`LDY #$53`). Raw form:
`$87C8:53:5B`. `_ShootIfWanted` sets up every shot the same way (state `$10`,
the shooter's direction and position), and `InitMonsterShot` gives the rock
its speed (3 pixels a frame), so the rock needs nothing else.
`UpdateMonsterShot` checks tile collision for types below `$55`, so the rock
breaks on solid tiles where an arrow flies on to the room edge.

**Evidence:** `ext/original.nes` has `A0 5B 4C D1 87` at bank 4 CPU `$87C7`.
`nes_gg.py` finds no other bank with `$5B` at `$87C8`.

**Caveat — the rock is a shot like the arrow.** `ShootLimited` counts types
`$53` and up toward the limit of 4 active monster shots, so the limit is the
same as before.

**Caveat — same address as the boomerang code.** This changes the same byte
as "Moblins throw boomerangs instead of arrows" (`GSKEANLS`). Use only one.

**Tested by the user:** works.

## Octoroks launch arrows

**Code:** `LIOENGLS`

Tags: `demo-ready` `play-start` `video-ready`

**Effect:** Octoroks shoot the Moblins' arrows instead of rocks. The arrows
pass over trees and rocks, and only stop at the room edge, at Link, or on his
shield.

**How it works:** This is the reverse of "Moblins throw rocks".
`UpdateOctorock` (`src/Z_04.asm`) passes the shot type to `_TryShooting`:

```
@Shoot:
    ; Shoot a flying rock (object type $53).
    LDY #$53
    JSR _TryShooting
```

The code patches the immediate at bank 4 CPU `$8C1F` (originally `$53`) to
`$5B`, the arrow that `UpdateMoblin` passes. Raw form: `$8C1F:5B:53`.
`_ShootIfWanted` sets the arrow's state, direction and position from the
Octorok, as it does for a Moblin. `UpdateMonsterArrow` sets the arrow's speed
(`$80`, 2 pixels a frame) itself.

**Evidence:** `ext/original.nes` has `A0 53 20 D3 87` at bank 4 CPU `$8C1E`.
`nes_gg.py` finds no other bank with `$53` at `$8C1F`.

**Caveat — arrows are slower.** `InitMonsterShot` gives a rock 3 pixels a
frame; `UpdateMonsterArrow` gives an arrow 2 pixels a frame.

**Caveat — the arrow does not break on terrain.** `UpdateMonsterShot` checks
tile collision only for types below `$55`. Arrows fly through trees and rocks.

**Caveat — the Moblin arrow's sprite tiles must be loaded.** Both Octoroks and
Moblins are overworld monsters, and the overworld sprite set has the arrow, so
it should look right.

**Tested by the user:** works.

## Most walking monsters shoot fireballs

**Codes:** `AXNETESP` + `YXNEYAZO` + `EPEAAPGE` (use all three)

Tags: `demo-ready` `play-start` `video-ready` `challenge`

**Effect:** Octoroks, Moblins, Stalfos, Gibdos, Darknuts, Like Likes, Ghinis,
Bubbles, Zols and Gels, Vires, blue Leevers and Dodongo shoot a fireball at
Link each time they turn to face him. The fireballs are the ones Zoras and
dungeon statues shoot: they fly straight at Link from where the monster is.
Octoroks and Moblins shoot fireballs instead of their rocks and arrows.

**How it works:** This is the NES version of the SNES Zelda code "Fireballs
continuously shot by most enemy types". Most walking monsters use
`Wanderer_TargetPlayer` (`src/Z_04.asm`), directly or through
`UpdateCommonWanderer`. When the monster is on a square boundary and lined
up with Link, it turns toward him and sets the "wants to shoot" flag:

```
@SetDirTowardTarget:
    STY ObjDir, X
    LDA Random, X
    STA ObjTurnTimer, X

    ; Set "wants to shoot" flag to 1.
    LDA #$01
    STA ObjWantsToShoot, X

    ; Go set input direction to facing direction.
    JMP L_Walker_SetInputDirAndTryShootingBoomerang
```

The codes change `STA ObjWantsToShoot, X` (`9D 12 04`, bank 4 CPU `$80FE`) to
`JSR ShootFireball55` (`20 2F 98`). Raw form: `$80FE:20:9D` + `$80FF:2F:12`
+ `$8100:98:04`. `ShootFireball55` (bank 4 `$982F`, `LDA #$55 / JMP
ShootFireball`) is the routine Aquamentus uses. `ShootFireball` puts a type
`$55` fireball at the shooter's position (X is kept), and the fireball aims
itself at Link. The code after it reloads A and Y, so nothing else changes.

**Evidence:** `ext/original.nes` has `A9 01 9D 12 04 4C 90 81` at bank 4 CPU
`$80FC` and `A9 55 4C AF 82` at `$982F`. `nes_gg.py` finds no other bank with
these bytes at `$80FE`-`$8100`.

**Caveat — normal shots stop.** Octoroks and Moblins only shoot rocks and
arrows when the "wants to shoot" flag is set. Nothing sets it now, so
fireballs replace their normal shots. Stalfos and Wizzrobes use other code.

**Caveat — Goriyas and Lynels are not included.** They use their own turn
code in `UpdateGoriya`. The same change there (`INC ObjWantsToShoot, X` at
`$8188`) would destroy the Y register, which the next instruction uses to
pick the direction, so the monster could face a bad direction. A code for
them was not possible without that risk.

**Caveat — there is no shot limit.** `ShootFireball` does not count shots. A
slow monster can stay on the square boundary for more than one frame and
shoot 2 fireballs at once. Fireballs take free monster slots, so a room full of
fireballs can stop new monsters from coming in from the screen edges.

**Caveat — the turn timer.** This only runs when the monster turns toward
Link. Monsters that are already lined up and keep walking straight at him do
not shoot again until they turn.

**Tested by the user:** works.

## Most walking monsters shoot arrows

**Codes:** `LSOATOGS` + `EUOEGPEY` + `SUKAGPSP` (use all three)

Tags: `demo-ready` `video-ready` `play-start`

**Effect:** Goriyas, Octoroks, Stalfos, Gibdos, Darknuts, Like Likes, Ghinis,
Bubbles, Zols and Gels, Vires, blue Leevers, Dodongo and woken Armos shoot a
Moblin arrow straight ahead each time they turn to face Link. Goriyas shoot
arrows instead of boomerangs, and Octoroks shoot arrows instead of rocks.
Moblins still shoot their own arrows.

**How it works:** This is the arrow version of "Most walking monsters shoot
fireballs", but it uses a different hook. Every monster that uses
`Wanderer_TargetPlayer`, and Goriyas through `UpdateGoriya`, end each frame
in `L_Walker_SetInputDirAndTryShootingBoomerang` (`src/Z_04.asm`). It lets
only Goriyas throw:

```
    ; Goriya will throw a boomerang (object type $5C).
    LDA #$5C

    ; If the monster is a blue goriya, go check the timer.
    LDY ObjType, X
    CPY #$05
    BEQ @CheckTimerToShoot
    ...
@CheckTimerToShoot:
    ; If object timer <> 0, return.
    LDY ObjTimer, X
    BNE @Exit
    ...
    LDA $00
    JSR _ShootIfWanted
    BCC @Exit

    ; Set monster's state to $80 for delaying after shooting.
    LDA #$80
    STA ObjState, X
```

The codes make three changes:

- `LDA #$5C` becomes `LDA #$5B` (arrow). Raw form: `$8196:5B:5C`.
- `BEQ` becomes `BCS`, so every monster type `$05` and up goes on to shoot.
  Raw form: `$819C:B0:F0`.
- `STA ObjState, X` (`95 AC`) becomes `LDA ObjState, X` (`B5 AC`), so the
  thrower's state is not set to `$80`. Many of these monsters use their
  state as a jump-table index, and `$80` would crash them. Raw form:
  `$81C4:B5:95`.

`_ShootIfWanted` only shoots when the "wants to shoot" flag is set.
`Wanderer_TargetPlayer` sets it when the monster turns toward Link, so the
rate is the same as the fireball code. The arrow is set up by `Shoot`, the
same as a Moblin's, and it counts toward the limit of 4 monster shots.

**Evidence:** `ext/original.nes` has `A9 5C BC 4F 03 C0 05 F0 10` at bank 4
CPU `$8195` and `A9 80 95 AC` at `$81C2`. `nes_gg.py` finds no other bank with
these bytes at `$8196`, `$819C` or `$81C4`.

**Caveat — not every monster.** Lynels (types 1, 2) and Moblins (3, 4) are
below `$05`, so they keep their normal shots only.

**Caveat — the thrower's timer.** After a throw, the code sets the thrower's
`ObjTimer` to a random value up to `$3F`. Monsters that use `ObjTimer` for
other things (Leevers, Zols) can pause or change phase early.

**Caveat — Octorok rocks stop.** The arrow uses up the "wants to shoot" flag
first, so Octoroks never get to shoot their rocks.

**Caveat — Goriyas don't pause after throwing,** because of the third code.

**Caveat — same bytes as "Most walking monsters launch Lynel swords".**
Use only one.
It works with "Most walking monsters shoot fireballs" (different bytes); then
Octoroks and Moblins shoot fireballs, and the rest shoot both.

**Tested by the user:** works.

## Most walking monsters launch Lynel swords

**Codes:** `YSOATOGI` + `EUOEGPEY` + `SUKAGPSP` (use all three)

Tags: `demo-ready` `play-start` `video-ready` `challenge`

**Effect:** The same monsters as "Most walking monsters shoot arrows" shoot
the flying sword that Lynels shoot, straight ahead each time they turn to face
Link. Goriyas shoot swords instead of boomerangs, and Octoroks instead of
rocks.

**How it works:** The same as "Most walking monsters shoot arrows", but
`LDA #$5C` becomes `LDA #$57`, the sword shot that `UpdateLynel`
(`src/Z_04.asm`) passes to `_TryShooting`:

```
UpdateLynel:
    JSR UpdateGoriya
    LDY #$57                    ; Sword shot object type
```

Raw form: `$8196:57:5C` + `$819C:B0:F0` + `$81C4:B5:95`. The sword is set
up by `Shoot`, the same as a Lynel's, and `InitMonsterShot` gives it its speed
(3 pixels a frame). `UpdateMonsterShot` draws it with
`DrawSwordShotOrMagicShot`.

**Evidence:** The same bytes as the arrow entry. `nes_gg.py` finds no other
bank with `$5C` at `$8196`.

**Caveat — red and blue Lynels shoot the same sword.** The shot type is the
same; there is no separate Blue Lynel sword.

**Caveat — the other caveats of the arrow entry apply.** Lynels and Moblins
are not included, throwers' timers are reset, Goriyas don't pause, and
Octorok rocks stop.

**Caveat — same bytes as "Most walking monsters shoot arrows".** Use only
one.

**Not tested:** derived from reading `L_Walker_SetInputDirAndTryShootingBoomerang`,
`UpdateLynel` and `UpdateMonsterShot` (`src/Z_04.asm`), not from observing it
in-game.

## Monsters launch bombs instead of projectiles

**Codes:** `EXOUGPKZ` + `POOUIOPI` + `POXLZPAP` (use all three)

Tags: `demo-ready` `play-start` `curated` `video-ready`

**Effect:** Each time an Octorok, Moblin, Lynel or Wizzrobe would shoot, it
drops one of Link's bombs where it stands instead. The bomb blows up after
the usual fuse and hurts monsters near it, the one that dropped it too, but
not Link. In dungeons it can open bombable walls. Other monsters, such
as Tektites and Leevers, act as normal.

**How it works:** Every monster shot goes through `Shoot` (`src/Z_04.asm`,
bank 4):

```
Shoot:
    LDX EmptyMonsterSlot
    LDA $00
    JSR SetTypeAndClearObject
    LDY EmptyMonsterSlot        ; A4 59 -> A0 11 (LDY #$11)
    LDX CurObjIndex
    LDA #$10                    ; A9 10 -> A9 11 (LDA #$11)
    STA a:ObjState, Y
    ...
    ; Set the shot's direction and coordinates the same as the thrower's.
```

- `EXOUGPKZ` + `POOUIOPI`: `LDY EmptyMonsterSlot` becomes `LDY #$11`
  (`$B19C:A0:A4`, `$B19D:11:59`). The shot's state, timer, direction and
  position go to slot `$11`, Link's second bomb or fire slot.
- `POXLZPAP`: the state becomes `$11` (`$B1A2:11:10`), the state
  `WieldBomb` (`src/Z_01.asm`) gives a new bomb. `UpdateBombOrFire` treats
  state `$1x` as a bomb, and `UpdateBomb` starts the fuse from `BombTimes`
  (`$30` frames first). `Shoot` has just set the timer to 0.

`CheckMonsterCollisions` (`src/Z_01.asm`) checks every monster against
slot `$11`, so the blast hurts monsters. Octoroks, Moblins and Lynels shoot
through `_TryShooting`, and Wizzrobes through `ShootMagicShot`. Both call
`Shoot`.

Without `POXLZPAP` the state stays `$10`. That is still a bomb, but
`UpdateBomb` reads its first fuse time from `BombTimes-1`, the `RTS`
(`$60`) before the table, so it waits 96 frames longer.

**Evidence:** `ext/original.nes` bank 4 has `A4 59 AE 40 03 A9 10 99 AC 00`
at CPU `$B19C`. `nes_gg.py` finds no other bank with the same bytes at
`$B19C`, `$B19D` or `$B1A2`. A headless Mesen2 run of the three codes, on
the screen above the start, showed three bombs dropped by Octoroks. All
three blew up and killed four Octoroks between them.

**Caveats:**

- Not tested.
- The monster's own shot type still goes into a free monster slot, cleared
  to state 0. A monster shot in state 0 runs `BounceShot`, so it may show
  briefly at an old position, bounce, and disappear. It is destroyed, so the
  4-shot count goes down again. Not checked in-game.
- Only one monster bomb can be out at a time. A new shot moves it and
  restarts its fuse.
- While a monster's bomb is out and not yet blowing up, Link can't use a
  bomb.
- `CreateChildGel` and Vire's split also use `Shoot`. The Gel or Keese goes
  into a free monster slot, but its position and direction go to slot `$11`,
  so it may appear where an old object was. `CreateChildGel` then sets slot
  `$11`'s state to 0, which removes a bomb that is out. Not checked in-game.
- Uses the same `Shoot` bytes as the monster Link-weapon cheats in
  `zelda_1_long_game_genie.md`. Use only one of them.
