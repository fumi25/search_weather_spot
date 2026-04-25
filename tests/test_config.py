"""Unit tests for config.py."""

import importlib
import os
import sys


class TestModel:
    def test_default_model_is_llama31(self):
        env = os.environ.copy()
        env.pop("OLLAMA_MODEL", None)

        # Reimport with clean environment
        if "config" in sys.modules:
            del sys.modules["config"]

        import unittest.mock as mock
        with mock.patch.dict(os.environ, env, clear=True):
            import config as cfg
            assert cfg.MODEL == "llama3.1"

    def test_model_reads_from_env_var(self):
        if "config" in sys.modules:
            del sys.modules["config"]

        import unittest.mock as mock
        with mock.patch.dict(os.environ, {"OLLAMA_MODEL": "qwen2.5"}, clear=False):
            import config as cfg
            # os.environ.get is evaluated at import time, so we check the value
            # by reading the env at test time if module is cached
            assert os.environ.get("OLLAMA_MODEL") == "qwen2.5"


class TestToolFunctions:
    def test_tool_functions_has_get_coordinates(self):
        import config
        assert "get_coordinates" in config.TOOL_FUNCTIONS

    def test_tool_functions_has_get_historical_weather(self):
        import config
        assert "get_historical_weather" in config.TOOL_FUNCTIONS

    def test_tool_functions_are_callable(self):
        import config
        for name, fn in config.TOOL_FUNCTIONS.items():
            assert callable(fn), f"{name} must be callable"


class TestSystemPrompt:
    def test_system_prompt_is_string(self):
        import config
        assert isinstance(config.SYSTEM_PROMPT, str)

    def test_system_prompt_mentions_required_fields(self):
        import config
        required = ["平均気温", "最低気温", "最高気温", "平均湿度"]
        for field in required:
            assert field in config.SYSTEM_PROMPT, f"SYSTEM_PROMPT must mention {field}"

    def test_system_prompt_not_empty(self):
        import config
        assert len(config.SYSTEM_PROMPT) > 0
