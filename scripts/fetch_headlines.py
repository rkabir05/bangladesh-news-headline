from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
import feedparser
from bs4 import BeautifulSoup

from config import (
    SOURCES,
    HEADLINES_PER_SOURCE,
    MAX_FETCH_PER_SOURCE,
    REQUEST_TIMEOUT,
    USER_AGENT,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "headlines.json"


def clean_text(value: str) -> str:
    value = BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", value).strip()


def parse_feed(source_name: str, site_url: str, feed_url: str):
    if not feed_url:
        return []

    response = requests.get(
        feed_url,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()

    feed = feedparser.parse(response.content)
    items = []

    for entry in feed.entries[:MAX_FETCH_PER_SOURCE]:
        title = clean_text(entry.get("title", ""))
        link = entry.get("link", "")
        if not title or not link:
            continue

        published = (
            entry.get("published")
            or entry.get("updated")
            or entry.get("created")
            or ""
        )

        items.append({
            "title": title,
            "url": urljoin(site_url, link),
            "time": clean_text(published),
        })

    return dedupe(items)


def parse_homepage(source_name: str, site_url: str):
    response = requests.get(
        site_url,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    candidates = []

    for tag in soup.select("h1 a, h2 a, h3 a, h4 a, article a"):
        title = clean_text(tag.get_text(" ", strip=True))
        href = tag.get("href", "")
        if not title or not href:
            continue
        if len(title) < 15 or len(title) > 220:
            continue

        low = title.lower()
        bad = (
            "সর্বশেষ", "আরও", "লগইন", "রেজিস্টার", "বিজ্ঞাপন",
            "ফেসবুক", "ইউটিউব", "instagram", "twitter", "menu",
        )
        if any(x in low for x in bad):
            continue

        candidates.append({
            "title": title,
            "url": urljoin(site_url, href),
            "time": "",
        })

    return dedupe(candidates)[:MAX_FETCH_PER_SOURCE]


def dedupe(items):
    seen = set()
    result = []
    for item in items:
        key = item["url"] or item["title"]
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def collect_source(name, site_url, feed_url):
    errors = []

    if feed_url:
        try:
            items = parse_feed(name, site_url, feed_url)
            if len(items) >= HEADLINES_PER_SOURCE:
                return items[:HEADLINES_PER_SOURCE], None
            errors.append(f"RSS returned only {len(items)} usable items")
        except Exception as exc:
            errors.append(f"RSS: {type(exc).__name__}: {exc}")

    try:
        items = parse_homepage(name, site_url)
        if len(items) >= HEADLINES_PER_SOURCE:
            return items[:HEADLINES_PER_SOURCE], None
        errors.append(f"Homepage returned only {len(items)} usable items")
    except Exception as exc:
        errors.append(f"Homepage: {type(exc).__name__}: {exc}")

    return [], " | ".join(errors)


def main():
    results = []
    failed = []

    for name, site_url, feed_url in SOURCES:
        items, error = collect_source(name, site_url, feed_url)

        source = {
            "source": name,
            "url": site_url,
            "count": len(items),
            "headlines": items,
            "status": "ok" if len(items) >= HEADLINES_PER_SOURCE else "warning",
        }

        if error:
            source["error"] = error
            failed.append(name)

        results.append(source)
        print(f"{name}: {len(items)} headlines")

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "refresh_minutes": 5,
        "minimum_headlines_per_source": HEADLINES_PER_SOURCE,
        "sources": results,
        "summary": {
            "sources": len(results),
            "sources_with_10_plus": sum(
                1 for item in results if item["count"] >= HEADLINES_PER_SOURCE
            ),
            "total_headlines": sum(item["count"] for item in results),
            "warnings": failed,
        },
    }

    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote {OUT}")
    print(json.dumps(payload["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
