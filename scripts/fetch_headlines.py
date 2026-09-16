from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests
import feedparser
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (  # noqa: E402
    HEADLINES_PER_SOURCE,
    MAX_FETCH_PER_SOURCE,
    REQUEST_TIMEOUT,
    REFRESH_MINUTES,
    USER_AGENT,
    SKIP_URL_PATTERNS,
    SKIP_TITLE_WORDS,
)

# Clean browser UA for sites that reject the project-suffixed UA.
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "headlines.json"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": BROWSER_UA, "Accept-Language": "bn,en;q=0.8"})


def clean_text(value: str) -> str:
    value = BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", value).strip()


def is_probable_article(url: str, title: str, pattern: str = "") -> bool:
    """Heuristic filter: news article links, not nav/category/meta pages."""
    path = urlparse(url).path.lower()
    if not path or path == "/":
        return False
    if any(pattern in path for pattern in SKIP_URL_PATTERNS):
        return False
    low = title.lower()
    if any(word in low for word in SKIP_TITLE_WORDS):
        return False
    if pattern and not re.search(pattern, url, re.IGNORECASE):
        return False
    return True


def resolve_bing_redirect(url: str) -> str:
    """Bing News RSS wraps links; extract the encoded target URL."""
    if "bing.com" not in urlparse(url).netloc:
        return url
    # Unescape HTML entities first (&amp; -> &) so query parsing sees all params.
    clean = url.replace("&amp;", "&")
    try:
        query = parse_qs(urlparse(clean).query)
        target = (query.get("url") or [""])[0]
        return unquote(target) if target else clean
    except Exception:
        return clean


def load_sources():
    """Load sources from sources.json (single source of truth for all builders)."""
    path = Path(__file__).resolve().parent / "sources.json"
    return json.loads(path.read_text(encoding="utf-8"))


def http_get(url: str) -> bytes:
    """Fetch a URL via curl, falling back to requests.

    Several publishers fingerprint TLS handshakes and block non-browser clients
    (Python requests gets 403 while the same URL loads through curl), so curl is
    the primary transport on both GitHub runners and local machines.
    """
    try:
        proc = subprocess.run(
            [
                "curl", "-sS", "-f", "-L",
                "--retry", "2", "--retry-delay", "2", "--max-time", "45",
                "-A", BROWSER_UA,
                "-H", "Accept: text/html,application/xhtml+xml,application/xml,application/rss+xml,*/*;q=0.8",
                "-H", "Accept-Language: bn,en;q=0.8",
                url,
            ],
            capture_output=True,
            timeout=60,
        )
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout
        last_error = f"curl exit {proc.returncode}: {proc.stderr.decode(errors='replace')[:200]}"
    except FileNotFoundError:
        last_error = "curl not available"
    except subprocess.TimeoutExpired:
        last_error = "curl timeout"

    try:
        response = SESSION.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.content
    except Exception as exc:  # noqa: BLE001 - report both transports
        raise RuntimeError(f"{last_error} | requests fallback: {exc}") from exc


def parse_feed(site_url: str, feed_url: str, pattern: str = "") -> list[dict]:
    feed = feedparser.parse(http_get(feed_url))
    items: list[dict] = []

    for entry in feed.entries[: MAX_FETCH_PER_SOURCE * 3]:
        title = clean_text(entry.get("title", ""))
        link = resolve_bing_redirect(entry.get("link", ""))
        if not title or not link:
            continue
        published = entry.get("published") or entry.get("updated") or ""
        items.append({
            "title": title,
            "url": urljoin(site_url, link),
            "time": clean_text(published),
        })

    return dedupe([i for i in items if is_probable_article(i["url"], i["title"], pattern)])


def parse_homepage(site_url: str, pattern: str = "", extra_pages: list[str] | None = None) -> list[dict]:
    pages = [site_url] + [p.replace("TODAY", datetime.now(timezone.utc).strftime("%Y-%m-%d")) for p in (extra_pages or [])]
    candidates: list[dict] = []

    for page_url in pages:
        try:
            content = http_get(page_url)
        except Exception as exc:  # noqa: BLE001
            print(f"    page fail {page_url}: {exc}")
            continue

        soup = BeautifulSoup(content, "html.parser")
        for tag in soup.select("h1 a, h2 a, h3 a, h4 a, article a"):
            title = clean_text(tag.get_text(" ", strip=True))
            href = tag.get("href", "")
            if not title or not href:
                continue
            if len(title) < 15 or len(title) > 220:
                continue
            candidates.append({
                "title": title,
                "url": urljoin(site_url, href),
                "time": "",
            })

    filtered = [
        c for c in candidates if is_probable_article(c["url"], c["title"], pattern)
    ]
    return dedupe(filtered)[:MAX_FETCH_PER_SOURCE]


def dedupe(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for item in items:
        key = item["url"] or item["title"]
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def merge_items(base: list[dict], extra: list[dict]) -> list[dict]:
    """Merge two headline lists keeping order and deduping by URL."""
    return dedupe(list(base) + list(extra))


def collect_source(source: dict) -> tuple[list[dict], str | None]:
    """Try each configured RSS endpoint (merged), then extra pages/homepage."""
    errors: list[str] = []
    pattern = source.get("pattern", "")
    merged: list[dict] = []

    for feed_url in source.get("feeds", []):
        try:
            items = parse_feed(source["site"], feed_url, pattern)
            merged = merge_items(merged, items)
            if len(merged) >= HEADLINES_PER_SOURCE:
                return merged[:HEADLINES_PER_SOURCE], None
        except Exception as exc:  # noqa: BLE001 - collect and report
            errors.append(f"{feed_url}: {type(exc).__name__}: {exc}")

        time.sleep(1)  # politeness delay between feed attempts

    try:
        items = parse_homepage(source["site"], pattern, source.get("pages", []))
        merged = merge_items(merged, items)
        if len(merged) >= HEADLINES_PER_SOURCE:
            return merged[:HEADLINES_PER_SOURCE], None
        errors.append(f"homepage: total {len(merged)} usable items")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"homepage: {type(exc).__name__}: {exc}")

    error = " | ".join(errors) if errors else None
    return merged, error


def collect_source_with_retry(source: dict) -> tuple[list[dict], str | None]:
    """Single attempt; collect_source already aggregates feeds + pages."""
    return collect_source(source)


def main() -> None:
    results = []
    failed = []

    for source in load_sources():
        items, error = collect_source_with_retry(source)

        status = "ok" if len(items) >= HEADLINES_PER_SOURCE else "warning"
        entry = {
            "source": source["name"],
            "url": source["site"],
            "count": len(items),
            "headlines": items,
            "status": status,
        }
        if error:
            entry["error"] = error
            failed.append(source["name"])

        results.append(entry)
        print(f"{source['name']}: {len(items)} headlines")

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "refresh_minutes": REFRESH_MINUTES,
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

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {OUT}")
    print(json.dumps(payload["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
