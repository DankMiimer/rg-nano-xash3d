#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
TASK_ROOT=$(cd "$(dirname "$0")/.." && pwd)
: "${FUNKEY_SDK:?Set FUNKEY_SDK to the extracted FunKey SDK 2.3.0 directory}"
export PATH="$FUNKEY_SDK/bin:$PATH"
export CCACHE_DIR="$TASK_ROOT/build/ccache"
TASK_CC="$FUNKEY_SDK/bin/arm-funkey-linux-musleabihf-gcc"
TASK_TOOLCHAIN="$FUNKEY_SDK/share/buildroot/toolchainfile.cmake"
test -x "$TASK_CC"
test -f "$TASK_TOOLCHAIN"
mkdir -p "$TASK_ROOT/build/bin"
python3 "$TASK_ROOT/tools/fetch_sources.py"
cmake -S "$TASK_ROOT/upstream/cs16-client" -B "$TASK_ROOT/build/cs" -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$TASK_TOOLCHAIN" -DCMAKE_BUILD_TYPE=Release \
  '-DCMAKE_C_FLAGS=-O2 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -fPIC' \
  '-DCMAKE_CXX_FLAGS=-O2 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -fPIC' \
  -DCMAKE_INSTALL_PREFIX="$TASK_ROOT/build/cs-install"
cmake --build "$TASK_ROOT/build/cs" --parallel "${JOBS:-4}"
cmake --install "$TASK_ROOT/build/cs"
cmake -S "$TASK_ROOT/renderer" -B "$TASK_ROOT/build/renderer" -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$TASK_TOOLCHAIN" \
  '-DCMAKE_C_FLAGS=-O2 -mfpu=neon-vfpv4 -mfloat-abi=hard -fPIC'
cmake --build "$TASK_ROOT/build/renderer" --parallel "${JOBS:-4}"
"$TASK_CC" -O2 -static "$TASK_ROOT/src/nano-clk.c" -o "$TASK_ROOT/build/bin/nano-clk-arm"
"$TASK_CC" -O2 -static "$TASK_ROOT/src/seed-rng.c" -o "$TASK_ROOT/build/bin/seed-rng-arm"
"$TASK_CC" -O2 -static -Wall -Wextra -Werror "$TASK_ROOT/src/nano-supervise.c" -o "$TASK_ROOT/build/bin/nano-supervise-arm"
echo 'Built CS client/server, software renderer and launch helpers.'
