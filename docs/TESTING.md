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
