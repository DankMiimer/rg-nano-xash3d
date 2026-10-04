# Large cleared pool allocations

The loading investigation found a 4 MiB temporary save buffer during Half-Life transitions. The pinned [pool allocator](https://github.com/FWGS/xash3d-fwgs/blob/e3e459bb6735c9e6a6bf18658f637bc71cdc73df/engine/common/zone.c) allocated memory, initialized its header/sentinel and explicitly cleared the entire payload. That writes unused buffer pages into physical RAM. [LOADING-AUDIO.md](LOADING-AUDIO.md) records the initial evidence.

## Change

In the native recipe, cleared pool allocations with payloads of at least 256 KiB now use libc `calloc(1, blocksize)`. Header, linked-list ownership, trailing sentinel and pool accounting are initialized as before; the redundant full-payload memset is skipped only for that path. The threshold limits the change to large blocks. Small and uncleared allocations retain their original path, as do realloc operations on existing blocks. With `XASH_CUSTOM_SWAP`, all allocations retain the swap allocator and explicit clearing; libc buffers must not be passed to its free function.

All requested bytes remain zero and all capacity remains available. This permits the firmware allocator to retain demand-zero pages where supported; it does not reduce tracked payload, guarantee lower RSS for reused blocks or save memory once every page is used. The save buffer, texture dimensions, original HUD artwork, audio settings, controls and movement speeds are unchanged.

## Actual pool-code probe on the Nano

Two fresh processes per method used dynamically linked firmware libc and the actual `_Mem_Alloc` header/link/accounting/sentinel code. The requested payload was 4,195,700 bytes, matching the save buffer plus its internal header. Metrics were read before a full payload scan, so the zero check itself did not populate every page before measurement.

| Method | Minor faults during allocation | RSS after allocation (KiB) | Explicitly cleared payload bytes | Tracked payload bytes |
|---|---:|---:|---:|---:|
| Original malloc + memset, run 1 | 1,027 | 4,624 | 4,195,700 | 4,195,700 |
| Original malloc + memset, run 2 | 1,027 | 4,612 | 4,195,700 | 4,195,700 |
| Large-block calloc, run 1 | 4 | 532 | 0 | 4,195,700 |
| Large-block calloc, run 2 | 4 | 532 | 0 | 4,195,700 |

Both methods then passed a complete payload zero check, dirty overwrite and free/accounting checks, with the trailing sentinel intact. This supports roughly 4 MiB less resident memory for this fresh, mostly unused buffer. It is not a measured whole-game RSS, FPS or load-time improvement. Real scenes, reused storage, swap/cache state and subsequent writes affect the result.

## Regression checks

`test_nano_demand_zero.py` compiles the actual pool allocation, sentinel, list, free, migration and realloc code with instrumented libc. AddressSanitizer/UndefinedBehaviorSanitizer checks cover full payload contents, both sides of the threshold, small/large headers, uncleared data, dirty/free/reallocate cycles, allocation failures with empty and occupied pools, sentinel corruption detection, mixed owners, small-to-large promotion, grow/shrink, pool migration and realloc failure. A separate `XASH_CUSTOM_SWAP` build confirms allocation/free pairing and explicit clearing; it does not claim a fix for unrelated upstream custom-swap realloc behavior.

The ARM native build, existing memory snapshot/peak sanitizer tests and fresh/partial/full patch-stack reapplication checks pass. Reapplication preserves unrelated source edits.

## Hardware checks (2026-10-04)

Half-Life retained one engine process for 359 seconds through natural tram changes, a verified station map, two new temporary saves and their loads, a normal adjacent-map reset and a landmark return. Station save/load captures showed the weapon and HUD. A plain `changelevel` resets player state; the following landmark return was a separate transition check, not proof that the preceding reset retained inventory. Active windows recovered to the saved 30 FPS cap, with transition stalls still present.

Counter-Strike retained one process for 392 seconds through team/class selection, weapon firing, a bot kill with A/Use while dead, two de_dust reloads, a later deliberate death and requested round restarts. Fresh captures showed the weapon, HUD, first-person spectator view and loaded world. Active windows returned to roughly the saved 40 FPS cap; a reload window still contained a 3.4-second interval. These were bounded gameplay checks, not controlled baseline/candidate timing comparisons or complete campaign/network validation.

Both processes ended by supervised request without a reported engine crash or forced KILL, returned to RetroFE and restored 1008 MHz after 1200 MHz launches. The ordinary Half-Life save folder was isolated, then restored with all 28 file hashes unchanged. Saved per-game settings and system volume remained unchanged; temporary configurations, wrappers and probes were removed. Installed native ELF hashes match the private manifest and final pinned build. Public files contain source, tests and documentation only.

## Remaining measurements

Use the same scenes and cache policy for repeated baseline/candidate comparisons before claiming faster loads or fewer gameplay faults. Compare transition/save timing and process RSS/faults, since `nano_mem` and peak payload counters deliberately report the same reserved capacity. Then investigate model animation/header storage and representative later Half-Life scenes. Keep the established controls, full-resolution HUD and save capacity intact.
