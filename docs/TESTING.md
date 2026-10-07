# Regression checks

Run from the repository root on Linux after building the sources. Set `NANO_NATIVE_DIR` when the native build is outside `build/native`. Sanitizer checks require native GCC. Tests compile project helpers or actual extracted upstream functions; [VALIDATION.md](VALIDATION.md) separately records hardware evidence and limits.

```sh
gcc -O2 -Wall -Wextra -Werror src/nano-supervise.c -o /var/tmp/rg-nano-supervise-host
python3 tests/test_supervisor.py
# After build-native.sh (uses NANO_NATIVE_DIR if set):
python3 tests/test_alsa_ring.py
python3 tests/test_renderer_triangles.py
python3 tests/test_renderer_decals.py
python3 tests/test_renderer_decal_reload.py
python3 tests/test_nano_menu.py
python3 tests/test_nano_settings.py
python3 tests/test_nano_options.py
python3 tests/test_nano_match.py
python3 tests/test_nano_match_launch.py
python3 tests/test_nano_match_patches.py
python3 tests/test_nav_import.py
python3 tests/test_nano_frame_stats.py
python3 tests/test_nano_texture_memory.py
gcc -std=c99 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined \
  -Isrc tests/test_nano_texture_share.c -o build/tests/nano-texture-share
build/tests/nano-texture-share
python3 tests/test_nano_skybox.py
python3 tests/test_nano_memory_report.py
python3 tests/test_nano_memory_peak.py
python3 tests/test_nano_demand_zero.py
python3 tests/test_nano_audio_start.py
```

The [controlled load comparison](LOAD-BENCHMARK.md) includes anonymous timing data and optional measurement patches. [Decal reload fixes](DECALS.md) document the later Half-Life save-load defect and renderer regression checks.

## Check renderer clipping

After fetching sources:

```sh
python3 tests/test_renderer_clipping.py
gcc -O1 -g -fsanitize=address,undefined build/tests/renderer-clipping-test.c -o build/tests/renderer-clipping-test
build/tests/renderer-clipping-test
```

This exercises the actual renderer function with normal, fully off-screen, zero-size and edge-clipped rectangles, checking framebuffer guards and texture sampling.

`python3 tests/test_nano_controls.py` checks the actual native evdev path, all physical button combinations, CS text-menu selection and strict preferences under sanitizers. Match tests check stock difficulty migration, NAV protection and launcher ordering.

Set `NANO_NATIVE_DIR` to the directory containing the fetched/patched `xash3d` and `hlsdk` trees when these live outside `build/native`:

```sh
NANO_NATIVE_DIR=/path/to/native python3 tests/test_nano_controls.py
NANO_NATIVE_DIR=/path/to/native python3 tests/test_nano_match_patches.py
```

The control test also resolves generated virtual-key bindings through the actual engine key parser. Patch checks cover fresh, partial and repeated application of the dependent HL, engine and CS stacks.

## Native UI profile v2

After fetching both patched source trees, use Python 3.12+ and set `NANO_NATIVE_DIR` when the native build is outside `build/native`:

```sh
python3 tests/test_nano_hud_text.py
python3 tests/test_nano_hud_input.py
python3 tests/test_nano_native_hud.py
python3 tests/test_nano_objectives.py
python3 tests/test_nano_alpha.py
python3 tests/test_nano_dialogs.py
python3 tests/test_nano_ui_migration.py
python3 tests/test_nano_ui_package.py
python3 tests/test_nano_menu.py
python3 tests/test_nano_options.py
python3 tests/test_nano_settings.py
python3 tests/test_nano_controls.py
python3 tests/test_nano_look_hud.py
python3 tests/test_renderer_clipping.py
```

Clipping checks generate a C harness; compile and run it with AddressSanitizer/UndefinedBehaviorSanitizer as described above. The alpha test covers the actual 2D draw function, monotonic ramps and all packed-pixel endpoint identities. Menu tests exercise both menu implementations and cached live font metrics; settings tests preserve unrelated pages and non-slider values. Dialog checks exercise wrapped messages, scrolling and pinned buttons.

For hardware comparisons, isolate one game with writable `/tmp` roots and read-only SD assets. Capture matching saved HL states and CS HUD-message fixtures at native size and 4x nearest-neighbour zoom. Exercise video preview rows, focus scrolling, save/load lists, fields, table columns, Cancel-default confirmations, team/buy selection, all spectator modes and both held/menu-opened scoreboard paging. Verify the original and candidate opacity ramps through actual menu rendering. Test viewer RGB565 orientation against fbgrab, partial-frame handling, helper-loss fallback/reconnect, freeze/resume and owned cleanup; benchmark capture disabled and at 2/5/10 fps. Consult [UI validation limits](NANO-UI-V2.md) before interpreting screenshots as physical-display evidence.

To check actual stb glyph bounds using a legally available local copy of the installed menu font, set `NANO_MENU_FONT=/path/to/FiraSans-Regular.ttf` and run `python3 tests/test_nano_font_metrics.py` with `NANO_NATIVE_DIR` as above. No game fonts are included in the source repository.

`python3 tests/test_nano_intro.py` executes the bounded player and actual cinematic
transitions with sanitizers. Set `NANO_INTRO_FILE=/path/to/nano_valve.nvi` to also
check an owned prepared clip's native dimensions and frame-buffer budget. It
does not display or play audio on the host or device. The control test verifies
that intro skip records cannot act on the following menu.

The settings layout regression also checks a parent's position changing while a
child keeps the same local rectangle, which previously left a button overlapping
the next row. See [native appearance validation](NANO-UI-VISUAL.md) for the installed
device checks and their limits.
