conda activate llm_adsorbate
python -m src.agent.agent \
  --smiles 'ClC(=O)[O-]' \
  --slab 'notebooks/NiFeO_slab.xyz' \
  --prompt 'Does the molecule stay covalently bound to a central bridge site containing Fe and Ni on the surface?'