# RG Nano Xash3D support project

Open-source launchers, controls, build recipes and source patches for running Half-Life and Counter-Strike on an RG Nano with FunKeyOS/DrUm78 firmware.

**This repository is a support project, not a complete open-source distribution of the installed games or the original Nano engine port.** It contains no commercial game data, extracted game icons, fonts, navigation files or prebuilt runtime libraries. Supply your own game installation and the separately obtained XASH3DFS base package. See [SOURCES.md](SOURCES.md) for exact provenance and the remaining source-availability gap.

## Current behavior

- Separate Half-Life and Counter-Strike entries in Native games, with icons extracted locally from each game's `game.ico`.
- D-pad walks/turns; L/R strafe; Y shoots; A uses; B jumps; X reloads.
- HUD scale 0.65 for the Nano's 240×240 display.
- Launchers set 1200 MHz and restore 1008 MHz when the game process exits.
- Half-Life launches the opening campaign directly with the current launcher settings.
- Counter-Strike launches an offline de_dust match with two easy bots, one-minute rounds and spectator picture-in-picture disabled.
- Private Nano SDL library uses ALSA's `default` device; firmware libraries are not overwritten.
- The user confirmed menu navigation and sound work correctly on the device.
- Software renderer permits 4096 textures and clips off-screen HUD graphics before accessing the framebuffer.

See [CONTROLS.md](docs/CONTROLS.md) and [VALIDATION.md](docs/VALIDATION.md). These remain experimental ports: HUD graphics have rendering defects, and extended campaign/multiplayer stability has not been established.

## Build the source components

Use Linux or Ubuntu under WSL, Python 3.12+, Pillow, Git, CMake, Ninja, a native C compiler, squashfs-tools, and ADB. Install the [FunKey SDK 2.3.0](https://github.com/FunKey-Project/FunKey-OS/releases) separately.

```sh
sudo apt install git cmake ninja-build gcc squashfs-tools python3-pil adb
export FUNKEY_SDK=/absolute/path/to/FunKey-sdk-2.3.0
bash tools/build.sh
```

The script fetches commits pinned in [sources.lock.json](sources.lock.json), applies the patches, then builds the ARM hard-float CS client/server, software renderer and two launch helpers. It does **not** rebuild the original Nano engine or Half-Life client/server: those still come from the external base OPK.

The Counter-Strike patch admits the base port's legacy build marker 4141 while retaining render-interface version checks. This is an experimental compatibility adjustment, not proof of full API compatibility.

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

## Check renderer clipping

After fetching sources:

```sh
python3 tests/test_renderer_clipping.py
gcc -O1 -g -fsanitize=address,undefined build/tests/renderer-clipping-test.c -o build/tests/renderer-clipping-test
build/tests/renderer-clipping-test
```

This exercises the actual renderer function with normal, fully off-screen, zero-size and edge-clipped rectangles, checking framebuffer guards and texture sampling.

## License and credits

New support code is GPL-3.0-or-later. Existing upstream code, patches and components retain their applicable licenses and notices; see [LICENSE](LICENSE), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [SOURCES.md](SOURCES.md). The GPL grant for this repository does not license Valve game data, extracted artwork, third-party fonts, or binaries with unestablished corresponding source.

Credits: Sn3zee-cmds/XASH3DFS; FWGS/Xash3D and its contributors; Velaron/CS16Client and its contributors; ReGameDLL_CS; FunKey-Project and firmware maintainers; and DankMiimer/NanoCraft for the clock helper. This is an independent project, unaffiliated with Valve or Anbernic.
