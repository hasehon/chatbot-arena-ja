"""arena-ai-leaderboards の非公式APIからランキングデータを取得し、
data/combined.json にまとめて保存するスクリプト。

取得に失敗したカテゴリがあっても処理を止めず、前回成功時のキャッシュ
(data/<category>.json)で代替する。キャッシュも無い場合は空リストにする。
失敗があった場合は data/failures.txt に記録し、GitHub Actions 側で
Issue の自動作成に使う。
"""

import json
import os
import urllib.error
import urllib.request

CATEGORIES = ["text", "code", "vision", "text-to-image"]
API_BASE = "https://api.wulong.dev/arena-ai-leaderboards/v1/leaderboard"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def fetch_category(name):
    url = f"{API_BASE}?name={name}"
    req = urllib.request.Request(url, headers={"User-Agent": "chatbot-arena-ja/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.load(resp)
    # レスポンスは {"meta": {...}, "models": [...]} の形。将来の変更に備え、
    # 素の配列で返ってきた場合もそのまま扱えるようにしておく。
    if isinstance(payload, dict):
        models = payload.get("models", [])
    else:
        models = payload
    # HTTP 200 でも中身が空(models キー欠落・空リスト)なら失敗として扱う。
    # ここで例外にしないと、正常だった前回キャッシュを空データで上書きしてしまう。
    if not models:
        raise ValueError(f"empty response for category '{name}'")
    return models


def load_cache(name):
    path = os.path.join(DATA_DIR, f"{name}.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def save_cache(name, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    result = {}
    failures = []

    for cat in CATEGORIES:
        try:
            data = fetch_category(cat)
            save_cache(cat, data)
            result[cat] = data
        except Exception as exc:  # noqa: BLE001 - ネットワーク/JSON/スキーマの
            # あらゆる失敗を「サイトを壊さず前回データを使う」の一言に集約するため
            cached = load_cache(cat)
            result[cat] = cached if cached is not None else []
            failures.append(f"{cat}: {exc}")

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "combined.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    failures_path = os.path.join(DATA_DIR, "failures.txt")
    if failures:
        with open(failures_path, "w", encoding="utf-8") as f:
            f.write("\n".join(failures))
        print("WARNING: 一部カテゴリの取得に失敗し、キャッシュ(または空)を使用しました:")
        for line in failures:
            print(" -", line)
    elif os.path.exists(failures_path):
        os.remove(failures_path)


if __name__ == "__main__":
    main()
