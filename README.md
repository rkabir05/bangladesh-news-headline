# Bangladesh News Headlines — 15 Portals

A GitHub-ready Bootstrap 5.3 news-headline dashboard.

## What it does

- 15 Bangladesh news portals
- Minimum target: 10 headlines per portal
- Python collector
- RSS-first collection with homepage fallback
- GitHub Actions runs every 5 minutes
- GitHub Pages deployment
- Responsive Bootstrap 5.3 UI
- Original article links only; no full article copying

## 15 configured sources

1. Prothom Alo
2. Bangladesh Pratidin
3. Kaler Kantho
4. Jugantor
5. Ittefaq
6. Samakal
7. Dhaka Post
8. Jago News 24
9. Bangla Tribune
10. RisingBD
11. bdnews24
12. BanglaNews24
13. BD24Live
14. Daily Naya Diganta
15. Manab Zamin

RSS availability can change. The collector therefore has a homepage fallback for sources whose RSS endpoint fails or returns fewer than 10 usable items.

## GitHub setup

1. Create a new GitHub repository.
2. Upload all files from this project to the repository root.
3. Make sure the default branch is `main`.
4. Go to **Settings → Pages**.
5. Under **Build and deployment → Source**, choose **GitHub Actions**.
6. Open **Actions** and run `Update headlines and deploy` manually once.
7. The Pages URL will appear in the workflow deployment result.

GitHub Actions supports scheduled workflows at a minimum five-minute interval, but scheduled jobs can be delayed by GitHub under load. The dashboard itself also refreshes its JSON every five minutes.

## Local test

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd scripts
python fetch_headlines.py
cd ..
pytest -q
```

Then serve the root folder with a local HTTP server:

```bash
py -m http.server 8000
```

Open:

http://localhost:8000/

## Important

RSS feeds and website structures are controlled by the publishers and may change. Respect each publisher's terms, robots rules, rate limits, and applicable copyright requirements. This project stores headline metadata and links rather than reproducing article bodies.
