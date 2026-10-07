# Power-off save and resume

Closing a FunKey S, or pressing the RG Nano power button, saves Half-Life and resumes it on the next power-on. Counter-Strike quits cleanly. This follows FunKey OS's own *Instant Play* protocol, the one its emulators use.

## FunKey OS protocol

- The GPIO daemon runs `powerdown schedule 0.1`. That sends `SIGUSR1` to the PID in `/var/run/funkey.pid`, waits 0.1 s and powers off, unless `powerdown handle` cancels the schedule first.
- Both frontends record the launched program. gmenu2x lets `opkrun` record it; RetroFE's `native_launch.sh` records `opkrun`, which then records its child. In both cases the recorded process is `launch.sh`, which `exec`s `nano-run.sh`, so the launcher receives the signal. A dummy OPK checked both paths on the device.
- At boot, `/root/.profile` runs `instant_play load` after all init scripts have started the button daemon and audio. It executes `/mnt/instant_play` once, then starts the frontend.

## Launcher

`nano-run.sh` traps `SIGUSR1`:

1. Checks that the supervised engine is running, using `child.pid` and `/proc/PID/comm`, with shell builtins only. It then cancels the scheduled shutdown with `pkill -f "powerdown schedule"`, well inside the 0.1 s window. If no engine is running yet, it leaves the firmware to power off as usual.
2. Shows *SAVING…* for Half-Life and forwards `SIGUSR1` to the engine.
3. Starts a guard: after 12 s it asks the supervisor to stop the game, and 8 s later it powers off regardless. A closed console never stays on.
4. When the engine has exited, it runs the normal cleanup: 1008 MHz clock, firmware keymap, amplifier state and launcher lock.
5. If Half-Life reported a save, it writes `/mnt/instant_play` in the same format `instant_play save` produces. That file runs `nano-run.sh ROOT valve resume` in the background and records its PID, so a later lid close works the same way. The launcher then runs `powerdown now`.

`nano-run.sh ROOT valve resume` starts with `-nointro +load nano_poweroff` instead of the opening map. If that save no longer exists, it starts normally.

## Engine

`engine-nano-power.patch` sets a flag from `SIGUSR1`. At the next frame `Host_NanoPowerFrame` does the following:

- In a single-player game it calls `SV_SaveGame("nano_poweroff")`. The engine's own checks apply, so there is no save while dead, during intermission or while loading. On success it creates the file named by `NANO_POWER_FLAG`.
- It waits at least four frames and 0.25 s, so the queued `saveshot` preview is written, then queues `quit`. Quitting writes `config.cfg` and shuts the engine down normally.
- Anywhere else (menus, Counter-Strike, loading) it queues `quit` immediately.

The save is an ordinary Half-Life save. It appears in *Save/Load Game* and is replaced at each power-off.

## Testing without powering off

`NANO_POWER_TEST=1` keeps every step except the final power-off. The resume file goes to `$NANO_RUN_DIR/xash-nano.instant_play` instead of `/mnt/instant_play`, and the launcher prints `power test: would power off now`. A stand-in `powerdown schedule` script checks that the cancel happens inside the firmware's window.
