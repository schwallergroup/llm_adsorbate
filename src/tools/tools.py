import ase
from ase.io import write
from autoadsorbate import Surface, Fragment
from autoadsorbate.Surf import attach_fragment
from ase.optimize import BFGS
import torch
from mace.calculators import mace_mp
from ase.md.langevin import Langevin
from ase import units
import os

# mace calculator harcoded for the time being

def read_atoms_object(path: str):
    """reads a atomistic structure file from the system,
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
        the columns of the returned dataframe are ['coordinates', 'connectivity', 'topology', 'n_vector', 'h_vector', 'site_formula'],
        - each index describes one site
        - 'coordinates': each entry is a list of 3 floats that locate the adsorption site in cartesian coordinates in angstrom;
        - 'connectivity': number of adjecent atoms, 1 - top site; 2 - bridge site; 3 - hollow site/3 fold site; etc.;
        - 'topology': list of ase.Atom.index from atoms that is directly adjecent to adsorption site;
        - 'n_vector': Unit vector pointing in the direction in with anutthyng attached to the site needs to be oriented;
        - 'h_vector': Unit vector describing the rotation around n_vector;
        - 'site_formula': dictionary indicating the composition of the site.
    """
    return Surface(atoms).site_df

def get_fragment(SMILES: str, to_initialize=1, conformer_i=0):
    """
    Args:
        SMILES: string of smiles that should be placed on surface sites.
        to_initialize: int = 1, if a SMILES is deamed to be conformationally complex. This number should be increased to deal with the increased complexity; in this case multiple fragment conformation should be tried.
        conformer_i: int, index of initialized conformer to be returned
    returns:
        ase.Atoms of molecule or molecular fragment, alligned relative to the site in [0,0,0]
    """
    return Fragment(SMILES, to_initialize=to_initialize).get_conformer(conformer_i)

def get_ads_slab(slab_atoms: ase.Atoms, fragment_atoms: ase.Atoms, site_dict: dict, height: float = 1.5, n_rotation: float = 0.):
    """
    Args:
        slab_atoms: ase.Atoms, atoms of slab that should host the fragment
        fragment_atoms: ase.Atoms, molecular fragment obtained from SMILES
        site_dict: dict, information about the selected site geometry
        n_rotation: float, rotation around the site vector provided in site_dict['n_vector']. This can be used to rotate the fragment conformer, to avoid atoms being too close to each other.
        height: float, distance from site in angstroms
    returns:
        ase.Atoms of molecule placed on slab
    """

    ads_slab_atoms = attach_fragment(
        atoms = slab_atoms,
        site_dict = site_dict,
        fragment = fragment_atoms,
        n_rotation = n_rotation,
        height = height   
    )

    return ads_slab_atoms

def relax_atoms(atoms: ase.Atoms, output_dir='./'):
    """
    Args:
        atoms: ase.Atoms, atoms that need to be relaxed
        output_dir: str, where to write relax trajectory file
    returns:
        relaxed_atoms: ase.Atoms, atoms of relaxed structure
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    mace_calculator = mace_mp(model="medium", device=str(device), dispersion=False)

    relaxed_atoms = atoms.copy()
    relaxed_atoms.calc = mace_calculator
    dyn = BFGS(relaxed_atoms, trajectory=os.path.join(output_dir, "relax.traj"), logfile="relax.log")
    dyn.run(fmax=0.01)

    return relaxed_atoms

def md_run_atoms(atoms: ase.Atoms, steps: int = 100, temperature_K: float = 300):
    """
    xxx
    Args:
        atoms: ase.Atoms, atoms that need to run MD
        steps: int, number of inonic steps in MD
        temperature_K: float, Temperature in K
        
    returns:
        MD_traj: list of ase.Atoms, frames of MD simulation.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    mace_calculator = mace_mp(model="medium", device=str(device), dispersion=False)

    relaxed_atoms = atoms.copy()
    relaxed_atoms.calc = mace_calculator
    
    dyn = Langevin(
        atoms,
        timestep=1.0 * units.fs,         
        temperature_K = temperature_K,   
        friction = 0.002,                
    )

    def print_status(a=atoms):
        epot = a.get_potential_energy() / len(a)
        ekin = a.get_kinetic_energy() / len(a)
        print(f"Epot = {epot:.3f} eV, Ekin = {ekin:.3f} eV, Etot = {epot+ekin:.3f} eV")

    dyn.attach(print_status, interval=5)

    MD_traj = []
    def save_frame():
        MD_traj.append(atoms.copy())

    dyn.attach(save_frame, interval=1)

    dyn.run(steps)

    return MD_traj