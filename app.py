import json

import ollama
import streamlit as st

from config import MODEL, SYSTEM_PROMPT, TOOL_FUNCTIONS
from tool_schema import TOOLS

TOOL_LABELS = {
    "get_coordinates": "座標を取得中...",
    "get_historical_weather": "天気データを取得中...",
}


def get_answer(history: list, user_input: str, status) -> str:
    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + history
        + [{"role": "user", "content": user_input}]
    )

    while True:
        response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)

        if response.message.tool_calls:
            messages.append(response.message)
            for tc in response.message.tool_calls:
                name = tc.function.name
                args = tc.function.arguments
                status.update(label=TOOL_LABELS.get(name, f"{name} を実行中..."))
                result = (
                    TOOL_FUNCTIONS[name](**args)
                    if name in TOOL_FUNCTIONS
                    else {"error": f"未知のツール: {name}"}
                )
                messages.append(
                    {"role": "tool", "content": json.dumps(result, ensure_ascii=False)}
                )
        else:
            return response.message.content


def check_ollama() -> tuple[bool, list[str]]:
    try:
        models_response = ollama.list()
        available = [m.model for m in models_response.models]
        return True, available
    except Exception:
        return False, []


# ページ設定
st.set_page_config(page_title="天気チャット", layout="centered")
st.title("天気チャット")

# サイドバー
with st.sidebar:
    st.header("設定")
    connected, available_models = check_ollama()

    if connected:
        st.success("Ollama: 接続済み")
        st.write(f"使用モデル: `{MODEL}`")
        if available_models:
            st.write("利用可能なモデル:")
            for m in available_models:
                st.write(f"- {m}")
    else:
        st.error("Ollama に接続できません。`ollama serve` を実行してください。")

    st.divider()
    if st.button("会話をリセット", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("入力例:")
    st.caption("東京の2023年7月15日の天気は？")
    st.caption("2022年1月10日のパリの気温を教えて")

# 会話履歴の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# 会話履歴を表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Ollama未接続時は入力を無効化
if not connected:
    st.info("Ollama が起動していません。サイドバーを確認してください。")
    st.stop()

# ユーザー入力
if prompt := st.chat_input("地点名と日付を入力してください"):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("回答を生成中...", expanded=True) as status:
            try:
                answer = get_answer(st.session_state.messages, prompt, status)
                status.update(label="完了", state="complete", expanded=False)
            except Exception as e:
                answer = f"エラーが発生しました: {e}"
                status.update(label="エラー", state="error", expanded=False)
        st.markdown(answer)

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": answer})
