# Inha Lee — Academic homepage

Personal research and CV website for [Inha Lee](https://epsilon8854.github.io/), inspired by the compact academic layout of [Marwan Taher](https://marwan99.github.io/) and [Jon Barron](https://jonbarron.info/).

## Edit and preview

1. Edit `data/profile.json` for papers, authors, venues, descriptions, and project links.
2. Edit `tools/build_site.py` for the introduction or page structure.
3. Run `python tools/build_site.py`.
4. Run `python -m http.server 8000` and open `http://localhost:8000`.
5. Commit the generated HTML, CSS, JavaScript, and local media. The existing `AiSDF/` project remains unchanged.

This is a plain static site: no runtime build service, trackers, analytics, or JavaScript framework. Core content is readable without JavaScript. The CV page offers the browser's Print / Save as PDF command; it is not a pre-existing downloadable CV PDF.

## Sources and media

Publication metadata and research thumbnails come from [UNIST 3D Vision & Robotics Lab](https://unist.info/?page_id=1064). Authorship roles are also cross-checked with the owner's public profile README. Individual project descriptions and demo media come from their linked original repositories. The publication status of UniSim-SLAM and FeDepth is **ECCV 2026**.

`assets/media/sources.json` records original sources, conversion results, and unavailable assets. `tools/prepare_media.py` and `tools/recover_media.py` reproduce optimized media from public originals. Third-party images and video remain the property of their respective owners. The page layout is independently implemented with attribution; no other researcher's biography or research content is copied.

Only genuine project footage is used. If YouTube prevents downloading the static-obstacle-avoidance video, its real poster and original video link remain available; no synthetic animation is substituted. After obtaining an original MP4, create `assets/media/obstacle-avoidance.gif`, then rebuild the page.

## Content still requiring owner input

Exact education dates, undergraduate degree, expected graduation, internships, awards beyond the verified public record, and internship availability are intentionally not invented. Add these to a full application CV after confirmation. Public profile content here is a starting point, not a claim of an exhaustively completed employment CV.

## Deployment

Repository: `Epsilon8854/Epsilon8854.github.io`. Serve `main` at the repository root with GitHub Pages. The `.nojekyll` file keeps existing static project assets intact. No custom domain or DNS changes are needed.
