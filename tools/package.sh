#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
TASK_ROOT=$(cd "$(dirname "$0")/.." && pwd)
python3 "$TASK_ROOT/tools/package_launchers.py" "$@"
if [[ "${1:-}" == --native ]]; then
  TASK_STAGE=native-launcher-stage
  TASK_DIST=native-dist
  TASK_SUFFIX=' (source)'
else
  TASK_STAGE=launcher-stage
  TASK_DIST=dist
  TASK_SUFFIX=''
fi
for TASK_GAME in valve cstrike; do
  chmod +x "$TASK_ROOT/build/$TASK_STAGE/$TASK_GAME/launch.sh"
done
mksquashfs "$TASK_ROOT/build/$TASK_STAGE/valve" "$TASK_ROOT/build/$TASK_DIST/Half-Life$TASK_SUFFIX.opk" \
  -noappend -comp gzip -no-xattrs -all-root -processors 1
mksquashfs "$TASK_ROOT/build/$TASK_STAGE/cstrike" "$TASK_ROOT/build/$TASK_DIST/Counter-Strike$TASK_SUFFIX.opk" \
  -noappend -comp gzip -no-xattrs -all-root -processors 1
