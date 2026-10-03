# Nano settings

In either source-built game, open **Menu → Options → Nano settings**. Up/Down selects a row, Left/Right adjusts a slider, and the confirm button toggles a checkbox or activates a button. Longer pages scroll with focus. Menu goes back.

Changes apply immediately and save automatically in that game's `nano-settings.cfg`. The status line reports whether saving succeeded. Each game keeps separate choices, loaded after the launcher defaults on every start. Installing updated controls does not replace this file. **Reset these settings** restores only the current page.

| Page / setting | Range | Default |
|---|---|---|
| Performance: Limit FPS | On/off | On |
| FPS cap | 15–60, steps of 5 | 30 |
| Sleep between frames | On/off | On |
| Aiming: Horizontal aim | 30–120 degrees/s, steps of 5 | 70 |
| Vertical aim | 30–150 degrees/s, steps of 5 | 75 |
| L fast aim | 1–4×, steps of 0.25 | 3× |
| Look acceleration | On/off; horizontal camera only | On |
| Turn delay | 0–0.5 seconds, steps of 0.05 | 0.15 |
| Turn ramp | 0.25–1.5 seconds, steps of 0.05 | 0.75 |
| HUD: Bottom HUD | 75–112.5%, steps of 2.5 | 112.5% |
| Side HUD | 75–150%, steps of 2.5 | 112.5% |
| Radar (CS) | 25–75%, steps of 5 | 50% |
| Crosshair | 100–300%, steps of 25 | 200% |
| Team/buy text (CS) | 100–125%, steps of 5 | 125% |

Turning off the FPS limit retains the slider value but disables it. The cap is a maximum, not a guarantee that a busy scene will reach that rate. Frame sleeping reduces busy-waiting when a capped frame finishes early; it is offered only by the source-built engine. VSync remains disabled for this framebuffer path.

Horizontal hold acceleration ramps from the horizontal aim setting toward that speed multiplied by L fast aim. Holding L immediately uses fast aiming; vertical look uses its own setting and never ramps. Walking and strafing speed are unaffected. R still switches the D-pad to vertical look and strafing.

HUD scaling keeps the original artwork and independent groups. The bottom maximum and CS text maximum preserve space for full counters and numbered choices on the 240×240 screen. Buy/bomb sprites retain one source pixel per display pixel. The CS crosshair rounds all four arms to equal whole-pixel lengths; its accepted default retains five-pixel arms. Main/pause/settings text keeps the tested 12-pixel font size; the CS text slider affects team and buy messages.

The menu and saved choices are installed in the isolated `(source)` entries. The legacy Half-Life menu remains supplied by the external base port. CPU frequency remains 1200 MHz while playing and restores to 1008 MHz on exit; there is no clock slider.
