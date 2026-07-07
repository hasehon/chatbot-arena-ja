import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import fetch_data  # noqa: E402


def test_fetch_falls_back_to_cache_on_error(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_data, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(fetch_data, "CATEGORIES", ["text"])

    cached = [{"rank": 1, "model": "Cached Model"}]
    (tmp_path / "text.json").write_text(json.dumps(cached), encoding="utf-8")

    def boom(_name):
        raise RuntimeError("network down")

    monkeypatch.setattr(fetch_data, "fetch_category", boom)

    fetch_data.main()

    combined = json.loads((tmp_path / "combined.json").read_text(encoding="utf-8"))
    assert combined["text"] == cached
    assert (tmp_path / "failures.txt").exists()


def test_fetch_falls_back_to_empty_list_without_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_data, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(fetch_data, "CATEGORIES", ["code"])

    def boom(_name):
        raise RuntimeError("network down")

    monkeypatch.setattr(fetch_data, "fetch_category", boom)

    fetch_data.main()

    combined = json.loads((tmp_path / "combined.json").read_text(encoding="utf-8"))
    assert combined["code"] == []


def test_fetch_success_clears_previous_failures_file(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_data, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(fetch_data, "CATEGORIES", ["text"])
    (tmp_path / "failures.txt").write_text("text: old failure", encoding="utf-8")

    monkeypatch.setattr(fetch_data, "fetch_category", lambda _name: [{"rank": 1, "model": "OK"}])

    fetch_data.main()

    assert not (tmp_path / "failures.txt").exists()
