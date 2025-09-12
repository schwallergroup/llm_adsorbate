import sys
import os
import re
import tempfile

# プロジェクトルートをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from src.agent.agent import get_agent_executor, _prepare_prompt

st.set_page_config(page_title="LLM Agent Demo", layout="wide")
st.title("adsKRK")

# --- エージェントの初期化 ---
@st.cache_resource
def initialize_agent_executor():
    return get_agent_executor()

agent_executor = initialize_agent_executor()

# --- 表示用ヘルパー関数 ---
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

# --- 新しい入力UI ---
st.sidebar.header("Inputs")
smiles_input = st.sidebar.text_input("SMILES String")
xyz_file = st.sidebar.file_uploader("Slab XYZ file", type=['xyz'])
user_query = st.sidebar.text_area("User Query", value="Please find a stable adsorption configuration for the adsorbate on the surface.")

run_button = st.sidebar.button("Run Agent")

# --- 会話履歴の初期化と表示 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        render_message(message["content"])

# --- エージェント実行ロジック ---
if run_button:
    # 入力チェック
    if not openrouter_api_key:
        st.sidebar.error("Please enter your OpenRouter API Key.")
    elif not smiles_input:
        st.sidebar.error("Please enter a SMILES string.")
    elif not xyz_file:
        st.sidebar.error("Please upload a slab XYZ file.")
    else:
        # XYZファイルを一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xyz", mode='w') as tmp_file:
            xyz_content = xyz_file.getvalue().decode('utf-8')
            tmp_file.write(xyz_content)
            tmp_file_path = tmp_file.name
        
        # プロンプトを準備
        try:
            prompt = _prepare_prompt(smiles=smiles_input, slab_path=tmp_file_path, user_request=user_query)
            
            # 生成されたプロンプトをユーザーメッセージとして表示
            st.session_state.messages.append({"role": "user", "content": f"**Inputs provided:**\n- SMILES: `{smiles_input}`\n- Slab file: `{xyz_file.name}`\n- Query: `{user_query}`\n\n**Generated prompt for the agent...**"})
            with st.chat_message("user"):
                st.markdown(f"**Inputs provided:**\n- SMILES: `{smiles_input}`\n- Slab file: `{xyz_file.name}`\n- Query: `{user_query}`")

            # エージェントを実行
            with st.chat_message("assistant"):
                final_answer = ""
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
            
            # 一時ファイルを削除
            os.remove(tmp_file_path)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.exception(e)
            # エラー発生時も一時ファイルを削除
            if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

st.sidebar.markdown("---")
st.sidebar.info("Provide SMILES, a slab file, and a query, then click 'Run Agent'.")