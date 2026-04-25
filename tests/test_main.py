"""Unit tests for main.py — check_model_available, _execute_tool_calls, chat, and main."""

import json
import sys
from unittest.mock import MagicMock, call, patch

import pytest


class TestCheckModelAvailable:
    def _make_models(self, *names):
        models = []
        for name in names:
            m = MagicMock()
            m.model = name
            models.append(m)
        resp = MagicMock()
        resp.models = models
        return resp

    def test_passes_when_model_exact_match(self):
        from main import check_model_available

        with (
            patch("main.ollama.list", return_value=self._make_models("llama3.1")),
            patch("main.MODEL", "llama3.1"),
        ):
            check_model_available()  # must not raise or exit

    def test_passes_when_model_matches_with_tag(self):
        from main import check_model_available

        with (
            patch("main.ollama.list", return_value=self._make_models("llama3.1:latest")),
            patch("main.MODEL", "llama3.1"),
        ):
            check_model_available()  # must not raise or exit

    def test_exits_when_model_not_found(self):
        from main import check_model_available

        with (
            patch("main.ollama.list", return_value=self._make_models("gemma2:2b")),
            patch("main.MODEL", "llama3.1"),
            pytest.raises(SystemExit),
        ):
            check_model_available()

    def test_exits_when_ollama_unreachable(self):
        from main import check_model_available

        with (
            patch("main.ollama.list", side_effect=Exception("connection refused")),
            pytest.raises(SystemExit),
        ):
            check_model_available()

    def test_prints_error_when_ollama_unreachable(self, capsys):
        from main import check_model_available

        with (
            patch("main.ollama.list", side_effect=Exception("connection refused")),
            pytest.raises(SystemExit),
        ):
            check_model_available()

        out = capsys.readouterr().out
        assert "接続に失敗" in out

    def test_prints_pull_hint_when_model_missing(self, capsys):
        from main import check_model_available

        with (
            patch("main.ollama.list", return_value=self._make_models("gemma2:2b")),
            patch("main.MODEL", "llama3.1"),
            pytest.raises(SystemExit),
        ):
            check_model_available()

        out = capsys.readouterr().out
        assert "ollama pull" in out


class TestMainLoop:
    def _make_chat_response(self, content):
        resp = MagicMock()
        resp.message.content = content
        resp.message.tool_calls = None
        return resp

    def test_quit_exits_cleanly(self, capsys):
        from main import main

        with (
            patch("main.check_model_available"),
            patch("builtins.input", side_effect=["quit"]),
        ):
            main()

        out = capsys.readouterr().out
        assert "終了します" in out

    def test_exit_exits_cleanly(self, capsys):
        from main import main

        with (
            patch("main.check_model_available"),
            patch("builtins.input", side_effect=["exit"]),
        ):
            main()

        out = capsys.readouterr().out
        assert "終了します" in out

    def test_eof_exits_cleanly(self, capsys):
        from main import main

        with (
            patch("main.check_model_available"),
            patch("builtins.input", side_effect=EOFError),
        ):
            main()

        out = capsys.readouterr().out
        assert "終了します" in out

    def test_empty_input_skipped(self, capsys):
        from main import main

        with (
            patch("main.check_model_available"),
            patch("builtins.input", side_effect=["", "quit"]),
        ):
            main()

        out = capsys.readouterr().out
        assert "アシスタント" not in out

    def test_prints_answer_for_valid_input(self, capsys):
        from main import main

        with (
            patch("main.check_model_available"),
            patch("builtins.input", side_effect=["東京の天気は？", "quit"]),
            patch("main.ollama.chat", return_value=self._make_chat_response("晴れです。")),
        ):
            main()

        out = capsys.readouterr().out
        assert "晴れです。" in out

    def test_prints_error_when_chat_raises(self, capsys):
        from main import main

        with (
            patch("main.check_model_available"),
            patch("builtins.input", side_effect=["質問です。", "quit"]),
            patch("main.ollama.chat", side_effect=Exception("LLMエラー")),
        ):
            main()

        out = capsys.readouterr().out
        assert "エラーが発生しました" in out


class TestExecuteToolCalls:
    def _make_tool_call(self, name, arguments):
        tc = MagicMock()
        tc.function.name = name
        tc.function.arguments = arguments
        return tc

    def test_known_tool_returns_tool_message(self):
        from main import _execute_tool_calls

        fake_result = {"latitude": 35.0, "longitude": 139.0, "name": "東京", "country": "日本"}
        tc = self._make_tool_call("get_coordinates", {"place": "東京"})

        with patch("main.TOOL_FUNCTIONS", {"get_coordinates": lambda **kw: fake_result}):
            results = _execute_tool_calls([tc])

        assert len(results) == 1
        assert results[0]["role"] == "tool"
        payload = json.loads(results[0]["content"])
        assert payload["latitude"] == 35.0

    def test_unknown_tool_returns_error_message(self):
        from main import _execute_tool_calls

        tc = self._make_tool_call("nonexistent_tool", {})

        with patch("main.TOOL_FUNCTIONS", {}):
            results = _execute_tool_calls([tc])

        assert len(results) == 1
        payload = json.loads(results[0]["content"])
        assert "error" in payload
        assert "nonexistent_tool" in payload["error"]

    def test_multiple_tool_calls_all_executed(self):
        from main import _execute_tool_calls

        tc1 = self._make_tool_call("get_coordinates", {"place": "東京"})
        tc2 = self._make_tool_call("get_coordinates", {"place": "Paris"})

        call_log = []

        def fake_fn(**kwargs):
            call_log.append(kwargs["place"])
            return {"latitude": 0.0, "longitude": 0.0, "name": kwargs["place"], "country": ""}

        with patch("main.TOOL_FUNCTIONS", {"get_coordinates": fake_fn}):
            results = _execute_tool_calls([tc1, tc2])

        assert len(results) == 2
        assert call_log == ["東京", "Paris"]

    def test_tool_result_is_json_encoded(self):
        from main import _execute_tool_calls

        tc = self._make_tool_call("get_coordinates", {"place": "テスト"})
        fake_result = {"name": "テスト", "latitude": 1.0, "longitude": 2.0, "country": "日本"}

        with patch("main.TOOL_FUNCTIONS", {"get_coordinates": lambda **kw: fake_result}):
            results = _execute_tool_calls([tc])

        # Must be valid JSON
        parsed = json.loads(results[0]["content"])
        assert parsed["name"] == "テスト"


class TestChat:
    def _make_response(self, content=None, tool_calls=None):
        response = MagicMock()
        response.message.content = content
        response.message.tool_calls = tool_calls
        return response

    def test_returns_assistant_answer_on_no_tool_calls(self):
        from main import chat

        final = self._make_response(content="東京の天気は晴れです。", tool_calls=None)

        with patch("main.ollama.chat", return_value=final):
            history = []
            answer = chat(history, "東京の天気は？")

        assert answer == "東京の天気は晴れです。"

    def test_appends_user_and_assistant_to_history(self):
        from main import chat

        final = self._make_response(content="回答です。", tool_calls=None)

        with patch("main.ollama.chat", return_value=final):
            history = []
            chat(history, "質問です。")

        assert history[0] == {"role": "user", "content": "質問です。"}
        assert history[1] == {"role": "assistant", "content": "回答です。"}

    def test_executes_tool_calls_before_final_answer(self):
        from main import chat

        tool_call = MagicMock()
        tool_call.function.name = "get_coordinates"
        tool_call.function.arguments = {"place": "東京"}

        tool_response = self._make_response(tool_calls=[tool_call])
        final_response = self._make_response(content="気温は30度です。", tool_calls=None)

        fake_coord = {"latitude": 35.0, "longitude": 139.0, "name": "東京", "country": "日本"}

        with (
            patch("main.ollama.chat", side_effect=[tool_response, final_response]),
            patch("main.TOOL_FUNCTIONS", {"get_coordinates": lambda **kw: fake_coord}),
        ):
            history = []
            answer = chat(history, "東京の気温は？")

        assert answer == "気温は30度です。"

    def test_history_preserved_across_multiple_turns(self):
        from main import chat

        response1 = self._make_response(content="東京は30度です。", tool_calls=None)
        response2 = self._make_response(content="パリは20度です。", tool_calls=None)

        history = []
        with patch("main.ollama.chat", return_value=response1):
            chat(history, "東京の気温は？")

        with patch("main.ollama.chat", return_value=response2):
            chat(history, "パリは？")

        assert len(history) == 4
        assert history[0]["content"] == "東京の気温は？"
        assert history[1]["content"] == "東京は30度です。"
        assert history[2]["content"] == "パリは？"
        assert history[3]["content"] == "パリは20度です。"
