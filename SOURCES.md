# Where the files came from

This documents the installation from which the support recipes were developed. Exact source commits and the base OPK digest are in [sources.lock.json](sources.lock.json).

| Component in the installation | Origin | What this repository publishes |
|---|---|---|
| Base `xash3d`, `libxash.so`, filesystem library, menu library and bundled dependencies | [Sn3zee-cmds/XASH3DFS](https://github.com/Sn3zee-cmds/XASH3DFS), `xash3dfs` release, `XASH3DFS.opk.-.LATEST` | Base-package reference, digest check and local assembly script; no binaries |
| Half-Life ARM client/server libraries | The same external OPK | No binaries; corresponding port source has not been established |
| Counter-Strike ARM client and server | [Velaron/cs16-client](https://github.com/Velaron/cs16-client) at `e30e27c3bd890f731ad7921d9c876d171aea4b32`, built with FunKey SDK 2.3.0 | Source patch and build recipe; upstream sources fetched at build time |
| ReGameDLL_CS, mainui_cpp, MiniUTL and YaPB source dependencies | Pinned submodules of that CS16Client commit | Submodule references; no vendored source trees. YaPB was built during exploration but is not activated or installed by this recipe |
| Software renderer | [FWGS/xash3d-fwgs](https://github.com/FWGS/xash3d-fwgs) at `e3e459bb6735c9e6a6bf18658f637bc71cdc73df` | Texture-capacity/clipping patch, standalone build recipe and clipping test |
| Private SDL library | Nano firmware's `/usr/lib/libSDL-1.2.so.0` | Recipe which copies it locally and changes the embedded ALSA device string; no firmware binary |
| Automatic overclock helper | [DankMiimer/nanocraft/src/nano-clk.c](https://github.com/DankMiimer/nanocraft/blob/8e4c9a88726a69b1fc90110767d3cc630e740330/src/nano-clk.c) | Original GPL helper source and credit; file digest recorded |
| Launchers, controls, RNG helper and build/installation tools | Created for this setup | Source under GPL-3.0-or-later |
| Half-Life and Counter-Strike maps, models, textures, sounds and game icons | User's installed Steam copies, `valve/` and `cstrike/` | No assets; icons are extracted locally from `game.ico` |
| Font used in the initial device setup | User's local Windows Tahoma font, copied under the font filenames expected by the port | No font. The public recipe accepts a user-supplied font, preferably freely licensed Fira Sans |
| de_dust NAV used in the initial setup | [phamvanhiepvn/cs](https://github.com/phamvanhiepvn/cs/blob/master/cstrike/maps/de_dust.nav), matching a 1,359,684-byte BSP | No NAV and no automatic download. Its redistribution license was not established |
| CA trust bundle | Local Linux system certificate bundle | No bundle; optional local assembly copy |

## Limits of the open-source claim

At the time of preparation, the XASH3DFS repository exposes a README, packaged OPK and icon, rather than the corresponding Nano port source. The upstream FWGS revision supplies the renderer source used here, but does not establish that it is complete corresponding source for the modified Nano engine or the supplied Half-Life libraries.

Accordingly, this repository is openly licensed **support code and patches**. It does not claim to relicense the entire installed runtime. Third-party compiled runtime libraries and game assets are excluded from Git and from repository releases. A fully source-buildable Nano port would require obtaining or reconstructing the missing port-specific source and confirming its dependencies and licenses.

The assembly recipe patches two exact binary strings locally: `/dev/random` becomes a launcher-created `/tmp/xash-r` symlink to `/dev/urandom`, and the private Nano SDL's `/dev/dsp` device name becomes ALSA `default`. It deliberately rejects unexpected input strings rather than guessing offsets.

There are no Steam credentials, account files, personal saves, RNG seeds, device identifiers or machine-specific paths in the published source.
