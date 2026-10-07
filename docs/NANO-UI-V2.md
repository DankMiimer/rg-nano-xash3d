# Native Nano UI profile v2

Gameplay stays at 240 x 240. The framebuffer backend uses the physical panel dimensions, so changing the requested video resolution would not enlarge the menus reliably. This profile changes the HUD canvas and the shared menu layout instead, retaining the existing artwork, bitmap HUD fonts, menu font face, colours, sounds and selection behaviour.

## HUD and text

Both games use `hud_scale 1`. Half-Life retains its 320-resolution sprites and scales its 16-pixel digits by 2 (32-pixel cells) for exact nearest-neighbour pixels. Custom group sizes remain available. Counter-Strike retains its complete 640-resolution sprite set and scales its 25-pixel digits by 0.8 (20-pixel cells). These are cell sizes: visible glyph ink is smaller. Armor stacks above health. Ammo reserves use fixed maximum widths and split above the clip count when needed; secondary ammo and pickup notifications remain.

The CS timer sits at the top centre with a four-pixel inset. Money and money changes sit on the right below it. The radar and crosshair compensate for the canvas change to preserve their previous physical footprints, including separate sprite and direct drawing paths.

`nano_hud_text_height` controls chat, kill notices, team/buy menus and spectator text together (12-18 pixels; default 14). Objectives use two pixels more. Drawing and measurement share the same transform. UTF-8 fitting, colour-aware wrapping and integer placement prevent double scaling. The four-notice kill queue retains weapon/headshot icons and team colours, shortens long names, and yields space to objectives and chat. Chat retains message order, colours and expiry. Team and buy menus show the selected row before removing control hints.

All six spectator camera modes retain their original behaviour. Spectator controls use readable scrolling rows. The scoreboard uses two lines per player and pages with the D-pad, preserving team colours, score, deaths, health, money and player status. Held and menu-opened scoreboards both route input as menus, and release restores gameplay input.

## Shared menus

The common layout applies to every page rather than a list of page names. Controls use measured 12-pixel text, main-menu and dialog text use 14 pixels, ordinary rows are 24 pixels and slider/field/spin rows are 42 pixels. Wrapped labels can enlarge rows; focus scrolls into view. Tables clip individual columns and shorten overflowing cells. Tabs, dropdowns, save previews and modal dialogs use the same native geometry. Nested groups have their own viewport and focus scrolling; previews reserve their label and retain their aspect ratio. Crosshair controls and the spray-colour dialog use the same helpers, including button-controlled colour swatches. Background art keeps its original coordinates.

Font metrics and caches now agree with drawing; a separate cache namespace avoids stale metrics. Text uses a restrained one-pixel shadow. Long dialogs wrap and scroll with pinned confirmation buttons. Destructive confirmations initially select Cancel. Navigation hints are removed, while focused-row highlights, save status and useful messages remain.

Nano menus hide Update, Touch, Gamepad/Joystick, mouse-only settings, resolution choices and the redundant HUD-canvas checkbox. The software-only Video page keeps gamma, brightness, texture filtering and a separate aspect-correct preview row. Inactive OpenGL settings (detail textures, VBO, water and overbright controls) are hidden because they do not affect this renderer.

An actual menu-rendered texture/global-alpha ramp reproduced the original bitwise opacity defect. Multiplication fixed alpha combination, but the software renderer's coarse colour lookup still caused brightness dips. The 2D UI path now blends complete channels in the renderer's internal packed colour representation. Opaque and transparent endpoints remain exact; 3D drawing retains its existing palette paths. Both the actual draw function and the hardware ramp pass monotonicity checks.

## Preferences and update safety

Version 2 performs one atomic migration per game and keeps `nano-settings.cfg.ui-v1.bak`. It preserves customised relative group scales within supported limits and translates the old CS menu scale into shared HUD text height. Future profile versions are left alone. FPS, aiming, controls, bindings, match choices and saves are preserved. Editing one settings page saves only that page and keeps other settings and unknown lines byte-for-byte, including values between slider increments.

`tools/package_ui_update.py` packages six libraries, two control-default files, the launcher, migration helper and component manifest. It checks the tested candidate hashes and the installed baseline before writing. Installation backs up every replaced file plus both settings files and supplies a complete rollback script. It refuses unexpected installed components. The follow-up includes the CS server library for bot-progress failure cleanup and duplicate camp announcements; game assets remain excluded. Source patches, headers, pinned revisions and licence notices accompany the package.

## USB viewer

The viewer lives in the separate `rg-nano-adb-tools` repository. Run `nanoctl view` or `viewer/Nano-view.cmd`; `NANO_PYTHON` selects host Python. It needs only the Python standard library and a browser. `NANO_ADB` and `NANO_SERIAL` remain supported. Continue using the Nano's buttons.

A read-only ARM helper is staged in `/tmp` and serves the displayed RGB565 framebuffer page over an owned ADB socket forward. The host converts and encodes PNG. Requests deliver the latest frame without building a queue. The viewer offers native size, integer nearest-neighbour zoom, 2/5/10 fps, freeze/resume, PNG capture, A/B difference, pixel inspection and connection status. Closing it stops its helper and removes its own forward; idle helpers expire after 30 seconds. Firmware that cannot forward uses a labelled, slower screenshot-and-pull fallback and periodically retries streaming.

The measured uncapped Half-Life scene lost 4.8-5.8% gameplay throughput at 2 captures/s, 13-14% at 5 and 26-31% at 10. The default was reduced to 2 fps. Capture remains useful for inspection, but should be frozen during performance comparisons. These measurements are specific to one scene and device; capture is not free.

## Verification limits

Host checks exercise actual menu callbacks and geometry, live settings saves, dialogs, HUD drawing, maximum counter widths, UTF-8/colour wrapping, objective expiry, renderer clipping and opacity, migration, input routing, and package install/rollback in a disposable runtime. Native ARM components build successfully. The existing ADB device suites pass, including timeout cleanup and short applications.

Hardware tests use RAM-only game roots and read-only SD assets, with a single game running. They cover menus, tables, dialogs, HUD counters, chat/radio text, notices/headshots, bomb/defuse announcements, buy menus, spectator modes and scoreboard paging. Diagnostic CS events travel through normal network HUD messages; they are not a complete bomb-plant gameplay round. Diagnostic libraries are excluded from the update. Native and integer-enlarged captures and anonymous measurements accompany the private candidate.

Framebuffer inspection checks rendered pixels, not backlight or viewing comfort. Final readability and button comfort require a glance at the physical 1.54-inch LCD. Physical cable unplug/replug remains a human check; transport-loss fallback and reconnect are exercised by stopping the owned helper. Tabs are covered by the shared layout tests where no installed page uses them. No persistent SD update is implied by preparing or testing this package.

The installed menu revision also aligns Half-Life’s stb font size with the FreeType em-size convention used by CS. It retains complete ascender/descender metrics and uses a new `nano-v2-r2` cache directory so existing generated glyphs cannot retain the smaller size.

## October follow-up

Confirmation dialogs fill the native viewport opaquely and keep the message and two accessible choices separate. The connection-progress window also gets a native layout; it inherits BaseWindow rather than Framework and therefore needs explicit placement. Half-Life adds one pixel to the 14-pixel menu font's character advances, using the same metrics for measurement and drawing. The `nano-v2-r3` font cache keeps older generated widths separate.

The CS client reads the title from the initial BotProgress message. A single persistent screen covers exploration, hiding-spot analysis and route analysis. Exploration has an indeterminate indicator because the server has no total; the two analysis stages advance the same monotonic bar. The runtime-only `nano_bot_loading` flag skips world rendering while server simulation continues. Gameplay commands have zero movement, buttons, impulse and weapon selection until preparation ends; Escape still opens the pause menu. A failed starting position dismisses the progress screen. Defuse bars keep their own original lifecycle.

Start cycles first-person, locked third-person and player-following overhead spectator views in the face-button control scheme. The existing spectator options retain the other modes. The server suppresses identical vague “I'm going to camp” samples from the same team for 20 seconds. Other radio messages and named bombsite announcements retain their behaviour.

Profile 3 migrates only Half-Life's old default 1.5 group scale to 2, retaining custom scales, and keeps `.ui-v2.bak`. Both games retain unrelated settings and unknown lines. Source patches and package rollback include the changed CS server as well as the UI libraries.

## Main-menu cleanup

The Nano main menus omit Change game, View Readme and Previews. The CS Spectator options button is registered between Offline match and Quit, matching its displayed row. Up/Down traversal therefore follows the screen order when the spectator entry appears. The menu-navigation regression exercises the actual cursor routine using registration and display order, with the spectator entry present and absent, and in both directions across wrap.
