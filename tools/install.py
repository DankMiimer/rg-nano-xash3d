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
    args = parser.parse_args()
    adb = ['adb'] + (['-s', args.serial] if args.serial else [])
    def run(*parts):
        subprocess.run(adb+list(parts), check=True)
    alive = subprocess.run(adb+['shell', 'pidof xash3d'], capture_output=True, text=True)
    if alive.stdout.strip():
        raise SystemExit('Quit Xash3D on the Nano before installing its runtime')
    if 'no devices' in alive.stderr or 'more than one' in alive.stderr:
        raise SystemExit(alive.stderr.strip())
    runtime = ROOT/'build/runtime'
    if not (runtime/'engine/xash3d').is_file():
        raise SystemExit('Run prepare_runtime.py first')
    run('shell', 'mkdir -p /mnt/FunKey/Xash3D "/mnt/Native games"')
    run('push', str(runtime)+ '/.', '/mnt/FunKey/Xash3D/')
    for title in ('Half-Life', 'Counter-Strike'):
        for suffix in ('opk', 'png'):
            filename = f'{title}.{suffix}'
            run('push', str(ROOT/'build/dist'/filename), f'/mnt/Native games/{filename}')
    run('shell', 'chmod +x /mnt/FunKey/Xash3D/engine/xash3d /mnt/FunKey/Xash3D/nano-clk-arm /mnt/FunKey/Xash3D/seed-rng-arm; sync')
    print('Installed. Refresh Native games or restart the frontend to reload icons.')
