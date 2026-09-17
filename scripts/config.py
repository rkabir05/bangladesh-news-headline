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

# Path segments that mark NON-Bangladesh news (sports/entertainment/lifestyle
# etc.). Any link whose URL path contains one of these segments is excluded so
# the site only ever shows Bangladesh-national headlines. Path SEGMENTS are
# matched exactly, so "/international/..." matches while "...international"
# inside another word does not.
NON_LOCAL_SECTION_SEGMENTS = (
    "international", "world", "bishwo", "bidesh", "foreign", "global",
    "south-asia", "asia", "americas", "europe", "africa", "middle-east",
    "entertainment", "binodon", "lifestyle", "life-style", "jibonjapon",
    "jibon_japon", "jibon-jaapon", "life", "showbiz", "music", "fashion",
    "technology", "tech", "probash", "probashi", "diaspora", "sport",
    "sports", "kheladhula", "khela", "cricket", "football", "game",
    "games", "gaming", "esports", "health", "shastho", "religion",
    "islam-life", "dharma", "education", "shikkha", "campus", "job",
    "jobs", "career", "business", "economy", "orthoniti", "trade",
    "corporate", "e-paper", "epaper", "opinion", "opinions", "editorial",
    "editorials", "uproktosh", "khelafat", "education-job", "edu-job",
    "how-to", "howto", "tips", "astrology", "bhobishyot", "recipe",
    "cooking", "horoscope", "religion-life", "glitz", "kidz", "showtime",
)

# Strong sports/entertainment markers. Applied ONLY to Google-mirror items,
# whose real URL section is hidden behind news.google.com redirect links, so
# non-domestic stories cannot sneak in through the fallback.
MIRROR_TITLE_EXCLUDES = (
    "ক্রিকেট", "ফুটবল", "বলিউড", "টলিউড", "ঢালিউড", "সিনেমা", "নাটক",
    "বিনোদন", "খেলোয়াড়", "টুর্নামেন্ট", "অভিনয়", "সঙ্গীত", "ম্যাচ",
    "উইকেট", "বিশ্বকাপ",
)

# Keywords that mark navigation/boilerplate rather than a headline.
SKIP_TITLE_WORDS = (
    "সর্বশেষ", "আরও", "লগইন", "রেজিস্টার", "বিজ্ঞাপন", "ফেসবুক",
    "ইউটিউব", "instagram", "twitter", "menu", "একনজরে সব", "সব খবর",
)
