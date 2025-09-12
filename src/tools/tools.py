import ase
from ase.io import write
from autoadsorbate import Surface, Fragment
from autoadsorbate.Surf import attach_fragment
from ase.optimize import BFGS
import torch
# from mace.calculators import mace_mp

# mace calculator harcoded for the time being

def read_atoms_object(path: str):
    """reads a atomistic structure file from the  system,
    Args:
        path: string - location on system
    returns:
        ase.Atoms object
    """
    return ase.io.read(path)

def get_sites_from_atoms(atoms: ase.Atoms): 
    """
    Args:
        atoms: ase.Atoms object. Determines all surface sites. 
    Returns:
        pandas.DataFrame containing all site information.
    """
    return Surface(atoms).site_df

def get_fragment(SMILES: str):
    """
    Args:
        SMILES: string of smiles that should be placed on surface sites.
    returns:
        ase.Atoms of molecule or molecular fragment, alligned relative to the site in [0,0,0]
    """
    return Fragment(SMILES).get_conformer(0)

def get_ads_slab(slab_atoms: ase.Atoms, fragment_atoms: ase.Atoms, site_dict: dict):
    """
    Args:
        slab_atoms: ase.Atoms, atoms of slab that should host the fragment
        fragment_atoms: ase.Atoms, molecular fragment obtained from SMILES
        site_dict: dict, information about the selected site geometry
    returns:
        ase.Atoms of molecule placed on slab
    """

    ads_slab_atoms = attach_fragment(
        atoms = slab_atoms,
        site_dict = site_dict,
        fragment = fragment_atoms,
        n_rotation = 0.,
        height=1.5
    )

    return ads_slab_atoms

# def relax_atoms(atoms: ase.Atoms):
#     """
#     Args:
#         atoms: ase.Atoms, atoms that need to be relaxed
        
#     returns:
#         relaxed_atoms: ase.Atoms, atoms of relaxed structure
#     """
#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     mace_calculator = mace_mp(model="medium", device=device, dispersion=False)

#     relaxed_atoms = atoms.copy()
#     relaxed_atoms.calc = mace_calculator
#     dyn = BFGS(relaxed_atoms, trajectory="relax.traj", logfile="relax.log")
#     dyn.run(fmax=0.5)

#     return relaxed_atoms

