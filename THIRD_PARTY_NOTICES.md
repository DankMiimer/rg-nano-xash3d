# Third-party notices

- **NanoCraft clock helper:** `src/nano-clk.c` is copied unchanged from DankMiimer/NanoCraft, whose repository supplies the GPL v3 license. The pinned commit and SHA-256 are recorded in the source lock. Retain its source comments and the GPL notice when redistributing it.
- **HLSDK Portable:** the native Half-Life libraries are built from FWGS/hlsdk-portable under Valve's Half-Life 1 SDK license. Its complete notice is in `licenses/hlsdk-portable.txt`. Distribution is free only, with the required notices; this is not a GPL relicensing.
- **Xash3D FWGS engine and software renderer:** source headers identify Uncle Mike and FWGS contributors and license the renderer under GPL-3.0-or-later. The renderer patch retains that license. Upstream has additional file-level licenses; fetching it does not relicense those files.
- **CS16Client:** GPL-2.0-or-later with its existing Valve linking exception. The source patch is provided under GPL-3.0-or-later as permitted by the upstream later-version option; the upstream exception is retained for the affected client code. Its license file also contains Valve SDK terms; the complete upstream notice is in `licenses/CS16Client.txt`. The repository's GPL does not replace those terms.
- **ReGameDLL_CS:** the pinned submodule's current license is MIT. Its license and transition notice are in `licenses/`; historical licensing must not be inferred from older releases.
- **Other source dependencies:** mainui_cpp, MiniUTL and YaPB retain their upstream licenses and notices. Build tools fetch pinned submodules without copying them into this repository. Consult each downloaded source tree before redistributing compiled components.
- **SDL and firmware dependencies:** no binary copies are included. SDL 1.2 and the Nano-specific modifications are third-party material; a binary patch recipe does not supply the corresponding firmware source or change its license.
- **External XASH3DFS OPK:** no runtime binary, artwork or bundled game data is included. Its port-specific corresponding source has not been established; see `SOURCES.md`.
- **Valve game assets and artwork:** not included and not covered by this repository's GPL. Icons are extracted only during local assembly from the user's game installation.
- **Fonts and navigation data:** not included. A user must supply these separately with rights appropriate to their intended use.

No third-party names or logos imply endorsement. The repository provides source and build instructions, not a grant to redistribute an assembled commercial game installation.
