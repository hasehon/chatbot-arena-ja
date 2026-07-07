import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_site  # noqa: E402


def test_normalize_row_with_full_data():
    raw = {
        "rank": 1,
        "model": "GPT-5.2",
        "vendor": "OpenAI",
        "score": 1421,
        "ci": 8,
        "votes": 142300,
    }
    row = build_site.normalize_row(raw)
    assert row["rank"] == 1
    assert row["model"] == "GPT-5.2"
    assert row["provider"] == "OpenAI"
    assert row["score"] == 1421
    assert "程度" in row["ci_text"]
    assert row["votes_text"] == "142,300"


def test_normalize_row_with_missing_fields():
    raw = {"name": "謎のモデル"}
    row = build_site.normalize_row(raw)
    assert row["model"] == "謎のモデル"
    assert row["provider"] == "不明"
    assert row["ci_text"] == "情報なし"
    assert row["votes_text"] == "不明"


def test_normalize_row_with_garbage_types():
    raw = {"rank": "abc", "model": None, "score": "N/A"}
    row = build_site.normalize_row(raw)
    assert row["rank"] == 0
    assert row["score"] == 0


def test_build_creates_html(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    combined = {
        "text": [{"rank": 1, "model": "Test Model", "vendor": "Test Co", "score": 1000, "votes": 10}],
        "code": [],
        "vision": [],
        "text-to-image": [],
    }
    (data_dir / "combined.json").write_text(json.dumps(combined), encoding="utf-8")

    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "style.css").write_text("body{}", encoding="utf-8")
    (tmp_path / "assets" / "site.js").write_text("//ok", encoding="utf-8")

    monkeypatch.setattr(build_site, "BASE_DIR", str(tmp_path))
    monkeypatch.setattr(build_site, "DATA_PATH", str(data_dir / "combined.json"))
    monkeypatch.setattr(build_site, "OUTPUT_DIR", str(tmp_path / "docs"))

    build_site.build()

    output = (tmp_path / "docs" / "index.html").read_text(encoding="utf-8")
    assert "Test Model" in output
    assert "<script" in output


def test_build_escapes_malicious_model_name(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    combined = {
        "text": [{"rank": 1, "model": "<script>alert(1)</script>", "vendor": "Evil", "score": 1}],
        "code": [],
        "vision": [],
        "text-to-image": [],
    }
    (data_dir / "combined.json").write_text(json.dumps(combined), encoding="utf-8")

    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "style.css").write_text("body{}", encoding="utf-8")
    (tmp_path / "assets" / "site.js").write_text("//ok", encoding="utf-8")

    monkeypatch.setattr(build_site, "BASE_DIR", str(tmp_path))
    monkeypatch.setattr(build_site, "DATA_PATH", str(data_dir / "combined.json"))
    monkeypatch.setattr(build_site, "OUTPUT_DIR", str(tmp_path / "docs"))

    build_site.build()

    output = (tmp_path / "docs" / "index.html").read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in output
