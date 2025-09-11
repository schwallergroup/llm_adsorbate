conda activate llm_adsorbate
python -m src.agent.agent \
  --smiles '*[O+]=C=O' \
  --slab 'notebooks/test_slab.xyz'