# Validation and remaining limitations

Checks were performed on an RG Nano with 56,164 KiB total RAM, SD-backed swap and FunKeyOS 2.3.0/DrUm78 firmware. Both launch paths use 1200 MHz while playing and restore 1008 MHz on exit.

## Established SDL ports

- The pinned build recipe produced ARM CS client/server/menu libraries, the software renderer and static helpers using FunKey SDK 2.3.0. Private assembly with user-supplied Steam assets, the external base OPK and the Nano’s SDL passed; no assets or runtime binaries are published.
- Game icons were extracted from the local `game.ico` files, packaged into launchers and checked against the installed PNG hashes.
- Half-Life rendered the opening campaign and created a quick-save. The user confirmed both games’ menu navigation and sound, and Y shooting in Counter-Strike.
- A CS headshot was followed by respawn and several more minutes of responsive play after the renderer clipping correction. Earlier runs exited or froze after death. These short runs do not establish the exact earlier cause or long-term stability.
- The central Half-Life launcher was exercised on hardware. Its stopped child was recovered through the supervisor, and clock readback confirmed restoration to 1008 MHz.

## Independent source-built ports

- The complete native recipe builds the FWGS engine, filesystem, menu, software renderer and portable Half-Life client/server from pinned source. Private assembly resolves SDK dependencies and uses firmware libc/ALSA. It does not open or copy from an XASH3DFS OPK or use its SDL or Half-Life libraries.
- Compilation and a fresh private assembly passed. The installation is isolated under `/mnt/FunKey/Xash3D-source`, with Native games entries labelled `(source)`. Ordinary entries still use the established SDL runtime.
- Framebuffer output renders at 240×240. Pitch and framebuffer allocation checks passed against the Nano’s 16-bit display. Double buffering has not been implemented or measured.
- Native evdev input uses the kernel’s 16-byte input records. A hardware ABI probe found that SDK `struct input_event` is 24 bytes because of its time64 layout. Correcting this restored user-confirmed controls. The firmware key-name index compensation remains necessary.
- Half-Life renders the opening tram and responds to controls. The user confirmed game audio after changing system volume. The launcher now reapplies saved volume and powers the amplifier before starting a game; direct ADB tests had bypassed the frontend’s audio setup.
- The user confirmed movement, shooting and sound in source-built Counter-Strike without first changing volume. Pressing A while spectating subsequently froze the display; the user stopped/restarted the device. The log captured a requested shutdown with no engine crash signal and restored the clock. A enables the inset camera in the upstream client. A published `spec_pip_allow` policy now blocks all second-view activation in the Nano profile. The user confirmed that A after death stays responsive and the next-round respawn works after this change. X fire/Y reload were installed at the user’s request.
- ALSA streaming handles partial writes and a full nonblocking queue without resetting it. Mixer time follows consumed frames, including whole-ring advances between slow updates. Repeated active notifications no longer discard the queue. Hardware PCM counters advance continuously during gameplay; loading can still underrun.
- Engine and Half-Life revisions are aligned to precede the newer FreeVGUI `SetPaintOffset` interface. An initially mismatched client compiled but crashed; neither compilation alone nor an engine version marker establishes API compatibility.

## Automated and recovery checks

- Triangle geometry tests extract the actual dispatcher and rasterizer winding gate and cover front/back faces, two-sided map tiles, mirrored weapons, quad fans, strip winding and fully clipped geometry under AddressSanitizer/UndefinedBehaviorSanitizer. The user subsequently confirmed complete first-person spectator weapons and a visible bird’s-eye map after the correction. The temporary death-test binding was removed.
- Renderer tests exercise the actual patched drawing function with normal, fully off-screen, zero-size and edge-clipped rectangles, guard checks and texture sampling under AddressSanitizer/UndefinedBehaviorSanitizer.
- ALSA tests extract the actual backend functions and check full queues, underruns, partial writes, wrap boundaries, paused output, bounded draining, mixed-data limits, absolute playback time, whole-ring consumption, restart, long-run counter rebasing and activation transitions under AddressSanitizer/UndefinedBehaviorSanitizer.
- Ten supervisor integration tests cover exit status, process crashes, engine-handled crash reports, stopped-child recovery, forced termination, unrelated-process ownership, socket ownership, stale-result cleanup, bounded logs and bounded FIFO writes. Host builds use `-Wall -Wextra -Werror`; ARM smoke checks also passed.
- Logs capture stdout/stderr and RAM/swap/page-fault/CPU samples. Each engine/metric log retains two files of at most 512 KiB. Xash can handle a crash and exit zero, so `result.txt` also records crash signals printed by its handler.
- Recovery resumes the owned game group, sends TERM and escalates to KILL after five seconds. Launcher cleanup restores the clock and default keys. This covers userspace hangs; it does not guarantee recovery from a kernel/driver lockup. There is no automatic freeze detector.

- The user confirmed that Fn + L + R returns from source-built Counter-Strike to the launcher. Clock readback was 1008 MHz and the speaker amplifier returned to its idle state. Menu is a separate power-button event, so the earlier Fn + Start + Menu combination did not work and was replaced.
- A subsequent ordinary Counter-Strike launch stayed running during a short unattended smoke check and restored 1008 MHz on supervised exit. Its latest renderer was not separately checked on the physical screen during that run.
- Fn + L/R is reserved for quick-save/load in both profiles; Counter-Strike menu choices 4/5 moved to Fn + Start + L/R. The engine explicitly rejects multiplayer saves, so CS bot rounds do not gain save-state support from these bindings.

- The new shoulder profile was packaged and installed with configuration hashes checked in both runtimes. Source-built Counter-Strike loaded de_dust with the bindings at 1200 MHz. The user confirmed R look/strafe and L camera speed work perfectly. At the user's request the speeds were then reversed: 70/75 degrees per second by default, 210/225 while holding L, restored to slow on release. The reversal is configuration-only; physical feedback on the reversed speeds is pending.

HUD scale is 0.65, but some sprites still render incorrectly. Initial loads and some scenes use substantial swap. Full campaign completion, extended multiplayer play, repeated suspend/resume and long sessions remain unverified. See [ROADMAP.md](ROADMAP.md) for the next improvements.
