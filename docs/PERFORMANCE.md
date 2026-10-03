# Frame pacing and measurements

Measurements on 2026-10-03 used the source-built framebuffer ports at 240×240 and 1200 MHz, on an RG Nano with 56,164 KiB RAM and SD-backed swap. Normal launches now use an explicit 30 FPS cap with `gl_vsync 0` and `nano_frame_sleep 1`. These are frame scheduling changes; movement speeds and the camera acceleration curve are unchanged.

## What changed

The pinned engine bypasses `fps_max` when `gl_vsync` is enabled. The software framebuffer does not supply a VSync wait, so the prior configuration could render continuously. With VSync disabled, the old frame limiter still busy-waited when frame work consumed more than half the available time. The Nano policy sleeps for the remaining time in chunks of at most 5 ms, leaving a 0.2 ms margin before the deadline. It retains the original path when disabled and on dedicated servers.

## Short hardware runs

Each phase lasted approximately 30 seconds. CS used de_dust with two easy bots: a fixed spawn view, followed by a held horizontal turn. HL used the opening tram, fixed view followed by turning. FPS is the frame-count-weighted mean of complete five-second reporting windows; the first crossing window was omitted. CPU is engine user+system tick growth divided by elapsed time, with the Nano's 100 Hz tick rate. It excludes other processes and driver work.

| Scene | Earlier uncapped FPS / CPU | 30 FPS with old wait: FPS / CPU | 30 FPS with Nano sleep: FPS / CPU |
|---|---|---|---|
| CS fixed spawn view | 58.01 / 92.6% | 28.67 / 87.5% | 29.48 / 50.1% |
| CS held horizontal turn | 65.96 / 93.6% | 29.95 / 93.5% | 29.98 / 46.3% |
| HL opening tram, fixed | Not measured | 29.88 / 92.6% | 29.93 / 56.2% |
| HL opening tram, turning | Not measured | 27.93 / 81.7% | 30.00 / 44.2% |

With Nano sleep, the CS turn's five-second p95 intervals were 33.33 ms, with a 36.08 ms maximum frame. HL turning had 33.33 ms p95 and a 34.38 ms maximum. The more variable CS fixed view had p95 values of 33.33–40.18 ms and a 59.73 ms maximum. Lower CPU use leaves scheduling headroom; these tests do not measure power consumption, battery life or input-to-display latency.

The phases are comparable short scenarios, not deterministic replays. Bots, tram position, asset cache and OS swap state vary. A prior HL run contained a 1.08-second stall; its absence in the later short run does not establish that loading stalls are fixed.

## Remaining memory and audio work

The new runs reached approximately 40–43 MiB resident engine memory and 5–6 MiB minimum available system memory. Swap and major faults still occur. Swap-page counters are system-wide; engine major faults are per-process. Different counts between runs cannot be attributed solely to pacing. The next measurements should distinguish initial loading, steady play, level changes and repeated launch/exit cycles before changing texture or cache budgets.

During repeated testing, the firmware's `amixer` command once blocked in uninterruptible kernel sleep in `snd_soc_dapm_get_enum_double`, before engine startup. Restarting the Nano cleared it; later CS and HL launches succeeded. The root cause is unresolved. Userspace recovery cannot guarantee recovery from an audio-driver lockup.

## Repeat the measurements

Profiling is off by default. Set `NANO_PROFILE=1` in the environment of a source launcher, or run `nano-run.sh` with that environment after stopping the frontend and arranging its restoration. Keep `NANO_DIAGNOSTIC=0` for comparable normal-game measurements. The legacy runtime has no frame profiler or Nano sleep implementation.

`diagnostics/<game>/engine.log` emits one `nano-profile:` summary about every five seconds: client state, configured cap/VSync, frame count, FPS, median/p95/maximum interval, mean work time and frames over 50 ms. Statistics use wall time, including waits and stalls. Work time measures the engine frame body. The sample ring holds at most 512 intervals; if a window exceeds that, percentiles cover its most recent 512 intervals, while FPS, mean work, maximum and slow-frame count cover the whole window.

Use `metrics.csv` for resource counters. Check that its PID matches a live `xash3d` process and that both elapsed time and profile count advance before accepting a phase. Old logs remain after shutdown. Exclude loading and windows crossing scene boundaries, and save the clock log alongside results. Set `nano_frame_sleep 0` to compare the old waiting behavior; use `nano_profile 0` to stop reports. The launcher always restores 1008 MHz and default keys on normal supervised exit.

`tests/test_nano_frame_stats.py` extracts the actual engine wait function and checks capped deadlines, bounded sleeps, timescale handling, opt-out, steady frames, stalls, invalid samples and bounded ring rollover under AddressSanitizer/UndefinedBehaviorSanitizer.
