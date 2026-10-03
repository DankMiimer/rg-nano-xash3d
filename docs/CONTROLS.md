# Controls

| Button | Both games |
|---|---|
| D-pad Up/Down | Walk forward/backward |
| D-pad Left/Right | Turn |
| L/R | Strafe left/right |
| X | Shoot |
| A | Use |
| B | Jump |
| Y | Reload |
| Fn/Select held | Crouch |
| Menu | Escape/back/game menu |

The original port remaps several letter keys internally. X uses regular `v`, rather than Control, because the modifier mapping did not fire reliably. The firmware keymap also compensates for the GPIO daemon's key-name index mismatch for arrow keys. Keep the supplied keymap together with the engine bindings.

## Counter-Strike

Fn + Left/Down/Right selects menu numbers 1/2/3. Fn + L/R selects 4/5. At team selection, 1 means Terrorists and 2 means Counter-Terrorists; then choose an appearance.

Start opens Buy. Fn + Start buys a default loadout. You respawn at the next round, not immediately on death. Offline rounds last one minute. The Nano profile keeps the spectator inset disabled, including when A is pressed after death; A remains Use while alive.

## Half-Life

Start toggles the flashlight. Fn + Start cycles weapons. Fn + Left/Right looks up/down; Fn + Down uses secondary fire. Fn + L quick-saves and Fn + R quick-loads. The opening tram sequence is unarmed; firing requires acquiring a weapon.

System volume, brightness and screenshot shortcuts are retained.

Hold **Fn + L + R** to stop a stuck game through the supervisor. Allow up to five seconds for forced shutdown and a little longer for launcher cleanup. The same shortcut is used by the isolated native test runtime.

Fn + Start + L + R toggles system stats. The Nano firmware processes Menu as a standalone power-button event; it cannot be included in these GPIO button combinations.
