#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepare the owner's Valve AVI for bounded, decoder-free Nano playback."""
from pathlib import Path
import argparse, hashlib, json, shutil, struct, subprocess, tempfile


def prepare(source, output, ffmpeg='ffmpeg', crop=None):
    if crop is not None:
        if len(crop) != 4 or min(crop[:2]) <= 0 or min(crop[2:]) < 0 or crop[0] * 3 != crop[1] * 4:
            raise ValueError('Crop must be a positive 4:3 WIDTH:HEIGHT:X:Y rectangle')
    filters = 'fps=15,' + ('crop=' + ':'.join(map(str, crop)) + ',' if crop else '') + 'scale=240:180:flags=lanczos'
    destination = output / 'valve/media/nano_valve.nvi'
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='nano-intro-') as directory:
        video, audio = (Path(directory) / name for name in ('video.raw', 'audio.raw'))
        subprocess.run([ffmpeg, '-v', 'error', '-y', '-i', str(source), '-an',
                        '-vf', filters, '-pix_fmt', 'rgb565le',
                        '-f', 'rawvideo', str(video)], check=True)
        subprocess.run([ffmpeg, '-v', 'error', '-y', '-i', str(source), '-vn',
                        '-ar', '22050', '-ac', '1', '-acodec', 'pcm_u8', '-f', 'u8',
                        str(audio)], check=True)
        frame_bytes = 240 * 180 * 2
        frames, remainder = divmod(video.stat().st_size, frame_bytes)
        samples = audio.stat().st_size
        if remainder or not 1 <= frames <= 450 or abs(samples / 22050 - frames / 15) > .1:
            raise ValueError('Expected a complete intro of at most 30 seconds with synchronized audio')
        with destination.open('wb') as stream:
            stream.write(struct.pack('<4s7I', b'NVI1', 240, 180, 15, frames, 22050, samples, 0))
            for part in (video, audio):
                with part.open('rb') as data:
                    shutil.copyfileobj(data, stream)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = {'input': source.name, 'input_sha256': sha(source), 'size': [240, 180],
                'framing': 'original 4:3 picture, embedded black margins removed' if crop else 'complete original 4:3 frame; black bars on the square display',
                'crop': list(crop) if crop else None,
                'fps': 15, 'frames': frames, 'duration': frames / 15,
                'audio': {'rate': 22050, 'channels': 1, 'format': 'unsigned PCM8', 'samples': samples},
                'components': {'valve/media/nano_valve.nvi': sha(destination)}}
    (output / 'intro.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Locally owned valve.avi')
    parser.add_argument('--output', type=Path, required=True, help='Private runtime root')
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--crop', type=lambda s: tuple(map(int, s.split(':'))),
                        help='4:3 picture rectangle WIDTH:HEIGHT:X:Y; original Valve AVI: 320:240:160:120')
    args = parser.parse_args()
    result = prepare(args.source, args.output, args.ffmpeg, args.crop)
    print(f'Prepared {result["duration"]:g} seconds of original picture/audio; hashes in intro.json')
