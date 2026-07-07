"""data/combined.json を読み込み、templates/index.html.j2 に流し込んで
docs/index.html (GitHub Pages公開用) を生成するスクリプト。

非公式APIのフィールド名は将来変わる可能性があるため、normalize_row() で
複数の候補名から値を拾い、無ければ既定値にフォールバックする。
"""

import json
import os
from datetime import datetime, timedelta, timezone

from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "combined.json")
HISTORY_PATH = os.path.join(BASE_DIR, "data", "rank_history.json")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs")

CATEGORIES = [
    {"id": "text", "label": "テキスト"},
    {"id": "code", "label": "コード"},
    {"id": "vision", "label": "画像理解"},
    {"id": "text-to-image", "label": "画像生成"},
]


def normalize_row(raw):
    def pick(*keys, default=None):
        for k in keys:
            if k in raw and raw[k] not in (None, ""):
                return raw[k]
        return default

    rank = pick("rank", "position", default=0)
    model = pick("model", "name", "model_name", default="不明なモデル")
    provider = pick("vendor", "provider", "organization", "org", default="不明")
    score = pick("score", "elo", "rating", default=0)
    ci = pick("ci", default=None)
    votes = pick("votes", "vote_count", "num_votes", default=None)

    if ci is not None:
        try:
            ci_text = f"±{abs(float(ci)):.0f}程度"
        except (TypeError, ValueError):
            ci_text = "情報なし"
    else:
        ci_text = "情報なし"

    try:
        votes_text = f"{int(votes):,}"
    except (TypeError, ValueError):
        votes_text = "不明"

    try:
        rank_val = int(rank)
    except (TypeError, ValueError):
        rank_val = 0

    try:
        score_val = float(score)
    except (TypeError, ValueError):
        score_val = 0

    return {
        "rank": rank_val,
        "model": str(model),
        "provider": str(provider),
        "score": score_val,
        "ci_text": ci_text,
        "votes_text": votes_text,
    }


def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    normalized = {}
    for cat in CATEGORIES:
        rows = raw.get(cat["id"], []) or []
        normalized[cat["id"]] = [normalize_row(r) for r in rows if isinstance(r, dict)]
    return normalized


def load_history():
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, encoding="utf-8") as f:
            return json.load(f)
    return None


def update_history(history, today, current_ranks):
    """前日比較用の履歴を更新する。

    baseline = 「前日(最後に日付が変わったとき)の順位」、latest = 「今日の順位」。
    同じ日に複数回ビルドしても baseline は動かないので、
    手動実行を繰り返しても前日比がゼロにリセットされない。
    """
    if history is None:
        return {
            "baseline_date": None,
            "baseline": {},
            "latest_date": today,
            "latest": current_ranks,
        }
    if history.get("latest_date") != today:
        return {
            "baseline_date": history.get("latest_date"),
            "baseline": history.get("latest") or {},
            "latest_date": today,
            "latest": current_ranks,
        }
    return {
        "baseline_date": history.get("baseline_date"),
        "baseline": history.get("baseline") or {},
        "latest_date": today,
        "latest": current_ranks,
    }


def apply_rank_deltas(data, baseline):
    """各行に前日比 delta(正=上昇)と is_new(新登場)を書き込む。

    baseline がまだ無いカテゴリ(初回ビルドなど)は全行 delta=None のままにし、
    全モデルが NEW 表示になるのを避ける。
    """
    for cat_id, rows in data.items():
        prev_ranks = baseline.get(cat_id) or {}
        for row in rows:
            prev = prev_ranks.get(row["model"])
            if not prev_ranks:
                row["delta"] = None
                row["is_new"] = False
            elif prev is None:
                row["delta"] = None
                row["is_new"] = True
            else:
                row["delta"] = int(prev) - row["rank"]
                row["is_new"] = False


def build():
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "j2"]),
    )
    template = env.get_template("index.html.j2")

    data = load_data()
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    updated_at = now.strftime("%Y-%m-%d %H:%M")

    current_ranks = {
        cat_id: {row["model"]: row["rank"] for row in rows}
        for cat_id, rows in data.items()
    }
    history = update_history(load_history(), now.strftime("%Y-%m-%d"), current_ranks)
    apply_rank_deltas(data, history["baseline"])

    html = template.render(categories=CATEGORIES, data=data, updated_at=updated_at)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    for name in ("style.css", "site.js"):
        src = os.path.join(BASE_DIR, "assets", name)
        with open(src, encoding="utf-8") as f:
            content = f.read()
        with open(os.path.join(OUTPUT_DIR, name), "w", encoding="utf-8") as f:
            f.write(content)


if __name__ == "__main__":
    build()
