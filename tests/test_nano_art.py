# SPDX-License-Identifier: GPL-3.0-or-later
"""On-device artwork tool: same output as the Pillow preparation script, from synthetic game files."""
from pathlib import Path
import importlib.util, random, struct, subprocess, tempfile
from PIL import Image

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_menu_art', root/'tools/prepare_menu_art.py')
prepare_menu_art = importlib.util.module_from_spec(spec); spec.loader.exec_module(prepare_menu_art)
rng = random.Random(7)


def noise(size, mode):
    """Smooth gradients plus noise, so resampling differences would show."""
    w, h = size
    image = Image.new(mode, size)
    image.putdata([tuple((x * 7 + y * 3 + c * 50 + rng.randrange(40)) % 256 for c in range(len(mode))) for y in range(h) for x in range(w)])
    return image


def tga(path, image, rle=False, top_left=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format='TGA', rle=rle, **({'orientation': 1} if top_left else {}))


with tempfile.TemporaryDirectory() as directory:
    base = Path(directory)
    games, reference = base/'games', base/'reference'
    # Half-Life: a 21:9 layout of 256px tiles with partial edge tiles, as in the Steam release.
    layout = ['resolution\t900\t300', '']
    for row, y in enumerate((0, 256)):
        for col, x in enumerate(range(0, 900, 256)):
            name = f'resource/background/21_9_{row+1}_{"abcd"[col]}_loading.tga'
            tga(games/'valve'/name, noise((min(256, 900-x), min(256, 300-y)), 'RGB'), rle=(row+col) % 2 == 1)
            layout.append(f'{name}\tfit\t{x}\t{y}')
    (games/'valve/resource/HD_BackgroundLayout.txt').write_text('\n'.join(layout) + '\n')
    tga(games/'valve/resource/logo.tga', noise((800, 86), 'RGBA'))
    # Counter-Strike: twelve loading tiles covering 800x600 and its menu logo (top-left origin).
    for row in range(1, 4):
        for col, letter in enumerate('abcd'):
            size = (min(256, 800 - col*256), min(256, 600 - (row-1)*256))
            tga(games/f'cstrike/resource/background/800_{row}_{letter}_loading.tga', noise(size, 'RGB'))
    tga(games/'cstrike/resource/game_menu.tga', noise((207, 32), 'RGBA'), top_left=True)

    prepare_menu_art.prepare(games, reference)
    tool = base/'nano-art'
    subprocess.run(['gcc', '-std=c99', '-O1', '-g', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined',
                    '-fno-sanitize-recover=all', str(root/'src/nano-art.c'), '-o', str(tool)], check=True)
    for game in ('valve', 'cstrike'):
        result = subprocess.run([str(tool), str(games), game], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        for name in ('gfx/nano/menu_background.tga', 'gfx/nano/menu_logo.tga'):
            produced = (games/game/name).read_bytes()
            expected = (reference/game/name).read_bytes()
            assert produced == expected, f'{game}/{name} differs from the Pillow reference'
    sprite = (games/'cstrike/sprites/nano_menu_background.spr').read_bytes()
    expected = (reference/'cstrike/sprites/nano_menu_background.spr').read_bytes()
    assert len(sprite) == len(expected) and sprite[:42] == expected[:42] and sprite[810:830] == expected[810:830]
    palette, pixels = sprite[42:810], sprite[830:]
    source = Image.open(reference/'cstrike/gfx/nano/menu_background.tga').convert('RGB')
    logo = Image.open(reference/'cstrike/gfx/nano/menu_logo.tga')
    composite = source.convert('RGBA'); composite.alpha_composite(logo, (14, 240 - logo.height - 10))
    rgb = composite.convert('RGB').tobytes()
    error = sum((palette[p*3+c] - rgb[i*3+c]) ** 2 for i, p in enumerate(pixels) for c in range(3))
    psnr = 10 * __import__('math').log10(255**2 / (error / (240*240*3)))
    assert psnr > 30, f'sprite quantization too lossy: {psnr:.1f} dB'

    # Launcher icons: BMP-style ICO entries like the Steam game.ico files, set in place
    # inside an uncompressed release OPK and beside it as RetroFE box art.
    def dib(size, bits, rng_seed, colors=0):
        r = random.Random(rng_seed)
        palette = [(r.randrange(256), r.randrange(256), r.randrange(256)) for _ in range(colors or (1 << bits if bits <= 8 else 0))]
        stride = (size * bits + 31) // 32 * 4
        rows = b''
        for _ in range(size):
            if bits == 4: row = bytes(r.randrange(256) for _ in range(size // 2))
            elif bits == 8: row = bytes(r.randrange(len(palette)) for _ in range(size))
            else: row = bytes(r.randrange(256) for _ in range(size * 3))
            rows += row.ljust(stride, b'\0')
        mask_stride = (size + 31) // 32 * 4
        mask = b''.join(bytes(r.choice((0, 0, 0, 255, 0x0f)) for _ in range(size // 8)).ljust(mask_stride, b'\0') for _ in range(size))
        header = struct.pack('<IiiHHIIiiII', 40, size, size * 2, 1, bits, 0, 0, 0, 0, colors, 0)
        return header + b''.join(bytes((b, g, r_, 0)) for r_, g, b in palette) + rows + mask

    def ico(entries):
        data, directory, offset = b'', b'', 6 + 16 * len(entries)
        for size, bits, colors, seed in entries:
            body = dib(size, bits, seed, colors)
            directory += struct.pack('<BBBBHHII', size, size, colors if colors < 256 else 0, 0, 0, 0, len(body), offset + len(data))
            data += body
        return struct.pack('<HHH', 0, 1, len(entries)) + directory + data

    (games/'valve/game.ico').write_bytes(ico([(16, 4, 16, 1), (16, 8, 0, 2), (32, 4, 16, 3), (32, 8, 0, 4)]))
    (games/'cstrike/game.ico').write_bytes(ico([(16, 8, 0, 5), (32, 8, 0, 6), (32, 24, 0, 7)]))
    spec = importlib.util.spec_from_file_location('make_icons', root/'tools/make_icons.py')
    make_icons = importlib.util.module_from_spec(spec); spec.loader.exec_module(make_icons)
    for game, title in (('valve', 'Half-Life'), ('cstrike', 'Counter-Strike')):
        stage = base/f'stage-{game}'; stage.mkdir()
        (stage/'launch.sh').write_text('#!/bin/sh\n')
        (stage/f'{game}.funkey-s.desktop').write_text(f'[Desktop Entry]\nName={title}\nIcon={game}\n')
        placeholder = make_icons.slot_png(make_icons.placeholder('HL', (255, 160, 32, 255)), game)
        (stage/f'{game}.png').write_bytes(placeholder)
        opk = base/f'{title}.opk'
        subprocess.run(['mksquashfs', str(stage), str(opk), '-noappend', '-comp', 'gzip', '-no-xattrs', '-all-root',
                        '-noI', '-noD', '-noF', '-noX', '-no-fragments', '-quiet'], check=True, stdout=subprocess.DEVNULL)
        assert opk.read_bytes().count(placeholder) == 1, 'placeholder slot not stored verbatim'
        (base/f'{title}.png').write_bytes(placeholder)
        result = subprocess.run([str(tool), '--icon', str(games), game, str(opk)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        extracted = base/f'unpacked-{game}'
        subprocess.run(['unsquashfs', '-q', '-d', str(extracted), str(opk)], check=True, stdout=subprocess.DEVNULL)
        with Image.open(games/game/'game.ico') as source:
            expected_icon = source.ico.getimage(max(source.ico.sizes(), key=lambda s: s[0]*s[1])).convert('RGBA')
        for produced in (extracted/f'{game}.png', base/f'{title}.png'):
            assert produced.stat().st_size == make_icons.SLOT
            with Image.open(produced) as image:
                assert image.mode == 'RGBA' and image.tobytes() == expected_icon.tobytes(), f'{produced.name} differs from Pillow'
        before = opk.read_bytes()
        assert subprocess.run([str(tool), '--icon', str(games), game, str(opk)], capture_output=True).returncode == 3
        assert opk.read_bytes() == before, 'icon set twice'
    other = base/'compressed.opk'
    subprocess.run(['mksquashfs', str(base/'stage-valve'), str(other), '-noappend', '-quiet'], check=True, stdout=subprocess.DEVNULL)
    compressed = other.read_bytes()
    assert subprocess.run([str(tool), '--icon', str(games), 'valve', str(other)], capture_output=True).returncode == 3
    assert other.read_bytes() == compressed
    # Another game's OPK is left alone, and so is box art the player supplied.
    assert subprocess.run([str(tool), '--icon', str(games), 'valve', str(base/'Counter-Strike.opk')], capture_output=True).returncode == 3
    mine = base/'Mine.opk'
    subprocess.run(['mksquashfs', str(base/'stage-valve'), str(mine), '-noappend', '-all-root', '-noI', '-noD', '-noF', '-noX',
                    '-no-fragments', '-quiet'], check=True, stdout=subprocess.DEVNULL)
    (base/'Mine.png').write_bytes(b'user box art')
    assert subprocess.run([str(tool), '--icon', str(games), 'valve', str(mine)], capture_output=True).returncode == 0
    assert (base/'Mine.png').read_bytes() == b'user box art'

    # Missing sources leave menus on their plain background; damaged files are errors.
    empty = base/'empty'; (empty/'valve').mkdir(parents=True)
    assert subprocess.run([str(tool), str(empty), 'valve'], capture_output=True).returncode == 3
    broken = games/'cstrike/resource/background/800_2_b_loading.tga'
    broken.write_bytes(broken.read_bytes()[:500])
    (games/'cstrike/gfx/nano/menu_background.tga').unlink()
    assert subprocess.run([str(tool), str(games), 'cstrike'], capture_output=True).returncode == 2
    assert not (games/'cstrike/gfx/nano/menu_background.tga').exists()
    assert subprocess.run([str(tool), str(games), 'quake'], capture_output=True).returncode == 2
print(f'Menu artwork: byte-identical backgrounds/logos to the Pillow script (RLE, partial tiles, both origins); '
      f'sprite {psnr:.1f} dB; missing sources skipped, damaged tiles rejected. Launcher icons: Pillow-identical '
      f'game.ico choice set once in uncompressed OPKs and box art; compressed or other games\' OPKs untouched.')
