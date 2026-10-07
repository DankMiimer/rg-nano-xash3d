# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import importlib.util,re,subprocess,tempfile,os
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fetch_nano',root/'tools/fetch_sources.py')
fetch=importlib.util.module_from_spec(spec);spec.loader.exec_module(fetch)
stacks=[
 (root/'upstream/cs16-client/3rdparty/mainui_cpp',('cs16-mainui-nano-menu.patch','cs16-nano-match-menu.patch','ui-v2-cs-menu.patch','ui-v3-cs-menu.patch','ui-v4-cs-menu.patch','ui-v5-cs-menu.patch','ui-v6-cs-menu.patch')),
 (root/'upstream/cs16-client',('cs16-nano-look.patch','cs16-nano-centerview.patch','cs16-nano-hud.patch','cs16-nano-controls.patch','cs16-nano-slow-aim.patch','ui-v2-cs-client.patch','ui-v3-cs-client.patch','ui-v5-cs-client.patch','ui-v6-cs-client.patch')),
 (root/'upstream/cs16-client/3rdparty/ReGameDLL_CS',('cs16-nano-nav-opt-in.patch','ui-v3-cs-server.patch'))]
if os.environ.get('NANO_NATIVE_DIR'):
    native=Path(os.environ['NANO_NATIVE_DIR'])
    stacks += [(native/'hlsdk',('hl-nano-look.patch','hl-nano-centerview.patch','hl-nano-hud.patch','hl-nano-slow-aim.patch','ui-v2-hl-client.patch')),
               (native/'xash3d',('renderer-nano.patch','renderer-nano-triangles.patch','renderer-decal-bounds.patch','engine-musl-timer.patch','engine-fbdev-nano.patch','engine-linux-entropy.patch','engine-fbdev-log.patch','engine-alsa-ring.patch','engine-nano-hud.patch','engine-evdev-time64.patch','engine-nano-controls.patch','engine-nano-profile.patch','ui-v2-engine.patch','ui-v3-engine.patch','ui-v5-engine.patch','ui-v6-engine.patch')),
               (native/'xash3d/3rdparty/mainui',('mainui-nano-menu.patch','ui-v2-hl-menu.patch','ui-v3-hl-menu.patch','ui-v4-hl-menu.patch','ui-v5-hl-menu.patch','ui-v6-hl-menu.patch'))]
for source,stack in stacks:
    names=set()
    for patch in stack:names.update(re.findall(r'^--- a/(.+)$',(root/'patches'/patch).read_text(),re.M))
    with tempfile.TemporaryDirectory() as directory:
        tree=Path(directory);subprocess.run(['git','init','-q',str(tree)],check=True)
        for name in names:
            dest=tree/name;dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(subprocess.check_output(['git','show','HEAD:'+name],cwd=source))
        unrelated=tree/'unrelated.txt';unrelated.write_text('keep this local change')
        fetch.apply_stack(tree,stack)
        expected={name:(tree/name).read_bytes() for name in names}
        fetch.apply_stack(tree,stack)
        assert expected=={name:(tree/name).read_bytes() for name in names}
        assert unrelated.read_text()=='keep this local change'
        # A baseline-only state must produce the same final source.
        for patch in reversed(stack):subprocess.run(['git','apply','--reverse',str(root/'patches'/patch)],cwd=tree,check=True)
        fetch.apply(tree,stack[0]);fetch.apply_stack(tree,stack)
        assert expected=={name:(tree/name).read_bytes() for name in names}
print('Nano match patch stacks: fresh, partial and repeated application agree and preserve unrelated files.')
