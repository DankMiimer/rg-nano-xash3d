#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Copy supplied CS 1.6 NAVs after checking their header against installed BSPs."""
from pathlib import Path
import argparse, re, shutil, struct

def check_nav(nav, bsp):
    if not bsp.is_file():
        raise ValueError('no matching installed BSP')
    with nav.open('rb') as stream:
        header=stream.read(12)
    if len(header)!=12:
        raise ValueError('truncated NAV header')
    magic,version,size=struct.unpack('<III',header)
    if magic!=0xFEEDFACE or version not in (4,5):
        raise ValueError('requires a CS NAV version 4 or 5 (not a YaPB graph or Source NAV)')
    if not size or size!=bsp.stat().st_size:
        raise ValueError('NAV belongs to a different BSP size')
    return version

def import_navs(source, maps):
    if not source.is_dir() or not maps.is_dir():
        raise ValueError('source NAV directory and target maps directory must exist')
    copied=[];skipped=[]
    for nav in sorted(source.glob('*.nav')):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,63}',nav.stem):
            skipped.append((nav.name,'invalid map name'));continue
        try:
            check_nav(nav,maps/(nav.stem+'.bsp'))
        except ValueError as error:
            skipped.append((nav.name,str(error)));continue
        destination=maps/nav.name
        if nav.resolve()!=destination.resolve():shutil.copy2(nav,destination)
        copied.append(nav.name)
    return copied,skipped

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--maps',type=Path,required=True)
    args=parser.parse_args()
    copied,skipped=import_navs(args.source,args.maps)
    print(f'Imported {len(copied)} matching NAV headers. Engine validates full contents on load.')
    for name,reason in skipped:print(f'Skipped {name}: {reason}')
