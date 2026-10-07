# SPDX-License-Identifier: MIT
"""Install/rollback integrity in a disposable host runtime, never on the SD."""
from pathlib import Path
import importlib.util, tempfile, json, hashlib, subprocess
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('package_ui_update',root/'tools/package_ui_update.py')
pkg=importlib.util.module_from_spec(spec);spec.loader.exec_module(pkg)
with tempfile.TemporaryDirectory(prefix='nano-ui-package-') as folder:
    folder=Path(folder);candidate=folder/'candidate';baseline=folder/'baseline';runtime=folder/'runtime'
    for base in (candidate,baseline,runtime):base.mkdir()
    for name in pkg.FILES:
        c=candidate/name;c.parent.mkdir(parents=True,exist_ok=True);c.write_text('new '+name)
        if name!='nano-ui-migrate.sh':
            for base in (baseline,runtime):
                p=base/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('old '+name)
    (candidate/'engine/libref_soft.so').write_bytes((baseline/'engine/libref_soft.so').read_bytes())
    artwork={}
    for name in pkg.MENU_ART:
        p=candidate/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'prepared original artwork')
        artwork[name]=pkg.sha(p)
    intro={}
    for name in pkg.INTRO_MEDIA:
        p=candidate/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'prepared original intro')
        intro[name]=pkg.sha(p)
    for base in (baseline,runtime):
        (base/'source-runtime.json').write_text(json.dumps({'components':{'unchanged':'kept'},'patches':{'old':'kept'},'sdk_libraries':{'kept':'hash'}}))
        for game in ('valve','cstrike'):(base/game/'nano-settings.cfg').write_text('fps_max 57\n')
    manifest={'components':{name:pkg.sha(candidate/name) for name in pkg.FILES},'patches':{'new':'hash'},'source_lock':{},'menu_art':artwork,'intro_media':intro}
    manifest['menu_art']={"../unexpected":"hash"};(candidate/'ui-update.json').write_text(json.dumps(manifest))
    try:pkg.package(candidate,baseline,folder/'invalid')
    except ValueError:pass
    else:raise AssertionError('Unexpected asset paths accepted')
    assert not (folder/'invalid').exists()
    manifest['menu_art']=artwork;(candidate/'ui-update.json').write_text(json.dumps(manifest))
    manifest['intro_media']={'../unexpected':'hash'};(candidate/'ui-update.json').write_text(json.dumps(manifest))
    try:pkg.package(candidate,baseline,folder/'invalid-intro')
    except ValueError:pass
    else:raise AssertionError('Unexpected intro paths accepted')
    assert not (folder/'invalid-intro').exists()
    manifest['intro_media']=intro;(candidate/'ui-update.json').write_text(json.dumps(manifest))
    evidence=folder/'evidence';evidence.mkdir();(evidence/'report.txt').write_text('verified pixels')
    output=folder/'update';archive=pkg.package(candidate,baseline,output,evidence);assert archive.exists()
    assert not (output/'payload/engine/libref_soft.so').exists()
    assert (output/'validation/report.txt').read_text()=='verified pixels'
    assert (output/'source-inputs/tests/test_nano_alpha.py').is_file()
    merged=json.loads((output/'payload/source-runtime.json').read_text());assert merged['sdk_libraries']=={'kept':'hash'} and merged['components']['unchanged']=='kept'
    for script in ('install.sh','rollback.sh'):
        p=output/script;p.write_text(p.read_text().replace('/mnt/FunKey/Xash3D-source',str(runtime)))
    # Changed installed files must be rejected before any backup or overwrite.
    (runtime/'nano-run.sh').write_text('custom changed launcher')
    assert subprocess.run(['sh',str(output/'install.sh')],capture_output=True).returncode!=0
    assert not (runtime/'ui-backups').exists()
    (runtime/'nano-run.sh').write_bytes((baseline/'nano-run.sh').read_bytes())
    subprocess.run(['sh',str(output/'install.sh')],check=True,capture_output=True)
    for name in pkg.FILES+pkg.MENU_ART+pkg.INTRO_MEDIA:assert pkg.sha(runtime/name)==pkg.sha(candidate/name)
    (runtime/'valve/nano-settings.cfg').write_text('modified after migration\n')
    backup=next((runtime/'ui-backups').iterdir());(runtime/'nano-run.sh.ui-v2-new').write_text('partial copy');subprocess.run(['sh',str(backup/'rollback.sh')],check=True,capture_output=True)
    assert not (runtime/'nano-run.sh.ui-v2-new').exists()
    for name in pkg.FILES+pkg.MENU_ART+pkg.INTRO_MEDIA+('source-runtime.json',):
        if (baseline/name).exists():assert pkg.sha(runtime/name)==pkg.sha(baseline/name)
        else:assert not (runtime/name).exists()
    assert (runtime/'valve/nano-settings.cfg').read_text()=='fps_max 57\n'
print('UI package: component integrity, preserved metadata, changed-baseline refusal, backups and complete rollback passed.')
