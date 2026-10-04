# Model and sound storage (2026-10-04)

`nano_mem` now adds one counter-only `nano-memory-assets:` line. It groups active pools into models, sound, maps, renderer and other storage; player-model bytes are a subset of model bytes, not another additive category. It reads pool counters/names only and runs on request. No model headers, audio buffers or allocation chains are walked during gameplay.

| CS de_dust team-menu snapshot | Payload bytes | MiB |
|---|---:|---:|
| All 136 model pools | 23,509,428 | 22.42 |
| Ten player-model pools (subset) | 20,809,404 | 19.85 |
| SoundLib pool | 4,404,243 | 4.20 |
| Map pool | 4,571,638 | 4.36 |
| Renderer pool | 38,903,946 | 37.10 |
| Other pools | 19,769,143 | 18.85 |

These counters reconcile to 91,158,398 bytes of tracked payload in that snapshot. They exclude ordinary libraries, stacks, allocator internals and kernel memory, and do not measure resident RAM. SoundLib includes decoded samples, temporary workspace and streams; it is not exclusively cached PCM. Counts vary with the map and game activity.

An offline header inspection of the ten user-owned CS player models found 23,366,588 source bytes, with exactly 20,809,404 bytes retained before the texture-data region. The existing low-memory engine already discards the remaining 2,557,184 texture bytes after upload. Removing that data again cannot provide another saving. These models use one sequence group each.

The next candidate is animation-storage duplication and ownership. Headers contain model-specific offsets and uploaded texture IDs; the client and server expect relative animation addresses. Whole-model sharing or truncating the retained prefix is unsafe without auditing every consumer. Measure identical animation regions first, then prototype ownership/offset handling outside the installed build. Require unchanged animation/geometry plus death, spectator, reload and campaign tests before adopting it. No animation buffers were shared or removed in this update.

Sound changes have a smaller measured ceiling in this scene. Inventory cache lifetime and temporary resampling workspace before choosing a budget; do not reduce sample rate or remove effects merely to make the pool smaller. Original visual and audio quality remains the priority.

The actual report regression test covers category totals, colored model/map names, inactive pools, stable ties, wide sums and bounded output. Sanitizers, ARM compilation and fresh/partial/full report/peak/allocation patch-stack application pass. Hardware summaries and sky/map tests are in [VALIDATION.md](VALIDATION.md). Private game files and raw logs are excluded from publication.
