#!/usr/bin/env python3
"""Verify profile content, local media, responsive layout and animation controls."""
from pathlib import Path
import functools
import http.server
import json
import threading
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup
from PIL import Image, ImageSequence
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'verification'
OUT.mkdir(exist_ok=True)
report = {'checks': {}, 'screenshots': []}
profile = json.loads((ROOT / 'data/profile.json').read_text(encoding='utf-8'))
for filename in ['index.html', 'cv.html']:
    soup = BeautifulSoup((ROOT / filename).read_text(encoding='utf-8'), 'html.parser')
    assert len(soup.find_all('h1')) == 1
    assert 'Inha Lee' in soup.title.text
    assert 'Research thumbnails:' not in soup.get_text()
    missing = []
    for tag in soup.select('[href], [src], [data-animation]'):
        for key in ['href', 'src', 'data-animation']:
            if not tag.get(key): continue
            parsed = urlsplit(tag[key])
            if parsed.scheme or parsed.netloc or not parsed.path: continue
            if not (ROOT / unquote(parsed.path)).exists(): missing.append(parsed.path)
    assert not missing, (filename, missing)
    report['checks'][filename] = {'missing_local_paths': []}
    for project in profile['projects']:
        assert project['title'] in soup.get_text()
        assert project['technologies'] in soup.get_text()
        assert str(project['year']) in soup.get_text()
    assert 'cylindrical coordinates' in soup.get_text()
    assert 'hand-built hardware' in soup.get_text()
    assert 'Team Development Lead' in soup.get_text()
    assert 'Python · ROS · NVIDIA Isaac Sim' in soup.get_text()
soup = BeautifulSoup((ROOT / 'index.html').read_text(encoding='utf-8'), 'html.parser')
assert len(soup.select('.publication')) == 5
assert len(soup.select('.project')) == 7
assert len(soup.select('.technologies')) == 12
assert '(Undergraduate)' in soup.select_one('#projects-heading').text
for ident, year, stage in [('hand-rhythm', 2018, '2nd'), ('line-tracer', 2018, '2nd'), ('lane-detection', 2019, '3rd'), ('obstacle-avoidance', 2020, '4th')]:
    metadata = soup.select_one(f'#{ident} .project-meta').text
    assert str(year) in metadata and stage + '-year undergraduate' in metadata
for article in soup.select('.publication'): assert 'Python' in article.select_one('.technologies').text
assert (ROOT / 'AiSDF').is_dir()
cv = BeautifulSoup((ROOT / 'cv.html').read_text(encoding='utf-8'), 'html.parser')
assert len(cv.select('.ongoing-item')) == 3
assert 'SLAM · Multi-Agent Systems · Lifelong SLAM · Active Perception' in cv.get_text()
assert 'RS-2022-II220907' in cv.get_text()
assert 'Funded research project (project period)' in cv.get_text()
for path in (ROOT / 'assets/media').glob('*.gif'):
    with Image.open(path) as image:
        frames = image.n_frames
        duration = sum(f.info.get('duration', 0) for f in ImageSequence.Iterator(image))
        assert frames > 1
        report['checks'][path.name] = {'frames': frames, 'duration_ms': duration, 'size': list(image.size), 'bytes': path.stat().st_size}
        if path.name == 'obstacle-avoidance.gif': assert frames == 122 and duration == 8540
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_address[1]}/'
errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for width, height, name in [(1200, 1000, 'desktop'), (390, 844, 'mobile')]:
        page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1, reduced_motion='reduce')
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url, wait_until='networkidle', timeout=60000)
        page.locator('img').evaluate_all('(imgs)=>imgs.forEach(img=>img.loading="eager")')
        page.wait_for_function('Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)', timeout=30000)
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'), name
        assert page.locator('img[data-remote-media]').count() == 0
        page.screenshot(path=str(OUT / (name + '.png')), full_page=True)
        page.locator('#other-projects').screenshot(path=str(OUT / (name + '-projects.png')))
        page.locator('#obstacle-avoidance').scroll_into_view_if_needed()
        image = page.locator('#obstacle-avoidance img')
        assert not image.get_attribute('src').endswith('.gif')
        button = page.locator('#obstacle-avoidance [data-toggle-clip]')
        button.wait_for(state='visible', timeout=20000)
        button.click()
        assert button.get_attribute('aria-pressed') == 'true'
        assert image.get_attribute('src').endswith('obstacle-avoidance.gif')
        page.wait_for_timeout(700)
        page.locator('#obstacle-avoidance').screenshot(path=str(OUT / (name + '-driving.png')))
        button.click()
        assert button.get_attribute('aria-pressed') == 'false'
        assert not image.get_attribute('src').endswith('.gif')
        page.goto(url + 'cv.html', wait_until='networkidle')
        assert page.locator('[data-print]').count() == 1
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        page.screenshot(path=str(OUT / (name + '-cv.png')), full_page=True)
        page.screenshot(path=str(OUT / (name + '-cv-top.png')))
        report['checks'][name] = {'horizontal_overflow': False, 'broken_images': [], 'driving_animation_controls': 'passed', 'reduced_motion': 'passed'}
        report['screenshots'].append(name + '-projects.png')
        page.close()
    browser.close()
server.shutdown()
assert not errors, errors
report['checks']['javascript_errors'] = errors
report['checks']['content'] = {'publications': 5, 'undergraduate_projects': 7, 'ongoing_research_and_projects': 3}
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
