#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepare bounded Nano menu textures from locally owned game resources."""
from pathlib import Path
import argparse, hashlib, json, struct
from PIL import Image


def square_crop(image, position):
    side = min(image.size)
    x = round((image.width - side) * position)
    y = (image.height - side) // 2
    return image.crop((x, y, x + side, y + side)).resize((240, 240), Image.Resampling.LANCZOS)


def sprite(image):
    """One opaque GoldSrc v2 frame; HUD SPR_Draw uses its indexed palette."""
    indexed = image.convert('RGB').quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    palette = bytes(indexed.getpalette()[:768]).ljust(768, b'\0')
    header = struct.pack('<4siiifiiifi', b'IDSP', 2, 2, 0, 170.0, 240, 240, 1, 0.0, 0)
    frame = struct.pack('<iiiii', 0, 0, 0, 240, 240)
    return header + struct.pack('<H', 256) + palette + frame + indexed.tobytes()


def prepare(games, output):
    records = {}
    inputs = {}

    def read(name):
        path = games / name
        inputs[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        with Image.open(path) as image:
            return image.convert('RGBA')

    hl_layout = 'valve/resource/HD_BackgroundLayout.txt'
    layout = (games / hl_layout).read_text().splitlines()
    inputs[hl_layout] = hashlib.sha256((games / hl_layout).read_bytes()).hexdigest()
    _, w, h = layout[0].split()
    hl = Image.new('RGBA', (int(w), int(h)))
    for line in layout[1:]:
        parts = line.split()
        if len(parts) == 4:
            name, _, x, y = parts
            hl.paste(read('valve/' + name), (int(x), int(y)))
    cs = Image.new('RGBA', (800, 600))
    for row in range(1, 4):
        for col, letter in enumerate('abcd'):
            cs.paste(read(f'cstrike/resource/background/800_{row}_{letter}_loading.tga'), (col * 256, (row - 1) * 256))

    def save(name, image):
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, format='TGA')
        records[name] = hashlib.sha256(path.read_bytes()).hexdigest()

    for game, art, position, logo_name, logo_width in (
        ('valve', hl, .60, 'resource/logo.tga', 154),
        ('cstrike', cs, 1., 'resource/game_menu.tga', 156),
    ):
        background = square_crop(art, position).convert('RGB')
        save(game + '/gfx/nano/menu_background.tga', background)
        logo = read(game + '/' + logo_name)
        logo = logo.resize((logo_width, max(1, round(logo.height * logo_width / logo.width))), Image.Resampling.LANCZOS)
        save(game + '/gfx/nano/menu_logo.tga', logo)
        if game == 'cstrike':
            name = game + '/sprites/nano_menu_background.spr'
            path = output / name
            path.parent.mkdir(parents=True, exist_ok=True)
            loading = background.convert('RGBA')
            loading.alpha_composite(logo, (14, 240 - logo.height - 10))
            path.write_bytes(sprite(loading))
            records[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {'size': [240, 240], 'crop': {'valve': .60, 'cstrike': 1.},
                'font': 'supplied Tahoma; exact retail WON lettering pending',
                'inputs': inputs, 'components': records}
    output.mkdir(parents=True, exist_ok=True)
    (output / 'menu-art.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--games', type=Path, required=True, help='Folder containing valve and cstrike')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.games, args.output)
    print(f'Prepared {len(result["components"])} bounded textures/sprites; hashes in menu-art.json')
