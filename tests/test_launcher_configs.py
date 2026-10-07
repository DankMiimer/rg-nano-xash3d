# SPDX-License-Identifier: GPL-3.0-or-later
"""Generated native configs equal the device-approved UI profile 3 files; keymaps are relocatable."""
from pathlib import Path
import subprocess, sys
r = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(r/'tools/make_icons.py'), str(r/'build/test-icons')], check=True, stdout=subprocess.DEVNULL)
subprocess.run([sys.executable, str(r/'tools/package_launchers.py'), '--native', '--release', '--icons', str(r/'build/test-icons')],
               check=True, stdout=subprocess.DEVNULL)
stage = r/'build/config-stage'
for game in ('valve', 'cstrike'):
    produced = (stage/game/'nano-controls.cfg').read_text()
    expected = (r/'tests/data'/f'nano-controls-{game}.cfg').read_text()
    assert produced == expected, f'{game}/nano-controls.cfg no longer matches the approved device file'
    assert (stage/game/'userconfig.cfg').read_text() == 'exec nano-controls.cfg\n'
listen = (stage/'cstrike/listenserver.cfg').read_text()
assert listen.endswith('exec nano-offline.cfg\n') and (stage/'cstrike/nano-listenserver.cfg').read_text() == listen
for key in ('nano.key', 'nano-face.key'):
    text = (stage/key).read_text()
    assert '@ROOT@/nano-supervise-arm --stop /run/xash-nano.sock' in text and '/mnt/FunKey' not in text, key
desktop = (r/'build/release-launcher-stage/valve/valve.funkey-s.desktop').read_text()
assert 'Name=Half-Life\n' in desktop and 'Exec=launch.sh' in desktop
assert 'ROOT=/mnt/FunKey/Xash3D-source' in (r/'build/release-launcher-stage/valve/launch.sh').read_text()
print('Launcher configs: native controls match the approved device files; listen-server copy, relocatable keymaps and release launchers checked.')
