# Improvement roadmap

1. **Observe and recover (implemented):** bounded crash/output logs, RAM/swap/CPU samples, owned-process shutdown and automatic clock/key restoration. Verify normal exit, crashes and manual recovery before investigating death freezes further.
2. **Remove the unknown binary dependency (built and running separately):** build FWGS engine, filesystem, renderer, menu and HLSDK libraries with the FunKey SDK; test a separate framebuffer/evdev/ALSA installation. Preserve the working SDL ports until display, navigation, shooting and sound pass on real hardware.
3. **Measure memory and stalls:** compare tram/campaign loading, a CS match, death/spectating/respawn and repeated launches using the same assets and 1200 MHz clock. Use faults/swap and engine timing to choose optimizations; avoid guessing at the freeze's cause.
4. **Repair HUD rendering (spectator geometry corrected; HUD work remains):** check sprite clipping, transparency and software-renderer scaling with representative HL and CS scenes. Keep the readable HUD scale; distinguish corrupt rendering from layout or font size.
5. **Tune control ergonomics:** retain Y fire and L/R strafe, working number menus and system shortcuts. Add alternate profiles only after physical-device feedback.
6. **Optimize demonstrated bottlenecks:** investigate texture/cache budgets, audio latency and loading work. Framebuffer double buffering and newer engine revisions are separate experiments; check renderer interfaces whenever changing the engine pin.
7. **Reproducible releases:** publish source and recipes with pinned dependencies and notices. Distribute no Valve data, extracted icons, unlicensed fonts/NAV or unknown base-port binaries. Only consider source-built binary releases after dependency-license and hardware parity checks.

Relevant upstream references: [FWGS engine](https://github.com/FWGS/xash3d-fwgs), [portable HLSDK](https://github.com/FWGS/hlsdk-portable), [CS16Client](https://github.com/Velaron/cs16-client), and [FunKey OS/SDK](https://github.com/FunKey-Project/FunKey-OS). See [VALIDATION.md](VALIDATION.md) for completed checks and limits.
