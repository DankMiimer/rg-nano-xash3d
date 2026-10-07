# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import importlib.util, struct, tempfile
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nav_import',root/'tools/import_navs.py')
nav_import=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav_import)
with tempfile.TemporaryDirectory() as directory:
    base=Path(directory);source=base/'supplied';maps=base/'maps';source.mkdir();maps.mkdir()
    (maps/'de_dust.bsp').write_bytes(b'BSP'*100)
    (maps/'cs_office.bsp').write_bytes(b'BSP'*200)
    (source/'de_dust.nav').write_bytes(struct.pack('<III',0xFEEDFACE,5,300)+b'opaque nav payload')
    (source/'cs_office.nav').write_bytes(struct.pack('<III',0xFEEDFACE,5,301))
    (source/'de_dust2.nav').write_bytes(struct.pack('<III',0xFEEDFACE,5,300))
    copied,skipped=nav_import.import_navs(source,maps)
    assert copied==['de_dust.nav'] and len(skipped)==2
    assert (maps/'de_dust.nav').read_bytes()==(source/'de_dust.nav').read_bytes()
    assert not (maps/'cs_office.nav').exists()
    for header in (b'',b'YaPB graph',struct.pack('<III',0xFEEDFACE,16,300),struct.pack('<III',0xFEEDFACE,5,0)):
        (source/'de_dust.nav').write_bytes(header)
        try:nav_import.check_nav(source/'de_dust.nav',maps/'de_dust.bsp')
        except ValueError:pass
        else:raise AssertionError('invalid or mismatched NAV accepted')
print('NAV import: matching data copied unchanged; missing maps, wrong formats, versions and BSP sizes rejected.')
