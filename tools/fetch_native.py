#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import sys
from fetch_sources import fetch, apply, run
base=Path(sys.argv[1]).resolve()
engine=fetch('xash3d',base)
for patch in ('renderer-nano.patch','renderer-nano-triangles.patch','engine-musl-timer.patch','engine-fbdev-nano.patch','engine-linux-entropy.patch','engine-evdev-time64.patch','engine-fbdev-log.patch','engine-alsa-ring.patch'):
    apply(engine,patch)
run('git','-C',str(engine),'submodule','update','--init','--recursive','--depth','1',
    '3rdparty/mainui','3rdparty/vgui_support','3rdparty/library_suffix',
    '3rdparty/libbacktrace/libbacktrace','3rdparty/mbedtls/mbedtls',
    '3rdparty/opus/opus','3rdparty/opusfile/opusfile','3rdparty/extras/xash-extras','3rdparty/MultiEmulator')
hl=fetch('hlsdk',base)
run('git','-C',str(hl),'submodule','update','--init','--recursive','--depth','1')
