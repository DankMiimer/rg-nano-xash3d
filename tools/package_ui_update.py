# SPDX-License-Identifier: MIT
"""Package an existing, tested Nano UI candidate without touching the device."""
from pathlib import Path
import argparse, hashlib, json, shutil, tarfile
ROOT=Path(__file__).resolve().parents[1]
FILES=('engine/libxash.so','engine/libmenu.so','engine/libref_soft.so',
       'valve/cl_dlls/client_armv7hf.so','cstrike/cl_dlls/client_armv7hf.so',
       'cstrike/cl_dlls/menu_armv7hf.so','cstrike/dlls/cs_armv7hf.so','nano-run.sh','nano-ui-migrate.sh',
       'valve/nano-controls.cfg','cstrike/nano-controls.cfg')
MENU_ART=('valve/gfx/nano/menu_background.tga','valve/gfx/nano/menu_logo.tga',
          'cstrike/gfx/nano/menu_background.tga','cstrike/gfx/nano/menu_logo.tga',
          'cstrike/sprites/nano_menu_background.spr')
INTRO_MEDIA=('valve/media/nano_valve.nvi',)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def package(candidate,baseline,output,evidence=None):
    candidate_manifest=json.loads((candidate/'ui-update.json').read_text())
    artwork=candidate_manifest.get('menu_art',{})
    intro=candidate_manifest.get('intro_media',{})
    if any(name not in MENU_ART for name in artwork):raise ValueError('Unsupported menu artwork path')
    if any(name not in INTRO_MEDIA for name in intro):raise ValueError('Unsupported intro media path')
    assets={**artwork,**intro}
    names_to_check=FILES+tuple(assets)
    for name in names_to_check:
        expected=assets[name] if name in assets else candidate_manifest['components'][name]
        if sha(candidate/name)!=expected:raise ValueError('Candidate hash mismatch: '+name)
    output.mkdir(parents=True,exist_ok=False)
    payload=output/'payload';payload.mkdir()
    runtime=json.loads((baseline/'source-runtime.json').read_text())
    changed=[]
    for name in names_to_check:
        source=candidate/name
        if (baseline/name).exists() and sha(source)==sha(baseline/name):continue
        changed.append(name)
        dest=payload/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
        runtime['components'][name]=sha(dest)
    runtime['patches'].update(candidate_manifest['patches'])
    runtime['ui_profile_version']=candidate_manifest.get('ui_profile_version',2)
    if artwork:runtime['menu_art']=artwork
    if intro:runtime['intro_media']=intro
    (payload/'source-runtime.json').write_text(json.dumps(runtime,indent=2)+'\n',newline='\n')
    names=tuple(changed)+('source-runtime.json',)
    old={name:sha(baseline/name) if (baseline/name).exists() else None for name in names}
    new={name:sha(payload/name) for name in names}
    manifest={'ui_profile_version':candidate_manifest.get('ui_profile_version',2),'old_components':old,'components':new,
              'source_lock':candidate_manifest['source_lock'],'patches':candidate_manifest['patches']}
    (output/'ui-update.json').write_text(json.dumps(manifest,indent=2)+'\n',newline='\n')
    (output/'payload.sha256').write_text(''.join(f'{new[name]}  {name}\n' for name in names),newline='\n')
    (output/'expected.sha256').write_text(''.join(f'{digest}  {name}\n' for name,digest in old.items() if digest),newline='\n')
    (output/'expected-absent.txt').write_text(''.join(name+'\n' for name,digest in old.items() if digest is None),newline='\n')
    (output/'files.txt').write_text('\n'.join(names)+'\n',newline='\n')
    # Source inputs accompany the binary patch; upstream trees remain pinned in sources.lock.json.
    source=output/'source-inputs';source.mkdir()
    for directory in ('patches','src'):
        shutil.copytree(ROOT/directory,source/directory)
    for name in ('sources.lock.json','README.md','LICENSE','THIRD_PARTY_NOTICES.md','SOURCES.md'):
        if (ROOT/name).exists():shutil.copy2(ROOT/name,source/name)
    shutil.copytree(ROOT/'tools',source/'tools',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(ROOT/'docs',source/'docs')
    shutil.copytree(ROOT/'tests',source/'tests',ignore=shutil.ignore_patterns('__pycache__'))
    if evidence is not None:shutil.copytree(evidence,output/'validation')
    shutil.copytree(ROOT/'licenses',source/'licenses')
    install=r'''#!/bin/sh
# Apply only after reviewing this package and authorizing SD changes.
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=/mnt/FunKey/Xash3D-source
[ -d "$ROOT/engine" ] || { echo 'Runtime missing' >&2; exit 1; }
[ -z "$(pidof xash3d || true)" ] || { echo 'Close both games first' >&2; exit 1; }
(cd "$HERE/payload" && sha256sum -c "$HERE/payload.sha256")
(cd "$ROOT" && sha256sum -c "$HERE/expected.sha256")
while IFS= read -r name;do [ ! -e "$ROOT/$name" ] || { echo "Unexpected existing file: $name" >&2;exit 1; };done < "$HERE/expected-absent.txt"
BACKUP="$ROOT/ui-backups/ui-v2-$(date +%Y%m%d-%H%M%S)-$$"
mkdir -p "$BACKUP"
cp "$HERE/files.txt" "$BACKUP/files.txt"
for name in valve/nano-settings.cfg cstrike/nano-settings.cfg; do
    if [ -f "$ROOT/$name" ]; then mkdir -p "$BACKUP/$(dirname "$name")";cp -p "$ROOT/$name" "$BACKUP/$name";fi
done
while IFS= read -r name; do
    mkdir -p "$BACKUP/$(dirname "$name")"
    if [ -f "$ROOT/$name" ]; then cp -p "$ROOT/$name" "$BACKUP/$name";else printf '%s\n' "$name" >> "$BACKUP/absent.txt";fi
done < "$HERE/files.txt"
cp "$HERE/rollback.sh" "$BACKUP/rollback.sh"
restore() { sh "$BACKUP/rollback.sh"; }
trap 'trap - EXIT HUP INT TERM; restore; exit 129' HUP
trap 'trap - EXIT HUP INT TERM; restore; exit 130' INT
trap 'trap - EXIT HUP INT TERM; restore; exit 143' TERM
trap 'code=$?;if [ "$code" -ne 0 ];then restore;fi' EXIT
while IFS= read -r name; do
    mkdir -p "$ROOT/$(dirname "$name")"
    cp "$HERE/payload/$name" "$ROOT/$name.ui-v2-new"
    case "$name" in *.sh) chmod 755 "$ROOT/$name.ui-v2-new";;esac
    mv "$ROOT/$name.ui-v2-new" "$ROOT/$name"
done < "$HERE/files.txt"
(cd "$ROOT" && sha256sum -c "$HERE/payload.sha256")
sync
trap - EXIT HUP INT TERM
printf 'Installed. Backup and rollback: %s\n' "$BACKUP"
'''
    rollback=r'''#!/bin/sh
set -eu
BACKUP=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=/mnt/FunKey/Xash3D-source
case "$BACKUP" in "$ROOT"/ui-backups/ui-v2-*) ;; *) echo 'Run the rollback copy inside the installed backup directory' >&2;exit 1;; esac
[ -z "$(pidof xash3d || true)" ] || { echo 'Close both games first' >&2;exit 1; }
while IFS= read -r name; do
    if [ -f "$BACKUP/$name" ]; then cp -p "$BACKUP/$name" "$ROOT/$name.ui-v2-rollback";mv "$ROOT/$name.ui-v2-rollback" "$ROOT/$name";fi
    rm -f "$ROOT/$name.ui-v2-new" "$ROOT/$name.ui-v2-rollback"
done < "$BACKUP/files.txt"
if [ -f "$BACKUP/absent.txt" ];then
    while IFS= read -r name;do rm -f "$ROOT/$name";done < "$BACKUP/absent.txt"
fi
for name in valve/nano-settings.cfg cstrike/nano-settings.cfg;do
    if [ -f "$BACKUP/$name" ];then cp -p "$BACKUP/$name" "$ROOT/$name";fi
done
sync
printf 'Restored %s\n' "$BACKUP"
'''
    for name,script in [('install.sh',install),('rollback.sh',rollback)]:
        p=output/name;p.write_text(script,newline='\n');p.chmod(0o755)
    (output/'README.txt').write_text('''Nano UI follow-up — minimal update

This package is prepared, not automatically installed. It contains only the
components in files.txt that differ from the reviewed baseline. ui-update.json
records their previous and new hashes.
Every changed binary or prepared artwork file is listed in files.txt.

Review ui-update.json and the native comparison images before installation.
Copy the extracted package to /tmp/nano-ui-update, close both games, then run:
  sh /tmp/nano-ui-update/install.sh
The script checks candidate and installed component hashes before writing, backs
up every replaced file plus both settings files, and prints its rollback path.
It refuses a different/changed installed baseline. Do not bypass that check.
Settings migrate atomically on the next game launch, with a separate .ui-v1.bak or .ui-v2.bak for the previous version.
To roll back, close both games and run the printed backup's rollback.sh.

source-inputs contains local headers and patches, without game assets. Fetch
pinned upstream sources using sources.lock.json and the repository build scripts.
When ui-update.json includes menu_art or intro_media, payload contains locally prepared media
from the owner's game installation; keep that package private.
Physical-display readability remains a
human check. The USB viewer's default is 2 fps because 5 fps measured 13-14% slower
in two uncapped Half-Life scenes; 2 fps measured 4.8-5.8% slower.
''',newline='\n')
    archive=output.with_suffix('.tar.gz')
    with tarfile.open(archive,'w:gz') as tar:tar.add(output,arcname='nano-ui-update')
    archive.with_suffix(archive.suffix+'.sha256').write_text(f'{sha(archive)}  {archive.name}\n',newline='\n')
    return archive
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--evidence',type=Path);a=p.parse_args()
    print(package(a.candidate,a.baseline,a.output,a.evidence))
