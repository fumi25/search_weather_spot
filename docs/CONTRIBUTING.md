# Contributing Guide

## 前提条件

| ツール | バージョン | インストール方法 |
|--------|-----------|----------------|
| Python | 3.11+ | https://python.org |
| uv | 最新版 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Ollama | 最新版 | https://ollama.com |

## 開発環境セットアップ

```bash
git clone https://github.com/fumi25/search_weather_spot.git
cd search_weather_spot

# 依存パッケージ (本番 + 開発) をインストール
uv sync --all-groups

# モデルをダウンロード
ollama pull llama3.1

# Ollamaサーバーを起動 (別ターミナル)
ollama serve
```

<!-- AUTO-GENERATED from pyproject.toml -->
## 依存パッケージ

### 本番依存

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| `ollama` | 0.6.1 | Ollama Python SDK |
| `requests` | 2.33.1 | HTTP クライアント |
| `streamlit` | >=1.56.0 | Web GUI フレームワーク |

### 開発依存

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| `pytest` | >=9.0.3 | テストランナー |
| `pytest-cov` | >=7.1.0 | カバレッジ計測 |

<!-- END AUTO-GENERATED -->

## テストの実行

```bash
# 全テスト実行
uv run pytest tests/

# カバレッジ付き
uv run pytest tests/ --cov=tools --cov=config --cov=main --cov=tool_schema --cov-report=term-missing

# 特定ファイルのみ
uv run pytest tests/test_tools.py -v
```

### カバレッジ要件

80% 以上を維持すること (現在 99%)。

### 新しいテストの書き方

`tests/test_*.py` にファイルを追加する。AAA パターンに従う:

```python
def test_xxxx(self):
    # Arrange
    ...

    # Act
    result = target_function(...)

    # Assert
    assert result == expected
```

外部 API (requests) は `unittest.mock.patch` でモックする:

```python
from unittest.mock import MagicMock, patch

def test_example(self):
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": [...]}
    with patch("tools.requests.get", return_value=mock_response):
        result = get_coordinates("東京")
```

## コードスタイル

- 関数は 50 行以内に収める
- ファイルは 800 行以内に収める
- エラーは例外を送出せず `{"error": "説明"}` の辞書で返す (tools.py の規約)
- 型ヒントを付ける

## ツールを追加する場合

1. `tools.py` に関数を実装する (戻り値は dict、エラーも dict)
2. `tool_schema.py` の `TOOLS` リストに JSON スキーマを追加する
3. `config.py` の `TOOL_FUNCTIONS` に関数を登録する
4. `tests/test_tools.py` にテストを追加する

## PR チェックリスト

- [ ] `uv run pytest tests/` が全て PASS する
- [ ] カバレッジが 80% 以上である
- [ ] 新機能にテストが含まれている
- [ ] ハードコードされた秘密情報がない
- [ ] `config.py` の `OLLAMA_MODEL` デフォルトが変更されていないこと (変更する場合は理由を記載)
