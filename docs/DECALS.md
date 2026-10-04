# Software-renderer decal reload fixes

Later Half-Life save testing exposed a signal-11 crash and a reproducible same-map reload hang in `c2a3d`. A fresh process could load the test save, while reloading it in a running process stopped frame updates. The supervisor recovered the crashed process and could stop the hung process.

## Confirmed reload defect

A remote debugger found the renderer repeatedly drawing a decal whose `pnext` pointed to itself. `R_NewMap` cleared the static decal pool but retained brush-surface list heads when the engine reused map storage. When restored decals reused those pool entries, a stale surface head could produce a self-link.

`renderer-decal-bounds.patch` now clears decal heads on every loaded non-inline brush model during `R_NewMap`, after resetting the pool and before restoring decals. Inline brush models share the world's surfaces. Missing handles and non-brush models are skipped. This follows the surface-head clearing already present in the pinned [OpenGL lightmap rebuild](https://github.com/FWGS/xash3d-fwgs/blob/e3e459bb6735c9e6a6bf18658f637bc71cdc73df/ref/gl/gl_rsurf.c). It repairs lifecycle state rather than hiding decals or restricting drawing to one list entry.

## Additional drawing defects

Inspection of the actual software decal drawing function found two separate problems:

- A projected decal wholly above the surface could leave a negative visible row count that wrapped to a huge unsigned height. The old function reproduces an out-of-bounds write under AddressSanitizer with synthetic geometry. Disjoint rectangles are now rejected before clipping, and clipped dimensions must remain positive.
- The opaque-texture path did not initialize its transparency flag. It now starts false for each decal; alpha textures explicitly enable it. Normal opaque pixel values are covered by the regression test.

The debugger directly established the stale-list cause of the repeatable hang. It did not establish the exact instruction responsible for the earlier signal-11 crash. The bounds defect is independently demonstrated by the sanitizer reproducer.

## Checks

`tests/test_renderer_decals.py` extracts the actual drawing function and runs over 120,000 synthetic rectangle/alpha cases, covering disjoint rectangles, exact boundaries, partial clipping on all edges and normal drawing. Guarded surface storage and AddressSanitizer/UndefinedBehaviorSanitizer check writes and texture reads. Explicit checks retain the expected normal, top-clipped and bottom-right-clipped pixels.

`tests/test_renderer_decal_reload.py` extracts the actual pool reset, allocation, unlinking, surface linking and new head-reset function. It reproduces the self-link when only the pool is cleared, then verifies 100 reset/reuse cycles across cached world, inline and separate brush models, missing handles, non-brush storage and linked-node replacement.

Both native ARM and standalone renderer builds pass, as do renderer triangle tests and fresh/repeated patch-application checks. The patch is included in both build recipes. Native installation hashes are checked against the private runtime manifest; optional load-measurement hooks are absent.

On the Nano, the corrected HL process ran for 209 seconds through a fresh load of the failing save, two same-save reloads, a load of the earlier `c1a2a` test save, a return to `c2a3d`, and creation/loading of a new temporary save. Monitored active windows returned to approximately the saved 30 FPS cap and fresh captures showed the weapon, world and original HUD. Tests used isolated saves and some earlier fixtures had test-only equipment/god state; this is not proof of complete campaign or enemy-combat reliability.

The renderer retains decal artwork, texture dimensions and the established HUD/control settings. Broader saves, map transitions and multiplayer still need testing.

Counter-Strike retained one process for 341 seconds through team/class selection, firing, a verified `de_dust` reload, a deliberate death, A/Use while spectating and a requested round restart. Fresh captures showed the dead spectator and returned first-person view; active windows were approximately the saved 40 FPS cap. Both corrected HL/CS processes ended by supervisor request without a reported crash or forced KILL, returned to RetroFE and restored 1008 MHz after 1200 MHz launches.

All 28 ordinary HL save files were restored with identical hashes. Both per-game settings hashes were unchanged. Temporary launchers, test configurations and debugger helpers were removed; commercial test saves/logs remain private. The device's current volume was retained rather than overwritten during cleanup. These checks do not establish full campaign/network reliability or reconfirm physical audio for every test.
