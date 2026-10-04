#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# A single entry point for legacy and independently built runtimes.
set -u
[ "$#" -eq 2 ] || { echo "usage: nano-run.sh ROOT valve|cstrike"; exit 2; }
ROOT=$1
GAME=$2
case "$GAME" in valve) SERVER=hl;; cstrike) SERVER=cs;; *) exit 2;; esac
cd "$ROOT" || exit 1
RUN_DIR=${NANO_RUN_DIR:-/run}
LOCK="$RUN_DIR/xash-nano.lock"
SOCKET="$RUN_DIR/xash-nano.sock"
FIFO=/tmp/fkgpiod.fifo
WATCH_PID=
AMP_STATE=
if ! mkdir "$LOCK" 2>/dev/null; then
    OWNER=$(cat "$LOCK/owner" 2>/dev/null)
    case "$OWNER" in ''|*[!0-9]*) echo "Unrecognized existing game lock"; exit 1;; esac
    if kill -0 "$OWNER" 2>/dev/null; then
        echo "Another Nano game launcher is running"; exit 1
    fi
    rm -f "$LOCK/owner"
    rmdir "$LOCK" || exit 1
    mkdir "$LOCK" || exit 1
fi
echo "$$" > "$LOCK/owner"
# Only remove a stale socket after establishing ownership of the launcher lock.
rm -f "$SOCKET"
LOGS="$ROOT/diagnostics/$GAME"
mkdir -p "$LOGS"
load_keys() {
    [ -p "$FIFO" ] || return 0
    sleep 0.3
    "$ROOT/nano-supervise-arm" --load-keys "$1" "$FIFO"
    KEY_STATUS=$?
    sleep 0.3
    return "$KEY_STATUS"
}
restore_volume() {
    case "$1" in ''|*[!0-9]*) return 1;; esac
    [ "$1" -le 100 ] 2>/dev/null || return 1
    if [ -f /mnt/FunKey/.asoundrc ]; then
        # USB audio uses the firmware's separate card/volume policy.
        volume set "$1"
        return $?
    fi
    # Same rounded 16..63 mapping as the firmware, without simple-mixer
    # enumeration of unrelated DAPM route controls. Quiet mode is essential:
    # non-quiet cset loads the full high-level control list for its report.
    AUDIO_PERCENT=$1
    while [ "${AUDIO_PERCENT#0}" != "$AUDIO_PERCENT" ]; do
        AUDIO_PERCENT=${AUDIO_PERCENT#0}
    done
    AUDIO_PERCENT=${AUDIO_PERCENT:-0}
    AUDIO_RAW=$((16 + (AUDIO_PERCENT * 47 + 50) / 100))
    amixer -c 0 -q cset "iface=MIXER,name='Headphone Playback Volume'" "$AUDIO_RAW" || return $?
    amixer -c 0 -q cset "iface=MIXER,name='Headphone Playback Switch'" on,on
}
cleanup() {
    trap - EXIT HUP INT TERM
    if [ -n "$WATCH_PID" ] && kill -0 "$WATCH_PID" 2>/dev/null; then
        "$ROOT/nano-supervise-arm" --stop "$SOCKET" >/dev/null 2>&1
        wait "$WATCH_PID"
    fi
    "$ROOT/nano-clk-arm" --restore >> "$ROOT/$GAME-clock.log" 2>&1
    if [ "$AMP_STATE" = 0 ]; then audio_amp off >/dev/null 2>&1; fi
    load_keys /etc/fkgpiod.conf
    if command -v termfix_all >/dev/null 2>&1; then termfix_all; fi
    rm -f "$LOCK/owner"
    rmdir "$LOCK"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
load_keys "$ROOT/nano.key" || { echo "Game keymap failed to load"; exit 1; }
CPU_MHZ=$(cat "$ROOT/cpu-mhz" 2>/dev/null)
CPU_MHZ=${CPU_MHZ:-1200}
if ! "$ROOT/nano-clk-arm" --set "$CPU_MHZ" > "$ROOT/$GAME-clock.log" 2>&1; then
    echo "Clock setup failed; see $GAME-clock.log"; exit 1
fi
# Frontend launches usually enable the amplifier. Direct/diagnostic launches
# must do so too; ALSA mixer volume alone does not power the Nano speaker.
if command -v audio_amp >/dev/null 2>&1; then
    AMP_STATE=$(cat /sys/class/gpio/gpio166/value 2>/dev/null)
    if command -v volume >/dev/null 2>&1; then
        NANO_VOLUME=$(volume get)
        case "$NANO_VOLUME" in ''|*[!0-9]*) ;; *)
            if [ "$NANO_VOLUME" -le 100 ]; then
                restore_volume "$NANO_VOLUME" >> "$ROOT/$GAME-clock.log" 2>&1 ||
                    echo "Audio volume restore incomplete; continuing with current mixer state" >> "$ROOT/$GAME-clock.log"
            fi;; esac
    fi
    audio_amp on >> "$ROOT/$GAME-clock.log" 2>&1
fi
BACKEND=$(cat "$ROOT/backend" 2>/dev/null || printf legacy)
if [ "$BACKEND" = legacy ]; then ln -sf /dev/urandom /tmp/xash-r; fi
if [ ! -f "$RUN_DIR/xash-rng-seeded" ] && [ -f "$ROOT/rng-seed" ]; then
    if "$ROOT/seed-rng-arm" "$ROOT/rng-seed"; then
        dd if=/dev/urandom of="$ROOT/rng-seed.new" bs=256 count=1 2>/dev/null
        mv "$ROOT/rng-seed.new" "$ROOT/rng-seed"
        touch "$RUN_DIR/xash-rng-seeded"
    fi
fi
export LD_LIBRARY_PATH="$ROOT:$ROOT/engine:$ROOT/engine/ref"
if [ "$BACKEND" = legacy ]; then
    export SDL_VIDEODRIVER=fbcon SDL_FBDEV=/dev/fb0 SDL_NOMOUSE=1 SDL_AUDIODRIVER=alsa AUDIODEV=default
elif [ "$BACKEND" != fbdev ]; then
    echo "Unsupported runtime backend: $BACKEND"; exit 1
fi
set -- "$ROOT/engine/xash3d" -game "$GAME" -ref soft -clientlib "$GAME/cl_dlls/client_armv7hf.so" -dll "$GAME/dlls/${SERVER}_armv7hf.so" -width 240 -height 240
[ "${NANO_DIAGNOSTIC:-0}" != 1 ] || set -- "$@" -dev 1 +s_info +volume
case "$GAME" in
    valve) set -- "$@" +map c0a0;;
    cstrike) set -- "$@" +maxplayers 4 +sv_lan 1 +exec nano-offline.cfg +map de_dust;;
esac
set -- "$@" +exec nano-controls.cfg
[ ! -f "$ROOT/$GAME/nano-settings.cfg" ] || set -- "$@" +exec nano-settings.cfg
[ "$BACKEND" != fbdev ] || [ "${NANO_PROFILE:-0}" != 1 ] || set -- "$@" +nano_profile 1
"$ROOT/nano-supervise-arm" "$LOGS" "$SOCKET" -- "$@" > "$LOGS/supervisor.log" 2>&1 &
WATCH_PID=$!
wait "$WATCH_PID"
STATUS=$?
WATCH_PID=
exit "$STATUS"
