# Texture memory and allocation checks

On 2026-10-04 the source-built RG Nano runtime was checked at 240×240 and 1200 MHz. CS used de_dust, two easy bots and the user's saved 40 FPS cap. Model, map and sound data, HUD scales and camera/movement settings were retained.

## What changed

The pinned software renderer generated four mip levels for every uploaded image. Menu/HUD/sprite drawing and the studio model sampler read only level zero. The native recipe now marks studio images for that existing base-only path and skips their unused lower levels, alongside menu/sprite images. Base-only skybox images also omit unused lower levels; BSP world-surface textures retain their four-level path. Base resolution, color conversion, alpha and original artwork are unchanged.

Texture reuploads previously overwrote owned pixel pointers and incremented size/mip counts without releasing the old buffers. They now free those buffers and replace their accounting. A retained source image is copied only when one does not already exist. The ownership regression test covers repeated content/size/alpha changes; these corrections do not establish that reuploads caused the earlier gameplay freezes.

`nano_mem` adds a counter-only diagnostic command: one total record and at most sixteen largest nonempty pools. It does not walk allocation chains, check sentinels, allocate a report buffer or run automatically during gameplay. The older `memlist` integrity scan took several seconds in this swapped-out process and is unsuitable for frequent timing samples.

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

Next measure the remaining world/model/alpha texture storage, model source payload and transient loading allocations. Consider sharing duplicate immutable texture data or avoiding redundant source copies only after ownership and remapping are understood. Preserve full-resolution HUD artwork and the existing controls. The firmware audio startup lock remains a separate unresolved issue.

The changes extend the pinned [FWGS software texture implementation](https://github.com/FWGS/xash3d-fwgs/blob/e3e459bb6735c9e6a6bf18658f637bc71cdc73df/ref/soft/r_image.c) and retain its applicable license; no Valve assets or compiled runtime are included in the public project.
