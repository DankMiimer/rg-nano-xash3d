#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Write the placeholder launcher icons for release OPKs.

Each is a 32x32 PNG padded to exactly 8192 bytes, with a marker chunk right after
IHDR. On first launch nano-art --icon finds the marker inside the uncompressed OPK
and overwrites the slot with the game's own icon from the player's game.ico, so
releases contain no Valve artwork.
"""
from pathlib import Path
import argparse, struct, zlib
from PIL import Image, ImageDraw

SLOT = 8192
GLYPHS = {  # 5x7 pixel letters
    'H': ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
    'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
    'C': ['01110', '10001', '10000', '10000', '10000', '10001', '01110'],
    'S': ['01111', '10000', '10000', '01110', '00001', '00001', '11110'],
}


def placeholder(text, colour):
    """A plain dark tile with two letters, shown until the real icon is set."""
    image = Image.new('RGBA', (32, 32))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((1, 1, 30, 30), radius=5, fill=(44, 44, 48, 255), outline=(90, 90, 96, 255))
    for i, letter in enumerate(text):
        for y, row in enumerate(GLYPHS[letter]):
            for x, bit in enumerate(row):
                if bit == '1':
                    draw.rectangle((5 + i * 12 + x * 2, 9 + y * 2, 6 + i * 12 + x * 2, 10 + y * 2), fill=colour)
    return image


def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))


def slot_png(image, game):
    raw = b''.join(b'\0' + image.tobytes()[y * 128:(y + 1) * 128] for y in range(32))
    head = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 32, 32, 8, 6, 0, 0, 0))
    tail = chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    marker = f'NANO-ICON-SLOT:{game}'.encode() + b'\0'
    padding = SLOT - len(head) - 12 - len(tail)
    png = head + chunk(b'npAd', marker.ljust(padding, b'\0')) + tail
    assert len(png) == SLOT
    return png


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='Directory for valve.png and cstrike.png')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'valve.png').write_bytes(slot_png(placeholder('HL', (255, 160, 32, 255)), 'valve'))
    (args.output/'cstrike.png').write_bytes(slot_png(placeholder('CS', (236, 236, 228, 255)), 'cstrike'))
    print(f'Wrote placeholder icons to {args.output}')
