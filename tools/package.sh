#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
TASK_ROOT=$(cd "$(dirname "$0")/.." && pwd)
python3 "$TASK_ROOT/tools/package_launchers.py"
for TASK_GAME in valve cstrike; do
  chmod +x "$TASK_ROOT/build/launcher-stage/$TASK_GAME/launch.sh"
done
mksquashfs "$TASK_ROOT/build/launcher-stage/valve" "$TASK_ROOT/build/dist/Half-Life.opk" \
  -noappend -comp gzip -no-xattrs -all-root -processors 1
mksquashfs "$TASK_ROOT/build/launcher-stage/cstrike" "$TASK_ROOT/build/dist/Counter-Strike.opk" \
  -noappend -comp gzip -no-xattrs -all-root -processors 1
