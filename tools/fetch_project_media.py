#!/usr/bin/env python3
"""Cache original project README thumbnails without replacing existing media."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen
ROOT = Path(__file__).resolve().parents[1]
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strict', action='store_true')
    args = parser.parse_args()
    profile = json.loads((ROOT / 'data/profile.json').read_text(encoding='utf-8'))
    manifest_path = ROOT / 'assets/media/sources.json'
    records = {entry['file']: entry for entry in json.loads(manifest_path.read_text(encoding='utf-8'))}
    failed = []
    for item in profile['projects']:
        source = item.get('image_source')
        target = ROOT / item['image']
        if target.exists() or not source: continue
        try:
            request = Request(source, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'image/*'})
            with urlopen(request, timeout=25) as response: content = response.read(10 * 1024 * 1024 + 1)
            if len(content) > 10 * 1024 * 1024: raise ValueError('Image exceeds 10 MB')
            valid = content.startswith((b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff', b'GIF87a', b'GIF89a')) or (content[:4] == b'RIFF' and content[8:12] == b'WEBP')
            if not valid: raise ValueError('Response is not a supported image')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            records[item['image']] = {'file': item['image'], 'source': source, 'status': 'ok', 'sha256': hashlib.sha256(content).hexdigest()}
            print(f'Cached {item["image"]} ({len(content):,} bytes)')
        except (OSError, ValueError, URLError, HTTPError) as exc:
            failed.append(item['id'])
            print(f'Not cached: {item["id"]}: {exc}')
    manifest_path.write_text(json.dumps(list(records.values()), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return int(args.strict and bool(failed))
if __name__ == '__main__': raise SystemExit(main())
