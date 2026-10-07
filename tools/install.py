#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Install a locally assembled runtime; retain saves on existing installations."""
from pathlib import Path
import argparse
import subprocess

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', help='ADB serial when multiple devices are connected')
    parser.add_argument('--native', action='store_true', help='Install separate source-built entries')
    args = parser.parse_args()
    device_root='/mnt/FunKey/Xash3D-source' if args.native else '/mnt/FunKey/Xash3D'
    dist=ROOT/'build'/('native-dist' if args.native else 'dist')
    suffix=' (source)' if args.native else ''
    adb = ['adb'] + (['-s', args.serial] if args.serial else [])
    def run(*parts):
        subprocess.run(adb+list(parts), check=True)
    alive = subprocess.run(adb+['shell', 'pidof xash3d'], capture_output=True, text=True)
    if alive.stdout.strip():
        raise SystemExit('Quit Xash3D on the Nano before installing its runtime')
    if 'no devices' in alive.stderr or 'more than one' in alive.stderr:
        raise SystemExit(alive.stderr.strip())
    runtime = ROOT/'build'/('native-runtime' if args.native else 'runtime')
    if not (runtime/'engine/xash3d').is_file():
        raise SystemExit('Run prepare_native.py first' if args.native else 'Run prepare_runtime.py first')
    run('shell', f'mkdir -p {device_root} "/mnt/Native games"')
    run('push', str(runtime)+ '/.', device_root+'/')
    label_suffix=suffix
    for title in ('Half-Life', 'Counter-Strike'):
        for extension in ('opk', 'png'):
            filename = f'{title}{label_suffix}.{extension}'
            run('push', str(dist/filename), f'/mnt/Native games/{filename}')
    run('shell', 'chmod +x '+ ' '.join(device_root+'/'+path for path in ('engine/xash3d','nano-clk-arm','seed-rng-arm','nano-supervise-arm','nano-art-arm','nano-run.sh'))+'; sync')
    print('Installed. Refresh Native games or restart the frontend to reload icons.')
