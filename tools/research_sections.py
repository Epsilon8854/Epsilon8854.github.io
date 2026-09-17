"""Render the owner's research interests and ongoing work for the HTML CV."""
from __future__ import annotations
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def render_research_sections() -> str:
    data = json.loads((ROOT / 'data/research.json').read_text(encoding='utf-8'))
    esc = lambda value: html.escape(str(value), quote=True)
    interests = esc(' · '.join(data['research_interests']))
    articles = []
    for item in data['ongoing_work']:
        period = item['period']
        if item.get('kind') == 'Funded research project':
            period += ' · Funded research project (project period)'
        funding = f'<p class="funding"><em>{esc(item["funding"])}</em></p>' if item.get('funding') else ''
        articles.append(
            f'<article class="cv-item ongoing-item" id="{esc(item["id"])}">'
            f'<h3>{esc(item["title"])}</h3><p class="note project-meta">{esc(period)}</p>'
            f'{funding}<p class="description">{esc(item["description"])}</p></article>'
        )
    return (
        '<section class="cv-section" id="research-interests"><h2>Research Interests</h2>'
        f'<p class="interests">{interests}</p></section>\n'
        '<section class="cv-section" id="ongoing-research"><h2>Ongoing Research &amp; Projects</h2>'
        + ''.join(articles) + '</section>\n'
    )
