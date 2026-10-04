# Stability measurements

Device checks on 2026-10-03–04 used the independent source-built runtime at 240×240, 1200 MHz and the accepted aiming/HUD settings. Counter-Strike's saved cap was 40 FPS; Half-Life's was 30. The main CS and HL runs provided over 24 minutes of combined process continuity. This is a bounded hardware check, not evidence of full campaign or multiplayer reliability.

## Counter-Strike

The controlled run lasted 681 seconds, with two easy bots on de_dust. Server logs recorded ten round starts and four deliberate player suicides across separate rounds. A/Use was pressed after each death, and first-person/bird's-eye spectator modes were requested. Timing and resource samples continued advancing with the same engine process. The inset remained disabled (`spec_pip_internal 0`). Supervised shutdown recorded a requested TERM, no engine crash signal and no forced KILL; the frontend returned and the clock restored to 1008 MHz.

| Measured phase | FPS | Engine CPU | Peak RSS (KiB) | Minimum available RAM (KiB) | Largest frame (ms) |
|---|---:|---:|---:|---:|---:|
| Initial play at cap 40 | 39.55 | 68.9% | 42,456 | 4,980 | 106.35 |
| First death/spectator period | 39.72 | 69.3% | 42,076 | 5,288 | 80.55 |
| Second death/spectator period | 38.86 | 87.0% | 41,348 | 5,428 | 162.00 |
| Third death/spectator period | 39.47 | 78.1% | 41,260 | 5,376 | 75.07 |
| Fourth death/spectator period | 36.85 | 94.4% | 41,504 | 5,180 | 261.24 |
| Following period, temporary cap 30 | 29.97 | 59.0% | 41,544 | 5,408 | 40.46 |

These are adjacent gameplay periods, not deterministic replays: bots, camera targets, rendering work and swap/cache state vary. The final 30 FPS comparison did not change the saved 40 FPS preference. RSS did not grow monotonically after deaths, but these samples cannot rule out slower leaks. Paging continued; system-wide swap counters do not identify which process caused every page transfer.

A previous ordinary CS process had remained alive for about nineteen minutes before the controlled restart. Its samples reached as little as 716 KiB available RAM. Frame profiling was off and its gameplay states were not recorded, so it is weaker stability evidence and is excluded from the table.

## Half-Life

The same engine process remained active through 792 seconds of captured resource samples. The tram crossed c0a0 through c0a0d naturally. Two temporary save slots were created and three loads were verified in the engine log. A separate `map c1a0` command exercised campaign assets beyond the tram; this was a map reset, not a campaign transition. A normal change to c1a0d and a landmark-preserving `changelevel2` back to c1a0 also completed. The user confirmed audible tram sound without adjusting system volume. The user later restarted the device and switched frontends; that ending is excluded from supervised-exit claims.

| Measured phase | FPS | Engine CPU | Peak RSS (KiB) | Minimum available RAM (KiB) | Largest frame (ms) |
|---|---:|---:|---:|---:|---:|
| Tram and natural transition | 28.87 | 45.4% | 42,388 | 4,348 | 1,524.98 |
| First save/load period | 28.38 | 64.8% | 39,948 | 10,124 | 1,854.36 |
| Second save/load period | 29.94 | 64.5% | 41,528 | 7,896 | 47.36 |
| Station save/load aftermath | 29.99 | 53.3% | 36,076 | 15,128 | 39.14 |
| Adjacent level observation | 29.99 | 37.0% | 36,076 | 14,912 | 39.12 |
| After landmark return | 30.00 | 36.5% | 35,836 | 15,536 | 34.31 |

The station save/load aftermath included an open console, so its CPU figure is not a clean gameplay comparison. The normal adjacent change reported a 921.67 ms maximum interval and the landmark return 814.57 ms in boundary windows outside the table's complete-window calculation. These loads recovered to roughly 30 FPS; their stalls remain real. Initial loading is also excluded from steady-play FPS. Missing first-visit neighboring `.HL1` cache messages were followed by successful game startup and advancing frame samples.

## Navigation path correction

The original run warned that its NAV belonged to another map version even though both the file header and installed BSP reported 1,359,684 bytes. ReGameDLL's BSP-size query constructed a Windows-style `maps\\de_dust.bsp` path; the pinned filesystem's direct size lookup uses forward-slash directory components. The published patch changes the query to `maps/de_dust.bsp`. It retains the actual size check and does not modify, generate or distribute NAV data.

The patched ARM server built successfully and was installed in the isolated source runtime with its hash checked against the private manifest. A fresh de_dust launch, team/class selection and two bot joins no longer produced the mismatch warning. The prior runtime's server was backed up before replacement.

That patched match continued through another deliberate death, an A/Use press and a new round. Its 182-second run ended by supervised request, with no reported crash or forced KILL. RetroFE returned and the clock restored to 1008 MHz.

## Method and next work

The temporary test launcher enables the console and frame profiler, loads a separate test configuration and retains the ordinary clock, audio and supervisor code. Temporary keys do not change camera or movement speeds. Engine PID, increasing two-second resource samples and increasing five-second frame reports are checked during each measurement. Phase calculations omit the first reporting window crossing the phase boundary and include complete active-client windows. CPU is process user+system tick growth over elapsed time, using the Nano's 100 Hz tick rate; FPS is weighted by frame counts and window duration. No battery-life or input-latency claim follows from these measurements.

The main remaining performance issue is loading/paging with little spare RAM. Measure model, sound and texture allocation before changing budgets or reducing visual quality. The earlier firmware mixer kernel wait was not reproduced in these runs; that does not establish that it is fixed. The subsequent [loading/audio stage](LOADING-AUDIO.md) avoids the broad startup mixer scan and records immediate user-confirmed HL sound, while retaining the kernel-driver limitation. Keep the existing recovery shortcut and the established SDL installation available while testing broader scenes.

Cleanup removed the unique test save slots and private launch/configuration files. New ordinary saves created after the user's restart were preserved, as were all current ordinary save-file hashes. Both per-game settings files were checked unchanged. Private backups retain the pre-test and post-restart save folders; they are not distributed.
