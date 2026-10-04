#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import sys, shutil
from fetch_sources import fetch, apply, apply_stack, run, ROOT
base=Path(sys.argv[1]).resolve()
engine=fetch('xash3d',base)
for patch in ('renderer-nano.patch','renderer-nano-triangles.patch','engine-musl-timer.patch','engine-fbdev-nano.patch','engine-linux-entropy.patch','engine-evdev-time64.patch','engine-fbdev-log.patch','engine-alsa-ring.patch','engine-nano-hud.patch'):
    apply(engine,patch)
run('git','-C',str(engine),'submodule','update','--init','--recursive','--depth','1',
    '3rdparty/mainui','3rdparty/vgui_support','3rdparty/library_suffix',
    '3rdparty/libbacktrace/libbacktrace','3rdparty/mbedtls/mbedtls',
    '3rdparty/opus/opus','3rdparty/opusfile/opusfile','3rdparty/extras/xash-extras','3rdparty/MultiEmulator')
apply(engine/'3rdparty/mainui', 'mainui-nano-menu.patch')
for header in ('nano-menu-options.h', 'nano-settings.h'):
    shutil.copy2(ROOT/'src'/header,engine/'3rdparty/mainui/menus'/header)
apply(engine, 'engine-nano-profile.patch')
apply_stack(engine, ('engine-nano-memory-report.patch', 'engine-nano-memory-peak.patch'))
apply_stack(engine, ('renderer-nano-texture-memory.patch', 'renderer-nano-texture-share.patch'))
shutil.copy2(ROOT/'src/nano-texture-share.h', engine/'ref/soft/nano-texture-share.h')
shutil.copy2(ROOT/'src/nano-frame-stats.h', engine/'engine/common/nano-frame-stats.h')
shutil.copy2(ROOT/'src/nano-hud-transform.h', engine/'engine/client/nano-hud-transform.h')
hl=fetch('hlsdk',base)
for patch in ('hl-nano-look.patch', 'hl-nano-hud.patch'): apply(hl,patch)
for header in ('nano-look.h', 'nano-hud-scope.h'): shutil.copy2(ROOT/'src'/header,hl/'cl_dll'/header)
run('git','-C',str(hl),'submodule','update','--init','--recursive','--depth','1')
