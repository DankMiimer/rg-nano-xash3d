# Validation and remaining limitations

Device checks were performed on an RG Nano with approximately 54 MiB of available system RAM, SD-backed swap and FunKeyOS 2.3.0.

- The published build recipe passed from fresh pinned source checkouts using FunKey SDK 2.3.0, producing ARM CS client/server/menu libraries, the software renderer and static launch helpers.
- Game icons were extracted from each local `game.ico`, packaged into the individual launchers, and verified against the installed Nano PNGs by SHA-256.
- Both launcher paths set the CPU to 1200 MHz; hardware register readback confirmed the applied clock. Normal game-process exit restored 1008 MHz.
- Half-Life rendered the opening campaign and created a quick-save. Full campaign completion has not been tested.
- Counter-Strike entered an offline de_dust match with two bots. The user confirmed Y fires after changing it to a regular key.
- After the renderer clipping correction, a subsequent enemy headshot was followed by respawn and several more minutes of responsive gameplay without a captured crash signal. Earlier runs had an exit and a reported freeze after death; this short successful test does not establish long-term stability.
- Renderer clipping tests exercise the actual patched drawing function with normal, fully off-screen, zero-size and edge-clipped rectangles, framebuffer guard checks, texture sampling checks, AddressSanitizer and UndefinedBehaviorSanitizer.
- The HUD scale increased from 0.375 to 0.65. Graphical defects remain in some HUD sprites.
- The user subsequently confirmed menu navigation and sound work correctly. The Half-Life launcher currently starts the campaign directly.
- Initial loads can be slow. The system uses considerable swap, so performance and responsiveness depend on the SD card and scene.
- The original Nano base engine and Half-Life client/server cannot yet be reproduced entirely from established corresponding source. The public build reproduces the separately built CS client/server, renderer, helpers and launchers.

Runtime and clock logs are stored under `/mnt/FunKey/Xash3D`. The supplied offline settings disable the spectator inset and shorten rounds; these settings do not prove the earlier freeze's exact cause.
