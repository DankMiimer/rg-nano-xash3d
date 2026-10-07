#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import sys, shutil
from fetch_sources import fetch, apply, apply_stack, remove_layer, run, ROOT
base=Path(sys.argv[1]).resolve()
engine=fetch('xash3d',base)
remove_layer(engine,'ui-v6-engine.patch')
remove_layer(engine,'ui-v5-engine.patch')
remove_layer(engine,'ui-v3-engine.patch')
remove_layer(engine/'3rdparty/mainui','ui-v6-hl-menu.patch')
remove_layer(engine/'3rdparty/mainui','ui-v5-hl-menu.patch')
remove_layer(engine/'3rdparty/mainui','ui-v4-hl-menu.patch')
remove_layer(engine/'3rdparty/mainui','ui-v3-hl-menu.patch')
remove_layer(engine,'ui-v2-engine.patch')
for patch in ('renderer-nano.patch','renderer-nano-triangles.patch','renderer-decal-bounds.patch','engine-musl-timer.patch','engine-fbdev-nano.patch','engine-linux-entropy.patch','engine-fbdev-log.patch','engine-alsa-ring.patch','engine-nano-hud.patch'):
    apply(engine,patch)
apply_stack(engine, ('engine-evdev-time64.patch', 'engine-nano-controls.patch'))
run('git','-C',str(engine),'submodule','update','--init','--recursive','--depth','1',
    '3rdparty/mainui','3rdparty/vgui_support','3rdparty/library_suffix',
    '3rdparty/libbacktrace/libbacktrace','3rdparty/mbedtls/mbedtls',
    '3rdparty/opus/opus','3rdparty/opusfile/opusfile','3rdparty/extras/xash-extras','3rdparty/MultiEmulator')
shutil.copy2(ROOT/'src/nano-ui-alpha.h',engine/'ref/soft/nano-ui-alpha.h')
shutil.copy2(ROOT/'src/nano-controls.h',engine/'engine/platform/linux/nano-controls.h')
shutil.copy2(ROOT/'src/nano-intro-player.h',engine/'engine/client/avi/nano-intro-player.h')
apply_stack(engine/'3rdparty/mainui', ('mainui-nano-menu.patch','ui-v2-hl-menu.patch','ui-v3-hl-menu.patch','ui-v4-hl-menu.patch','ui-v5-hl-menu.patch','ui-v6-hl-menu.patch'))
for header in ('nano-menu-options.h', 'nano-settings.h', 'nano-menu-controls.h', 'nano-control-preference.h', 'nano-menu-layout.h', 'nano-menu-theme.h', 'nano-save-browser.h'):
    shutil.copy2(ROOT/'src'/header,engine/'3rdparty/mainui/menus'/header)
apply(engine, 'engine-nano-profile.patch')
apply_stack(engine, ('engine-nano-memory-report.patch', 'engine-nano-memory-peak.patch', 'engine-nano-demand-zero.patch', 'engine-nano-memory-assets.patch'))
apply_stack(engine, ('renderer-nano-texture-memory.patch', 'renderer-nano-texture-share.patch'))
apply(engine, 'renderer-nano-skybox.patch')
shutil.copy2(ROOT/'src/nano-skybox.h', engine/'ref/soft/nano-skybox.h')
shutil.copy2(ROOT/'src/nano-texture-share.h', engine/'ref/soft/nano-texture-share.h')
shutil.copy2(ROOT/'src/nano-frame-stats.h', engine/'engine/common/nano-frame-stats.h')
shutil.copy2(ROOT/'src/nano-hud-transform.h', engine/'engine/client/nano-hud-transform.h')
apply(engine,'ui-v2-engine.patch')
apply(engine,'ui-v3-engine.patch')
apply(engine,'ui-v5-engine.patch')
apply(engine,'ui-v6-engine.patch')
hl=fetch('hlsdk',base)
apply_stack(hl,('hl-nano-look.patch','hl-nano-centerview.patch','hl-nano-hud.patch','hl-nano-slow-aim.patch','ui-v2-hl-client.patch'))
for header in ('nano-look.h', 'nano-hud-scope.h', 'nano-hud-layout.h'): shutil.copy2(ROOT/'src'/header,hl/'cl_dll'/header)
run('git','-C',str(hl),'submodule','update','--init','--recursive','--depth','1')
