# Controls

| Button | Both games |
|---|---|
| D-pad Up/Down | Walk forward/backward |
| D-pad Left/Right | Turn |
| Hold R + D-pad Up/Down | Look up/down |
| Hold R + D-pad Left/Right | Strafe left/right |
| Hold L | Temporarily use fast camera movement |
| X | Shoot |
| A | Use |
| B | Jump |
| Y | Reload |
| Fn/Select held | Crouch |
| Menu | Escape/back/game menu |

The original port remaps several letter keys internally. X uses regular `v`, rather than Control, because the modifier mapping did not fire reliably. The firmware keymap also compensates for the GPIO daemon's key-name index mismatch for arrow keys. Keep the supplied keymap together with the engine bindings.

Camera movement is slow by default (70/75 degrees per second for yaw/pitch). Holding L makes both turning and vertical look three times faster, without changing walking or strafing speed. Hold L + R and use Up/Down for fast vertical look. Releasing L restores precise camera speed; releasing R restores ordinary D-pad movement.

## Counter-Strike

Fn + Left/Down/Right selects menu numbers 1/2/3. Fn + Start + L/R selects 4/5. At team selection, 1 means Terrorists and 2 means Counter-Terrorists; then choose an appearance.

Fn + L/R retains the quick-save/load bindings. Counter-Strike's engine rejects saving multiplayer matches, including the offline bot setup; these shortcuts cannot save or restore a CS round. They work in Half-Life.

Start opens Buy. Fn + Start buys a default loadout. You respawn at the next round, not immediately on death. Offline rounds last one minute. The Nano profile keeps the spectator inset disabled, including when A is pressed after death; A remains Use while alive.

## Half-Life

Start toggles the flashlight. Fn + Start cycles weapons. Fn + Left/Right looks up/down; Fn + Down uses secondary fire. Fn + L quick-saves and Fn + R quick-loads. The opening tram sequence is unarmed; firing requires acquiring a weapon.

System shortcuts retain their usual positions: Fn + A/Y raises/lowers volume, Fn + X/B raises/lowers brightness, and Fn + Up takes a screenshot. Fn + L/R remains quick-save/load, subject to the game's save support. These invoke game commands rather than an emulator save state.

Hold **Fn + L + R** to stop a stuck game through the supervisor. Allow up to five seconds for forced shutdown and a little longer for launcher cleanup. The same shortcut is used by the isolated native test runtime.

Fn + Start + L + R toggles system stats. The Nano firmware processes Menu as a standalone power-button event; it cannot be included in these GPIO button combinations.
