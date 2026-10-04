# Loading peaks and audio startup

Checks on 2026-10-04 used the source-built RG Nano runtime at 240×240 and 1200 MHz, with the accepted controls, original artwork and saved caps of 30 FPS for Half-Life and 40 FPS for Counter-Strike.

## Targeted speaker volume restoration

An earlier firmware `amixer` process blocked in `snd_soc_dapm_get_enum_double` before the game started. The installed firmware volume script uses the simple-mixer `sset` path, which loads unrelated mixer controls. Startup now uses quiet `cset` calls for only `Headphone Playback Volume` and `Headphone Playback Switch`, preserving the firmware's rounded 0–100 to 16–63 mapping. The existing `audio_amp` policy still respects volume zero. A configured USB audio output retains the firmware volume command.

Quiet mode matters: the [installed ALSA 1.2.4 command implementation](https://github.com/alsa-project/alsa-utils/blob/v1.2.4/amixer/amixer.c) opens the specified low-level control for `cset`, but loads the high-level control list to display the result when quiet mode is absent. This workaround avoids that broad scan during built-in speaker startup. It does not establish that the kernel driver bug is fixed; firmware volume shortcuts and the USB path still use firmware commands.

The actual launcher function passes tests for all 101 volume values, leading zeroes, invalid inputs, either targeted command failing and USB fallback. On the Nano, an interposition probe rejected broad `snd_mixer_load`/`snd_hctl_load` calls and traced only reads/writes of the two requested controls; restoration succeeded. The user confirmed audible Half-Life sound immediately, without adjusting volume.

## Optional peak intervals

The two-second resource sampler can miss short-lived allocations. The new console commands `nano_mem_begin` and `nano_mem_end` bracket an interval using existing memory-pool accounting hooks. Begin seeds the total from live pools; end reports starting/current/peak payload, the largest positive accounting delta and growth/shrink counts. Two bounded end records also identify the pools responsible for the peak-triggering and largest-growth events. Those labels do not rank the largest pools.

Tracking is off by default. Inactive hooks take one conditional branch; active hooks do not walk allocation chains or print. Ordinary launches do not start an interval or add an overlay. The counters include tracked pool payload and realloc growth/shrink deltas, but exclude allocator-internal realloc temporaries, untracked malloc calls, libraries, stacks and kernel memory. They are not resident RAM measurements or a complete process peak.

For a console-enabled diagnostic launch, place `+nano_mem_begin` before the initial `+map`, then issue `nano_mem_end` after loading. To measure a transition or reload, begin another interval before it and end afterward. Collect `nano-memory-begin:`, `nano-memory-peak:` and `nano-memory-peak-pools:` alongside resource/frame reports. Beginning again resets the interval. Logs remain private.

| Interval | Payload at end (MiB) | Peak payload (MiB) | Peak above end (MiB) | Largest positive delta (bytes) |
|---|---:|---:|---:|---:|
| HL opening load | 26.13 | 26.23 | 0.105 | 3,600,000 |
| HL natural tram transition | 29.78 | 33.36 | 3.582 | 4,195,700 |
| CS de_dust opening load | 86.93 | 90.81 | 3.874 | 5,570,560 |
| CS map reload | 87.66 | 91.46 | 3.799 | 5,400,000 |

These are separate scene intervals, not equal-cache before/after trials. CS still needs paging and loading stalls remain. No loading-time or FPS improvement is established by adding counters.

Actual-function sanitizer tests cover live/inactive pool seeding, transient allocations, growth/shrink, migration, disabled hooks, interval reset, 10,000 randomized accounting operations, 64-bit totals and bounded output. The existing snapshot report tests, ARM build and fresh/partial/full patch-stack reapplication checks pass.

## Next optimization target

The HL transition's 4,195,700-byte growth matches the 4 MiB save buffer plus its header in the pinned [save implementation](https://github.com/FWGS/xash3d-fwgs/blob/e3e459bb6735c9e6a6bf18658f637bc71cdc73df/engine/server/sv_save.c). The [pool allocator](https://github.com/FWGS/xash3d-fwgs/blob/e3e459bb6735c9e6a6bf18658f637bc71cdc73df/engine/common/zone.c) currently allocates and explicitly clears that entire buffer, touching pages even when the save uses only part of its capacity. This attribution is an inference from the measured delta and source.

An isolated, dynamically linked on-device probe modeled the header, 4 MiB capacity and trailing sentinel. Across two fresh processes per method, malloc plus full memset incurred 1,029 minor faults and approximately 4.6 MiB RSS; calloc with only header/end touches incurred six minor faults and approximately 0.6 MiB RSS. First/last payload bytes were zero. This demonstrates a possible demand-zero mechanism in the firmware libc, not an engine performance improvement or a complete allocator regression check.

Next test libc calloc for large cleared pool allocations while preserving save capacity, zero-initialization, sentinels, ownership and the custom-swap allocator path. Include dirty-block reuse, allocation failures, realloc/free and real save/load/landmark transitions before adoption. Follow with CS load/reload and later HL scenes using both pool peaks and RSS/page-fault timing. Do not shrink save capacity or reduce HUD/model quality to obtain a smaller number.

## Hardware checks and cleanup

The profiled HL process ran for 182 seconds through loading and a natural tram transition; CS ran for 366 seconds through loading and a map reload. Both ended by supervised request without a reported crash or forced KILL. Separate ordinary launches ran for 322 seconds in HL and 123 seconds in CS, rendering the tram and team menu with PCM playback running and no frame profiling or memory interval enabled. These are bounded startup checks, not full campaign or multiplayer validation.

All launches used 1200 MHz and supervised exits restored 1008 MHz and RetroFE. Ordinary HL saves were isolated during testing and restored with all 28 file hashes unchanged; both saved settings remained unchanged. Named test wrappers/configuration/probes were removed. Installed native ELF hashes match the private manifest and final pinned source build. No game assets, extracted artwork, private logs or compiled runtime are published.
