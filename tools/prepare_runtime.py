#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Assemble a PRIVATE runtime from user-owned assets and external dependencies."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT/'sources.lock.json').read_text())

def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)

def patch_bytes(path, old, new):
    data = path.read_bytes()
    if len(old) != len(new) or data.count(old) != 1:
        raise RuntimeError(f'{path.name}: expected one exact binary string; refusing to patch')
    path.write_bytes(data.replace(old, new))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--games', type=Path, required=True, help='Your Half-Life installation containing valve and cstrike')
    parser.add_argument('--opk', type=Path, required=True, help='The pinned external XASH3DFS release OPK')
    parser.add_argument('--device-sdl', type=Path, required=True, help="Nano's /usr/lib/libSDL-1.2.so.0, copied via ADB")
    parser.add_argument('--font', type=Path, required=True, help='A font you may use locally, preferably SIL-OFL Fira Sans')
    parser.add_argument('--nav', type=Path, help='Optional matching de_dust.nav generated from your game')
    parser.add_argument('--ca-bundle', type=Path, default=Path('/etc/ssl/certs/ca-certificates.crt'))
    args = parser.parse_args()
    digest = hashlib.sha256(args.opk.read_bytes()).hexdigest()
    if digest != LOCK['xash3dfs-opk']['sha256']:
        raise SystemExit('XASH3DFS OPK hash mismatch; this recipe targets the pinned release only')
    for game in ('valve', 'cstrike'):
        if not (args.games/game/'game.ico').is_file():
            raise SystemExit(f'Missing {game}/game.ico in your game installation')
    runtime = ROOT/'build/runtime'
    extracted = ROOT/'build/external-opk'
    if runtime.exists() or extracted.exists():
        raise SystemExit('build/runtime or build/external-opk already exists; use a fresh build workspace')
    subprocess.run(['unsquashfs', '-d', str(extracted), str(args.opk.resolve())], check=True)
    runtime.mkdir()
    omitted_dirs = {'save', 'controller_configs', 'manual', '.fontcache'}
    omitted_files = {'config.cfg', 'autoexec.cfg', 'userconfig.cfg', 'steam_autocloud.vdf'}
    for game in ('valve', 'cstrike'):
        for source in (args.games/game).rglob('*'):
            rel = source.relative_to(args.games)
            if not source.is_file() or source.suffix.lower() in {'.dll', '.exe', '.asi', '.so', '.dylib'}:
                continue
            if any(p.lower() in omitted_dirs for p in rel.parts) or source.name.lower() in omitted_files:
                continue
            copy(source, runtime/rel)
    for source in extracted.rglob('*'):
        if not source.is_file():
            continue
        rel = source.relative_to(extracted)
        if rel.parts[0] == 'valve':
            if source.name != 'config.cfg':
                copy(source, runtime/rel)
        elif source.name == 'xash3d' or '.so' in source.name:
            copy(source, runtime/'engine'/rel)
    copy(runtime/'engine/filesystem_stdio.so', runtime/'filesystem_stdio.so')
    patch_bytes(runtime/'engine/libxash.so', b'/dev/random\0', b'/tmp/xash-r\0')
    copy(args.device_sdl, runtime/'engine/libSDL-1.2.so.0')
    patch_bytes(runtime/'engine/libSDL-1.2.so.0', b'/dev/dsp\0', b'default\0\0')
    cs = ROOT/'build/cs-install/cstrike'
    for rel in ('cl_dlls/client_armv7hf.so', 'cl_dlls/menu_armv7hf.so', 'dlls/cs_armv7hf.so', 'extras.pk3'):
        copy(cs/rel, runtime/'cstrike'/rel)
    copy(ROOT/'build/renderer/libref_soft.so', runtime/'engine/ref/libref_soft.so')
    for helper in ('nano-clk-arm', 'seed-rng-arm', 'nano-supervise-arm'):
        copy(ROOT/'build/bin'/helper, runtime/helper)
    copy(ROOT/'tools/nano-run.sh', runtime/'nano-run.sh')
    (runtime/'backend').write_text('legacy\n')
    for name in ('tahoma.ttf', 'FiraSans-Regular.ttf'):
        copy(args.font, runtime/'valve/gfx/fonts'/name)
    if args.nav:
        copy(args.nav, runtime/'cstrike/maps/de_dust.nav')
    if args.ca_bundle.is_file():
        copy(args.ca_bundle, runtime/'cacert.pem')
    (runtime/'rng-seed').write_bytes(os.urandom(256))
    (runtime/'cpu-mhz').write_text('1200\n')
    subprocess.run(['python3', str(ROOT/'tools/extract_icons.py'), '--games', str(args.games.resolve())], check=True)
    subprocess.run(['bash', str(ROOT/'tools/package.sh')], check=True)
    with tarfile.open(ROOT/'build/configs.tar') as archive:
        archive.extractall(runtime, filter='data')
    print(f'Private runtime prepared at {runtime}. Do not upload this directory or generated OPKs/icons.')

if __name__ == '__main__':
    main()
