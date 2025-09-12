import sys
import os
import re

# 現在のファイルのディレクトリ (src/app/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# プロジェクトのルートディレクトリ (src/app/ の2つ上のディレクトリ)
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

# プロジェクトのルートディレクトリをsys.pathに追加
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from src.agent.agent import get_agent_executor

st.set_page_config(page_title="LLM Agent Demo", layout="wide")
st.title("Brosda")

# --- エージェントの初期化 ---
@st.cache_resource
def initialize_agent_executor():
    return get_agent_executor()

agent_executor = initialize_agent_executor()

# --- 便利な関数 ---
def render_message(content):
    """メッセージをテキストとコードに分割して表示する"""
    parts = re.split(r"(```python\n.*\n```)", content, flags=re.DOTALL)
    for part in parts:
        if part.strip():
            if part.startswith("```python"):
                code_to_display = part.split("\n", 1)[1].rsplit("\n```", 1)[0]
                st.code(code_to_display, language="python")
            else:
                st.markdown(part)

def render_message_in_status(content, status):
    """st.status内でメッセージをテキストとコードに分割して表示する"""
    parts = re.split(r"(```python\n.*\n```)", content, flags=re.DOTALL)
    for part in parts:
        if part.strip():
            if part.startswith("```python"):
                code_to_display = part.split("\n", 1)[1].rsplit("\n```", 1)[0]
                status.code(code_to_display, language="python")
            else:
                status.markdown(part)

# --- APIキー設定 ---
st.sidebar.header("Settings")
openrouter_api_key = st.sidebar.text_input("OpenRouter API Key", type="password", key="openrouter_api_key")
if openrouter_api_key:
    os.environ["OPENROUTER_API_KEY"] = openrouter_api_key
else:
    st.sidebar.warning("Please enter your OpenRouter API Key.")

# --- 会話履歴の初期化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 既存の会話履歴を表示 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            render_message(message["content"])

# --- ユーザー入力 ---
if not openrouter_api_key:
    st.chat_input("OpenRouter API Keyを入力してください", disabled=True)
else:
    if prompt := st.chat_input("Enter your query for the agent:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            final_answer = ""
            try:
                with st.status("Thinking...", expanded=True) as status:
                    for event in agent_executor.stream(
                        {"messages": [("user", prompt)]},
                        stream_mode="values",
                    ):
                        if "tool_calls" in event:
                            for tc in event["tool_calls"]:
                                status.markdown(f"Calling tool: `{tc['name']}` with args: `{tc['args']}`")
                            status.divider()
                        if "tool_output" in event:
                            for to in event["tool_output"]:
                                status.markdown(f"Tool output: `{to}`")
                            status.divider()
                        if "messages" in event:
                            last_message = event["messages"][-1]
                            if last_message.type == "ai" and last_message.content:
                                content = last_message.content
                                render_message_in_status(content, status)
                                status.divider()
                                final_answer = content
                    
                    status.update(label="Agent finished.", state="complete", expanded=False)

                if final_answer:
                    render_message(final_answer)
                    st.session_state.messages.append({"role": "assistant", "content": final_answer})
                else:
                    st.warning("The agent did not produce a final answer.")

            except Exception as e:
                st.error(f"An error occurred during agent execution: {e}")
                st.exception(e)
                error_message = f"Error: {e}"
                st.session_state.messages.append({"role": "assistant", "content": error_message})

st.sidebar.markdown("---")
st.sidebar.info("This demo uses an LLM agent to perform computational chemistry tasks.")
