#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
TASK_ROOT=$(cd "$(dirname "$0")/.." && pwd)
: "${FUNKEY_SDK:?Set FUNKEY_SDK to the extracted FunKey SDK 2.3.0 directory}"
# A Linux filesystem is considerably faster than /mnt/c when building in WSL.
TASK_NATIVE=${NANO_NATIVE_DIR:-$TASK_ROOT/build/native}
mkdir -p "$TASK_NATIVE"
TASK_NATIVE=$(cd "$TASK_NATIVE" && pwd)
python3 "$TASK_ROOT/tools/fetch_native.py" "$TASK_NATIVE"
export PATH="$FUNKEY_SDK/bin:$PATH"
export CC="$FUNKEY_SDK/bin/arm-funkey-linux-musleabihf-gcc"
export CXX="$FUNKEY_SDK/bin/arm-funkey-linux-musleabihf-g++"
export AR="$FUNKEY_SDK/bin/arm-funkey-linux-musleabihf-ar"
export STRIP="$FUNKEY_SDK/bin/arm-funkey-linux-musleabihf-strip"
export PKG_CONFIG="$FUNKEY_SDK/bin/pkg-config"
export CFLAGS='-O2 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard'
export CXXFLAGS="$CFLAGS"
export CCACHE_DIR="$TASK_NATIVE/ccache"
cd "$TASK_NATIVE/xash3d"
python3 waf configure --enable-fbdev --disable-gl --low-memory-mode=1 --enable-stbtt --disable-werror -T release --prefix=/ --out="$TASK_NATIVE/engine-build"
python3 waf build -j"${JOBS:-4}"
python3 waf install --destdir="$TASK_NATIVE/engine-install"
cmake -S "$TASK_NATIVE/hlsdk" -B "$TASK_NATIVE/hl-build" -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$FUNKEY_SDK/share/buildroot/toolchainfile.cmake" -DCMAKE_BUILD_TYPE=Release \
  '-DCMAKE_C_FLAGS=-O2 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -fPIC' \
  '-DCMAKE_CXX_FLAGS=-O2 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -fPIC' \
  -DCMAKE_INSTALL_PREFIX="$TASK_NATIVE/hl-install"
cmake --build "$TASK_NATIVE/hl-build" --parallel "${JOBS:-4}"
cmake --install "$TASK_NATIVE/hl-build"
echo "Source-built engine and Half-Life libraries: $TASK_NATIVE"
