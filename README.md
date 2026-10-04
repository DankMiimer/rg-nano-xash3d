# RG Nano Xash3D support project

Open-source launchers, controls, build recipes and source patches for running Half-Life and Counter-Strike on an RG Nano with FunKeyOS/DrUm78 firmware.

**This repository is a support project, not a complete open-source distribution of the installed games or the original Nano engine port.** It contains no commercial game data, extracted game icons, fonts, navigation files or prebuilt runtime libraries. Supply your own game installation. The established SDL runtime uses the separately obtained XASH3DFS base package; an experimental framebuffer runtime builds the engine and Half-Life libraries from pinned upstream source without that package. See [SOURCES.md](SOURCES.md) for exact provenance and the remaining source-availability gap.

## Current behavior

- Separate Half-Life and Counter-Strike entries in Native games, with icons extracted locally from each game's `game.ico`.
- D-pad walks/turns; hold R for vertical look and strafing; precise camera speed by default, hold L for three times faster look. X shoots; A uses; B jumps; Y reloads.
- Source-built profile adds horizontal hold acceleration, independently scaled original HUD groups, half-size CS radar, a pixel-symmetric crosshair and larger main/pause/settings menus on the Nano's 240×240 display.
- Source-built renderer avoids unused menu/sprite/model mipmaps and replaces texture-update storage correctly, reducing CS tracked allocations by approximately 10 MiB in the tested scene. Original base pixels and world mipmaps are retained; see [memory measurements](docs/MEMORY.md).
- Software profiles explicitly disable VSync so the configured 30 FPS cap is respected.
- Source-built **Options → Nano settings** provides FPS-limit/frame-sleep toggles, an FPS slider, camera speed/acceleration controls and separate HUD size sliders. Choices save per game; see [Nano settings](docs/NANO-SETTINGS.md).
- Launchers set 1200 MHz and restore 1008 MHz when the game process exits.
- Half-Life launches the opening campaign directly with the current launcher settings.
- Counter-Strike launches an offline de_dust match with two easy bots, one-minute rounds and spectator picture-in-picture prevented from being re-enabled by the Use button.
- Private Nano SDL library uses ALSA's `default` device; firmware libraries are not overwritten.
- The user confirmed menu navigation and sound on the established ports, and movement, shooting and sound on source-built Counter-Strike.
- Software renderer permits 4096 textures and clips off-screen HUD graphics before accessing the framebuffer.

See [CONTROLS.md](docs/CONTROLS.md), [VALIDATION.md](docs/VALIDATION.md) and the [controller/HUD reuse research](docs/HUD-CONTROLLER-RESEARCH.md). These remain experimental ports: specialized dialogs and extended campaign/multiplayer stability remain under development.

## Build the source components

Use Linux or Ubuntu under WSL, Python 3.12+, Pillow, Git, CMake, Ninja, a native C compiler, squashfs-tools, and ADB. Install the [FunKey SDK 2.3.0](https://github.com/FunKey-Project/FunKey-OS/releases) separately.

```sh
sudo apt install git cmake ninja-build gcc squashfs-tools python3-pil adb
export FUNKEY_SDK=/absolute/path/to/FunKey-sdk-2.3.0
bash tools/build.sh
```

The script fetches commits pinned in [sources.lock.json](sources.lock.json), applies the patches, then builds the ARM hard-float CS client/server, software renderer and three launch helpers. It does **not** rebuild the original Nano engine or Half-Life client/server: those still come from the external base OPK.

The Counter-Strike patch admits the base port's legacy build marker 4141 while retaining render-interface version checks. This is an experimental compatibility adjustment, not proof of full API compatibility.

## Experimental source-built runtime

The native recipe builds the Xash3D engine, filesystem, software renderer, menu and ARM Half-Life client/server from source. It uses Linux framebuffer, evdev and ALSA directly. It does not consume the original XASH3DFS OPK, its Half-Life libraries, or the Nano SDL library. The same source-built CS components are used for Counter-Strike. Build the regular components above first, then:

```sh
# Optional: choose a persistent Linux build directory for faster WSL builds.
export NANO_NATIVE_DIR=/absolute/path/to/native-build
bash tools/build-native.sh
python3 tools/prepare_native.py \
  --games /absolute/path/to/your/Half-Life \
  --native-build "$NANO_NATIVE_DIR" \
  --sdk "$FUNKEY_SDK" \
  --font /absolute/path/to/FiraSans-Regular.ttf \
  --nav /absolute/path/to/your/de_dust.nav
```

The source-built engine now renders and accepts controls in both games; Half-Life audio and Counter-Strike movement, firing and audio have been confirmed on hardware. Extended stability remains unverified.

Assembly resolves shared-library dependencies from the SDK and records their hashes. FunKeyOS supplies musl libc and its established ALSA output stack; Valve assets, fonts and optional navigation remain user-supplied. The default output is `build/native-runtime`, intended for `/mnt/FunKey/Xash3D-source`. This is a separate test installation. `python3 tools/install.py --native` adds entries labelled `(source)`; normal `install.py` updates the established legacy runtime. Do not switch normal game entries until hardware display, controls, sound and gameplay have passed comparison checks.

Half-Life SDK code is source-available under Valve's SDK license, which permits free distribution and requires notices; it is not covered by this project's GPL. See `licenses/hlsdk-portable.txt`. Building from public source removes the unknown base-binary dependency, but does not make the commercial games or every component uniformly open source.

## Assemble a private installation

Obtain the exact [XASH3DFS base release](https://github.com/Sn3zee-cmds/XASH3DFS/releases/download/xash3dfs/XASH3DFS.opk.-.LATEST) separately. Its expected SHA-256 is recorded in the lock file and checked by the assembly script.

Copy the Nano's own SDL library before assembly:

```sh
mkdir -p build
adb pull /usr/lib/libSDL-1.2.so.0 build/nano-sdl.so
python3 tools/prepare_runtime.py \
  --games /absolute/path/to/your/Half-Life \
  --opk /absolute/path/to/XASH3DFS.opk.-.LATEST \
  --device-sdl build/nano-sdl.so \
  --font /absolute/path/to/FiraSans-Regular.ttf \
  --nav /absolute/path/to/your/de_dust.nav
```

The `--games` folder must contain `valve/` and `cstrike/`. Prefer a freely licensed font such as [Fira Sans](https://github.com/mozilla/Fira). The optional NAV must match your de_dust BSP; without it, the bots may perform a slow, resource-intensive navigation analysis on first use. No NAV is supplied or downloaded by this project.

Assembly creates `build/runtime/`, launcher OPKs and PNGs in `build/dist/`, and a fresh per-install RNG seed. These are private outputs containing third-party and commercial material; the repository excludes them. Start in a fresh build workspace when assembling again.

To extract/repackage only the icons and launchers:

```sh
python3 tools/extract_icons.py --games /absolute/path/to/your/Half-Life
bash tools/package.sh
```

Generated OPKs are tiny launchers which require `/mnt/FunKey/Xash3D` on the SD card. They are not standalone game packages.

## Install

Quit either game on the Nano, connect it in ADB mode, then:

```sh
python3 tools/install.py
```

An existing save directory is retained. Runtime files, controls and launcher entries are updated. Refresh Native games or restart the frontend to reload cached icons. To use a different tested clock, edit `/mnt/FunKey/Xash3D/cpu-mhz`; the launcher reads it at every start. The default is 1200 MHz.

## Recovery and diagnostics

At startup, the launcher reapplies saved system volume and enables the speaker amplifier, respecting volume zero. Built-in speaker restoration targets two quiet ALSA controls to avoid a broad mixer scan; USB audio retains the firmware policy. See [audio startup and loading peaks](docs/LOADING-AUDIO.md). It runs the game under `nano-supervise-arm`. Hold **Fn + L + R** to request shutdown. The supervisor resumes a stopped child, sends TERM to its own process group, and escalates to KILL after five seconds if needed. The launcher then restores the stock clock and default keys. This covers ordinary crashes and userspace hangs; it does not guarantee recovery from a kernel or device-driver lockup.

Diagnostics are under `diagnostics/valve` or `diagnostics/cstrike` inside the runtime. `engine.log` captures output, `metrics.csv` samples RAM/swap/page faults/CPU counters every two seconds, and `result.txt` records exit status, termination signals and crash signals printed by Xash's own handler (which can otherwise exit with code zero). Engine and metric logs keep two files of at most 512 KiB each. There is no automatic freeze detector; recovery is user-triggered.

Source-built games also sleep between capped frames to reduce busy-waiting. Optional `NANO_PROFILE=1` reports frame timing without an on-screen overlay. See [performance measurements and remaining limits](docs/PERFORMANCE.md), the [longer hardware stability checks](docs/STABILITY.md) and [texture memory reductions](docs/MEMORY.md) and [large cleared allocations](docs/DEMAND-ZERO.md).

```sh
gcc -O2 -Wall -Wextra -Werror src/nano-supervise.c -o /var/tmp/rg-nano-supervise-host
python3 tests/test_supervisor.py
# After build-native.sh (uses NANO_NATIVE_DIR if set):
python3 tests/test_alsa_ring.py
python3 tests/test_renderer_triangles.py
python3 tests/test_nano_menu.py
python3 tests/test_nano_settings.py
python3 tests/test_nano_options.py
python3 tests/test_nano_frame_stats.py
python3 tests/test_nano_texture_memory.py
gcc -std=c99 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined \
  -Isrc tests/test_nano_texture_share.c -o build/tests/nano-texture-share
build/tests/nano-texture-share
python3 tests/test_nano_memory_report.py
python3 tests/test_nano_memory_peak.py
python3 tests/test_nano_demand_zero.py
python3 tests/test_nano_audio_start.py
```

## Check renderer clipping

After fetching sources:

```sh
python3 tests/test_renderer_clipping.py
gcc -O1 -g -fsanitize=address,undefined build/tests/renderer-clipping-test.c -o build/tests/renderer-clipping-test
build/tests/renderer-clipping-test
```

This exercises the actual renderer function with normal, fully off-screen, zero-size and edge-clipped rectangles, checking framebuffer guards and texture sampling.

## License and credits

Support tools and the menu integration in `src/nano-menu-options.h` are GPL-3.0-or-later; the small aiming/HUD, frame statistics, texture sharing and numeric settings helpers are MIT, as marked in each file. Existing upstream code, patches and components retain their applicable licenses and notices; see [LICENSE](LICENSE), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [SOURCES.md](SOURCES.md). The GPL grant for this repository does not license Valve game data, extracted artwork, third-party fonts, or binaries with unestablished corresponding source.

Credits: Sn3zee-cmds/XASH3DFS; FWGS/Xash3D and its contributors; Velaron/CS16Client and its contributors; ReGameDLL_CS; FunKey-Project and firmware maintainers; and DankMiimer/NanoCraft for the clock helper. This is an independent project, unaffiliated with Valve or Anbernic.
