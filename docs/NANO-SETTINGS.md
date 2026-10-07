# Nano settings

In either source-built game, open **Menu → Options → Nano settings**. Up/Down selects a row, Left/Right adjusts a slider, and the confirm button toggles a checkbox or activates a button. Longer pages scroll with focus. Menu goes back.

Performance, aiming and HUD changes apply immediately and save automatically in that game's `nano-settings.cfg`. The status line reports whether saving succeeded. Each game keeps separate choices, loaded after the launcher defaults on every start. Installing updated controls does not replace this file. **Reset these settings** restores only the current page.

**Control scheme → Face-button aiming** saves separately to `nano-control.cfg` and applies on the next launch. It defaults to the original scheme. See [the button table](CONTROLS.md).

| Page / setting | Range | Default |
|---|---|---|
| Performance: Limit FPS | On/off | On |
| FPS cap | 15–60, steps of 5 | 30 |
| Sleep between frames | On/off | On |
| Aiming: Horizontal aim | 30–120 degrees/s, steps of 5 | 70 |
| Vertical aim | 30–150 degrees/s, steps of 5 | 75 |
| Original L fast aim | 1–4×, steps of 0.25 | 3× |
| Look acceleration | On/off; horizontal camera only | On |
| Turn delay | 0–0.5 seconds, steps of 0.05 | 0.15 |
| Turn ramp | 0.25–1.5 seconds, steps of 0.05 | 0.75 |
| HUD: Bottom HUD | 60–200% | HL 150%; CS 80% |
| Side HUD | 60–200% | HL 150%; CS 80% |
| Radar (CS) | 25–75%, steps of 5 | Preserved from the installed profile |
| Crosshair | 100–300%, steps of 25 | Preserved from the installed profile |
| HUD text (both games) | 12–18 pixel cells | 14 pixels |

Turning off the FPS limit retains the slider value but disables it. The cap is a maximum, not a guarantee that a busy scene will reach that rate. Frame sleeping reduces busy-waiting when a capped frame finishes early; it is offered only by the source-built engine. VSync remains disabled for this framebuffer path.

Horizontal hold acceleration ramps from the horizontal aim setting toward that speed multiplied by L fast aim. Holding L immediately uses fast aiming; vertical look uses its own setting and never ramps. Walking and strafing speed are unaffected. The original scheme uses R for vertical look and strafing. Face-button aiming keeps D-pad movement, uses L to shoot and R to modify actions; its L fast-aim shortcut is unused.

UI profile v2 keeps gameplay at 240×240 and uses a native HUD canvas. The original HUD sprites, font faces, colours and selection sounds remain. Default HL digits use 24-pixel cells, with 32-pixel cells at 200%; CS digits use 20-pixel cells. CS money sits below the top-centred clock. Armor stacks above health, and wide ammo counters split into two rows. The radar and crosshair retain their previous physical size.

HUD text sets chat, notices, spectator and team/buy text together. Objective announcements use cells two pixels taller. Main-menu and confirmation text uses the supplied menu font at 14 pixels; ordinary menu controls use 12 pixels, measured wrapping and focus scrolling. Navigation hints are removed, while selection highlights and status messages remain.

The one-time version-2 migration keeps custom relative HUD sizes where supported and backs up the old settings file as `nano-settings.cfg.ui-v1.bak`. Editing a settings page preserves the other pages and unknown settings, including custom values outside slider increments. See [UI implementation and validation](NANO-UI-V2.md).

The menu and saved choices are installed in the isolated `(source)` entries. The legacy Half-Life menu remains supplied by the external base port. CPU frequency remains 1200 MHz while playing and restores to 1008 MHz on exit; there is no clock slider.

In face-button aiming, Select + face buttons use one-quarter of the saved horizontal/vertical rates without acceleration. A plain Select tap reloads; an aiming chord does not reload on release.
