#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fetch pinned source trees and apply the reviewed Nano patches."""
from pathlib import Path
import json
import subprocess, shutil

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT/'sources.lock.json').read_text())

def run(*args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True)

def fetch(name, source_root=None):
    target = (source_root or ROOT/'upstream')/name
    spec = LOCK[name]
    if not target.exists():
        target.mkdir(parents=True)
        run('git', 'init', str(target))
        run('git', '-C', str(target), 'remote', 'add', 'origin', spec['url'])
        run('git', '-C', str(target), 'fetch', '--depth', '1', 'origin', spec['commit'])
        run('git', '-C', str(target), 'checkout', '--detach', 'FETCH_HEAD')
    actual = subprocess.check_output(['git', '-C', str(target), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != spec['commit']:
        raise SystemExit(f'{target}: expected {spec["commit"]}, found {actual}; no files reset')
    if name == 'cs16-client':
        run('git', '-C', str(target), 'submodule', 'update', '--init', '--recursive', '--depth', '1')
    return target

def apply(target, filename):
    patch = ROOT/'patches'/filename
    already = subprocess.run(['git', 'apply', '--reverse', '--check', str(patch)], cwd=target, capture_output=True)
    if already.returncode == 0:
        print(f'{filename}: already applied')
        return
    run('git', 'apply', '--check', str(patch), cwd=target)
    run('git', 'apply', str(patch), cwd=target)

if __name__ == '__main__':
    renderer=fetch('xash3d')
    apply(renderer, 'renderer-nano.patch')
    apply(renderer, 'renderer-nano-triangles.patch')
    client=fetch('cs16-client')
    apply(client, 'cs16-nano-4141.patch')
    apply(client, 'cs16-nano-spectator.patch')
    apply(client/"3rdparty/ReGameDLL_CS", "cs16-nav-bsp-path.patch")
    apply(client/"3rdparty/mainui_cpp", "cs16-mainui-nano-menu.patch")
    for header in ("nano-menu-options.h", "nano-settings.h"):
        shutil.copy2(ROOT/"src"/header,client/"3rdparty/mainui_cpp/menus"/header)

    for patch in ("cs16-nano-look.patch", "cs16-nano-hud.patch"): apply(client,patch)
    for header in ("nano-look.h", "nano-hud-scope.h", "nano-crosshair.h"): shutil.copy2(ROOT/"src"/header,client/"cl_dll"/header)
