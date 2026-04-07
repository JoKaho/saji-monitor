import requests
import json
import os
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup

# ============================================================
# 設定
# ============================================================
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

SEARCH_KEYWORDS = [
    "サジー 新商品",
    "サジー 新発売",
    "シーバックソーン 新商品",
    "sea buckthorn 新商品",
]

MONITOR_URLS = [
    {
        "name": "豊潤サジー（フィネス）",
        "url": "https://finess.jp/products/",
        "selector": ".product-item",
    },
    {
        "name": "GOLDEN SAJI（ファビウス）",
        "url": "https://fabius.jp/collections/saji",
        "selector": ".product-card",
    },
]

STATE_FILE = "state.json"


# ============================================================
# 状態管理（前回との差分を検知）
# ============================================================
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# ============================================================
# Googleニュース検索
# ============================================================
def search_google_news(keyword):
    """GoogleニュースRSSフィードからサジー新商品ニュースを取得"""
    import xml.etree.ElementTree as ET

    encoded = requests.utils.quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=ja&gl=JP&ceid=JP:ja"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = []
        for item in root.findall(".//item")[:5]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            items.append({"title": title, "link": link, "date": pub_date})
        return items
    except Exception as e:
        print(f"[ERROR] Googleニュース取得失敗 ({keyword}): {e}")
        return []


# ============================================================
# サイト監視
# ============================================================
def check_site(site_info):
    """指定サイトのコンテンツハッシュを取得して変化を検知"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; SajiMonitor/1.0)"}
        resp = requests.get(site_info["url"], headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        elements = soup.select(site_info["selector"])
        content = " ".join([e.get_text(strip=True) for e in elements])
        return get_hash(content), content[:500]
    except Exception as e:
        print(f"[ERROR] サイト監視失敗 ({site_info['name']}): {e}")
        return None, None


# ============================================================
# Slack通知
# ============================================================
def send_slack(message):
    if not SLACK_WEBHOOK_URL:
        print("[INFO] SLACK_WEBHOOK_URL が未設定のためコンソール出力します")
        print(message)
        return

    payload = {"text": message}
    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
        print("[INFO] Slack通知送信完了")
    except Exception as e:
        print(f"[ERROR] Slack通知失敗: {e}")


# ============================================================
# メイン処理
# ============================================================
def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] サジー監視スタート")
    state = load_state()
    updates = []

    # 1) Googleニュース検索
    print("--- Googleニュース検索 ---")
    seen_links = set(state.get("seen_news_links", []))
    new_links = []

    for keyword in SEARCH_KEYWORDS:
        articles = search_google_news(keyword)
        for article in articles:
            link = article["link"]
            if link and link not in seen_links:
                seen_links.add(link)
                new_links.append(link)
                updates.append(
                    f"📰 *新着ニュース*\n"
                    f"*{article['title']}*\n"
                    f"🔗 {link}\n"
                    f"📅 {article['date']}"
                )
                print(f"  新着: {article['title']}")

    state["seen_news_links"] = list(seen_links)

    # 2) サイト変化監視
    print("--- サイト変化監視 ---")
    site_states = state.get("site_hashes", {})

    for site in MONITOR_URLS:
        current_hash, preview = check_site(site)
        if current_hash is None:
            continue
        prev_hash = site_states.get(site["name"])
        if prev_hash and prev_hash != current_hash:
            updates.append(
                f"🆕 *サイト更新検知*\n"
                f"*{site['name']}* のページが更新されました！\n"
                f"🔗 {site['url']}"
            )
            print(f"  更新検知: {site['name']}")
        site_states[site["name"]] = current_hash

    state["site_hashes"] = site_states
    save_state(state)

    # 3) Slack通知
    if updates:
        header = f"🌿 *サジー新商品・新情報アラート* ({datetime.now().strftime('%Y/%m/%d')})\n\n"
        message = header + "\n\n---\n\n".join(updates)
        send_slack(message)
    else:
        print("[INFO] 新しい情報はありませんでした")

    print("監視完了")


if __name__ == "__main__":
    main()
