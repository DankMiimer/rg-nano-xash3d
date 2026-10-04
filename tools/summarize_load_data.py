#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Print descriptive load-duration summaries from the anonymous experiment CSV."""
from pathlib import Path
import csv, statistics, sys
path=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'docs/data/load-benchmark-2026-10-04.csv'
groups={}
with path.open(newline='') as stream:
    for row in csv.DictReader(stream):
        if row['included']!='1':continue
        key=(row['game'],row['cache'],row['variant'])
        groups.setdefault(key,[]).append(float(row['duration_ms'])/1000)
for key,values in sorted(groups.items()):
    print(f"{' / '.join(key)}: n={len(values)} median={statistics.median(values):.3f}s range={min(values):.3f}-{max(values):.3f}s")
