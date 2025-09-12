import os
import builtins
import contextlib
import io
import math
import argparse
from typing import Any

import numpy as np
import pandas as pd
import scipy
import sklearn
import ase
import autoadsorbate
import torch
import mace
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph_codeact import create_codeact

import weave
weave.init("liac/llm-hackathon")

from src.agent.prompts import prompt_codeact
from src.tools.tools import read_atoms_object, get_sites_from_atoms, get_fragment, get_ads_slab, relax_atoms, md_run_atoms

load_dotenv()

if not os.environ.get("OPENROUTER_API_KEY"):
    raise ValueError("OPENROUTER_API_KEY environment variable not set.")

exec_globals = builtins.__dict__.copy()
exec_globals.update({
    "np": np, "pd": pd, "scipy": scipy, "sklearn": sklearn, "math": math,
    "ase": ase, "autoadsorbate": autoadsorbate, "torch": torch, "mace": mace,
})

def eval_code(code: str, context: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    import traceback
    exec_scope = exec_globals.copy()
    exec_scope.update(context)
    stdout_io = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_io):
            exec(code, exec_scope)
        output = stdout_io.getvalue()
        if not output:
            output = "<code ran, no output printed to stdout>"
    except Exception:
        output = f"Error during execution:\n{traceback.format_exc()}"
    context_after_exec = {k: v for k, v in exec_scope.items() if not isinstance(v, type)}
    return output, context_after_exec

llm = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    model="google/gemini-2.5-pro",
    streaming=False, max_completion_tokens=20000, request_timeout=600, seed=420
)

registered_tools = [
    read_atoms_object, get_sites_from_atoms, get_fragment,
    get_ads_slab, relax_atoms, md_run_atoms
]

def get_agent_executor():
    code_graph = create_codeact(llm, registered_tools, eval_code)
    return code_graph.compile()

def _prepare_prompt(smiles: str, slab_path: str, user_request: str) -> str:
    prompt = prompt_codeact.replace("{{SMILES}}", smiles)
    prompt = prompt.replace("{{SLAB_XYZ}}", slab_path)
    prompt = prompt.replace("{{USER_REQUEST}}", user_request)
    return prompt

def parse_args():
    parser = argparse.ArgumentParser(description="Run the CodeAct agent.")
    parser.add_argument("--smiles", type=str, required=True, help="SMILES string.")
    parser.add_argument("--slab_path", type=str, required=True, help="Path to the slab .xyz file.")
    parser.add_argument("--user_request", type=str, default="Find a stable adsorption configuration.", help="User's request.")
    return parser.parse_args()

@weave.op()
def main_cli():
    args = parse_args()
    prompt = _prepare_prompt(args.smiles, args.slab_path, args.user_request)
    agent_executor = get_agent_executor()
    print("\n--- Running Agent with generated prompt ---\n")
    messages = [("user", prompt)]
    for typ, chunk in agent_executor.stream({"messages": messages}, stream_mode=["values", "messages"]):
        if typ == "messages":
            print(chunk[0].content, end="")
        elif typ == "values":
            print("\n\n---answer---\n\n", chunk)
    print("\n\n--- Agent finished ---\n")

if __name__ == '__main__':
    main_cli()