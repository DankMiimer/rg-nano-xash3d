#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the public release zip: prebuilt runtime and launchers, without Valve game data.

Players copy their own valve/ and cstrike/ folders into FunKey/Xash3D-source. The first
launch builds the menu artwork and launcher icons from those files (src/nano-art.c).
"""
from pathlib import Path
import argparse, getpass, hashlib, json, os, shutil, stat, subprocess, sys, tarfile, urllib.request, zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_native import is_elf, needed  # noqa: E402
from prepare_runtime import ROOT, LOCK, copy  # noqa: E402

DEVICE_ROOT = '/mnt/FunKey/Xash3D-source'
# CS16Client's extras.pk3 also carries unlicensed Condition Zero/Valve material: bot
# voices and profiles, training maps and sounds, menu bitmaps and sounds. Releases keep
# only its default config files and add an original BotProfile.db (assets/cstrike).
# Touch support is unused on these consoles. FWGS's engine extras ship unchanged.
CS_EXTRAS_KEEP = ('userconfig.d/',)
# Never shipped: Valve game data and artwork, or anything a player's install adds later.
FORBIDDEN_SUFFIXES = {'.wad', '.bsp', '.mdl', '.spr', '.tga', '.bmp', '.ico', '.wav', '.mp3', '.avi', '.webm', '.nav',
                      '.sav', '.gam', '.nvi', '.dll', '.exe'}
FORBIDDEN_NAMES = {'config.cfg', 'rng-seed', 'game.ico', 'liblist.gam'}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch_pinned(url, digest, cache):
    cache.mkdir(parents=True, exist_ok=True)
    path = cache/f'{digest[:16]}-{url.rsplit("/", 1)[1]}'
    if not path.is_file():
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != digest:
            raise SystemExit(f'{url}: SHA-256 mismatch')
        path.write_bytes(data)
    if sha256(path) != digest:
        raise SystemExit(f'{path}: cached file changed')
    return path


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True, help='Release version, e.g. v1.0.0')
    parser.add_argument('--native-build', type=Path, default=Path(os.environ.get('NANO_NATIVE_DIR', ROOT/'build/native')))
    parser.add_argument('--sdk', type=Path, default=os.environ.get('FUNKEY_SDK'))
    parser.add_argument('--output', type=Path, default=ROOT/'build/release')
    parser.add_argument('--allow-dirty', action='store_true', help='Package uncommitted changes (testing only)')
    a = parser.parse_args()
    if not a.sdk:
        parser.error('Set FUNKEY_SDK or pass --sdk')
    commit = git('rev-parse', 'HEAD')
    if git('status', '--porcelain', '--untracked-files=no') and not a.allow_dirty:
        parser.error('Working tree has uncommitted changes; commit first or pass --allow-dirty')
    name = f'rg-nano-half-life-cs-{a.version}'
    stage = a.output/name
    if stage.exists():
        shutil.rmtree(stage)
    sd = stage/'SD card'
    rt = sd/'FunKey/Xash3D-source'
    engine, hl, cs = a.native_build/'engine-install', a.native_build/'hl-install', ROOT/'build/cs-install/cstrike'

    # Engine, game libraries and Nano helpers, exactly as prepare_native.py assembles them.
    for name_ in ('xash3d', 'libxash.so', 'libmenu.so', 'libref_soft.so', 'filesystem_stdio.so'):
        copy(engine/name_, rt/'engine'/name_)
    copy(engine/'filesystem_stdio.so', rt/'filesystem_stdio.so')
    copy(engine/'valve/extras.pk3', rt/'valve/extras.pk3')
    for rel in ('valve/cl_dlls/client_armv7hf.so', 'valve/dlls/hl_armv7hf.so'):
        copy(hl/rel, rt/rel)
    for rel in ('cl_dlls/client_armv7hf.so', 'cl_dlls/menu_armv7hf.so', 'dlls/cs_armv7hf.so'):
        copy(cs/rel, rt/'cstrike'/rel)
    with zipfile.ZipFile(cs/'extras.pk3') as source, zipfile.ZipFile(rt/'cstrike/extras.pk3', 'w') as target:
        for info in sorted(source.infolist(), key=lambda i: i.filename):
            if info.is_dir() or not info.filename.startswith(CS_EXTRAS_KEEP):
                continue
            entry = zipfile.ZipInfo(info.filename, date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            target.writestr(entry, source.read(info))
    copy(ROOT/'assets/cstrike/BotProfile.db', rt/'cstrike/BotProfile.db')
    for tool in ('nano-clk-arm', 'seed-rng-arm', 'nano-supervise-arm', 'nano-art-arm'):
        copy(ROOT/'build/bin'/tool, rt/tool)
    copy(ROOT/'tools/nano-run.sh', rt/'nano-run.sh')
    copy(ROOT/'tools/nano-ui-migrate.sh', rt/'nano-ui-migrate.sh')
    readelf = a.sdk/'bin/arm-funkey-linux-musleabihf-readelf'
    sysroot = a.sdk/'arm-funkey-linux-musleabihf/sysroot'
    queue = [f for f in rt.rglob('*') if is_elf(f)]
    supplied = {f.name for f in queue}
    libraries = {}
    while queue:
        for lib in needed(queue.pop(), readelf):
            if lib in {'libc.so', 'libasound.so.2'} or lib in supplied:
                continue  # firmware libc and ALSA stack
            source = next((f for f in (sysroot/'usr/lib'/lib, sysroot/'lib'/lib) if f.is_file()), None)
            if source is None:
                raise SystemExit(f'SDK cannot resolve {lib}')
            copy(source, rt/'engine'/lib)
            supplied.add(lib)
            libraries[lib] = sha256(rt/'engine'/lib)
            queue.append(rt/'engine'/lib)

    # Launchers with placeholder icons, controls and configs.
    icons = a.output/'icons'
    subprocess.run([sys.executable, str(ROOT/'tools/make_icons.py'), str(icons)], check=True)
    subprocess.run(['bash', str(ROOT/'tools/package.sh'), '--native', '--release', '--runtime-root', DEVICE_ROOT,
                    '--icons', str(icons)], check=True)
    with tarfile.open(ROOT/'build/configs.tar') as archive:
        archive.extractall(rt, filter='data')
    for title in ('Half-Life', 'Counter-Strike'):
        for ext in ('opk', 'png'):
            copy(ROOT/'build/release-dist'/f'{title}.{ext}', sd/'Native games'/f'{title}.{ext}')
    (rt/'backend').write_text('fbdev\n')
    (rt/'cpu-mhz').write_text('1200\n')

    # Free Tahoma-compatible menu font from Wine (never Microsoft's Tahoma).
    font = LOCK['wine-tahoma']
    cache = a.output/'cache'
    ttf = fetch_pinned(font['url'], font['sha256'], cache)
    for target in ('tahoma.ttf', 'FiraSans-Regular.ttf'):
        copy(ttf, rt/'valve/gfx/fonts'/target)

    # Licences, notices and the corresponding source pointer.
    lic = rt/'licenses'
    copy(ROOT/'LICENSE', lic/'GPL-3.0.txt')
    copy(ROOT/'THIRD_PARTY_NOTICES.md', lic/'THIRD_PARTY_NOTICES.md')
    for f in (ROOT/'licenses').rglob('*'):
        if f.is_file():
            copy(f, lic/f.relative_to(ROOT/'licenses'))
    copy(fetch_pinned(font['source_url'], font['source_sha256'], cache), lic/'runtime/wine-tahoma.sfd')
    copy(ROOT/'sources.lock.json', lic/'sources.lock.json')
    (lic/'SOURCE.txt').write_text(
        f'Source code for this release: https://github.com/DankMiimer/rg-nano-xash3d/tree/{commit}\n'
        f'Release {a.version}. Upstream revisions and patches are pinned in sources.lock.json and the\n'
        f'repository\'s patches/ folder; tools/build.sh and tools/build-native.sh rebuild every binary.\n'
        f'The menu font is Wine\'s Tahoma (wine-10.0, LGPL-2.1-or-later); its FontForge source is\n'
        f'runtime/wine-tahoma.sfd.\n', newline='\n')
    readme = (ROOT/'tools/release-readme.txt').read_text().replace('@VERSION@', a.version)
    (stage/'README.txt').write_text(readme, newline='\r\n')
    (rt/'README.txt').write_text(readme, newline='\r\n')

    # Same as the tested device updates: debug data off, dynamic symbols kept.
    strip = a.sdk/'bin/arm-funkey-linux-musleabihf-strip'
    for f in sorted(rt.rglob('*')):
        if is_elf(f):
            subprocess.run([str(strip), '--strip-unneeded', str(f)], check=True)
    manifest = {'release': a.version, 'commit': commit, 'backend': 'fbdev', 'runtime_root': DEVICE_ROOT,
                'firmware_dependencies': ['libc.so', 'libasound.so.2'], 'sdk_libraries': libraries,
                'source_lock': LOCK,
                'patches': {f.name: sha256(f) for f in sorted((ROOT/'patches').glob('*.patch'))},
                'components': {f.relative_to(rt).as_posix(): sha256(f) for f in sorted(rt.rglob('*')) if is_elf(f)}}
    (rt/'source-runtime.json').write_text(json.dumps(manifest, indent=2) + '\n')

    # Refuse to publish anything that looks like game data, a user file or a non-free font,
    # or binaries carrying the builder's name through compiled-in source paths.
    files = sorted(f for f in stage.rglob('*') if f.is_file())
    private = {t.encode() for t in (getpass.getuser(), str(Path.home())) if len(t) >= 4}
    for f in files:
        rel = f.relative_to(stage).as_posix()
        if f.suffix.lower() in FORBIDDEN_SUFFIXES or f.name.lower() in FORBIDDEN_NAMES:
            raise SystemExit(f'Refusing to package {rel}')
        if f.suffix.lower() == '.ttf' and sha256(f) != font['sha256']:
            raise SystemExit(f'Unexpected font {rel}')
        if any(token in f.read_bytes() for token in private):
            raise SystemExit(f'{rel} contains the builder\'s user name or home path; build outside the home folder')
    with zipfile.ZipFile(rt/'cstrike/extras.pk3') as extras:
        stray = [n for n in extras.namelist() if not n.startswith(CS_EXTRAS_KEEP)]
        if stray or not extras.namelist():
            raise SystemExit(f'Unexpected cstrike/extras.pk3 contents: {stray[:5]}')
    archive = a.output/f'{name}.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in files:
            info = zipfile.ZipInfo(f.relative_to(stage).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            executable = is_elf(f) or f.suffix == '.sh'
            info.external_attr = (stat.S_IFREG | (0o755 if executable else 0o644)) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, f.read_bytes())
    (a.output/f'{name}.zip.sha256').write_text(f'{sha256(archive)}  {archive.name}\n')
    print(f'{archive} ({archive.stat().st_size // 1024} KiB, {len(files)} files) from {commit[:7]}')


if __name__ == '__main__':
    main()
