# Controls

| Button | Both games |
|---|---|
| D-pad Up/Down | Walk forward/backward |
| D-pad Left/Right | Turn |
| L/R | Strafe left/right |
| Y | Shoot |
| A | Use |
| B | Jump |
| X | Reload |
| Fn/Select held | Crouch |
| Menu | Escape/back/game menu |
| Fn + Menu | Centre aim |

The original port remaps several letter keys internally. Y uses regular `v`, rather than Control, because the modifier mapping did not fire reliably. The firmware keymap also compensates for the GPIO daemon's key-name index mismatch for arrow keys. Keep the supplied keymap together with the engine bindings.

## Counter-Strike

Fn + Left/Down/Right selects menu numbers 1/2/3. Fn + L/R selects 4/5. At team selection, 1 means Terrorists and 2 means Counter-Terrorists; then choose an appearance.

Start opens Buy. Fn + Start buys a default loadout. You respawn at the next round, not immediately on death. Offline rounds last one minute.

## Half-Life

Start toggles the flashlight. Fn + Start cycles weapons. Fn + Left/Right looks up/down; Fn + Down uses secondary fire. Fn + L quick-saves and Fn + R quick-loads. The opening tram sequence is unarmed; firing requires acquiring a weapon.

System volume, brightness and screenshot shortcuts are retained.
