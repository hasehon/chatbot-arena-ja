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


def build():
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "j2"]),
    )
    template = env.get_template("index.html.j2")

    data = load_data()
    jst = timezone(timedelta(hours=9))
    updated_at = datetime.now(jst).strftime("%Y-%m-%d %H:%M")

    html = template.render(categories=CATEGORIES, data=data, updated_at=updated_at)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
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
