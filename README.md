# mailcraft-llm

Streamlit + langchain_openai のメール文章作成アプリです。

## セットアップ

### プロジェクト作成

```bash
mkdir mailcraft-llm
cd mailcraft-llm
```

### venv作成（Python3.11）

```bash
python3.11 -m venv .venv
```

### venv有効化

```bash
source .venv/bin/activate
```

### インストール

```bash
pip install -U pip
pip install -r requirements.txt
```

### .env 作成（必須）

`.env` が必須です。`mailcraft-llm/.env` に以下を記載してください。

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

.env には秘密情報が含まれるため、GitHubなどにコミットしないでください。

### 起動

```bash
streamlit run app.py
```

## 使い方

1. 入力欄を埋めて「生成する」を押します。
2. 出力された本文を確認し、必要なら「もっと丁寧に」「もっと短く」で再生成します。

## よくあるエラー

- **.venvが有効化されていない**
  - `which python` で `.venv` 配下になっているか確認してください。
    - 例: `/Users/yourname/Desktop/mailcraft-llm/.venv/bin/python`
- **OPENAI_API_KEY が読み込めない**
  - `.env` が `mailcraft-llm/.env` に存在するか確認してください。
  - `.env` の記載が `OPENAI_API_KEY=...` になっているか確認してください。