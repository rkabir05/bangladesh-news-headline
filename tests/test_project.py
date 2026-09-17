import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from config import SOURCES, HEADLINES_PER_SOURCE, REFRESH_MINUTES  # noqa: E402

EXPECTED_NAMES = {
    "বাংলাদেশ প্রতিদিন", "প্রথম আলো", "কালবেলা", "ঢাকা পোস্ট", "এশিয়া পোস্ট",
    "জাগো নিউজ ২৪", "কালের কণ্ঠ", "যুগান্তর", "সমকাল", "বিডিনিউজ২৪ বাংলা",
    "ডেইলি স্টার বাংলা", "TBS বাংলা", "ইত্তেফাক", "ঢাকা ট্রাইবিউন বাংলা",
    "বাংলানিউজ২৪",
}


def test_source_count():
    assert len(SOURCES) == 15


def test_expected_source_names():
    names = {unicodedata.normalize("NFC", s["name"]) for s in SOURCES}
    expected = {unicodedata.normalize("NFC", n) for n in EXPECTED_NAMES}
    assert names == expected


def test_source_shape():
    for source in SOURCES:
        assert set(source) >= {"name", "site", "feeds"}
        assert source["site"].startswith("https://")
        assert isinstance(source["feeds"], list)
        assert isinstance(source.get("pages", []), list)
        assert isinstance(source.get("pattern", ""), str)


def test_config_values():
    assert HEADLINES_PER_SOURCE == 10
    assert REFRESH_MINUTES == 10


def test_headline_schema():
    path = ROOT / "data" / "headlines.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["refresh_minutes"] == 10
    assert len(payload["sources"]) == 15
    for source in payload["sources"]:
        assert {"source", "url", "count", "headlines", "status"} <= set(source)
        for item in source["headlines"]:
            assert item["title"]
            assert item["url"].startswith("http")
            assert "bing.com/news/apiclick" not in item["url"]  # redirects resolved
            # Thumbnails (optional) must be absolute URLs from enclosures/media tags.
            # Bing News thumbnails (www.bing.com/th?id=...) have no file extension,
            # so only the absolute-URL shape is asserted here.
            image = item.get("image", "")
            if image:
                assert image.startswith("http")
                assert " " not in image
                assert "bing.com/news/apiclick" not in image  # never a redirect wrap


def test_no_duplicate_source_names():
    names = [unicodedata.normalize("NFC", s["name"]) for s in SOURCES]
    assert len(names) == len(set(names))
