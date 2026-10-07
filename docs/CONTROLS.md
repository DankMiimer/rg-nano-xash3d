# Controls

Source-built games also offer **Menu → Options → Nano settings** for FPS, aiming and independent HUD sizes. Changes apply immediately and save separately for each game. See [settings ranges and defaults](NANO-SETTINGS.md).

## Original scheme

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

The source-built profile starts camera movement at 70/75 degrees per second for yaw/pitch. Holding Left/Right keeps precise yaw for 0.15 seconds, then smoothly increases it to 210 over 0.75 seconds. Release, reversal, R strafing, or a long frame stall resets the ramp. Only yaw accelerates; walking, strafing and vertical look do not ramp. Holding L makes both turning and vertical look three times faster, without changing walking or strafing speed. Hold L + R and use Up/Down for fast vertical look. Releasing L restores precise camera speed; releasing R restores ordinary D-pad movement.

## Counter-Strike (original scheme)

Fn + Left/Down/Right selects menu numbers 1/2/3. Fn + Start + L/R selects 4/5. At team selection, 1 means Terrorists and 2 means Counter-Terrorists; then choose an appearance.

Fn + L holds secondary fire; Fn + R levels the view. Half-Life retains its quick-save/load shortcuts.

Start opens Buy. Fn + Start buys a default loadout. You respawn at the next round, not immediately on death. The launcher opens offline match setup with installed maps, 0–7 bots, four stock difficulties and advanced settings. Defaults use two Easy bots and three-minute rounds. The Nano profile keeps the spectator inset disabled, including when A is pressed after death; A remains Use while alive.

## Half-Life (original scheme)

Start toggles the flashlight. Fn + Start cycles weapons. Fn + Left/Right looks up/down; Fn + Down uses secondary fire. Fn + L quick-saves and Fn + R quick-loads. The opening tram sequence is unarmed; firing requires acquiring a weapon.

System shortcuts retain their usual positions: Fn + A/Y raises/lowers volume, Fn + X/B raises/lowers brightness, and Fn + Up takes a screenshot. In Half-Life, Fn + L/R invokes game quick-save/load.

Hold **Fn + L + R** to stop a stuck game through the supervisor. Allow up to five seconds for forced shutdown and a little longer for launcher cleanup. The same shortcut is used by the isolated native test runtime.

Fn + Start + L + R toggles system stats. The Nano firmware processes Menu as a standalone power-button event; it cannot be included in these GPIO button combinations.

## Source-built settings menus

The main settings categories and Audio, Video options/modes, keyboard controls, advanced controls and input-device pages use readable 12-pixel text and one column. Up/Down selects rows; pages scroll to keep the selected control fully visible. Left/Right adjusts sliders and choices. Use the existing confirm button to toggle a checkbox or activate Done; Menu goes back. The key-binding table keeps its own row navigation. Specialized dialogs and touch/gamepad editing pages still use their upstream layouts.

## Optional face-button aiming

Enable **Menu → Options → Nano settings → Control scheme → Face-button aiming**, then exit and relaunch. Each game remembers its choice in `nano-control.cfg`; the original scheme is the default.

| Button | Action |
|---|---|
| D-pad | Forward/backward and strafe left/right, including while R is held |
| X / B | Look up / down |
| Y / A | Look left / right |
| L | Shoot |
| R | Modifier |
| Start | CS: Buy; spectating: cycle first person / third person / overhead; Half-Life: Use |
| Tap Select | Reload |
| Hold Select + face buttons | Quarter-speed camera aim, without acceleration |
| R + A | Crouch |
| R + B | Jump |
| R + X / Y | Next / previous weapon |
| R + L | Secondary fire |
| R + Start | CS: Use; Half-Life: flashlight |
| R + Select | Level view, retaining horizontal direction |
| Menu | Main menu / back |

Menus use D-pad navigation, A confirm and B back. CS team/buy text menus skip unavailable numbered choices; B returns where a Back/Exit choice exists. Half-Life saving/loading are available from its main menu.

Horizontal camera hold acceleration and the aim speed sliders apply to this scheme. Holding Select with a face button uses 25% of your normal horizontal/vertical aim speeds and disables the acceleration ramp. Using this chord does not reload on release. Pressing R retains its existing modifier actions; R+Select still levels the view. D-pad movement and shooting remain available while aiming slowly. The original L fast-aim shortcut applies only to the original scheme.

Hold **Select + Start + A/Y** for volume up/down or **Select + Start + X/B** for brightness up/down. Use these from the main menu to avoid triggering the first gameplay button actions. **Select + L + R** stops a stuck game; **Select + Start + L + R** toggles system stats.

The firmware emits all twelve gameplay buttons separately and the engine handles R. Menu transitions release gameplay actions and block held buttons until released. Keep the optional keymap, controls config and updated engine together. See [offline match setup](CS-MATCH-SETUP.md) for CS map/bot choices and the four stock difficulty levels.
