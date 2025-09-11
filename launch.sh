conda activate llm_adsorbate
python -m src.agent.agent \
  --smiles 'ClC(=O)[O-]' \
  --slab 'notebooks/test_slab.xyz' \
  --prompt 'Find the top site in the center of the cell. Does the molecule bind there covalently?'