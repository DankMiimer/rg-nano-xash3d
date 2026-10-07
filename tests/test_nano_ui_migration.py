# SPDX-License-Identifier: MIT
"""Migration must be one-time, preserve unrelated settings, and retain relative sizes."""
from pathlib import Path
import subprocess,tempfile,re,hashlib
ROOT=Path(__file__).resolve().parents[1]
script=ROOT/'tools/nano-ui-migrate.sh'
with tempfile.TemporaryDirectory() as folder:
    for game,default in [('valve',2.0),('cstrike',.8)]:
        file=Path(folder)/game
        original='// custom preferences\nfps_max "40"\ncl_yawspeed "85"\nbind "q" "impulse 100"\nset nano_hud_bottom "1.125"\nset nano_hud_side "1.5"\nset nano_hud_menu "1.25"\nset nano_hud_radar "0.50"\n'
        file.write_text(original)
        subprocess.run(['sh',str(script),str(file),game],check=True)
        result=file.read_text()
        assert f'nano_hud_bottom "{default:.3f}"' in result
        assert f'nano_hud_side "{min(2,default*1.5/1.125):.3f}"' in result
        assert 'nano_hud_text_height "14"' in result
        for line in original.splitlines():
            if not any(x in line for x in ('nano_hud_bottom','nano_hud_side','nano_hud_menu')):assert line in result
        assert Path(str(file)+'.ui-v1.bak').read_text()==original
        first=file.read_bytes();subprocess.run(['sh',str(script),str(file),game],check=True);assert file.read_bytes()==first
        for size,target in [(.1,12),(2,18)]:
            file.write_text(f'set nano_hud_menu "{size}"\n')
            subprocess.run(['sh',str(script),str(file),game],check=True)
            assert f'nano_hud_text_height "{target}"' in file.read_text()
        assert Path(str(file)+'.ui-v1.bak').read_text()==original
        for custom in (1.5,1.75,2):
            original2=f'fps_max "60"\nset nano_hud_bottom "{custom}"\nset nano_hud_side "{custom}"\nset nano_ui_profile_version "2"\n'
            file.write_text(original2);subprocess.run(['sh',str(script),str(file),game],check=True)
            target=2 if game=='valve' and custom==1.5 else custom
            assert f'nano_hud_bottom "{target}"' in file.read_text()
            assert 'fps_max "60"' in file.read_text() and 'nano_ui_profile_version "3"' in file.read_text()
            first=file.read_bytes();subprocess.run(['sh',str(script),str(file),game],check=True);assert file.read_bytes()==first
        future='set nano_ui_profile_version \"3\"\nfps_max \"40\"\n'
        file.write_text(future);subprocess.run(['sh',str(script),str(file),game],check=True);assert file.read_text()==future
print('Migration: both defaults, relative custom sizes, bounds, unrelated settings, backup and idempotence passed.')
