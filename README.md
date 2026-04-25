# search-weather-spot

地点名と過去の日付を入力すると気温・湿度を返す天気チャットアプリ。  
Ollama (ローカルLLM) と Open-Meteo API (無料・APIキー不要) を組み合わせ、CLIとStreamlit GUIの両方で動作する。

---

## 目次

- [機能](#機能)
- [必要環境](#必要環境)
- [ディレクトリ構成](#ディレクトリ構成)
- [環境変数](#環境変数)
- [コマンド一覧](#コマンド一覧)
- [セットアップ](#セットアップ)
- [実行方法](#実行方法)
- [設計思想](#設計思想)
- [外部API](#外部api)

---

## 機能

- 自然言語で地点名と日付を入力できる (例: 「東京の2023年7月15日の天気は？」)
- 平均・最低・最高気温 (°C) と平均湿度 (%) を返す
- 会話履歴を保持し、複数回のやり取りが可能
- 地点未発見・日付範囲外の場合はクラッシュせずエラー内容を説明する
- 使用モデルを環境変数 `OLLAMA_MODEL` で変更できる

---

## 必要環境

| ツール | バージョン | 用途 |
|--------|-----------|------|
| Python | 3.11+ | ランタイム |
| uv | 最新版 | パッケージ管理・仮想環境 |
| Ollama | 最新版 | ローカルLLMサーバー |
| llama3.1 | - | デフォルトモデル (ツール呼び出し対応が必要) |

---

## ディレクトリ構成

```
search-weather-spot/
├── main.py          # CLIエントリーポイント、チャットループ
├── app.py           # Streamlit GUIエントリーポイント
├── config.py        # 共有定数 (MODEL, TOOL_FUNCTIONS, SYSTEM_PROMPT)
├── tools.py         # ツール実装 (ジオコーディング・天気取得)
├── tool_schema.py   # Ollama用ツールJSONスキーマ定義
├── tests/
│   ├── test_tools.py       # tools.py ユニットテスト (14件)
│   ├── test_main.py        # main.py ユニットテスト (20件)
│   ├── test_config.py      # config.py ユニットテスト (8件)
│   └── test_tool_schema.py # tool_schema.py ユニットテスト (10件)
├── pyproject.toml   # uvプロジェクト設定・依存関係
├── requirements.txt # パッケージ一覧 (参照用)
└── CLAUDE.md        # AI向け作業指示
```

### 各ファイルの役割

**`config.py`**  
`main.py` と `app.py` で共有する定数 (`MODEL`, `TOOL_FUNCTIONS`, `SYSTEM_PROMPT`) をまとめたモジュール。

**`tools.py`**  
Open-Meteo APIを呼び出す2つのツール関数を実装している。
- `get_coordinates(place)` - 地点名を緯度・経度に変換する
- `get_historical_weather(latitude, longitude, date)` - 過去の気象データを取得し日次集計する

エラーは例外を送出せず `{"error": "..."}` の辞書を返す。LLMがエラー内容をユーザーに説明する設計。

**`tool_schema.py`**  
Ollamaの `chat()` に渡すツールJSONスキーマを定義している。関数名・説明・引数の型をLLMに伝えることで、LLMが自律的にどのツールをどの順番で呼ぶかを判断する。

**`main.py`**  
標準入出力を使うCLIループ。起動時に `ollama.list()` でモデルの存在確認を行う。会話履歴をリストで管理し、毎回の `ollama.chat()` に全履歴を渡す。

**`app.py`**  
Streamlit GUIループ。`st.session_state` で会話履歴を管理する。ツール実行中は `st.status` で進捗をリアルタイム表示する。

---

<!-- AUTO-GENERATED from config.py -->
## 環境変数

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|-----------|------|
| `OLLAMA_MODEL` | No | `llama3.1` | 使用するOllamaモデル名。ツール呼び出し対応モデルを指定すること。 |

<!-- END AUTO-GENERATED -->

---

<!-- AUTO-GENERATED from pyproject.toml -->
## コマンド一覧

| コマンド | 説明 |
|---------|------|
| `uv sync` | 依存パッケージをインストール |
| `uv run python main.py` | CLIチャットを起動 |
| `uv run streamlit run app.py` | Streamlit GUIを起動 |
| `uv run pytest tests/` | テストを実行 |
| `uv run pytest tests/ --cov=tools --cov=config --cov=main --cov=tool_schema --cov-report=term-missing` | カバレッジ付きでテストを実行 |

<!-- END AUTO-GENERATED -->

---

## セットアップ

```bash
# 1. Ollamaをインストール (https://ollama.com)
ollama pull llama3.1

# 2. リポジトリをクローン
git clone <repo-url>
cd search-weather-spot

# 3. uv で依存パッケージをインストール
uv sync
```

---

## 実行方法

### Ollamaサーバーを起動 (別ターミナル)

```bash
ollama serve
```

### CLI版

```bash
uv run python main.py
```

```
天気チャット (モデル: llama3.1)
終了するには 'quit' または 'exit' と入力してください。
--------------------------------------------------
あなた: 東京の2023年7月15日の天気は？
アシスタント: 2023年7月15日の東京の天気は...
```

### Streamlit GUI版

```bash
uv run streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動的に開く。

### モデルを変更する

```bash
OLLAMA_MODEL=qwen2.5 uv run python main.py
OLLAMA_MODEL=gemma2:2b uv run streamlit run app.py
```

---

## 設計思想

### LLMをオーケストレーターとして使う

日付のパースや地点名の解釈はLLMに任せ、ツール側はシンプルな入出力に徹する。ツールに渡す日付はYYYY-MM-DD形式のみとし、自然言語の変換はLLMが行う。これにより外部パーサーライブラリが不要になり、依存が `ollama` と `requests` だけで済む。

### ツール呼び出しループ

`ollama.chat()` のレスポンスに `tool_calls` が含まれる間、ツールを実行して結果をメッセージ履歴に追加し、再度 `ollama.chat()` を呼ぶループを維持する。このパターンで複数ツールの連鎖実行 (座標取得 → 天気取得) を実現している。

```
ユーザー入力
  → ollama.chat() [tool_calls あり]
  → get_coordinates() 実行
  → ollama.chat() [tool_calls あり]
  → get_historical_weather() 実行
  → ollama.chat() [最終回答]
```

### エラーを例外ではなくデータとして扱う

ツール関数はAPIエラーや地点未発見を例外でなく `{"error": "説明文"}` として返す。LLMがエラー辞書を受け取り、ユーザーへの説明文を生成する。アプリ側のエラーハンドリングをシンプルに保ちつつ、ユーザーには自然な日本語でエラーが伝わる。

### 会話履歴の管理

ツール呼び出しの中間メッセージ (アシスタントのtool_callsメッセージ・ツール結果) は一時的なリストで管理し、永続的な会話履歴には最終的なユーザー発話とアシスタント回答のみを保存する。これにより履歴が肥大化しない。

---

## 外部API

### ジオコーディング API

```
GET https://geocoding-api.open-meteo.com/v1/search
    ?name=Tokyo&count=1&language=ja
```

### 過去天気 API

```
GET https://archive-api.open-meteo.com/v1/archive
    ?latitude=35.68&longitude=139.76
    &start_date=2023-07-15&end_date=2023-07-15
    &hourly=temperature_2m,relative_humidity_2m
    &timezone=auto
```

取得可能期間: 1940-01-01 から現在の約5日前まで。
