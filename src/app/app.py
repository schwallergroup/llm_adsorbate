import sys
import os

# 現在のファイルのディレクトリ (src/app/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# プロジェクトのルートディレクトリ (src/app/ の2つ上のディレクトリ)
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

# プロジェクトのルートディレクトリをsys.pathに追加
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import os
from src.agent.agent import get_agent_executor
from src.agent.prompts import prompt_codeact

st.set_page_config(page_title="LLM Agent Demo", layout="wide")
st.title("LLM Agent Demo: Computational Chemistry Assistant")

# --- エージェントの初期化 ---
@st.cache_resource
def initialize_agent_executor():
    return get_agent_executor()

agent_executor = initialize_agent_executor()

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
        st.markdown(message["content"])

# --- ユーザー入力 ---
# APIキーが設定されていない場合は入力を無効にする
if not openrouter_api_key:
    st.chat_input("OpenRouter API Keyを入力してください", disabled=True)
else:
    # ユーザーからの新しい入力
    if prompt := st.chat_input("Enter your query for the agent:"):
        # ユーザーメッセージを履歴に追加し、UIに表示
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # エージェントの応答を生成
        with st.chat_message("assistant"):
            # agent_executor.streamから返されるイベントを処理
            # "values"にはLangGraphの各ステップの出力が含まれる
            # "messages"には会話履歴の更新が含まれる
            
            final_answer = ""
            tool_calls = []

            try:
                # 思考プロセスをst.statusで表示
                with st.status("Thinking...", expanded=False) as status:
                    for event in agent_executor.stream(
                        {"messages": [("user", prompt)]},
                        stream_mode="values",
                    ):
                        # eventのキーをチェックして処理を分岐
                        if "tool_calls" in event:
                            # ツール呼び出しの情報を表示
                            for tool_call in event["tool_calls"]:
                                tool_name = tool_call["name"]
                                tool_args = tool_call["args"]
                                status.write(f"Calling tool: `{tool_name}` with args: `{tool_args}`")
                                tool_calls.append(tool_call)

                        if "tool_output" in event:
                            # ツールの実行結果を表示
                            for tool_output in event["tool_output"]:
                                status.write(f"Tool output: `{tool_output}`")
                        
                        if "messages" in event:
                            # "messages"イベントから最新のメッセージを取得
                            last_message = event["messages"][-1]
                            if last_message.content:
                                # エージェントの思考プロセス（中間的な応答）をステータスにリスト風に表示
                                status.write(f"- {last_message.content}")
                                # これを最終回答として保持（ループの最後で上書きされる）
                                final_answer = last_message.content
                    
                    # 思考プロセスの表示を完了
                    if final_answer:
                        status.update(label="Agent finished.", state="complete", expanded=False)
                    else:
                        status.update(label="No final answer found.", state="error", expanded=True)

                # 最終的な回答を表示
                if final_answer:
                    st.markdown(final_answer)
                    # 最終回答を会話履歴に保存
                    st.session_state.messages.append({"role": "assistant", "content": final_answer})
                else:
                    # 最終回答が見つからなかった場合のフォールバック
                    st.warning("The agent did not produce a final answer.")
                    # この場合でも、何らかの情報を履歴に残すか検討
                    # st.session_state.messages.append({"role": "assistant", "content": "[No final answer produced]"})

            except Exception as e:
                st.error(f"An error occurred during agent execution: {e}")
                st.exception(e)
                # エラーメッセージを履歴に追加
                error_message = f"Error: {e}"
                st.session_state.messages.append({"role": "assistant", "content": error_message})


st.sidebar.markdown("---")
st.sidebar.info("This demo uses an LLM agent to perform computational chemistry tasks.")