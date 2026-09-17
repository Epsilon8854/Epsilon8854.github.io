#!/usr/bin/env python3
"""Check content parity, local media, responsive layout, and animation controls."""
from pathlib import Path
import functools
import http.server
import json
import os
import threading
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'verification'; OUT.mkdir(exist_ok=True)
profile=json.loads((ROOT/'data/profile.json').read_text())
report={'checks':{},'warnings':[],'screenshots':[]}
for filename in ['index.html','cv.html']:
    soup=BeautifulSoup((ROOT/filename).read_text(),'html.parser')
    assert len(soup.find_all('h1'))==1
    assert 'Inha Lee' in soup.title.text
    missing=[]
    for tag in soup.select('[href], [src]'):
        url=tag.get('src') or tag.get('href')
        parsed=urlsplit(url)
        if parsed.scheme or parsed.netloc or not parsed.path: continue
        path=ROOT/unquote(parsed.path)
        if not path.exists(): missing.append(str(parsed.path))
    report['checks'][filename]={'missing_local_paths':sorted(set(missing))}
    assert not missing, filename+': missing assets '+str(sorted(set(missing)))
    assert 'Research thumbnails:' not in soup.get_text()
    for item in profile['publications']:
        article=soup.find(id=item['id'])
        assert article and item['technologies'] in article.select_one('.technologies').get_text()
    for item in profile['projects']:
        article=soup.find(id=item['id'])
        assert article, filename+': missing project '+item['id']
        metadata=article.select_one('.project-meta').get_text()
        assert str(item['year']) in metadata
        assert item.get('academic_stage','') in metadata
        assert item.get('role','') in metadata
        assert item['technologies'] in article.select_one('.technologies').get_text()
soup=BeautifulSoup((ROOT/'index.html').read_text(),'html.parser')
assert len(soup.select('.publication'))==len(profile['publications'])
assert len(soup.select('.project'))==len(profile['projects'])==7
assert 'Undergraduate' in soup.select_one('#projects-heading').text
assert soup.select_one('#obstacle-avoidance img')['src']==next(x['image'] for x in profile['projects'] if x['id']=='obstacle-avoidance')
assert soup.select_one('#unisim-slam .venue').text.count('2026')==1
assert soup.select_one('#fedepth .venue').text.count('2026')==1
assert (ROOT/'AiSDF').is_dir(), 'Existing AiSDF project must be preserved'
for item in profile['projects']:
    if item.get('animation_source'): assert (ROOT/item['animation']).is_file(), 'Missing project animation'
for path in (ROOT/'assets/media').glob('*.gif'):
    with Image.open(path) as image:
        report['checks'][path.name]={'frames':image.n_frames,'size':list(image.size),'bytes':path.stat().st_size}
        assert image.n_frames>1
handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT))
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_address[1]}/'
errors=[]
with sync_playwright() as p:
    executable=os.environ.get('CHROMIUM_EXECUTABLE')
    browser=p.chromium.launch(headless=True,**({'executable_path':executable} if executable else {}))
    for width,height,name in [(1200,1000,'desktop'),(390,844,'mobile'),(320,740,'mobile-small')]:
        page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1,reduced_motion='reduce')
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(url,wait_until='networkidle',timeout=60000)
        page.locator('img').evaluate_all('(imgs)=>imgs.forEach(img=>img.loading="eager")')
        page.wait_for_timeout(3000)
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'), 'Horizontal overflow: '+name
        broken=page.locator('img').evaluate_all('(imgs)=>imgs.filter(img=>!img.complete||img.naturalWidth===0).map(img=>img.src)')
        report['checks'][name]={'horizontal_overflow':False,'broken_images':broken}
        assert not broken, name+': broken images '+str(broken)
        page.screenshot(path=str(OUT/(name+'.png')),full_page=True)
        page.screenshot(path=str(OUT/(name+'-top.png')),full_page=False)
        page.locator('#other-projects').screenshot(path=str(OUT/(name+'-projects.png')))
        report['screenshots'].append(name+'.png')
        page.goto(url+'cv.html',wait_until='networkidle')
        assert page.locator('[data-print]').count()==1
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        page.screenshot(path=str(OUT/(name+'-cv.png')),full_page=True)
        page.close()
    page=browser.new_page(viewport={'width':1200,'height':1000})
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(url,wait_until='domcontentloaded')
    for item in profile['projects']:
        if not item.get('animation') or not (ROOT/item['animation']).is_file(): continue
        page.locator('#'+item['id']).scroll_into_view_if_needed()
        button=page.locator('#'+item['id']+' [data-toggle-clip]')
        button.wait_for(state='visible',timeout=20000)
        page.wait_for_function('(id)=>document.querySelector("#"+id+" [data-toggle-clip]").getAttribute("aria-pressed")==="true"',arg=item['id'])
        button.click(); assert button.get_attribute('aria-pressed')=='false'
        button.click(); assert button.get_attribute('aria-pressed')=='true'
    report['checks']['animation_buttons']='passed'
    browser.close()
server.shutdown()
assert not errors,errors
report['checks']['javascript_errors']=errors
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
