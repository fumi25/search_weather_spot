# CLAUDE.md

## 作業方針
- コードを書く前に既存ファイルを読む。変更がない限り再読しない。
- 推論は丁寧に、出力は簡潔に。
- 100KB超のファイルは必要な場合を除きスキップする。
- 冒頭の褒め言葉や末尾の締め言葉は不要。
- 絵文字・ダッシュ記号は使わない。
- API、バージョン、フラグ、コミットSHA、パッケージ名を推測しない。コードまたはドキュメントを読んで確認してから断言する。

## プロジェクト概要

Ollamaをローカルで動かし、地点名と過去の日付を入力すると気温・湿度を返すCLIチャットアプリ。

## 技術スタック

- 言語: Python 3.11+
- LLM: Ollama (ローカル) / `ollama` Python SDK
- 天気データ: Open-Meteo Historical Weather API (APIキー不要)
- ジオコーディング: Open-Meteo Geocoding API (APIキー不要)
- UI: CLIチャットループ (stdin/stdout)

## アーキテクチャ

```
ユーザー入力 (地点名 + 日付)
  -> Ollama LLM (ツール呼び出し)
  -> ツール: get_coordinates(place) -> 緯度/経度
  -> ツール: get_historical_weather(lat, lon, date) -> 気温・湿度
  -> LLM が自然な日本語で回答を整形して返す
```

## 外部API

### ジオコーディング
- エンドポイント: https://geocoding-api.open-meteo.com/v1/search
- パラメータ: name (地点名), count=1, language=ja
- 認証不要

### 過去天気
- エンドポイント: https://archive-api.open-meteo.com/v1/archive
- パラメータ: latitude, longitude, start_date, end_date (YYYY-MM-DD), hourly=temperature_2m,relative_humidity_2m, timezone=auto
- 認証不要
- 取得可能期間: 1940-01-01 から今日の約5日前まで

## ツール定義

Ollamaのツール呼び出し用に2つのツールを登録する。

1. `get_coordinates(place: str) -> dict`
   - 地点名を緯度・経度に変換する
   - 戻り値: {latitude, longitude, name, country}

2. `get_historical_weather(latitude: float, longitude: float, date: str) -> dict`
   - date形式: YYYY-MM-DD
   - 戻り値: 日平均・最低・最高気温 (摂氏) と平均湿度 (%)

## ファイル構成

```
weather-chat/
  main.py          # エントリーポイント、チャットループ
  tools.py         # ツール実装 (ジオコーディング + 天気取得)
  tool_schema.py   # Ollama用ツールJSONスキーマ定義
  requirements.txt
  CLAUDE.md
```

## 実装上の注意

- HTTPクライアントは `requests` を使う。`httpx` は requirements に含まれない限り使わない。
- Ollamaのツール呼び出し: `ollama.chat()` に tools リストを渡す。レスポンスに `tool_calls` が含まれる間はツールを実行し、再度 `ollama.chat()` を呼ぶループを維持する。
- 日付のパース: ユーザーの自然言語入力はLLMに任せる。ツール側はYYYY-MM-DD形式のみ受け付ける。
- Open-Meteoから返る時間単位データを日次集計 (平均・最低・最高気温、平均湿度) に変換してからLLMに渡す。
- エラーは明示的に処理する。地点未発見・日付範囲外・API障害の場合はツールからエラー文字列を返し、LLMがユーザーに説明する。
- チャットループは会話履歴を保持し、毎回の `ollama.chat()` 呼び出しに全履歴を渡す。

## モデル

デフォルト: `llama3.1` (ツール呼び出し対応)。環境変数 `OLLAMA_MODEL` で変更可能。
起動前に `ollama list` でモデルが存在することを確認する。