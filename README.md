# Bangladesh News Headlines — 15 Portals

A GitHub-ready Bootstrap 5.3 news-headline dashboard.

## What it does

- 15 Bangladesh news portals (exactly the sources requested)
- 10 headlines per portal
- Python collector
- RSS-first collection with homepage fallback
- GitHub Actions runs every 10 minutes
- GitHub Pages deployment
- Responsive Bootstrap 5.3 UI with live search
- Original article links only; no full article copying

## 15 configured sources

1. বাংলাদেশ প্রতিদিন (BD Pratidin)
2. প্রথম আলো (Prothom Alo)
3. কালবেলা (Kalbela)
4. ঢাকা পোস্ট (Dhaka Post)
5. এশিয়া পোস্ট (Asia Post)
6. জাগো নিউজ ২৪ (Jago News 24)
7. কালের কণ্ঠ (Kaler Kantho)
8. যুগান্তর (Jugantor)
9. সমকাল (Samakal)
10. বিডিনিউজ২৪ বাংলা (bdnews24 Bangla)
11. ডেইলি স্টার বাংলা (Daily Star Bangla)
12. TBS বাংলা (The Business Standard Bangla)
13. ইত্তেফাক (Ittefaq)
14. ঢাকা ট্রাইবিউন বাংলা (Dhaka Tribune Bangla)
15. বাংলানিউজ২৪ (Banglanews24)

RSS availability can change. The collector therefore has a homepage fallback for sources whose RSS endpoint fails or returns fewer than 10 usable items. See `docs/sources.md` for the verified feed list.

## GitHub setup

1. Create a new GitHub repository.
2. Upload all files from this project to the repository root.
3. Make sure the default branch is `main`.
4. Go to **Settings → Pages**.
5. Under **Build and deployment → Source**, choose **GitHub Actions**.
6. Open **Actions** and run `Update headlines and deploy` manually once.
7. The Pages URL will appear in the workflow deployment result.

GitHub Actions supports scheduled workflows at a minimum five-minute interval; this project runs every 10 minutes, but scheduled jobs can be delayed by GitHub under load. The dashboard itself also refreshes its JSON every 10 minutes.

## Local test

With Python installed:

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest -q
```

### Windows without Python

A PowerShell fallback builder fetches all 15 sources and regenerates `data/headlines.json`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build-data.ps1
```

Then serve the root folder with a local HTTP server (any static server works):

```powershell
python -m http.server 8000   # or use any static file server
```

Open:

http://localhost:8000/

## Important

RSS feeds and website structures are controlled by the publishers and may change. The collector tries each source's own RSS feed first, then a Bing News mirror, then direct page parsing — so a single broken feed never empties a portal.

Respect each publisher's terms, robots rules, rate limits, and applicable copyright requirements. This project stores headline metadata and links rather than reproducing article bodies.
