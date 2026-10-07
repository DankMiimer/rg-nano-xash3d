#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# A single entry point for legacy and independently built runtimes.
set -u
[ "$#" -eq 2 ] || [ "$#" -eq 3 ] || { echo "usage: nano-run.sh ROOT valve|cstrike [resume]"; exit 2; }
ROOT=$1
GAME=$2
MODE=${3:-}
case "$GAME" in valve) SERVER=hl;; cstrike) SERVER=cs;; *) exit 2;; esac
case "$MODE" in ''|resume) ;; *) exit 2;; esac
cd "$ROOT" || exit 1
RUN_DIR=${NANO_RUN_DIR:-/run}
LOCK="$RUN_DIR/xash-nano.lock"
SOCKET="$RUN_DIR/xash-nano.sock"
FIFO=/tmp/fkgpiod.fifo
WATCH_PID=
AMP_STATE=
POWER=0
POWER_GUARD=
export NANO_POWER_FLAG="$RUN_DIR/xash-nano.power-saved"
# FunKey OS draws this text over whatever is on screen.
say() { command -v notif >/dev/null 2>&1 && notif set "$1" "$2"; }
missing() {
    for MISSING_FILE in "$@"; do [ -f "$ROOT/$MISSING_FILE" ] || return 0; done
    return 1
}
if missing valve/liblist.gam valve/halflife.wad; then
    echo "Half-Life game files not found in $ROOT/valve"
    say 8 "^^^   HALF-LIFE FILES MISSING^^ Copy your valve folder into^   FunKey/Xash3D-source^^"
    exit 1
fi
if [ "$GAME" = cstrike ] && missing cstrike/liblist.gam cstrike/cstrike.wad; then
    echo "Counter-Strike game files not found in $ROOT/cstrike"
    say 8 "^^^ COUNTER-STRIKE FILES MISSING^^Copy your cstrike folder into^   FunKey/Xash3D-source^^"
    exit 1
fi
# Steam's listenserver.cfg replaces ours when game files are copied after the release;
# CS match setup needs ours to apply nano-offline.cfg when the server starts.
LISTEN="$ROOT/cstrike/listenserver.cfg"
if [ "$GAME" = cstrike ] && [ -f "$ROOT/cstrike/nano-listenserver.cfg" ] && ! grep -q 'exec nano-offline.cfg' "$LISTEN" 2>/dev/null; then
    [ ! -f "$LISTEN" ] || mv -f "$LISTEN" "$LISTEN.steam"
    cp "$ROOT/cstrike/nano-listenserver.cfg" "$LISTEN"
fi
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
rm -f "$SOCKET" "$NANO_POWER_FLAG"
LOGS="$ROOT/diagnostics/$GAME"
mkdir -p "$LOGS"
rm -f "$LOGS/child.pid"
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
power_off_now() {
    if [ "${NANO_POWER_TEST:-0}" = 1 ]; then echo "power test: would power off now"; return 0; fi
    exec powerdown now
}
# FunKey OS sends SIGUSR1 when the console powers off (FunKey S lid, RG Nano power
# button) and powers off 0.1 s later unless the running game cancels that schedule.
# Builtins only until the cancel, so it happens well inside that window.
on_power() {
    [ "$POWER" = 0 ] || return 0
    CHILD=
    COMM=
    read -r CHILD 2>/dev/null < "$LOGS/child.pid"
    case "$CHILD" in ''|*[!0-9]*) return 0;; esac
    read -r COMM 2>/dev/null < "/proc/$CHILD/comm"
    [ "$COMM" = xash3d ] || return 0
    pkill -f "powerdown schedule" 2>/dev/null
    POWER=1
    [ "$GAME" != valve ] || say 0 "^^^^^^^^          SAVING...^^^^^^^^"
    kill -USR1 "$CHILD" 2>/dev/null
    # Never leave a closed console running: stop the game, then power off regardless.
    ( sleep 12; "$ROOT/nano-supervise-arm" --stop "$SOCKET"; sleep 8; power_off_now ) >/dev/null 2>&1 &
    POWER_GUARD=$!
}
# Resume through FunKey OS Instant Play on the next power-on, like its emulators.
write_resume() {
    case "$ROOT" in *"'"*) return 1;; esac
    RESUME_FILE=/mnt/instant_play
    [ "${NANO_POWER_TEST:-0}" != 1 ] || RESUME_FILE="$RUN_DIR/xash-nano.instant_play"
    printf "'%s/nano-run.sh' '%s' '%s' 'resume' &\npid record \$!\nwait \$!\npid erase\n" \
        "$ROOT" "$ROOT" "$GAME" > "$RESUME_FILE.tmp" && mv "$RESUME_FILE.tmp" "$RESUME_FILE"
}
power_off() {
    [ -z "$POWER_GUARD" ] || kill "$POWER_GUARD" 2>/dev/null
    RESUME=0
    [ "$GAME" != valve ] || [ ! -f "$NANO_POWER_FLAG" ] || RESUME=1
    rm -f "$NANO_POWER_FLAG"
    cleanup
    if [ "$RESUME" = 1 ]; then write_resume || echo "Resume file not written" >> "$LOGS/supervisor.log"; fi
    echo "power-off: resume=$RESUME" >> "$LOGS/supervisor.log"
    if [ "${NANO_POWER_TEST:-0}" = 1 ]; then notif clear 2>/dev/null; fi
    power_off_now
    exit 0
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
trap on_power USR1
BACKEND=$(cat "$ROOT/backend" 2>/dev/null)
BACKEND=${BACKEND:-legacy}
CONTROL_SCHEME=0
if [ "$BACKEND" = fbdev ] && [ -f "$ROOT/$GAME/nano-control.cfg" ]; then
    CONTROL_BYTES=$(wc -c < "$ROOT/$GAME/nano-control.cfg")
    if [ "$CONTROL_BYTES" -le 9 ]; then
        CONTROL_LINE=
        IFS= read -r CONTROL_LINE < "$ROOT/$GAME/nano-control.cfg" || true
        [ "$CONTROL_LINE" != "scheme 1" ] || CONTROL_SCHEME=1
    fi
fi
# Firmware key maps hold the stop command's absolute path; write them for this location.
KEYMAP="$ROOT/nano.key"
[ "$CONTROL_SCHEME" != 1 ] || KEYMAP="$ROOT/nano-face.key"
if grep -q '@ROOT@' "$KEYMAP" 2>/dev/null; then
    sed "s|@ROOT@|$ROOT|g" "$KEYMAP" > "$RUN_DIR/xash-nano.key" && KEYMAP="$RUN_DIR/xash-nano.key"
fi
load_keys "$KEYMAP" || { echo "Game keymap failed to load"; exit 1; }
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
# First launch: build the menu artwork from the player's own game files.
case "$GAME" in valve) ART_SOURCE=resource/logo.tga;; *) ART_SOURCE=resource/game_menu.tga;; esac
if [ -x "$ROOT/nano-art-arm" ] && [ -f "$ROOT/$GAME/$ART_SOURCE" ] && [ ! -f "$ROOT/$GAME/gfx/nano/menu_background.tga" ]; then
    say 0 "^^^^^^^^   PREPARING MENU ARTWORK...^^^^^^^^"
    "$ROOT/nano-art-arm" "$ROOT" "$GAME" > "$LOGS/art.log" 2>&1
    notif clear 2>/dev/null
fi
# Release OPKs carry a placeholder icon; put the game's own icon from game.ico in its place.
OPK_FILE=$(cat /mnt/last_opk 2>/dev/null)
case "$OPK_FILE" in
    *.opk) [ ! -x "$ROOT/nano-art-arm" ] || "$ROOT/nano-art-arm" --icon "$ROOT" "$GAME" "$OPK_FILE" >> "$LOGS/art.log" 2>&1;;
esac
BACKEND=$(cat "$ROOT/backend" 2>/dev/null || printf legacy)
if [ "$BACKEND" = legacy ]; then ln -sf /dev/urandom /tmp/xash-r; fi
[ -f "$ROOT/rng-seed" ] || dd if=/dev/urandom of="$ROOT/rng-seed" bs=256 count=1 2>/dev/null
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
    valve)
        if [ "$MODE" = resume ] && [ -f "$ROOT/valve/save/nano_poweroff.sav" ]; then
            set -- "$@" -nointro +load nano_poweroff
        else
            set -- "$@" +map c0a0
        fi;;
    cstrike)
        if [ "$BACKEND" = fbdev ]; then
            set -- "$@" +maxplayers 8 +sv_lan 1
        else
            set -- "$@" +maxplayers 4 +sv_lan 1 +exec nano-offline.cfg +map de_dust
        fi;;
esac
if [ "$BACKEND" = fbdev ] && [ -f "$ROOT/nano-ui-migrate.sh" ]; then
    sh "$ROOT/nano-ui-migrate.sh" "$ROOT/$GAME/nano-settings.cfg" "$GAME" ||
        echo "HUD migration failed; original settings retained" >> "$LOGS/supervisor.log"
fi
set -- "$@" +exec nano-controls.cfg
[ ! -f "$ROOT/$GAME/nano-settings.cfg" ] || set -- "$@" +exec nano-settings.cfg
if [ "$BACKEND" = fbdev ]; then
    set -- "$@" +nano_control_scheme "$CONTROL_SCHEME"
    [ "$CONTROL_SCHEME" != 1 ] || set -- "$@" +exec nano-face-controls.cfg
fi
[ "$GAME" != cstrike ] || [ "$BACKEND" != fbdev ] || set -- "$@" +menu_nano_match
[ "$BACKEND" != fbdev ] || [ "${NANO_PROFILE:-0}" != 1 ] || set -- "$@" +nano_profile 1
"$ROOT/nano-supervise-arm" "$LOGS" "$SOCKET" -- "$@" > "$LOGS/supervisor.log" 2>&1 &
WATCH_PID=$!
# A trapped power-off signal interrupts wait; keep waiting until the supervisor ends.
while :; do
    wait "$WATCH_PID"
    STATUS=$?
    kill -0 "$WATCH_PID" 2>/dev/null || break
done
WATCH_PID=
[ "$POWER" = 0 ] || power_off
exit "$STATUS"
