# Counter-Strike offline match setup

The source-built CS launcher opens match setup before loading a map. **Menu → Offline match** returns to it during play. Starting another match asks before ending the current round. Network play remains available from the setup page; this menu creates a local bot match rather than an online matchmaking service.

Use Up/Down to select, Left/Right to change a choice, A to activate Start or toggle a checkbox, and Menu to go back. The existing 240×240 layout scrolls to keep the focused row visible.

## Choices

- **Map:** installed `maps/*.bsp` files, alphabetically sorted, including custom maps with simple names. The list supports up to 256 maps and ignores unsafe names and duplicate entries; it does not depend on `maps.lst`.
- **Bots:** 0–7 total across the selected teams. Two remains the recommended count. Four or more is unmeasured on the Nano and shows a performance warning. The server has eight slots, including the human player; actual bot population also depends on available team spawn points.
- **Difficulty:** the four original Easy/Normal/Hard/Expert levels. Easy is the default.
- **Bot teams:** both teams, Terrorists only, or Counter-Terrorists only. For enemies-only play, choose the opposing human team at the ordinary team prompt. One-sided bot placement disables auto-balancing and the team difference limit.
- **Advanced:** mixed weapons, pistols, pistols + SMGs, or knives; round length 1–9 minutes; freeze time 0–10 seconds; starting money $800–$16,000; friendly fire; walking bots; optional NAV analysis.

Preferences save to `cstrike/nano-match.cfg` as bounded data. They are not executed as console commands. Changes configure the next match; the current match continues with its existing rules until Start. The generated `nano-offline.cfg` is applied by `listenserver.cfg` when the new server spawns. Defaults are two Easy bots, mixed weapons, both teams, three-minute rounds, one second freeze, $16,000, friendly fire off, and analysis off.

The extra Nano easier modes have been removed. Legacy Target practice through Easy become stock Easy; Normal, Hard and Expert retain their stock levels. Version 2 preferences use four-level numbering. Other saved choices are preserved. Generated configuration resets `bot_zombie`; the server uses original bot aim and firing behavior.

## Maps and bot navigation

Every discovered map is selectable with zero bots. Bot matches need matching CS NAV data. A missing NAV shows **No NAV: bots 0 or Advanced** and blocks Start until bots are set to zero or analysis is explicitly enabled. If a present NAV fails the server's loader, automatic analysis is also blocked by default and bots are disabled with a console message. Analysis can be slow and memory intensive on the Nano; importing already generated matching data is preferable.

The menu checks NAV presence. The server validates the full format and map compatibility. The private device also has the completed `de_nuke` NAV from the user’s analysis run. Other maps still require compatible navigation data.

Assembly now accepts `--nav-directory /path/to/your/navs` to import NAV files for multiple maps. Alternatively, prepare an update locally:

```sh
python3 tools/import_navs.py --source /path/to/your/navs --maps /path/to/private/runtime/cstrike/maps
```

The importer accepts CS NAV versions 4/5 with magic `0xFEEDFACE` and a stored BSP size matching the supplied map. It copies matching files unchanged and reports skipped files. Header validation does not prove the remaining payload is complete; the engine remains the full validator. YaPB `.graph` files and modern Source-game NAVs are incompatible. No navigation files or commercial map assets are included or automatically fetched by this feature.

## Controls

CS **Fn+L** now holds secondary fire (zoom, silencer, alternate attacks); **Fn+R** immediately levels the view while retaining the horizontal direction. The CS client registers a Nano-specific command because this Xash input backend lacks a working stock centerview command. These replace CS's unusable multiplayer quick-save/load commands. Half-Life retains Fn+L/R quick-save/load. Existing system and supervisor shortcuts remain in the generated firmware keymap.

The optional [face-button controls](CONTROLS.md) add D-pad selection, A confirm and B back in CS team/buy text menus.

## Validation status

Host checks cover actual menu callbacks, four stock difficulties, legacy migration, bounded inputs, NAV opt-in, startup order and patch application. Input-router checks cover simultaneous buttons, held-button transitions and actual CS team/buy text-menu selection under sanitizers. See [Validation](VALIDATION.md) for build/device evidence and limits.
