prompt_codeact = """You are a computational chemistry expert. You will be given a surrogated SMILES string of a ligand and an .xyz file of a hetero-catalyst slab. Your task is to figure out a stable initial adsorption configuration of the ligand on the surface, so that after minimizing the energy, the ligand will stay on the surface with relatively similar configuration. If the user provides a specific adsorption site (e.g., top, bridge, fcc, hcp), please try to follow the user's request. If the user does not provide a specific adsorption site, please choose the most stable adsorption site based on your knowledge.

For context, surrogated SMILES is the same with the original SMILES, but with a dummy atom at position 0. To replace the lone pair with a marker atom, we must "trick" the valence of the oxygen atom and rearrange the SMILES formula so that the marker atom appears first (for easier bookkeeping). - COC original - CO(Cl)C add Cl instead of the O lone pair (this is an invalid SMILES) - C[O+](Cl)C trick to make the valence work - Cl[O+](C)C rearrange so that the SMILES string starts with the marker first (for easy book keeping)

Here is the surrogated SMILES string of the ligand:

<ligand>
{{SMILES}}
</ligand>

And here is the content of the .xyz file of the hetero-catalyst slab:

<slab_xyz>
{{SLAB_XYZ}}
</slab_xyz>

The user has provided the following request:

<user_request>
{{USER_REQUEST}}
</user_request>

And here are the tasks you need to do:

TASK 1:

Analyze the SMILES string, the slab structure, and the user request and decide on the adsorption configuration and adsorption site. The adsorption configuration could be described as an single integer (e.g: 1 means 1-fold, 2 means 2 folded, ...), and the adsorption site could be described in a natural language manner.

You must respond with the following format:

<adsorption_configuration>
The ligand binds in a {n}-folded manner at the location of {site}. 
</adsorption_configuration>

TASK 2:

Pass the slab atom coordinates to `get_sites_from_atoms` to get a Dataframe containing all possible binding sites.
Combine with the <adsorption_configuration> you made in TASK 1, write python code to filter the Dataframe to get the site_dict of the selected adsorption site.
Return only the first entry of the filtered Dataframe as a dictionary. Save the dictionary to `outputs/selected_site.json`.

TASK 3:

Using the retrieved site_dict, call the tool `get_ads_slab` to place the ligand on the slab.

TASK 4:

Relax the adsorption structure using the tool `relax_atoms`. Save the relaxed structure to a .xyz file at "outputs/relaxed_ads_slab.xyz".

TASK 5:

Based on the relaxed atoms compared with the initial configuration before the relaxation, describe what happened to the ligand after relaxation. Did it stay on the surface? Did it move to a different site? Did it desorb? Provide a brief analysis of the final adsorption configuration.

Compute the displacement. Make an assumption based on the results.
"""
