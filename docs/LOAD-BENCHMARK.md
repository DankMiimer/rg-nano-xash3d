# Controlled load comparison — 2026-10-04

The large-cleared-buffer change was compared with the previous allocator in twelve Nano launches. In these tested scenes, the cache-cleared median was lower with the change. Warm results overlap substantially; they do not establish a general loading-speed improvement.

## Timing results

Times run from an accepted engine load request to the client becoming active. They exclude launcher/audio startup and initial engine/library initialization, and stop before the first rendered frame and subsequent lazy asset work. They are **not launch-button-to-playable times**.

| Game / scene | Cache policy | Previous allocator median (range), seconds | Large-block calloc median (range), seconds | Observations per variant |
|---|---|---:|---:|---:|
| Half-Life, fixed station save (`c1a0`) | Cleared | 4.630 (4.281–4.918) | 3.749 (3.299–4.205) | 3 |
| Half-Life, same save | Warm | 1.920 (0.634–2.420) | 1.660 (0.403–2.219) | 9 |
| Counter-Strike, `de_dust`, team menu | Cleared | 23.720 (23.414–23.790) | 22.396 (20.165–22.752) | 3 |
| Counter-Strike, same map | Warm | 8.872 (7.453–9.523) | 8.299 (7.394–9.250) | 9 |

The cache-cleared median differences are approximately 19% for this HL save and 5.6% for this CS map. These are descriptive results from three launches per variant, not statistical guarantees or whole-campaign estimates. The nine warm observations are three reloads within each of three processes, not nine independent boots.

## Resource results and limits

For cache-cleared loads, median process major-fault growth fell from 140 to 19 in HL and from 898 to 727 in CS. Approximate median process CPU time was 2.14 versus 2.24 seconds in HL and 9.22 versus 8.91 seconds in CS. Less wall time does not imply less CPU work in every scene.

Sampled median peak RSS was 44,920 versus 43,648 KiB for cache-cleared HL, and 45,632 versus 45,520 KiB for cache-cleared CS. Warm HL peak RSS was **higher** with calloc: 42,692 versus 43,944 KiB. Fresh-buffer demand-zero savings do not guarantee uniformly lower whole-process RSS.

CS still paged heavily. System-wide swap counters are included in the data but cannot be attributed solely to the engine. Warm CS median swap-out growth was higher with the candidate even though its median load time was lower. No FPS, input-latency, battery-life or universal paging improvement follows from this test.

RSS and available-memory observations used a nominal 100 ms sampler; the observed median interval was 102 ms. A sampled peak can miss a shorter peak. CPU estimates bracket request/ready timestamps with those samples, use the Nano's 100 Hz process tick rate, and are approximate. Minor/major faults and before/after RSS are read directly from the engine's `/proc/self/stat` snapshots. Phase sample selection allows 20 ms around request/ready uptime timestamps because uptime is quantized.

## Controlled procedure

- Build two engines from project revision `95075b98ea0e51ab0f75bd1c19915bc636eb4199`, the locked upstream commits and FunKey SDK 2.3.0. Both receive the same temporary measurement hooks. Only the large-cleared-buffer allocator differs: baseline reverses `engine-nano-demand-zero.patch`, candidate retains it. Renderer/client/server/menu, game files, controls and saved settings are identical. The later decal fixes were **not** part of this comparison.
- Use 1200 MHz for every launch, saved caps of 30 FPS for HL and 40 FPS for CS, and the same frame-sleep configuration. Keep ordinary HL saves in a separate verified backup folder; supply a byte-identical test-save fixture for each launch. Private saves and commercial assets are not published.
- For each game, launch variants in A–B–B–A–A–B order. Stop the frontend, run `sync`, then write `3` to `/proc/sys/vm/drop_caches` before the first scene load. This clears eligible clean filesystem pages and reclaimable slab; it does not reset anonymous memory, swap or storage-controller state. Call this **cache-cleared**, not power-off cold. See the [Linux kernel documentation](https://docs.kernel.org/admin-guide/sysctl/vm.html#drop-caches).
- Record the first load, perform one excluded warm primer, then three measured warm reloads with at least two seconds between ready and the next request. HL reloads the same fixed station save; CS reloads the map at the team menu, without a player joining the offline match during measurement.
- Require matching live engine PID, advancing resource/profile samples, active client state and unchanged settings/fixture hashes. All twelve launches ended by supervisor request without a reported crash or forced KILL; RetroFE returned and 1008 MHz was restored. PCM playback was active and owned by the engine, but physical sound was not reconfirmed for each trial.
- Restore the normal engine and sampler after the experiment. Temporary hooks, sampler and wrappers are absent from ordinary launches. Cache dropping is a one-shot command, not a persistent cache policy; the Nano retains the last command value (`3`) and rejects a write of zero. Ordinary launchers do not drop caches.

## Public data and measurement code

[The CSV](data/load-benchmark-2026-10-04.csv) contains 60 anonymous phase records: twelve excluded primers and 48 measured observations. It includes no device identifiers, local paths, game assets, saves or raw logs.

```sh
python3 tools/summarize_load_data.py
python3 tests/test_load_measurement.py
```

`experiments/engine-load-measurement.patch` adds request/ready timing and snapshots to the already patched native engine. `experiments/supervisor-load-samples.patch` adds monotonic timestamps and a temporary faster sampler to the project supervisor. They are optional measurement code, outside the normal patch recipe. The actual probe's timing, sequence reset, live proc parsing and single-ready gate pass AddressSanitizer/UndefinedBehaviorSanitizer tests. A full experiment also needs a privately supplied save and game files and a harness that verifies phase boundaries and restoration.

Next profile remaining CS model/animation/header and sound storage, and test broader HL saves/transitions. Preserve original texture/HUD pixels, controls and save capacity; do not reduce cache budgets without evidence.
