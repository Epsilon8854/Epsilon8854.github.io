#!/usr/bin/env python3
"""Fetch the profile owner's public research/project media; never invent demos.

Run: python -m pip install Pillow 'yt-dlp[default]'; python tools/prepare_media.py
Requires ffmpeg/ffprobe. An unavailable video leaves an honest static poster.
Original assets and third-party media retain their owners' rights.
"""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import urllib.request
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / 'assets' / 'images'
MEDIA = ROOT / 'assets' / 'media'
IMAGES.mkdir(parents=True, exist_ok=True)
MEDIA.mkdir(parents=True, exist_ok=True)
SOURCES = [
 ('profile.jpg', 'https://unist.info/wp-content/uploads/2026/07/%EC%9D%B4%EC%9D%B8%ED%95%981-1.png', 640),
 ('unisim-slam.jpg', 'https://unist.info/wp-content/uploads/2026/06/unisimslam_public-1-pdf.jpg', 900),
 ('fedepth.jpg', 'https://unist.info/wp-content/uploads/2026/06/Homepage_publication-pdf.jpg', 900),
 ('cse-dataset.jpg', 'https://unist.info/wp-content/uploads/2024/11/CSEDataset_News-pdf.jpg', 900),
 ('aisdf.jpg', 'https://unist.info/wp-content/uploads/2024/02/ral2024-AiSDF-teaser.png', 900),
 ('frasier.jpg', 'https://unist.info/wp-content/uploads/2023/12/ICASSP2024-pulbication.png', 900),
 ('lane-detection.jpg', 'https://i.imgur.com/Vvnq9gl.jpg', 800),
 ('line-tracer.jpg', 'https://i.imgur.com/5YUE6kI.jpg', 800),
 ('obstacle-avoidance.jpg', 'https://img.youtube.com/vi/2bW5VAYirro/hqdefault.jpg', 640),
]

def fetch(url: str, target: Path) -> None:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (academic profile media preparation)'})
    with urllib.request.urlopen(req, timeout=45) as response:
        content = response.read(150 * 1024 * 1024)
    if not content:
        raise ValueError('Empty response')
    target.write_bytes(content)

def still(item: tuple[str, str, int]) -> dict:
    name, url, width = item
    target = IMAGES / name
    try:
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / 'source'
            fetch(url, raw)
            with Image.open(raw) as image:
                image = ImageOps.exif_transpose(image).convert('RGB')
                image.thumbnail((width, width), Image.Resampling.LANCZOS)
                image.save(target, 'JPEG', quality=88, optimize=True)
        result = {'file': str(target.relative_to(ROOT)), 'source': url, 'status': 'ok', 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
    except Exception as exc:
        result = {'file': str(target.relative_to(ROOT)), 'source': url, 'status': 'unavailable', 'error': str(exc)}
    print(json.dumps(result), flush=True)
    return result

def gif(raw: Path, output: Path, *, start: float = 0, duration: float = 8, width: int = 400) -> None:
    filters = f'fps=12,scale={width}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-ss', str(start), '-t', str(duration), '-i', str(raw), '-filter_complex', filters, '-loop', '0', str(output)], check=True, timeout=120)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-ss', str(start), '-i', str(raw), '-frames:v', '1', '-vf', f'scale={width}:-1', str(IMAGES / (output.stem + '.jpg'))], check=True, timeout=45)
    with Image.open(output) as image:
        if getattr(image, 'n_frames', 1) < 2:
            raise ValueError('Output is not an animated GIF')

def existing_animation(name: str, url: str, duration: float) -> dict:
    output = MEDIA / (name + '.gif')
    try:
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / 'source.gif'
            fetch(url, raw)
            gif(raw, output, duration=duration)
        result = {'file': str(output.relative_to(ROOT)), 'source': url, 'status': 'ok', 'duration_seconds': duration, 'fps': 12}
    except Exception as exc:
        result = {'file': str(output.relative_to(ROOT)), 'source': url, 'status': 'unavailable', 'error': str(exc)}
    print(json.dumps(result), flush=True)
    return result

def obstacle_video() -> dict:
    url = 'https://www.youtube.com/watch?v=2bW5VAYirro'
    output = MEDIA / 'obstacle-avoidance.gif'
    result = {'file': str(output.relative_to(ROOT)), 'source': url}
    try:
        with tempfile.TemporaryDirectory() as td:
            prefix = str(Path(td) / 'obstacle.%(ext)s')
            subprocess.run(['yt-dlp', '--no-playlist', '--socket-timeout', '20', '--retries', '1', '--fragment-retries', '1', '--js-runtimes', 'node', '-f', 'best[height<=480]/best', '-o', prefix, url], check=True, timeout=180)
            candidates = [p for p in Path(td).glob('obstacle.*') if p.suffix not in {'.part', '.ytdl', '.json'}]
            if not candidates:
                raise FileNotFoundError('No video downloaded')
            raw = candidates[0]
            probe = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(raw)], timeout=30)
            length = float(json.loads(probe)['format']['duration'])
            duration = min(10.0, length)
            start = max(0.0, (length - duration) / 2)
            gif(raw, output, start=start, duration=duration, width=480)
            result.update(status='ok', clip_start_seconds=round(start, 3), duration_seconds=duration, fps=12)
    except Exception as exc:
        result.update(status='unavailable', error=str(exc), note='Keep the linked original video poster. No simulated footage is substituted.')
    print(json.dumps(result), flush=True)
    return result

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        manifest = list(pool.map(still, SOURCES))
    manifest.append(existing_animation('lane-detection', 'https://i.imgur.com/2yoQeIb.gif', 8))
    manifest.append(existing_animation('hand-rhythm', 'https://raw.githubusercontent.com/Epsilon8854/HandPlaying_RhythmGame/main/image/HandPlayingGameExample.gif', 8))
    manifest.append(obstacle_video())
    (MEDIA / 'sources.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print('MEDIA_SUMMARY', json.dumps({r['file']: r['status'] for r in manifest}), flush=True)
