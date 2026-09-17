#!/usr/bin/env python3
"""One-time assembly of the user-supplied animation and prepared UI additions."""
import base64
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageSequence
ROOT = Path(__file__).resolve().parents[1]
parts = sorted((ROOT / '.profile-update').glob('part-*.bin'))
assert len(parts) == 6
blocks = [p.read_bytes() for p in parts]
# Repair a detected transport insertion before checking the complete media hash.
encoded = base64.b64encode(blocks[2]).decode('ascii')
assert encoded.count('1yexEVQYY+x') == 1
blocks[2] = base64.b64decode(encoded.replace('1yexEVQYY+x', '1yexEVQY+x') + 'W')
assert hashlib.sha1(b'blob 4800\0' + blocks[2]).hexdigest() == 'b1ebab79300e344f60fedcc905f14db336c0dba2'
clip = b''.join(blocks)
assert hashlib.sha256(clip).hexdigest() == '06f3a5604b0244d0ea018da3bde8124ef3464af0adc997421fe649522d7967fa'
output = ROOT / 'assets/media/obstacle-avoidance.gif'
poster = ROOT / 'assets/images/obstacle-avoidance-upload.webp'
with tempfile.TemporaryDirectory() as td:
    source = Path(td) / 'source.mp4'
    source.write_bytes(clip)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(source), '-filter_complex', '[0:v]split[a][b];[a]palettegen=max_colors=128:stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=4', '-fps_mode', 'passthrough', '-loop', '0', str(output)], check=True)
with Image.open(output) as image:
    assert image.n_frames == 122
    duration = sum(f.info.get('duration', 0) for f in ImageSequence.Iterator(image))
    assert duration == 8540
    image.seek(0)
    image.convert('RGB').save(poster, format='WEBP', quality=90)
    dimensions = list(image.size)
manifest_path = ROOT / 'assets/media/sources.json'
records = {r['file']: r for r in json.loads(manifest_path.read_text(encoding='utf-8'))}
for path in [output, poster]:
    rel = path.relative_to(ROOT).as_posix()
    records[rel] = {'file': rel, 'source': 'User-supplied Sep-17-2026 15-11-27.gif (ZIP attachment)', 'original_gif_sha256': 'e906931c20b6b5e715f4ec2138e045b3ae001737f21b50e02d03f1de2fe67896', 'status': 'ok', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'dimensions': dimensions, 'note': 'Thumbnail optimized through an AV1 transfer intermediate; original scene, all 122 frames and 8.54-second timeline retained.'}
    if path == output: records[rel].update(frames=122, duration_ms=8540)
manifest_path.write_text(json.dumps(list(records.values()), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
css = '''
/* Academic stage and implementation details, shared by homepage and CV. */
.project-meta{font-size:12px;line-height:1.55;color:#5c5c5c;margin:2px 0 7px}
.section-subtitle{display:inline-block;font-size:.76em;color:var(--muted)}
.section-head{flex-wrap:wrap}
.section-head .text-button{flex-shrink:0}
.cv-item .project-meta,.cv-item .funding{font-size:12px;color:#555}
.cv-item .technologies{font-size:12px;line-height:1.5}
.cv-section .interests{font-size:13px;line-height:1.6}
.ongoing-item .description{margin-top:6px}
.thumb .media-unavailable{border:1px solid var(--rule);border-radius:3px}
@media print{.cv-item .project-meta,.cv-item .funding,.cv-item .technologies{font-size:9pt;color:#333}.cv-section .interests{font-size:10pt}.cv-section h2{break-after:avoid}}
'''
css_path = ROOT / 'assets/site.css'
assert hashlib.sha256(css_path.read_bytes()).hexdigest() == 'f07de64a5fdcf4432a604796407f8b76412feee91b0d61b53e13f6d0b0babe6f'
css_path.write_text(css_path.read_text(encoding='utf-8') + css, encoding='utf-8')
js = '''
// Keep a usable project link when a remotely hosted legacy thumbnail is unavailable.
(() => {
  document.querySelectorAll('img[data-remote-media]').forEach(img => {
    const placeholder = img.closest('figure')?.querySelector('[data-media-placeholder]');
    const recover = () => { if (placeholder) { img.hidden = true; placeholder.hidden = false; } };
    img.addEventListener('error', recover);
    if (img.complete && img.naturalWidth === 0) recover();
  });
})();
'''
js_path = ROOT / 'assets/site.js'
assert hashlib.sha256(js_path.read_bytes()).hexdigest() == '2b4ea2410cd2d3029aa2d6a4b81f21a4417452ed07757c5d5d7f4c7e317273a2'
js_path.write_text(js_path.read_text(encoding='utf-8') + js, encoding='utf-8')
subprocess.run(['python', str(ROOT / 'tools/fetch_project_media.py'), '--strict'], check=True)
shutil.rmtree(ROOT / '.profile-update')
print('Prepared animated thumbnail, original project media and shared styles.')
