# Controller and original-style HUD research

Research date: 2026-10-03. The target is the Nano's 240x240 software-rendered display and digital buttons. The user's preference is original artwork and recognizable placement, with individual elements made larger or smaller as needed. Independent HUD transforms and horizontal camera acceleration are now implemented in the source-built runtime. Main/pause menu changes apply to both the engine menu and Counter-Strike's separate menu module. Settings submenus remain a separate layout task.

## Candidates worth using

| Project / code | Useful part | Nano decision |
|---|---|---|
| [FWGS portable HLSDK input](https://github.com/FWGS/hlsdk-portable/blob/9c45ba22fba98517fdd303d446c78dafcf74fd07/cl_dll/input.cpp) | `CL_AdjustAngles`, `+klook`, `+strafe`, yaw/pitch speed variables | Already in the native Half-Life client. Use these existing commands for R look/strafe and a paired press/release alias for L fast look. No controller backend is needed for this mapping. |
| [FWGS controller input](https://github.com/FWGS/xash3d-fwgs/blob/master/engine/client/input/in_joy.c) | Joystick axis mapping, dead zones, look rates and button handling | Useful for an eventual external analog controller. Analog response curves/dead zones do not improve the Nano's digital D-pad directly. Keep the current firmware/evdev route. |
| [CS16Client HUD](https://github.com/Velaron/cs16-client/tree/e30e27b/cl_dll) | Existing individual health, battery, ammo, radar, timer, money, menus and drawing utilities | Best place to extend CS. We already build it; preserve its original sprite loading and add small layout/scaling changes. [Drawing helpers](https://github.com/Velaron/cs16-client/blob/main/cl_dll/draw_util.cpp) draw the original numeric sprites. |
| [BugfixedHL sprite renderer](https://github.com/tmp64/BugfixedHL-Rebased/blob/4d32095e3c33d5ca60809d9c51f8aafe51c0a521/src/game/client/hud_renderer.cpp) | Central sprite drawing wrapper; validates source rectangles and separates drawing from HUD elements | Useful design reference. Its `IsAvailable()` explicitly requires OpenGL, so it cannot be copied as a working software-renderer replacement. Avoid importing its VGUI2 UI stack. |
| [Half-Life Unified SDK HUD](https://github.com/twhl-community/halflife-unified-sdk/blob/3dea394bfbe600f77f915dcb4e39bcf4a12a0ee8/docs/features/hud-sprite-system.md) | Named sprite regions and configuration separate from artwork; [health/armor layout](https://github.com/twhl-community/halflife-unified-sdk/blob/3dea394bfbe600f77f915dcb4e39bcf4a12a0ee8/src/game/client/ui/hud/health.cpp) positions armor after the measured health area | Borrow the layout idea. Its JSON width/height fields describe source sprite regions, not independent on-screen scaling. Its [README](https://github.com/twhl-community/halflife-unified-sdk#what-isnt-supported) explicitly excludes Xash, so replacing our SDK with it is unsuitable. |

The older [vitaXash3D](https://github.com/fgsfdsfgs/vitaXash3D) also documents handheld constraints and notes that some mods expect at least 640x400. Its README says Vita support moved into mainline and this older port is no longer updated. Prefer current FWGS code when investigating handheld input rather than replacing our engine with an old console fork.

## Controls installed now

R runs `+strafe` and `+klook` together. The clients turn forward/back into vertical look while suppressing forward movement, and turn left/right into lateral movement while suppressing yaw. Releasing R ends both actions. This also accommodates diagonal input without creating overlapping firmware chords.

The user confirmed the initial controls worked perfectly, then requested slow aiming as the default. Yaw/pitch now starts at 70/75 degrees per second; holding L selects 210/225 and releasing L restores the slow values. It changes camera rates only. L + R gives fast vertical look. Fn volume/brightness/save/load and recovery keep their existing mappings. The user confirmed the shoulder controls and subsequent yaw acceleration feel correct.

## Digital aiming: research and implementation

[Halo Infinite's official settings guide](https://support.halowaypoint.com/hc/en-us/articles/4407649252116-Guide-to-Halo-Infinite-Game-Settings) separates horizontal/vertical sensitivity and describes look acceleration as the rate of reaching maximum camera speed. [EA's Apex Legends accessibility guide](https://www.ea.com/able/resources/apex-legends/pc/features) documents controller response curves. Analog curves require an analog signal; the Nano D-pad instead provides direction and hold duration.

Our implementation uses hold duration: 70 degrees/second yaw, 0.15 seconds of precise aiming, then a 0.75-second smoothstep ramp to 210. A fresh press, reversal, release, R strafing, L override/release or a frame stall resets it. L gives immediate fast look. Pitch and movement arithmetic are unchanged. This is newly written code inspired by the behavior, not copied Halo or Apex code. The client changes are opt-in and leave ordinary input unchanged when disabled.

## Current HUD profile

| Group | Default | Placement / treatment |
|---|---|---|
| Health, armor, ammo | 1.125x | Whole blocks measured, health left and ammo right, approximately one physical pixel inside the bottom edge. Armor follows the reserved health width. CS ammo retains both three-digit fields with compact separator spacing, avoiding the armor group. Reserve-only and secondary ammo share the right edge. |
| CS timer | 1.125x | Centered row immediately above the bottom counters to prevent overlap on the square screen. |
| CS money | 1.125x | Top-right edge; temporary gain/loss amounts appear to the left of the balance. Kill notices start just below it. |
| Status icons | 1 source pixel per display pixel | Original buy-zone/bomb artwork, typically 32×32, without downsampling; left edge with four-pixel vertical gaps. |
| CS radar | 0.5x | Upper left, map and markers share one transform. |
| Team/buy text | 1.25x | Original number-menu text and spacing transformed together; user confirmed good size. |
| CS dynamic crosshair | At least five-pixel arms | Original colors, fades and dynamic spread; four mirrored rectangles share one physical center, three-pixel minimum gap and one-pixel stroke. |
| Static crosshair | 2x | Original sprites; scope overlays excluded from enlargement. |
| Main/pause buttons | 2x | Original menu font, row spacing and hitboxes resized; engine and CS menu libraries both patched; font rasterized at the larger size and cached, including CS's additional Readme row. Nano uses font text rather than stretched picture-button labels; the decorative title and debug Console entry are hidden to keep the rows unobstructed. |

The overall virtual HUD scale remains 0.65. Per-group transforms preserve aspect ratios and round destination edges to physical pixels. Every scope restores scale, anchors and offsets, including early returns and nested draws. Source sprite rectangles stay unchanged. Texture UVs must always be normalized: an initial crisp-sampling experiment omitted normalization and hid the HUD; the correction is covered by a regression test. Thin positive fills retain at least one pixel.

The CS crosshair is laid out directly in physical pixels to avoid truncation through the legacy integer drawing API. A fresh framebuffer capture confirmed five pixels in every arm and equal mirrored gaps. Full-screen scope/night vision and spectator views retain their existing behavior.

## Remaining layout and verification work

1. Adapt settings submenus with suitable row spacing/scrolling, rather than only enlarging their fonts.
2. Verify Half-Life with suit, armor, weapon/ammo and damage indicators. Its 320-pixel sprite set differs from CS's 640-pixel set, so compare physical readability independently.
3. Check extreme values, money deltas, empty/full armor, primary/secondary ammo, radar contacts, long team/buy text and death/respawn. Preserve original colors, fades and artwork.
4. Measure a repeatable CS round and HL campaign scene for frame-time, memory/swap and audio stalls at 1200 MHz. Optimize only demonstrated bottlenecks.
5. Keep source-built entries separate until parity and extended stability are established; publish source/recipes without game assets, extracted icons or unlicensed fonts/navigation.

Run `NANO_NATIVE_DIR=/path/to/native-build python3 tests/test_nano_look_hud.py` under Linux after fetching/building. It compiles actual client yaw functions and engine HUD functions with AddressSanitizer/UndefinedBehaviorSanitizer, and exercises frame rates, reversals, pitch/strafe invariance, nested scopes, edge placement, symmetric crosshair geometry normalized sprite UVs, full health/armor alongside three-digit ammo, top-edge money and death-notice clearance.

`test_nano_menu.py` compiles both real menu arrangement methods and font-cache method against a small host harness; it checks maximum rows, late visibility changes and reuse/invalidation of the enlarged font.
