#!/usr/bin/env python3
"""Check authored content, local links, images, mobile overflow, and animation UI."""
from pathlib import Path
import functools
import http.server
import json
import threading
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'verification'; OUT.mkdir(exist_ok=True)
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
    if missing: report['warnings'].append(filename+': missing assets '+str(sorted(set(missing))))
soup=BeautifulSoup((ROOT/'index.html').read_text(),'html.parser')
assert len(soup.select('.publication'))==5
assert len(soup.select('.project'))==4
assert soup.select_one('#unisim-slam .venue').text.count('2026')==1
assert soup.select_one('#fedepth .venue').text.count('2026')==1
assert (ROOT/'AiSDF').is_dir(), 'Existing AiSDF project must be preserved'
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
    browser=p.chromium.launch(headless=True)
    for width,height,name in [(1200,1000,'desktop'),(390,844,'mobile')]:
        page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1,reduced_motion='reduce')
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(url,wait_until='networkidle',timeout=60000)
        page.locator('img').evaluate_all('(imgs)=>imgs.forEach(img=>img.loading="eager")')
        page.wait_for_timeout(3000)
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'), 'Horizontal overflow: '+name
        broken=page.locator('img').evaluate_all('(imgs)=>imgs.filter(img=>!img.complete||img.naturalWidth===0).map(img=>img.src)')
        report['checks'][name]={'horizontal_overflow':False,'broken_images':broken}
        if broken: report['warnings'].append(name+': some image sources unavailable')
        page.screenshot(path=str(OUT/(name+'.png')),full_page=True)
        page.screenshot(path=str(OUT/(name+'-top.png')),full_page=False)
        report['screenshots'].append(name+'.png')
        page.goto(url+'cv.html',wait_until='networkidle')
        assert page.locator('[data-print]').count()==1
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        page.close()
    page=browser.new_page(viewport={'width':1200,'height':1000})
    page.goto(url,wait_until='domcontentloaded')
    page.locator('#lane-detection').scroll_into_view_if_needed()
    button=page.locator('#lane-detection [data-toggle-clip]')
    button.wait_for(state='visible',timeout=20000)
    button.click()
    assert button.get_attribute('aria-pressed')=='false'
    button.click()
    assert button.get_attribute('aria-pressed')=='true'
    report['checks']['animation_buttons']='passed'
    browser.close()
server.shutdown()
assert not errors,errors
report['checks']['javascript_errors']=errors
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
