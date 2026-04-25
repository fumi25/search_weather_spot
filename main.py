import json
import sys

import ollama

from config import MODEL, SYSTEM_PROMPT, TOOL_FUNCTIONS
from tool_schema import TOOLS


def check_model_available() -> None:
    try:
        models_response = ollama.list()
        available = [m.model for m in models_response.models]
    except Exception as e:
        print(f"Ollamaへの接続に失敗しました: {e}")
        print("Ollamaが起動しているか確認してください。")
        sys.exit(1)

    if not any(MODEL == m or m.startswith(f"{MODEL}:") for m in available):
        print(f"モデル '{MODEL}' が見つかりません。")
        print(f"利用可能なモデル: {', '.join(available) if available else 'なし'}")
        print(f"'ollama pull {MODEL}' を実行してモデルをダウンロードしてください。")
        sys.exit(1)


def _execute_tool_calls(tool_calls) -> list[dict]:
    results = []
    for tc in tool_calls:
        name = tc.function.name
        args = tc.function.arguments
        if name in TOOL_FUNCTIONS:
            result = TOOL_FUNCTIONS[name](**args)
        else:
            result = {"error": f"未知のツール: {name}"}
        results.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False)})
    return results


def chat(history: list, user_input: str) -> str:
    history.append({"role": "user", "content": user_input})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    while True:
        response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)

        if response.message.tool_calls:
            messages.append(response.message)
            messages.extend(_execute_tool_calls(response.message.tool_calls))
        else:
            answer = response.message.content
            history.append({"role": "assistant", "content": answer})
            return answer


def main() -> None:
    check_model_available()
    print(f"天気チャット (モデル: {MODEL})")
    print("終了するには 'quit' または 'exit' と入力してください。")
    print("-" * 50)

    history: list = []

    while True:
        try:
            user_input = input("あなた: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n終了します。")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("終了します。")
            break

        try:
            answer = chat(history, user_input)
            print(f"\nアシスタント: {answer}\n")
        except Exception as e:
            print(f"\nエラーが発生しました: {e}\n")


if __name__ == "__main__":
    main()
