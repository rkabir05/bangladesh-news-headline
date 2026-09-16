import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_source_count():
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from config import SOURCES
    assert len(SOURCES) == 15

def test_headline_schema():
    path = ROOT / "data" / "headlines.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert len(payload["sources"]) == 15
    for source in payload["sources"]:
        assert "source" in source
        assert "headlines" in source
        for item in source["headlines"]:
            assert "title" in item
            assert "url" in item
