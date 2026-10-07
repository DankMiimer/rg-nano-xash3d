# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[1]
text=(root/'tools/nano-run.sh').read_text()
start=text.index('set -- "$ROOT/engine/xash3d"');end=text.index('\n"$ROOT/nano-supervise-arm"',start)
with tempfile.TemporaryDirectory() as directory:
    base=Path(directory);(base/'cstrike').mkdir();(base/'valve').mkdir()
    for game in ('cstrike','valve'):(base/game/'nano-settings.cfg').write_text('saved settings')
    script=base/'argv.sh'
    script.write_text('ROOT=$1\nGAME=$2\nBACKEND=$3\nSERVER=cs\nCONTROL_SCHEME=${4:-0}\n'+text[start:end]+'\nprintf "%s\\0" "$@"\n')
    def args(game,backend,scheme=0):
        env={**os.environ,'NANO_PROFILE':'1','NANO_DIAGNOSTIC':'0'}
        output=subprocess.check_output(['sh',str(script),str(base),game,backend,str(scheme)],env=env)
        return output.decode().rstrip('\0').split('\0')
    cs=args('cstrike','fbdev');hl=args('valve','fbdev');legacy=args('cstrike','legacy')
    assert '+map' not in cs and '+menu_nano_match' in cs and cs[cs.index('+maxplayers')+1]=='8'
    assert cs.index('nano-controls.cfg')<cs.index('nano-settings.cfg')<cs.index('+menu_nano_match')
    assert hl[hl.index('+map')+1]=='c0a0' and '+menu_nano_match' not in hl
    assert legacy[legacy.index('+map')+1]=='de_dust' and '+menu_nano_match' not in legacy
    face=args('cstrike','fbdev',1);assert face[face.index('+nano_control_scheme')+1]=='1'
    assert face.index('nano-settings.cfg')<face.index('nano-face-controls.cfg')<face.index('+menu_nano_match')
    assert 'nano-face-controls.cfg' not in args('valve','legacy',1)
    assert '+exec' in legacy and 'nano-offline.cfg' in legacy
print('Actual launcher argv: CS match setup after saved controls/settings; HL and legacy map startup retained.')

# Exercise the actual strict launch-time preference/keymap selection.
text=(root/'tools/nano-run.sh').read_text()
start=text.index('BACKEND=$(cat "$ROOT/backend"');end=text.index('load_keys "$KEYMAP"',start)
with tempfile.TemporaryDirectory() as directory:
    base=Path(directory);(base/'cstrike').mkdir();(base/'backend').write_text('fbdev\n')
    script=base/'select.sh';script.write_text('ROOT=$1\nGAME=cstrike\n'+text[start:end]+'\nprintf "%s" "$CONTROL_SCHEME"\n')
    for pref,want in [('scheme 1\n','1'),('scheme 1','1'),('scheme 0\n','0'),('scheme 1;quit\n','0'),('scheme 1\nquit\n','0'),('scheme  1\n','0'),('scheme 1\r\n','0')]:
        (base/'cstrike/nano-control.cfg').write_text(pref)
        assert subprocess.check_output(['sh',str(script),str(base)],text=True)==want,pref
print('Strict per-game control preference: valid optional preset selected; malformed/oversized data retains original controls.')
