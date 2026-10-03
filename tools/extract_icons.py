#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Convert each user's own game.ico into an unmodified RGBA PNG."""
from pathlib import Path
from PIL import Image
import argparse

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--games', type=Path, required=True, help='Parent of valve/ and cstrike/')
    args = parser.parse_args()
    destination = ROOT/'build/icons'
    destination.mkdir(parents=True, exist_ok=True)
    for game in ('valve', 'cstrike'):
        with Image.open(args.games/game/'game.ico') as icon:
            size = max(icon.ico.sizes(), key=lambda s: s[0]*s[1])
            icon.ico.getimage(size).convert('RGBA').save(destination/f'{game}.png')
            print(f'{game}: extracted {size[0]}x{size[1]} icon')
