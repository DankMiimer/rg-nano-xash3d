# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import argparse, shutil, tarfile, re
parser=argparse.ArgumentParser()
parser.add_argument("--native",action="store_true")
parser.add_argument("--runtime-root")
parser.add_argument("--release",action="store_true",help="Public build: plain titles and original icons")
parser.add_argument("--icons",help="Directory with valve.png and cstrike.png (default build/icons)")
args=parser.parse_args()
runtime_root=args.runtime_root or ("/mnt/FunKey/Xash3D-source" if args.native else "/mnt/FunKey/Xash3D")
if not re.fullmatch(r"/mnt/FunKey/[A-Za-z0-9_-]+",runtime_root): parser.error("Invalid runtime directory")
base=Path(__file__).resolve().parents[1]/'build'
icons=Path(args.icons) if args.icons else base/'icons'
out=base/('release-dist' if args.release else 'native-dist' if args.native else 'dist')
out.mkdir(exist_ok=True)
stage=base/('release-launcher-stage' if args.release else 'native-launcher-stage' if args.native else 'launcher-stage')
common='''// RG Nano controls and modest memory settings.
unbindall
bind "ESCAPE" "cancelselect"
bind "UPARROW" "+forward"
bind "DOWNARROW" "+back"
bind "LEFTARROW" "+left"
bind "RIGHTARROW" "+right"
bind "ENTER" "+use"
bind "SPACE" "+jump"
bind "e" "+reload"
bind "v" "+attack"
// R switches forward/back to pitch and turn keys to strafe.
alias "+nano_rlook" "+strafe; +klook"
alias "-nano_rlook" "-strafe; -klook"
bind "g" "+nano_rlook"
// Precise camera speed is the default; L temporarily gives fast look.
cl_yawspeed "70"
cl_pitchspeed "75"
set nano_aim_yaw "70"
set nano_aim_pitch "75"
set nano_aim_fast_multiplier "3"
alias "+nano_aim" "nano_look_fast 1; cl_yawspeed 210; cl_pitchspeed 225"
alias "-nano_aim" "nano_look_fast 0; cl_yawspeed 70; cl_pitchspeed 75"
bind "t" "+nano_aim"
nano_look_accel "1"
nano_look_fast "0"
nano_look_delay "0.15"
nano_look_ramp "0.75"
nano_look_max_yaw "210"
nano_hud_profile "1"
nano_hud_element_scale "1"
nano_hud_anchor_x "0"
nano_hud_anchor_y "0"
nano_hud_offset_x "0"
nano_hud_offset_y "0"
nano_hud_pixel_coordinates "0"
set nano_hud_bottom "1.5"
set nano_hud_side "1.5"
set nano_hud_radar "0.5"
set nano_hud_menu "1"
set nano_hud_text_height "14"
set nano_ui_profile_version "2"
set nano_hud_crosshair "2"
set nano_hud_identity "1"
bind "z" "centerview"
bind "c" "+duck"
cl_himodels "0"
cl_allowdownload "0"
cl_allowupload "0"
mp_decals "64"
r_decals "128"
hud_fontrender "0"
hud_scale "1"
hud_scale_minimal_width "320"
con_fontrender "0"
touch_enable "0"
joy_enable "0"
cmd_scripting "1"
fps_max "30"
set nano_fps_limit "1"
set nano_fps_value "30"
// The software framebuffer has no VSync wait; retain the explicit frame cap.
gl_vsync "0"
set nano_frame_sleep "1"
scr_drawversion "0"
name "RG Nano"
'''
data=base/'config-stage'
for game,title,server,extra in [
 ('valve','Half-Life','hl',' +map c0a0'),
 ('cstrike','Counter-Strike','cs',' +maxplayers 4 +sv_lan 1 +exec nano-offline.cfg +map de_dust')]:
    if args.native and not args.release: title += " (source)"
    target=stage/game
    target.mkdir(parents=True,exist_ok=True)
    (target/'xash3d.png').unlink(missing_ok=True)
    launcher=f'''#!/bin/sh
ROOT={runtime_root}
exec "$ROOT/nano-run.sh" "$ROOT" {game}
'''
    (target/'launch.sh').write_text(launcher,newline='\n')
    (target/f'{game}.funkey-s.desktop').write_text(f'[Desktop Entry]\nName={title}\nComment={title} for RG Nano and FunKey S\nExec=launch.sh\nIcon={game}\nTerminal=false\nType=Application\nStartupNotify=false\nCategories=games;\n',newline='\n')
    shutil.copy2(icons/f'{game}.png',target/f'{game}.png')
    shutil.copy2(icons/f'{game}.png',out/f'{title}.png')
    cfgdir=data/game
    cfgdir.mkdir(parents=True,exist_ok=True)
    binds='bind "1" "+lookup"\nbind "3" "+lookdown"\nbind "2" "+attack2"\nbind "4" "savequick"\nbind "5" "loadquick"\nbind "p" "impulse 100"\nbind "f" "invnext"\n'
    if game=='cstrike':
        binds=''.join(f'bind "{i}" "slot{i}"\n' for i in range(1,4))
        binds+='bind "4" "+attack2"\nbind "5" "nano_centerview"\nbind "6" "slot4"\nbind "7" "slot5"\n'
        binds+='cl_oldtouchmenus "0"\n_vgui_menus "0"\nhud_fastswitch "1"\nspec_pip_allow "0"\nspec_pip_internal "0"\ncl_corpsestay "5"\ncl_shadows "0"\nbind "p" "buy"\nbind "f" "autobuy"\n'
    game_common=common
    if not args.native:
        game_common=game_common.replace('hud_scale \"1\"','hud_scale \"0.65\"').replace('set nano_hud_bottom \"1.5\"','set nano_hud_bottom \"1.125\"').replace('set nano_hud_side \"1.5\"','set nano_hud_side \"1.125\"').replace('set nano_hud_menu \"1\"','set nano_hud_menu \"1.25\"')
        game_common=re.sub(r'^set nano_(hud_text_height|ui_profile_version).*\n','',game_common,flags=re.M)
    if game=='cstrike':
        game_common=game_common.replace('set nano_hud_bottom "1.5"','set nano_hud_bottom "0.8"').replace('set nano_hud_side "1.5"','set nano_hud_side "0.8"')
    else:
        game_common=game_common.replace('set nano_hud_crosshair "2"','set nano_hud_crosshair "1.5"')
    controls=re.sub(r'bind "([A-Z])"([^\n]*)',lambda m: 'bind "'+m[1].lower()+'"'+m[2]+'\nbind "'+m[1]+'"'+m[2],game_common+binds)
    (cfgdir/'nano-controls.cfg').write_text(controls,newline='\n')
    face_commands=['+forward','+back','+moveleft','+moveright','+right','+lookdown','+lookup','+left',
                   '+attack','+reload','buy' if game=='cstrike' else '+use','+duck','+jump','invnext','invprev',
                   '+attack2','+use' if game=='cstrike' else 'impulse 100','nano_centerview']
    face_cfg='// Optional face-button aim; firmware inputs are routed by the native engine.\n'
    face_cfg+=''.join(f'bind "0x{206+i:x}" "{action}"\n' for i,action in enumerate(face_commands,1))
    if game=='cstrike':face_cfg+='_extended_menus "0"\ncl_oldtouchmenus "1"\n_vgui_menus "0"\nhud_fastswitch "1"\n'
    (cfgdir/'nano-face-controls.cfg').write_text(face_cfg,newline='\n')
    (cfgdir/'userconfig.cfg').write_text('exec nano-controls.cfg\n',newline='\n')
    if game=='cstrike':
        (cfgdir/'nano-offline.cfg').write_text('bot_quota 2\nbot_join_after_player 1\nbot_difficulty 0\nmp_startmoney 16000\nmp_freezetime 1\nmp_roundtime 1\nmp_timelimit 0\n',newline='\n')
        listen='sv_aim 0\npausable 0\nsv_maxspeed 320\nsv_cheats 0\nexec nano-offline.cfg\n'
        (cfgdir/'listenserver.cfg').write_text(listen,newline='\n')
        # Steam's own listenserver.cfg can replace ours; nano-run.sh restores it from this copy.
        (cfgdir/'nano-listenserver.cfg').write_text(listen,newline='\n')
keymap='''CLEAR
MAP FN       TO KEY     KEY_C
MAP START    TO KEY     KEY_P
MAP UP       TO KEY     KEY_PAGEUP
MAP LEFT     TO KEY     KEY_RIGHT
MAP DOWN     TO KEY     KEY_PAGEDOWN
MAP RIGHT    TO KEY     KEY_END
MAP FN+LEFT  TO KEY     KEY_1
MAP FN+DOWN  TO KEY     KEY_2
MAP FN+RIGHT TO KEY     KEY_3
MAP R        TO KEY     KEY_G
MAP L        TO KEY     KEY_T
MAP A        TO KEY     KEY_ENTER
MAP B        TO KEY     KEY_SPACE
MAP X        TO KEY     KEY_V
MAP Y        TO KEY     KEY_E
MAP MENU     TO KEY     KEY_ESC
MAP FN+START TO KEY     KEY_F
MAP FN+UP    TO COMMAND snapshot
MAP FN+A     TO COMMAND volume up
MAP FN+Y     TO COMMAND volume down
MAP FN+X     TO COMMAND brightness up
MAP FN+B     TO COMMAND brightness down
MAP FN+L     TO KEY     KEY_4
MAP FN+R     TO KEY     KEY_5
MAP FN+START+L TO KEY    KEY_6
MAP FN+START+R TO KEY    KEY_7
MAP FN+L+R   TO COMMAND @ROOT@/nano-supervise-arm --stop /run/xash-nano.sock
MAP FN+START+L+R TO COMMAND system_stats toggle
'''
# nano-run.sh replaces @ROOT@ with the installed location before loading the keymap.
(data/'nano.key').write_text(keymap,newline='\n')
# The first 71 key-name table indices equal Linux codes on the installed daemon.
# Send each button independently: firmware chords would consume R and lose simultaneous actions.
face_keymap="CLEAR\n"
physical=['UP','DOWN','LEFT','RIGHT','A','B','X','Y','L','R','START','FN']
raw_keys=[f'KEY_F{i}' for i in range(1,11)]+['KEY_NUMLOCK','KEY_SCROLLLOCK']
face_keymap+=''.join(f'MAP {button} TO KEY {key}\n' for button,key in zip(physical,raw_keys))
face_keymap+='MAP MENU TO KEY KEY_ESC\n'
face_keymap+='MAP FN+L+R TO COMMAND @ROOT@/nano-supervise-arm --stop /run/xash-nano.sock\n'
face_keymap+='MAP FN+START+L+R TO COMMAND system_stats toggle\n'
for button,command in [('A','volume up'),('Y','volume down'),('X','brightness up'),('B','brightness down')]:
    face_keymap+=f'MAP FN+START+{button} TO COMMAND {command}\n'
(data/'nano-face.key').write_text(face_keymap,newline='\n')
with tarfile.open(base/'configs.tar','w') as archive:
    archive.add(data/'valve',arcname='valve')
    archive.add(data/'cstrike',arcname='cstrike')
    archive.add(data/'nano.key',arcname='nano.key')
    archive.add(data/'nano-face.key',arcname='nano-face.key')
print('Prepared launchers and controls.')
