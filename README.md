# Half-Life and Counter-Strike for RG Nano

Source-built Half-Life and Counter-Strike 1.6 ports for the RG Nano running FunKeyOS/DrUm78 firmware, adapted for its 240×240 screen and built-in buttons.

The current ports build the **Xash3D FWGS engine, software renderer, filesystem, menus and game libraries from pinned public source**. They use Linux framebuffer, evdev input and the Nano's ALSA audio stack directly. **The source-built installation does not require the XASH3DFS OPK or its engine/Half-Life binaries.**

This repository contains source, patches, build recipes and tests. No prebuilt runtime, Valve game data, extracted icons, font or bot navigation file is included. Supply your own Half-Life and Counter-Strike installation. Components retain their individual licenses, including Valve's Half-Life SDK terms; the commercial games are not open source.

## Current features

- **Half-Life:** starts the opening campaign; supports weapons, saves/loads and tested level transitions.
- **Counter-Strike:** starts an offline de_dust match with two easy bots and one-minute rounds. Select a team and appearance; respawn occurs at the next round.
- **Controls:** precise default aim, L for fast aim, R for pitch/strafing, X fire and Y reload. Held horizontal turning gradually accelerates; movement and vertical look do not accelerate.
- **Display:** original map skyboxes and HUD artwork, independent HUD scales, compact radar, symmetric crosshair, readable team/buy menus and larger main/pause/settings menus.
- **Settings:** **Menu → Options → Nano settings** offers FPS-limit/frame-sleep toggles, an FPS slider, aiming/acceleration controls and separate HUD sliders. Choices save per game.
- **Audio:** source-built ALSA streaming and targeted speaker/volume initialization. Immediate sound startup is confirmed on the physical Nano.
- **Launch/recovery:** every launch applies **1200 MHz**; cleanup restores **1008 MHz** and firmware keys. **Fn + L + R** requests supervised shutdown.
- **Launcher entries:** `Half-Life (source)` and `Counter-Strike (source)`, with icons extracted locally from each game's `game.ico`.

Fresh assemblies default to **30 FPS in both games**, frame sleeping enabled and VSync disabled. The tested device has 30 FPS saved for Half-Life and 40 FPS for Counter-Strike. A cap is a maximum, not a guaranteed frame rate.

## Controls

| Button | Action |
|---|---|
| D-pad Up/Down | Walk forward/backward |
| D-pad Left/Right | Turn |
| Hold R + Up/Down | Look up/down |
| Hold R + Left/Right | Strafe |
| Hold L | Fast camera look |
| X / Y | Fire / reload |
| A / B | Use / jump |
| Hold Fn/Select | Crouch |
| Menu | Menu/back |
| Start | HL flashlight; CS buy menu |
| Fn + Start | HL next weapon; CS autobuy |
| Fn + L / R | HL quick-save / quick-load |
| Fn + L + R | Stop game and recover launcher |

CS numbers: **Fn + Left/Down/Right** selects **1/2/3**; **Fn + Start + L/R** selects **4/5**. Choose a team, then an appearance. CS cannot save an offline multiplayer round.

Firmware shortcuts remain: **Fn + A/Y** for volume, **Fn + X/B** for brightness and **Fn + Up** for screenshots. See [all controls](docs/CONTROLS.md) and [settings defaults](docs/NANO-SETTINGS.md).

## Build and install

Use Linux or Ubuntu under WSL with Python **3.12+**, Pillow, Git, CMake, Ninja, a native C compiler, squashfs-tools and ADB. Install **FunKey SDK 2.3.0** separately from the [FunKey OS releases](https://github.com/FunKey-Project/FunKey-OS/releases). Revisions and submodules are pinned in [sources.lock.json](sources.lock.json).

Run from the repository root:

```sh
sudo apt install git cmake ninja-build gcc squashfs-tools python3-pil adb
export FUNKEY_SDK=/absolute/path/to/FunKey-sdk-2.3.0
# Optional: a Linux filesystem speeds up native builds under WSL.
export NANO_NATIVE_DIR=/absolute/path/to/native-build

# CS libraries/menu, standalone renderer and launch helpers:
bash tools/build.sh
# Engine, filesystem, native renderer/menu and Half-Life libraries:
bash tools/build-native.sh

python3 tools/prepare_native.py \
  --games /absolute/path/to/your/Half-Life \
  --native-build "$NANO_NATIVE_DIR" \
  --sdk "$FUNKEY_SDK" \
  --font /absolute/path/to/FiraSans-Regular.ttf \
  --nav /absolute/path/to/your/de_dust.nav

# Quit either game, then connect the Nano in ADB mode:
python3 tools/install.py --native
```

The `--games` directory must contain `valve/` and `cstrike/`, including each `game.ico`. Supply a usable TrueType font; [Fira Sans](https://github.com/mozilla/Fira) is one option. `--nav` is optional, but without matching data bots may perform slow, memory-intensive map analysis. No NAV is supplied or downloaded.

Assembly requires a fresh output directory and creates `build/native-runtime/` plus launcher OPKs/icons in `build/native-dist/`. These private outputs include your game data and are excluded from Git. The OPKs are launchers, not standalone game packages.

Installation uses `/mnt/FunKey/Xash3D-source` and adds the `(source)` entries to Native games. Refresh that collection or restart the frontend to reload icons. A fresh assembly excludes personal saves; installation does not delete the existing device save directory. Keep assembled outputs private.

The runtime uses firmware libc, ALSA and hardware drivers. SDK dependencies are resolved during assembly; `source-runtime.json` records source pins, patch and component hashes. See [SOURCES.md](SOURCES.md) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

The earlier SDL/XASH3DFS setup remains separate under `/mnt/FunKey/Xash3D`. Instructions are in [LEGACY.md](docs/LEGACY.md).

## Validation and limits

Physical-device feedback confirms rendering, menus, movement, shooting, immediate audio, controls, HUD layout and the original CS skybox. Bounded runs cover CS deaths/spectating/respawns and reloads, and HL saves/loads and several campaign transitions. See [VALIDATION.md](docs/VALIDATION.md) and [regression checks](docs/TESTING.md) for evidence and scope.

These remain experimental ports on a device with very limited RAM. Loading and paging stalls persist. Full campaign coverage, arbitrary mods/maps and network multiplayer are not validated. Specialized dialogs and touch/gamepad editors retain upstream layouts. Targeted audio startup avoids the demonstrated broad mixer scan; the underlying firmware driver lock remains unresolved.

Texture changes remove unused menu/sprite/model mips and share identical converted buffers, saving approximately **27 MiB of tracked allocation** in the tested CS scene while retaining base pixels and world mipmaps. This is not a whole-process RAM or guaranteed FPS saving. Large cleared allocations avoid eagerly touching unused pages. Controlled load tests showed improved colder medians, with overlapping warm results. See [MEMORY.md](docs/MEMORY.md), [DEMAND-ZERO.md](docs/DEMAND-ZERO.md) and [LOAD-BENCHMARK.md](docs/LOAD-BENCHMARK.md).

Latest work: [original sky rendering](docs/SKYBOX.md) and [model/sound measurements](docs/MODEL-SOUND.md). The [roadmap](docs/ROADMAP.md) prioritizes animation-storage investigation and broader campaign checks before quality reductions.

## Recovery and diagnostics

Hold **Fn + L + R** to stop the game. The supervisor targets its own process group, sends TERM and escalates to KILL after five seconds if needed. Cleanup restores stock clock and firmware keys. Userspace recovery cannot guarantee recovery from a kernel lock.

Logs are under `diagnostics/valve` or `diagnostics/cstrike`: `engine.log`, resource samples in `metrics.csv`, and exit details in `result.txt`. Engine/metric logs retain two bounded files each. There is no automatic freeze detector. Review private logs before sharing.

Optional `NANO_PROFILE=1` enables frame timing without an overlay. Console commands `nano_mem` and `nano_tex` report pool/asset categories and texture storage on request, without allocation-chain scans or automatic gameplay reports. More detail: [performance](docs/PERFORMANCE.md) and [loading/audio](docs/LOADING-AUDIO.md).

## License and credits

Support tools and menu integration are GPL-3.0-or-later. Small aiming, HUD, crosshair, frame-statistics, texture-sharing, sky-projection and numeric-settings helpers are MIT, as marked in each file. Upstream code retains its applicable licenses. Half-Life SDK code remains under Valve's SDK terms, including free distribution and required notices. See [LICENSE](LICENSE), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), [SOURCES.md](SOURCES.md) and `licenses/`.

Credits: FWGS/Xash3D and HLSDK Portable contributors; Velaron/CS16Client; ReGameDLL_CS; FunKey-Project and firmware maintainers; DankMiimer/NanoCraft for the clock helper; and Sn3zee-cmds/XASH3DFS for the original packaged port that started this work. This independent project is unaffiliated with Valve or Anbernic.
