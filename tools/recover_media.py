#!/usr/bin/env python3
"""Cache original public research/project media without inventing demonstrations."""
from __future__ import annotations
import concurrent.futures
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlsplit
from curl_cffi import requests
from PIL import Image, ImageOps
from prepare_media import ROOT, IMAGES, MEDIA, SOURCES, gif

HEADERS = {'Referer':'https://unist.info/?page_id=1064', 'Accept':'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'}

def recover(item):
    name, original, width = item
    path = IMAGES / name
    if path.exists(): return None
    candidates = [original]
    if urlsplit(original).hostname == 'unist.info':
        candidates += [original.replace('https://unist.info/', 'https://www.unist.info/'), original.replace('https://','http://'), 'https://i0.wp.com/' + original.split('://',1)[1], original.replace('https://unist.info/', 'https://wny.baz.mybluehost.me/')]
    attempts = []
    for url in candidates:
        try:
            response = requests.get(url, headers=HEADERS, impersonate='chrome', timeout=20)
            response.raise_for_status()
            with Image.open(io.BytesIO(response.content)) as source:
                source = ImageOps.exif_transpose(source).convert('RGBA')
                image = Image.new('RGBA',source.size,'white'); image.alpha_composite(source)
                image = image.convert('RGB'); image.thumbnail((width,width),Image.Resampling.LANCZOS)
                image.save(path, 'JPEG', quality=90, optimize=True)
            record = {'file':str(path.relative_to(ROOT)), 'source':original, 'retrieved_from':url, 'status':'ok', 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            print('RECOVERED',json.dumps(record),flush=True)
            return record
        except Exception as exc:
            attempts.append({'url':url,'error':str(exc)[:250]})
    record = {'file':str(path.relative_to(ROOT)), 'source':original, 'status':'unavailable', 'attempts':attempts}
    print('UNAVAILABLE',json.dumps(record),flush=True)
    return record

def recover_video():
    output = MEDIA / 'obstacle-avoidance.gif'
    if output.exists(): return None
    url = 'https://www.youtube.com/watch?v=2bW5VAYirro'
    attempts=[]
    for client in ['android_vr','web_safari']:
        try:
            with tempfile.TemporaryDirectory() as td:
                command=['yt-dlp','--no-playlist','--socket-timeout','15','--retries','0','--fragment-retries','0','--js-runtimes','node','--extractor-args','youtube:player_client='+client,'-f','best[height<=480]/best','-o',str(Path(td)/'original.%(ext)s'),url]
                subprocess.run(command,check=True,timeout=100)
                raw=next(p for p in Path(td).glob('original.*') if p.suffix not in {'.part','.ytdl'})
                duration=float(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(raw)],timeout=20))['format']['duration'])
                length=min(10,duration); start=max(0,(duration-length)/2)
                gif(raw,output,start=start,duration=length,width=480)
                return {'file':str(output.relative_to(ROOT)),'source':url,'status':'ok','clip_start_seconds':start,'duration_seconds':length,'fps':12}
        except Exception as exc: attempts.append(str(exc)[:250])
    preview='https://i.ytimg.com/an_webp/2bW5VAYirro/mqdefault_6s.webp'
    try:
        response=requests.get(preview,impersonate='chrome',timeout=20); response.raise_for_status()
        with Image.open(io.BytesIO(response.content)) as image:
            frames=[]; times=[]
            for n in range(getattr(image,'n_frames',1)):
                image.seek(n); frames.append(image.convert('RGB').copy()); times.append(image.info.get('duration',100))
            if len(frames)<2: raise ValueError('No animated preview available')
            frames[0].save(output,save_all=True,append_images=frames[1:],duration=times,loop=0,optimize=True)
            frames[0].save(IMAGES/'obstacle-avoidance.jpg',quality=90)
        return {'file':str(output.relative_to(ROOT)),'source':url,'retrieved_from':preview,'status':'ok','note':'Official animated video preview; no synthetic footage.'}
    except Exception as exc: attempts.append(str(exc)[:250])
    return {'file':str(output.relative_to(ROOT)),'source':url,'status':'unavailable','attempts':attempts,'note':'Original video remains linked. An original MP4 can be converted locally using tools/prepare_media.py.'}

def recover_animation(item):
    """Optimize a project-owned public GIF and keep the original source recorded."""
    source=item.get('animation_source'); relative=item.get('animation')
    if not source or not relative: return []
    output=ROOT/relative
    if output.exists(): return []
    try:
        with tempfile.TemporaryDirectory() as td:
            raw=Path(td)/'source.gif'
            response=requests.get(source,impersonate='chrome',timeout=45)
            response.raise_for_status(); raw.write_bytes(response.content)
            gif(raw,output,duration=8,width=480)
        poster=IMAGES/(output.stem+'.jpg')
        records=[]
        for path in [output,poster]:
            record={'file':str(path.relative_to(ROOT)),'source':source,'status':'ok','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            if path==output: record.update(duration_seconds=8,fps=12)
            records.append(record)
        return records
    except Exception as exc:
        output.unlink(missing_ok=True)
        return [{'file':relative,'source':source,'status':'unavailable','error':str(exc)}]

if __name__=='__main__':
    profile=json.loads((ROOT/'data/profile.json').read_text())
    manifest_path=MEDIA/'sources.json'
    old=json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    records={r['file']:r for r in old}
    sources={item[0]:item for item in SOURCES}
    for item in profile['publications']+profile['projects']:
        if item.get('image_source') and Path(item['image']).suffix=='.jpg':
            name=Path(item['image']).name
            sources.setdefault(name,(name,item['image_source'],800))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for record in pool.map(recover,sources.values()):
            if record: records[record['file']]=record
    for item in profile['projects']:
        for record in recover_animation(item): records[record['file']]=record
    # Do not retry or replace a user-supplied static thumbnail with unrelated media.
    if any(item.get('animation')=='assets/media/obstacle-avoidance.gif' for item in profile['projects']):
        record=recover_video()
        if record: records[record['file']]=record
    manifest_path.write_text(json.dumps(list(records.values()),ensure_ascii=False,indent=2)+'\n')
    print('MEDIA_SUMMARY',json.dumps({k:v['status'] for k,v in records.items()}),flush=True)
