"""Configuration for the Bangladesh news headline collector.

The source list lives in scripts/sources.json (UTF-8) so that the Python
collector and the PowerShell fallback builder share one source of truth.
"""

import json
from pathlib import Path

_SOURCE_FILE = Path(__file__).resolve().parent / "sources.json"

with open(_SOURCE_FILE, encoding="utf-8") as _fh:
    SOURCES = json.load(_fh)

HEADLINES_PER_SOURCE = 10
MAX_FETCH_PER_SOURCE = 20
REQUEST_TIMEOUT = 20
REFRESH_MINUTES = 10

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 BangladeshNewsHeadlines/1.0"
)

# Link paths that are navigation/meta pages, not news articles.
SKIP_URL_PATTERNS = (
    "/tag", "/tags", "/topic", "/category", "/author", "/writer",
    "/video", "/videos", "/photo", "/gallery", "/epaper", "/archive",
    "/login", "/register", "/subscribe", "/contact", "/about",
    "/privacy", "/terms", "/jobs", "/advertisement", "/rss", "/feed",
)

# Keywords that mark navigation/boilerplate rather than a headline.
SKIP_TITLE_WORDS = (
    "সর্বশেষ", "আরও", "লগইন", "রেজিস্টার", "বিজ্ঞাপন", "ফেসবুক",
    "ইউটিউব", "instagram", "twitter", "menu", "একনজরে সব", "সব খবর",
)
