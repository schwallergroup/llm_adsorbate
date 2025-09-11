import streamlit as st
import os
from src.agent.agent import get_agent_executor
from src.agent.prompts import prompt_codeact

st.set_page_config(page_title="LLM Agent Demo", layout="wide")
st.title("LLM Agent Demo: Computational Chemistry Assistant")

@st.cache_resource
def initialize_agent_executor():
    return get_agent_executor()

agent_executor = initialize_agent_executor()

st.sidebar.header("Settings")
openrouter_api_key = st.sidebar.text_input("OpenRouter API Key", type="password", key="openrouter_api_key")
if openrouter_api_key:
    os.environ["OPENROUTER_API_KEY"] = openrouter_api_key
else:
    st.sidebar.warning("Please enter your OpenRouter API Key.")

user_query = st.text_area("Enter your query for the agent:", value=prompt_codeact, height=150)

if st.button("Run Agent", disabled=not openrouter_api_key):
    if not user_query:
        st.warning("Please enter a query.")
    else:
        st.subheader("Agent Output:")
        output_container = st.empty()
        full_output = ""
        
        messages = [("user", user_query)]
        
        try:
            for typ, chunk in agent_executor.stream(
                {"messages": messages},
                stream_mode=["values", "messages"],
            ):
                if typ == "messages":
                    full_output += chunk[0].content
                    output_container.markdown(full_output + "▌")
                elif typ == "values":
                    st.success("Agent finished with final answer:")
                    st.json(chunk)
            output_container.markdown(full_output)
        except Exception as e:
            st.error(f"An error occurred during agent execution: {e}")
            st.exception(e)

st.sidebar.markdown("---")
st.sidebar.info("This demo uses an LLM agent to perform computational chemistry tasks.")
