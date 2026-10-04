#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Assemble a private framebuffer runtime without opening an external OPK."""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess, tarfile
from prepare_runtime import ROOT, copy


def is_elf(path):
    if not path.is_file(): return False
    with path.open("rb") as stream: return stream.read(4) == b"\x7fELF"


def needed(path, readelf):
    text=subprocess.check_output([str(readelf),'-d',str(path)],text=True)
    return re.findall(r'\(NEEDED\).*\[(.*?)\]',text)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--games',type=Path,required=True)
    p.add_argument('--native-build',type=Path,default=ROOT/'build/native')
    p.add_argument('--sdk',type=Path,required=True)
    p.add_argument('--font',type=Path,required=True)
    p.add_argument('--nav',type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'build/native-runtime')
    p.add_argument('--device-root',default='/mnt/FunKey/Xash3D-source')
    a=p.parse_args()
    if not re.fullmatch(r'/mnt/FunKey/[A-Za-z0-9_-]+',a.device_root):
        p.error('--device-root must be a simple directory under /mnt/FunKey')
    if a.output.exists():
        p.error('Output already exists; choose a fresh directory')
    for game in ('valve','cstrike'):
        if not (a.games/game/'game.ico').is_file(): p.error(f'Missing {game}/game.ico')
    engine=a.native_build/'engine-install'
    hl=a.native_build/'hl-install'
    cs=ROOT/'build/cs-install/cstrike'
    required=[engine/name for name in ('xash3d','libxash.so','libmenu.so','libref_soft.so','filesystem_stdio.so','valve/extras.pk3')]
    required += [hl/'valve/cl_dlls/client_armv7hf.so',hl/'valve/dlls/hl_armv7hf.so',a.font]
    required += [ROOT/'build/bin'/name for name in ('nano-clk-arm','seed-rng-arm','nano-supervise-arm')]
    required += [cs/rel for rel in ('cl_dlls/client_armv7hf.so','cl_dlls/menu_armv7hf.so','dlls/cs_armv7hf.so','extras.pk3')]
    for file in required:
        if not file.is_file(): p.error(f'Missing build/input: {file}')
    a.output.mkdir(parents=True)
    omit_dirs={'save','controller_configs','manual','.fontcache'}
    omit_files={'config.cfg','autoexec.cfg','userconfig.cfg','steam_autocloud.vdf'}
    for game in ('valve','cstrike'):
        for source in (a.games/game).rglob('*'):
            rel=source.relative_to(a.games)
            if not source.is_file() or source.suffix.lower() in {'.dll','.exe','.asi','.so','.dylib'}: continue
            if any(part.lower() in omit_dirs for part in rel.parts) or source.name.lower() in omit_files: continue
            copy(source,a.output/rel)
    for name in ('xash3d','libxash.so','libmenu.so','libref_soft.so','filesystem_stdio.so'):
        copy(engine/name,a.output/'engine'/name)
    copy(engine/'filesystem_stdio.so',a.output/'filesystem_stdio.so')
    copy(engine/'valve/extras.pk3',a.output/'valve/extras.pk3')
    for rel in ('valve/cl_dlls/client_armv7hf.so','valve/dlls/hl_armv7hf.so'):
        copy(hl/rel,a.output/rel)
    for rel in ('cl_dlls/client_armv7hf.so','cl_dlls/menu_armv7hf.so','dlls/cs_armv7hf.so','extras.pk3'):
        copy(cs/rel,a.output/'cstrike'/rel)
    for name in ('nano-clk-arm','seed-rng-arm','nano-supervise-arm'):
        copy(ROOT/'build/bin'/name,a.output/name)
    copy(ROOT/'tools/nano-run.sh',a.output/'nano-run.sh')
    # Resolve the complete shared-library closure from the SDK, never from an OPK.
    readelf=a.sdk/'bin/arm-funkey-linux-musleabihf-readelf'
    sysroot=a.sdk/'arm-funkey-linux-musleabihf/sysroot'
    queue=[f for f in a.output.rglob('*') if is_elf(f)]
    supplied={f.name for f in queue}
    libraries={}
    while queue:
        elf=queue.pop()
        for name in needed(elf,readelf):
            # Use the firmware libc and its established ALSA output stack.
            if name in {'libc.so','libasound.so.2'} or name in supplied: continue
            choices=[sysroot/'usr/lib'/name,sysroot/'lib'/name]
            source=next((f for f in choices if f.is_file()),None)
            if source is None: raise RuntimeError(f'SDK cannot resolve {name} required by {elf.name}')
            target=a.output/'engine'/name
            copy(source,target)
            supplied.add(name)
            libraries[name]=hashlib.sha256(target.read_bytes()).hexdigest()
            queue.append(target)
    for name in ('tahoma.ttf','FiraSans-Regular.ttf'):
        copy(a.font,a.output/'valve/gfx/fonts'/name)
    if a.nav: copy(a.nav,a.output/'cstrike/maps/de_dust.nav')
    subprocess.run(['python3',str(ROOT/'tools/extract_icons.py'),'--games',str(a.games)],check=True)
    subprocess.run(['bash',str(ROOT/'tools/package.sh'),'--native','--runtime-root',a.device_root],check=True)
    with tarfile.open(ROOT/'build/configs.tar') as archive:
        archive.extractall(a.output,filter='data')
    key=a.output/'nano.key'
    text=key.read_text().replace('/mnt/FunKey/Xash3D/',a.device_root+'/')
    # FunKey's parser returns the key-name table index, not its Linux code.
    # Retain the proven arrow compensation even with direct evdev input.
    key.write_text(text,newline='\n')
    (a.output/'backend').write_text('fbdev\n')
    (a.output/'cpu-mhz').write_text('1200\n')
    (a.output/'rng-seed').write_bytes(os.urandom(256))
    # Hashes establish which fresh source outputs were assembled, without local paths.
    manifest={'backend':'fbdev','external_opk_used':False,'firmware_dependencies':['libc.so','libasound.so.2'],'sdk_libraries':libraries,
        'runtime_root':a.device_root,
        'source_lock':json.loads((ROOT/'sources.lock.json').read_text()),
        'patches':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (ROOT/'patches').glob('*.patch')},
        'components':{f.relative_to(a.output).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in a.output.rglob('*') if is_elf(f)}}
    (a.output/'source-runtime.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Private native runtime assembled at {a.output}; no external OPK used.')

if __name__=='__main__': main()
