# Controller and original-style HUD research

Research date: 2026-10-03. The target is the Nano's 240x240 software-rendered display and digital buttons. The user's preference is original artwork and recognizable placement, with individual elements made larger or smaller as needed. This document records candidates and an implementation plan; independent HUD scaling is not installed yet.

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

The user confirmed the initial controls worked perfectly, then requested slow aiming as the default. Yaw/pitch now starts at 70/75 degrees per second; holding L selects 210/225 and releasing L restores the slow values. It changes camera rates only. L + R gives fast vertical look. Fn volume/brightness/save/load and recovery keep their existing mappings. The reversed speed profile still needs physical confirmation.

## User sizing targets

- CS top-left radar: half its current width and height.
- Crosshair: currently too small to see; preserve its recognizable shape but give it a visible minimum pixel thickness and larger arms.
- HUD along the bottom and side: slightly larger, starting with a 1.15x trial.
- Main/pause/settings menu text: 2-3x current size, with scrolling/layout adjusted so options remain accessible.
- Team/weapon selection text: 1.25x current size.

These are independent settings. The radar's map and player markers must transform together; the crosshair stays exactly at screen center. A menu cannot be fixed by enlarging its font while leaving line spacing and hitboxes unchanged.

## Scaling quality requirements

Ratios are targets, not a reason to distort artwork. Preserve aspect ratios and use rounded physical-pixel extents/anchors. Compare exact sprite pixel sizes and nearby scales on the Nano before selecting a default. Thin crosshair strokes must remain at least one physical pixel; test a two-pixel option for visibility. Downsampling needs special attention to icon outlines and radar contacts so important pixels do not vanish.

The pinned Half-Life client selects a 320-pixel sprite set when its virtual HUD width is below 640, while CS16Client explicitly loads the 640 set. Thus an identical global scale gives different physical glyph sizes. Check available original sprite variants before choosing per-element dimensions. Prefer sharp original sprite sampling, with no invented replacement font or artwork; compare filtering where reductions lose detail.

Main/pause/settings menus belong to [FWGS mainui_cpp](https://github.com/FWGS/mainui_cpp), whereas CS team/buy number menus use `CHudMenu`. Their fonts and line spacing must be handled separately. The larger main menu target must not accidentally enlarge all game text or scale the rendered world.

## HUD implementation plan

1. Establish a reliable baseline using fresh framebuffer captures tied to a logged frame/run and a physical-screen check. Include HL with suit, weapons and damage indicators; CS alive with armor/ammo, buy menus, death/respawn and each spectator mode. Separate wrong sprite samples, transparency and clipping from an element that is simply too small.
2. Keep the original `hud.txt` / weapon sprite assets, colors, numeric font, fades, icons and familiar left/right placement. Add opt-in Nano layout settings to the clients, with independent controls for health digits, armor digits, ammo digits, accompanying icons, radar, timer/money, weapon selection and text. Crosshair and full-screen scope/night vision overlays need separate treatment.
3. Prototype health and ammo first. Measure the complete block, including digits, icon and gaps, then anchor health at the bottom left and ammunition at the bottom right. Place armor using the measured health extent, rather than a hard-coded fraction of screen width. Reserve the CS timer area and test large values before choosing defaults.
4. Add the remaining groups. Initial direction, subject to physical feedback: enlarge important numbers and menu text where unreadable; compact decorative icons and weapon selection; size the CS radar independently so it does not dominate the upper-left view. Preserve radar blips and useful text rather than shrinking everything equally. Do not change crosshair behavior or shapes by default.
5. Build a small shared transform helper for destination position/size and anchoring; keep source sprite rectangles separate. Inspect engine sprite drawing before choosing its interface: the pinned `SPR_DrawGeneric` path overwrites width/height with the source subrectangle extent, so passing arbitrary destination dimensions with `prc` is not sufficient. A limited, opt-in engine/client extension may be needed. Keep the existing renderer/client interface layout stable and leave ordinary drawing unchanged when disabled.
6. Apply the same transform to icon/digit drawing, fills, text measurement and clipping within a group, then reset it after the group. Use pixel-aligned sampling and original transparency modes. Keep full-screen overlays, centered crosshair, menus and spectator map outside ordinary corner transforms.
7. Verify 0/9/10/99/100 values, long names, empty/full armor, low-health flashes, ammo changes, radar contacts, weapon selection and all four screen edges. Check cropping and alpha under the existing renderer sanitizers; validate the final dimensions on the physical Nano. Compare frame time/RAM at 1200 MHz and preserve a profile switch to the previous layout.

A single global `hud_scale` cannot meet the mixed-size requirement. It currently remains 0.65 until the element-specific path has been implemented and checked. Avoid replacing assets with a modern HUD pack: that adds a different visual style without solving layout in both clients.

## Reuse and attribution

No additional third-party source was copied by this research. For subsequent imports, record the exact revision and files and retain their copyright/license notices. CS16Client's drawing helper carries GPL-2.0-or-later with an HL linking exception; BugfixedHL's repository advertises GPL-3.0 and includes SDK-derived code; portable/Unified SDK files also carry Valve SDK notices. Treat each file's notice separately rather than assigning a blanket license to all game code. Continue distributing patches/recipes without the user's game sprites or extracted icons.
