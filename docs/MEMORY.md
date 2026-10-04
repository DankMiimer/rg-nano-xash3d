# Texture memory and allocation checks

On 2026-10-04 the source-built RG Nano runtime was checked at 240×240 and 1200 MHz. CS used de_dust, two easy bots and the user's saved 40 FPS cap. Model, map and sound data, HUD scales and camera/movement settings were retained.

## What changed

The pinned software renderer generated four mip levels for every uploaded image. Menu/HUD/sprite drawing and the studio model sampler read only level zero. The native recipe now marks studio images for that existing base-only path and skips their unused lower levels, alongside menu/sprite images. Base-only skybox images also omit unused lower levels; BSP world-surface textures retain their four-level path. Base resolution, color conversion, alpha and original artwork are unchanged.

Texture reuploads previously overwrote owned pixel pointers and incremented size/mip counts without releasing the old buffers. They now free those buffers and replace their accounting. A retained source image is copied only when one does not already exist. The ownership regression test covers repeated content/size/alpha changes; these corrections do not establish that reuploads caused the earlier gameplay freezes.

`nano_mem` adds a counter-only diagnostic command: one total record, one asset-category record and at most sixteen largest nonempty pools. It does not walk allocation chains, check sentinels, allocate a report buffer or run automatically during gameplay. The older `memlist` integrity scan took several seconds in this swapped-out process and is unsuitable for frequent timing samples.

## Allocation measurements

| CS snapshot | Tracked payload (MiB) | Renderer pool payload (MiB) |
|---|---:|---:|
| Before texture changes | 114.25 | 64.41 |
| Menu/sprite change only | 112.77 | 62.91 |
| Menu/sprite and studio change | 104.20 | 54.33 |

The original values are rounded `memlist` output; later values come from byte counters. The full change saves approximately 10 MiB of tracked allocation in this scene. The studio step alone reduces renderer payload by 8,987,742 bytes (8.57 MiB). Total payload can vary slightly with bot/sound/filesystem state. These are allocation counts, not resident RAM or whole-process virtual memory; ordinary libraries, stacks, allocator internals and kernel memory are outside the pool totals. The remaining allocations still exceed physical RAM.

Each following timing phase covered approximately sixty seconds of play, omitting its first crossing profile window. These were separate live matches, not deterministic replays or equal-cache trials.

| Phase | FPS | Engine CPU | Peak RSS (KiB) | Minimum available RAM (KiB) | Engine major faults |
|---|---:|---:|---:|---:|---:|
| Before | 39.55 | 70.9% | 44,176 | 5,732 | 130 |
| Menu/sprite only | 39.77 | 67.3% | 43,360 | 5,132 | 335 |
| Including studio | 39.57 | 66.2% | 36,848 | 4,820 | 435 |

The lower allocation count is supported directly. These timing/paging samples do not establish an FPS gain, faster loading or less swapping in every scene. Later matches had different cache state and activity; their available-RAM minima and fault counts did not improve consistently. Loading remains around thirty-plus seconds for the tested CS starts.

The final CS runtime continued through a deliberate death/A press and a new round, then ended by supervised request after 312 seconds without a reported engine crash or forced KILL. A fresh framebuffer capture shows the weapon, HUD and world. The user noticed new text at the top-left: a capture identified timestamped server-event lines from temporary `log on` testing. Logging was turned off; this was not a new HUD element or the counter-only report.

Half-Life also rendered the tram and station in short checks. A fresh station capture shows a selected pistol firing, its view model, ammo and health. Two supervised HL runs ended by requested TERM without a reported crash or forced KILL; clocks restored to 1008 MHz. The ordinary HL save folder was isolated throughout these checks, then restored with every file hash unchanged. Temporary configuration, test keys and cheats were removed/reset, and both per-game settings hashes were unchanged. This is not a later-campaign stability test or an HL before/after allocation comparison.

## Verification and next work

`test_nano_texture_memory.py` extracts the actual upload, mip-generation and source-retention functions. It compares base pixels and alpha with the pinned unmodified renderer, verifies retained world mip pixels, and checks bounded live allocations across 200 uploads with changing dimensions and alpha flags. Odd dimensions and one-pixel textures are included. `test_nano_memory_report.py` checks actual report totals, inactive/empty pools, stable ties and the sixteen-pool output limit. Both run under AddressSanitizer/UndefinedBehaviorSanitizer. Existing renderer triangle and clipping sanitizer checks also pass. The ARM build and patch reapplication checks pass; the installed native ELF hashes match the private manifest.

For a console-enabled diagnostic launch, issue `nano_mem` after the scene loads and collect its `nano-memory:` / `nano-memory-pool:` lines from `diagnostics/<game>/engine.log`, paired with `metrics.csv` and frame reports. Do not treat `memlist`-induced stalls as ordinary game performance. Logs remain private and may contain asset names.

The next stage below shares duplicate immutable texture buffers. Remaining work includes transient loading allocations, model animation/header storage and later-campaign measurements. Preserve full-resolution HUD artwork and the existing controls. The later [loading/audio stage](LOADING-AUDIO.md) adds peak intervals and a targeted mixer startup workaround; the kernel driver cause remains unresolved.

The changes extend the pinned [FWGS software texture implementation](https://github.com/FWGS/xash3d-fwgs/blob/e3e459bb6735c9e6a6bf18658f637bc71cdc73df/ref/soft/r_image.c) and retain its applicable license; no Valve assets or compiled runtime are included in the public project.

## Sharing identical pixels (2026-10-04)

The low-memory engine already truncates studio model source data after texture upload; removing that copy again would not save memory. An offline scan instead found many repeated hand, glove and weapon skins under different model texture names. Its estimate was only a candidate count because palette/gamma/alpha processing can affect the final bytes.

The renderer now shares completed byte-identical pixel buffers, including individual world mip levels and alpha buffers. FNV-1a hashes select candidates; matching size and a complete `memcmp` establish equality. Texture names, geometry, flags and retained source/remapping images remain independent. Updates release their old references, build fresh pixels and then share the resulting buffer if it matches another. Drawing only reads the buffers. A final reference release frees both the buffer and its registry node; color/alpha conversion and image dimensions are unchanged.

`nano_tex` prints one counter record to the diagnostic log on request. It does not run automatically or add an overlay. The hash tables occupy 4 KiB of static storage on the Nano; node metadata is included in the renderer memory pool. Interning needs a temporary newly converted buffer and adds hashing/comparison work while uploading, rather than eliminating conversion or guaranteeing a smaller instantaneous loading peak.

| CS de_dust snapshot | Tracked payload (MiB) | Renderer pool payload (MiB) |
|---|---:|---:|
| Mip reduction, before sharing | 104.20 | 54.33 |
| Mip reduction plus sharing | 86.96 | 37.10 |

The shared-buffer counters report 55,401,490 logical pixel bytes represented by 37,260,426 unique bytes: 18,141,064 bytes saved before 70,656 bytes of node metadata. The renderer payload reduction is exactly 18,070,408 bytes (17.23 MiB), plus the separate 4 KiB static table cost. Small differences elsewhere in total allocation reflect live game state. These are tracked allocations, not physical RAM; the process still needs paging. Compared with the original pre-mip snapshot, the two changes together remove roughly 27 MiB of tracked payload in this scene.

The actual upload/deletion test compares output pixels with the pinned baseline, checks shared pixel/alpha identity, modifies one owner and verifies the other survives unchanged, then deletes owners in both orders. Generic ownership checks force every hash to collide, exercise differing contents/sizes, metadata allocation failure and 100 cycles of randomized ownership changes. Both pass AddressSanitizer/UndefinedBehaviorSanitizer. The ARM build, existing triangle/clipping checks and fresh/partial/full patch-stack reapplication checks pass; unrelated edits survive reapplication.

The updated CS process ran for 419 seconds with a deliberate death/A press, a later respawn, weapon firing and two map reloads. After the first reload cached additional images, the second returned exactly the same logical/unique byte, buffer and reference counts. Fresh captures show the normal weapon/HUD, spectator view, respawn and team menu. Active/death timing windows were approximately 39.8 FPS at the saved 40 FPS limit. Reload windows still included 1.2–3.6 second stalls; this is no proof of an FPS or loading improvement over the previous build.

Half-Life ran for 421 seconds through a natural tram transition, a station map, pistol firing and one verified temporary save/load. Opening-scene sharing saved 904,752 bytes before 30,168 bytes of node metadata (about 0.83 MiB net, excluding the static tables). Station and post-load windows stayed near the saved 30 FPS limit. An initial injected function-key attempt did not save or load because the backend lacks those mappings; only the subsequent mapped-key attempt, with a saved file and corresponding load log, counts as a save/load check. Fresh captures show the station pistol and HUD before and after that load. Physical-device audio was not reconfirmed during this stage; its code/settings were unchanged.

Both processes exited by supervised request without a reported crash signal or forced KILL, returned to RetroFE and restored 1008 MHz after their 1200 MHz launches. All 28 ordinary HL save files were restored with matching hashes, both saved settings files were unchanged, cheats were reset and private test configuration/wrappers were removed. Installed native ELF hashes match the refreshed private manifest. These bounded checks do not establish full campaign or network-play reliability.

The latest [model/sound measurements](MODEL-SOUND.md) split existing pool counters into asset categories. Player-model storage remains a larger candidate than the tested sound pool; no animation or sound-quality reduction has been adopted.
