import os

from tools import get_coordinates, get_historical_weather

MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")

TOOL_FUNCTIONS = {
    "get_coordinates": get_coordinates,
    "get_historical_weather": get_historical_weather,
}

SYSTEM_PROMPT = (
    "あなたは天気情報アシスタントです。"
    "ユーザーが地点名と日付を伝えたら、get_coordinates と get_historical_weather を順番に呼び出して情報を取得し、"
    "日本語で回答してください。\n"
    "回答には必ず以下を含めてください: 日付、地点名、平均気温 (°C)、最低気温 (°C)、最高気温 (°C)、平均湿度 (%)。\n"
    "ツールからエラーが返った場合は、その内容をユーザーに分かりやすく説明してください。"
)
