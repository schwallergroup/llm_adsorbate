import os
import builtins
import contextlib
import io
import math
import uuid
from typing import Any

import numpy as np
import pandas as pd
import scipy
import sklearn
import ase
import autoadsorbate
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph_codeact import create_codeact

import weave
weave.init("llm-hackathon")

# Import the tools we defined

from .prompts import prompt_codeact
from ..tools.tools import read_atoms_object, get_sites_from_atoms, get_fragment, get_ads_slab

# Load environment variables from .env file
load_dotenv()

# Check for Portkey API key
if not os.environ.get("OPENROUTER_API_KEY"):
    raise ValueError("OPENTOURTER_API_KEY environment variable not set. Please set it in your .env file.")


# Prepare a globals dictionary for the exec context
exec_globals = builtins.__dict__.copy()
exec_globals.update({
    "np": np,
    "pd": pd,
    "scipy": scipy,
    "sklearn": sklearn,
    "math": math,
    "ase": ase,
    "autoadsorbate": autoadsorbate,
})


# Bring-your-own code sandbox
def eval_code(code: str, context: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    A safe and enhanced code evaluation function to execute generated Python code.
    It uses traceback for detailed error reporting and handles variable scope correctly.
    """
    import traceback

    # The execution scope starts with the globally available libraries.
    exec_scope = exec_globals.copy()
    # It is then updated with the context from previous turns.
    exec_scope.update(context)

    stdout_io = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_io):
            # Execute the code in the prepared scope.
            # New variables will be added to exec_scope.
            exec(code, exec_scope)
        
        output = stdout_io.getvalue()
        if not output:
            output = "<code ran, no output printed to stdout>"

    except Exception:
        # Capture the full traceback on error.
        output = f"Error during execution:\n{traceback.format_exc()}"

    # The exec_scope now contains the state after execution.
    # We filter out any non-serializable types (like class definitions)
    # before returning the context for the next turn.
    context_after_exec = {
        k: v for k, v in exec_scope.items() if not isinstance(v, type)
    }
    
    return output, context_after_exec



# Instantiate the LLM
llm = ChatOpenAI(
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        model="google/gemini-2.5-pro",
        streaming=False,
        max_completion_tokens=20000,
        request_timeout=120,
    )

registered_tools = [
    read_atoms_object, get_sites_from_atoms, get_fragment, get_ads_slab 
]

@weave.op()
def main():
    """Main function to set up and run the agent."""
    # Checkpointer is disabled, so conversation state is not saved between runs.

    # Create the CodeAct graph using the factory function
    code_graph = create_codeact(llm, registered_tools, eval_code)

    # Compile the graph into a runnable executor (without memory)
    agent_executor = code_graph.compile()

    print(f"\n--- Running Agent with query: '{prompt_codeact}' ---\n")
    
    # The agent expects a list of messages as input
    messages = [("user", prompt_codeact)]
    
    # Stream the agent's response (no config needed for thread_id)
    for typ, chunk in agent_executor.stream(
        {"messages": messages},
        stream_mode=["values", "messages"],
    ):
        if typ == "messages":
            print(chunk[0].content, end="")
        elif typ == "values":
            print("\n\n---answer---\n\n", chunk)

    print(f"\n\n--- Agent finished ---")

if __name__ == '__main__':
    main()
