#!/usr/bin/env python3
"""Build the static homepage and printable CV. Existing AiSDF is never touched."""
from __future__ import annotations
import html
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT / 'data/profile.json').read_text())
def esc(value): return html.escape(str(value), quote=True)
def link(url, text): return f'<a href="{esc(url)}">{esc(text)}</a>'
def resources(items): return '<div class="resource-links">' + ''.join(link(u, t) for t, u in items.items()) + '</div>'
def authors(names): return ', '.join(f'<strong>{esc(n)}</strong>' if n.rstrip('*') == P['name'] else esc(n) for n in names)
def contact(cv=False):
    entries = [('mailto:' + P['email'], 'Email'), ('cv.html', 'CV'), (P['scholar'], 'Scholar'), (P['github'], 'GitHub'), (P['linkedin'], 'LinkedIn')]
    if cv: entries = [('mailto:' + P['email'], P['email']), (P['site'], 'Website'), (P['scholar'], 'Scholar'), (P['github'], 'GitHub')]
    return '<nav class="contact-links" aria-label="Contact and profiles">' + ''.join(link(u,t) for u,t in entries) + '</nav>'
def head(title, path=''):
    description = 'Inha Lee — SLAM, geometric foundation models, neural 3D reconstruction, and collaborative robot perception. UNIST 3D Vision & Robotics Lab.'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="author" content="Inha Lee">
<link rel="canonical" href="{esc(P['site']+path)}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(P['site']+path)}"><meta property="og:image" content="{esc(P['site'])}assets/images/profile.jpg"><meta name="twitter:card" content="summary">
<meta name="color-scheme" content="light"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/site.css"><script src="assets/site.js" defer></script>
</head>'''
def thumb(item):
    target = item.get('repo') or next(iter(item['links'].values()))
    fallback = f' data-fallback="{esc(item["image_source"])}"' if item.get('image_source') else ''
    animation = f' data-animation="{esc(item["animation"])}"' if item.get('animation') and (ROOT / item['animation']).is_file() else ''
    button = f'<button class="text-button animation-button" data-toggle-clip aria-label="Play or pause {esc(item["title"])} demo" aria-pressed="false" hidden>Play demo</button>' if animation else ''
    return f'<figure class="thumb"><a href="{esc(target)}" aria-label="{esc(item["title"])}"><img class="thumb-image" src="{esc(item["image"])}" alt="{esc(item["alt"])}" width="410" height="290" loading="lazy" decoding="async"{fallback}{animation}></a>{button}</figure>'
def publication(item, cv=False):
    target = next(iter(item['links'].values()))
    note = f'<p class="note">{esc(item["note"])}</p>' if item.get('note') else ''
    role = f'<span class="role">{esc(item["role"])}</span>' if item.get('role') and item['role'] != 'Co-author' else ''
    content = f'''<h3>{link(target,item['title'])}</h3><p class="authors">{authors(item['authors'])}</p><p class="venue"><strong>{esc(item['venue'])}, {item['year']}</strong>{role}</p>{note}{resources(item['links'])}<p class="description">{esc(item['description'])}</p>'''
    if cv: return f'<article class="cv-item">{content}</article>'
    return f'<article class="entry publication" id="{esc(item["id"])}">{thumb(item)}<div>{content}</div></article>'
def project(item, cv=False):
    content = f'<h3>{link(item["repo"],item["title"])}</h3><p class="description">{esc(item["description"])}</p><p class="technologies">{esc(item["technologies"])}</p>{resources(item["links"])}'
    if cv: return f'<article class="cv-item">{content}</article>'
    return f'<article class="entry project" id="{esc(item["id"])}">{thumb(item)}<div>{content}</div></article>'
bio = '''<p>Hi! I am an integrated M.S.–Ph.D. student in the <a href="https://unist.info/">3D Vision &amp; Robotics Lab</a> at <a href="https://www.unist.ac.kr/">UNIST</a>, advised by <a href="https://unist.info/">Kyungdon Joo</a>.</p>
<p>I am interested in <strong>SLAM, 3D reconstruction, and collaborative robot perception</strong>. My research connects geometric foundation models with consistent online mapping, neural scene representations, and learning across heterogeneous robots.</p>
<p>I also enjoy building robotic systems—from autonomous driving and embedded control to interactive computer vision.</p>'''
footer = '''<footer class="footer"><p>Inha Lee · UNIST</p><p>Layout inspired by <a href="https://marwan99.github.io/">Marwan Taher</a> and <a href="https://jonbarron.info/">Jon Barron</a>.</p></footer>'''
page = head('Inha Lee | Robotics & 3D Vision') + f'''<body><a class="skip-link" href="#research">Skip to research</a><main class="site">
<header class="intro" id="about"><div class="intro-copy"><h1>Inha Lee <span class="native-name" lang="ko">이인하</span></h1>{bio}{contact()}</div>
<a class="portrait-link" href="assets/images/profile.jpg" aria-label="View Inha Lee’s profile photo"><img class="portrait" src="assets/images/profile.jpg" data-fallback="https://unist.info/wp-content/uploads/2026/07/%EC%9D%B4%EC%9D%B8%ED%95%981-1.png" alt="Inha Lee" width="228" height="244" fetchpriority="high"></a></header>
<nav class="section-nav" aria-label="Page sections"><a href="#research">Research</a><a href="#other-projects">Other Projects</a><a href="cv.html">Curriculum Vitae</a></nav>
<section id="research" aria-labelledby="research-heading"><h2 id="research-heading">Research</h2><p class="section-intro">Selected publications. An asterisk (*) denotes equal contribution.</p>{''.join(publication(p) for p in P['publications'])}</section>
<section id="other-projects" aria-labelledby="projects-heading"><div class="section-head"><h2 id="projects-heading">Other Projects</h2><button class="text-button" data-toggle-animations aria-pressed="true" hidden>Pause animations</button></div><p class="section-intro">Hands-on projects in perception, autonomous driving, and embedded robotics.</p>{''.join(project(p) for p in P['projects'])}</section>{footer}</main></body></html>'''
(ROOT / 'index.html').write_text(page, encoding='utf-8')
cv = head('Inha Lee | Curriculum Vitae', 'cv.html') + f'''<body><main class="cv-page"><div class="cv-toolbar"><a href="index.html">← Back to homepage</a><button class="print-button" data-print>Print / Save as PDF</button></div>
<header class="cv-header"><h1>Inha Lee <span lang="ko" style="font-size:17px;letter-spacing:0">이인하</span></h1><p>{esc(P['degree'])} · UNIST</p><p>SLAM · Geometric foundation models · Neural 3D reconstruction · Collaborative perception</p>{contact(True)}</header>
<section class="cv-section"><h2>Education &amp; Research Affiliation</h2><article class="cv-item"><h3>Ulsan National Institute of Science and Technology (UNIST)</h3><p>Integrated M.S.–Ph.D. program · 3D Vision &amp; Robotics Lab</p><p>Advisor: Kyungdon Joo</p></article></section>
<section class="cv-section"><h2>Selected Research &amp; Publications</h2><p class="cv-small">* Equal contribution. Author order follows the original publications.</p>{''.join(publication(p,True) for p in P['publications'])}</section>
<section class="cv-section"><h2>Selected Engineering Projects</h2>{''.join(project(p,True) for p in P['projects'])}</section>
<footer class="footer"><p>Full publication record: <a href="{esc(P['scholar'])}">Google Scholar</a></p><p><a href="index.html">epsilon8854.github.io</a></p></footer></main></body></html>'''
(ROOT / 'cv.html').write_text(cv, encoding='utf-8')
(ROOT / '.nojekyll').write_text('')
(ROOT / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + P['site'] + 'sitemap.xml\n')
(ROOT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+esc(P['site']+s)+'</loc></url>' for s in ['', 'cv.html'])+'</urlset>\n')
(ROOT / 'assets/favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#1772d0"/><text x="32" y="44" font-family="Arial,sans-serif" font-size="38" text-anchor="middle" fill="white">IL</text></svg>\n')
print('Built index.html and cv.html; existing project pages preserved.')
