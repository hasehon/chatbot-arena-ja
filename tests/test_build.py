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
    monkeypatch.setattr(build_site, "HISTORY_PATH", str(data_dir / "rank_history.json"))
    monkeypatch.setattr(build_site, "OUTPUT_DIR", str(tmp_path / "docs"))

    build_site.build()

    output = (tmp_path / "docs" / "index.html").read_text(encoding="utf-8")
    assert "Test Model" in output
    assert "<script" in output
    # ビルド後に履歴ファイルが作られること
    assert (data_dir / "rank_history.json").exists()


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
    monkeypatch.setattr(build_site, "HISTORY_PATH", str(data_dir / "rank_history.json"))
    monkeypatch.setattr(build_site, "OUTPUT_DIR", str(tmp_path / "docs"))

    build_site.build()

    output = (tmp_path / "docs" / "index.html").read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in output


def test_update_history_first_run():
    ranks = {"text": {"GPT-5.2": 1}}
    history = build_site.update_history(None, "2026-07-08", ranks)
    assert history["baseline"] == {}
    assert history["latest_date"] == "2026-07-08"
    assert history["latest"] == ranks


def test_update_history_promotes_baseline_on_new_day():
    old = {
        "baseline_date": "2026-07-06",
        "baseline": {"text": {"GPT-5.2": 2}},
        "latest_date": "2026-07-07",
        "latest": {"text": {"GPT-5.2": 1}},
    }
    today_ranks = {"text": {"GPT-5.2": 3}}
    history = build_site.update_history(old, "2026-07-08", today_ranks)
    # 日付が変わったら「昨日の latest」が新しい比較基準(baseline)になる
    assert history["baseline_date"] == "2026-07-07"
    assert history["baseline"] == {"text": {"GPT-5.2": 1}}
    assert history["latest"] == today_ranks


def test_update_history_keeps_baseline_on_same_day_rerun():
    old = {
        "baseline_date": "2026-07-07",
        "baseline": {"text": {"GPT-5.2": 5}},
        "latest_date": "2026-07-08",
        "latest": {"text": {"GPT-5.2": 1}},
    }
    rerun_ranks = {"text": {"GPT-5.2": 2}}
    history = build_site.update_history(old, "2026-07-08", rerun_ranks)
    # 同じ日の再実行では baseline は動かない(前日比がリセットされない)
    assert history["baseline"] == {"text": {"GPT-5.2": 5}}
    assert history["latest"] == rerun_ranks


def _row(model, rank):
    return {"rank": rank, "model": model, "provider": "X", "score": 1000,
            "ci_text": "情報なし", "votes_text": "不明"}


def test_apply_rank_deltas_up_down_new():
    data = {"text": [_row("A", 1), _row("B", 2), _row("C", 3)]}
    baseline = {"text": {"A": 3, "B": 1}}
    build_site.apply_rank_deltas(data, baseline)
    assert data["text"][0]["delta"] == 2       # 3位 → 1位 = ▲2
    assert data["text"][1]["delta"] == -1      # 1位 → 2位 = ▼1
    assert data["text"][2]["is_new"] is True   # 前日データに無い = NEW


def test_apply_rank_deltas_without_baseline():
    data = {"text": [_row("A", 1)]}
    build_site.apply_rank_deltas(data, {})
    # 初回ビルドでは全モデルが NEW 扱いにならないこと
    assert data["text"][0]["delta"] is None
    assert data["text"][0]["is_new"] is False
