# Legacy XASH3DFS installation

This path retains the externally packaged engine and Half-Life libraries. The current [source-built ports](../README.md) do not require it. This separate installation uses `/mnt/FunKey/Xash3D`; [SOURCES.md](../SOURCES.md) documents its source-availability limitation.

Run `bash tools/build.sh` from the repository root with the FunKey SDK configured first. It builds the CS libraries, standalone renderer and helpers, but does not rebuild the external engine or Half-Life libraries.

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
