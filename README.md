# 🌿 サジー新商品モニター

サジー（Sea Buckthorn）の新商品・新情報を自動でSlackに通知するツールです。

## できること

- 📰 Googleニュースで「サジー 新商品」などを毎日自動検索
- 🆕 サジーブランドの公式サイト更新を検知
- 💬 新情報があればSlackに自動通知
- ⏰ 毎朝9時（日本時間）に自動実行

## セットアップ手順

### 1. このリポジトリをGitHubにアップロード

```
GitHubで新しいリポジトリを作成
→ このフォルダの中身をアップロード
```

### 2. Slack Webhook URLを取得

1. [Slack API](https://api.slack.com/apps) にアクセス
2. 「Create New App」→「From scratch」
3. 「Incoming Webhooks」を有効化
4. 「Add New Webhook to Workspace」でチャンネルを選択
5. Webhook URLをコピー

### 3. GitHub Secretsに登録

1. GitHubのリポジトリページへ
2. `Settings` → `Secrets and variables` → `Actions`
3. `New repository secret` をクリック
4. Name: `SLACK_WEBHOOK_URL`
5. Value: コピーしたWebhook URLを貼り付け

### 4. 完了！

毎朝9時に自動実行されます。
手動で試したい場合は `Actions` タブ → `サジー新商品モニター` → `Run workflow`

## 監視対象のカスタマイズ

`monitor.py` の以下の部分を編集できます：

```python
# 検索キーワード
SEARCH_KEYWORDS = [
    "サジー 新商品",
    "サジー 新発売",
    ...
]

# 監視するサイト
MONITOR_URLS = [
    {
        "name": "豊潤サジー（フィネス）",
        "url": "https://finess.jp/products/",
        ...
    },
]
```

## ファイル構成

```
saji-monitor/
├── monitor.py                    # メインスクリプト
├── .github/
│   └── workflows/
│       └── monitor.yml           # GitHub Actions設定
└── README.md                     # このファイル
```
