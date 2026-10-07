# Where the files came from

The current framebuffer ports independently build the engine, renderer, filesystem, menus and HL/CS libraries from pinned public source. They do not consume the XASH3DFS package. Source pins and the historic base-package digest are in [sources.lock.json](sources.lock.json). Rendering, controls, immediate audio, saves/loads, bounded transitions and original CS sky rendering have passed the checks described in [VALIDATION.md](docs/VALIDATION.md). Game data remain user-supplied.

The table below records the original legacy installation; the [independent native recipe](#independent-native-recipe) describes the current ports.

| Component in the installation | Origin | What this repository publishes |
|---|---|---|
| Base `xash3d`, `libxash.so`, filesystem library, menu library and bundled dependencies | [Sn3zee-cmds/XASH3DFS](https://github.com/Sn3zee-cmds/XASH3DFS), `xash3dfs` release, `XASH3DFS.opk.-.LATEST` | Base-package reference, digest check and local assembly script; no binaries |
| Half-Life ARM client/server libraries | The same external OPK | No binaries; corresponding port source has not been established |
| Counter-Strike ARM client and server | [Velaron/cs16-client](https://github.com/Velaron/cs16-client) at `e30e27c3bd890f731ad7921d9c876d171aea4b32`, built with FunKey SDK 2.3.0 | Version-compatibility and spectator-inset policy patches plus build recipe; upstream sources fetched at build time |
| ReGameDLL_CS, mainui_cpp, MiniUTL and YaPB source dependencies | Pinned submodules of that CS16Client commit | Submodule references; no vendored source trees. YaPB was built during exploration but is not activated or installed by this recipe |
| Software renderer | [FWGS/xash3d-fwgs](https://github.com/FWGS/xash3d-fwgs) at `e3e459bb6735c9e6a6bf18658f637bc71cdc73df` | Texture-capacity/clipping and triangle-winding/culling patches, standalone build recipe and geometry tests |
| Private SDL library | Nano firmware's `/usr/lib/libSDL-1.2.so.0` | Recipe which copies it locally and changes the embedded ALSA device string; no firmware binary |
| Automatic overclock helper | [DankMiimer/nanocraft/src/nano-clk.c](https://github.com/DankMiimer/nanocraft/blob/8e4c9a88726a69b1fc90110767d3cc630e740330/src/nano-clk.c) | Original GPL helper source and credit; file digest recorded |
| Launchers, controls, RNG helper and build/installation tools | Created for this setup | Source under GPL-3.0-or-later |
| Half-Life and Counter-Strike maps, models, textures, sounds and game icons | User's installed Steam copies, `valve/` and `cstrike/` | No assets; icons are extracted locally from `game.ico` |
| Font used in the initial device setup | User's local Windows Tahoma font, copied under the font filenames expected by the port | No font. The public recipe accepts a user-supplied font, preferably freely licensed Fira Sans |
| de_dust NAV used in the initial setup | [phamvanhiepvn/cs](https://github.com/phamvanhiepvn/cs/blob/master/cstrike/maps/de_dust.nav), matching a 1,359,684-byte BSP | No NAV and no automatic download. Its redistribution license was not established |
| CA trust bundle | Local Linux system certificate bundle | No bundle; optional local assembly copy |

## Limits of the open-source claim

At the time of preparation, the XASH3DFS repository exposes a README, packaged OPK and icon, rather than the corresponding Nano port source. The upstream FWGS revision supplies the renderer source used here, but does not establish that it is complete corresponding source for the modified Nano engine or the supplied Half-Life libraries.

Accordingly, this repository is openly licensed **support code and patches**. It does not claim to relicense the entire installed runtime. Game assets are excluded from Git and from releases. Releases contain only the independently built native runtime described below; nothing from the XASH3DFS package is redistributed. The legacy assembly still has that limitation. The separate native recipe reconstructs the hardware support from upstream source and small published patches; hardware checks now cover rendering, controls, audio and bounded gameplay. Extended campaign and network coverage remain incomplete.

The assembly recipe patches two exact binary strings locally: `/dev/random` becomes a launcher-created `/tmp/xash-r` symlink to `/dev/urandom`, and the private Nano SDL's `/dev/dsp` device name becomes ALSA `default`. It deliberately rejects unexpected input strings rather than guessing offsets.

There are no Steam credentials, account files, personal saves, RNG seeds, device identifiers or machine-specific paths in the published source.

## Independent native recipe

| Component | Source and treatment |
|---|---|
| Engine, filesystem, software renderer and default menu | FWGS/xash3d-fwgs at the pinned renderer revision; gitlink-pinned submodules; published framebuffer, musl timer, Linux entropy, evdev input-record, console logging and ALSA streaming patches |
| Half-Life ARM client/server | FWGS/hlsdk-portable at `9c45ba22fba98517fdd303d446c78dafcf74fd07`; Valve SDK notice retained in `licenses/hlsdk-portable.txt` |
| bzip2, Ogg/Vorbis, C++ and GCC runtime dependencies | FunKey SDK 2.3.0 sysroot, resolved recursively by ELF NEEDED entries during private assembly; no OPK libraries or SDL used |
| musl libc, ALSA and hardware drivers | Existing FunKeyOS firmware; ALSA uses the device’s existing output stack |
| Commercial resources, icons, font and optional NAV | Same user-supplied inputs as above; no assets published |

`source-runtime.json` in each private native assembly records component/dependency hashes and that no external OPK was used. This documents the new build's provenance; it does not assert that it reproduces Sn3zee's implementation. Upstream credits remain intact, and no private port binary is reverse-engineered into the new engine.

The Half-Life pin precedes the September 2026 freevgui SetPaintOffset extension, which the August engine does not implement. Engine and client revisions must be aligned when updating either.

## Public releases

`tools/package_release.py` builds the release zip from a committed revision. Releases are built outside any home folder, so compiled-in source paths name no user; the packager checks this.

| Release content | Source and treatment |
|---|---|
| Engine, filesystem, renderer, menus, HL and CS libraries, Nano helper tools | Built from the pins and patches above with FunKey SDK 2.3.0, then `strip --strip-unneeded`. `source-runtime.json` records the commit, pins, patch hashes and component hashes |
| SDK runtime libraries | FunKey SDK 2.3.0 sysroot, resolved by ELF NEEDED entries; licence texts in `licenses/runtime/` |
| Menu font | Wine's Tahoma at `wine-10.0`, pinned by SHA-256 in `sources.lock.json`; its `.sfd` source and LGPL/Bitstream Vera licences ship in the zip |
| Launcher icons | Plain placeholder drawn by `tools/make_icons.py`; replaced on the console by the icon in the player's own `game.ico` |
| Menu artwork | Not shipped. Built on the console at first launch from the player's own files by `src/nano-art.c`; output matches `tools/prepare_menu_art.py` byte for byte |
| Engine `extras.pk3` | FWGS/xash-extras as built by the engine, unchanged |
| Counter-Strike `extras.pk3` | Only `userconfig.d/` from CS16Client's `cs16client-extras`; its Condition Zero bot voices, bot/chatter databases, training maps and sounds, menu bitmaps and sounds are dropped |
| Counter-Strike `BotProfile.db` | Original bot names and personalities, `assets/cstrike/BotProfile.db` |
| Valve intro, NAV files, game data, saves, RNG seed | Not shipped |

The packager refuses to finish if the zip contains game-data file types, a font other than the pinned one, or the builder's user name or home path.

## Nano aiming and HUD changes

`src/nano-look.h`, `nano-hud-transform.h`, `nano-hud-scope.h`, `nano-crosshair.h` and `nano-frame-stats.h` are newly written helpers under MIT (notices in each file). Client, engine and menu patches retain the upstream files' licenses. Corresponding menu patches apply to both gitlink-pinned mainui submodules: FWGS engine's default menu and CS16Client's game-specific menu. No external HUD artwork, replacement font, controller mod or proprietary-game source was copied. The research document links behavior and layout references.

The bounded frame statistics helper records elapsed frame intervals and processing time through an opt-in engine hook. It does not copy an external profiler. Menu settings changes rearrange the existing controls and reuse their original callbacks and menu face.

`src/nano-settings.h` is a newly written MIT helper for bounded numeric preferences and serialization. `src/nano-menu-options.h` integrates it with upstream menu controls under GPL-3.0-or-later. The settings UI uses existing sliders, checkboxes and artwork, with no copied external mod code or assets.

`src/nano-texture-share.h` is a newly written MIT helper for sharing immutable byte-identical buffers with reference counting. Its software-renderer integration retains the upstream GPL license. It compares final converted pixels, including alpha storage, without importing an external texture-sharing implementation or publishing game images.

`src/nano-skybox.h` is a newly written MIT cube-projection helper matching the pinned engine's original sky orientation. The software renderer samples user-supplied sky textures already loaded by the engine; no replacement sky artwork or external mod implementation was copied.
