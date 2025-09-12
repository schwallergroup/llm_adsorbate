import ase
from ase.io import read, write
from autoadsorbate import Surface, Fragment
from ase.constraints import FixAtoms
from autoadsorbate.Surf import attach_fragment
from ase.optimize import BFGS
from ase.io.trajectory import Trajectory
import torch
from mace.calculators import mace_mp
from ase.md.langevin import Langevin
from ase import units
import os
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution

# mace calculator harcoded for the time being

def read_atoms_object(path: str):
    """Reads a atomistic structure file 
    Args:
        path: string - location on system
    returns:
        ase.Atoms object
    """
    return ase.io.read(path)

def get_sites_from_atoms(atoms: ase.Atoms): 
    """Get all possible binding sites from atoms of a slab.
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
    """Generate a molecular fragment with conformations from a SMILES string.
    Args:
        SMILES: string of smiles that should be placed on surface sites.
        to_initialize: int = 1, if a SMILES is deamed to be conformationally complex. This number should be increased to deal with the increased complexity; in this case multiple fragment conformation should be tried.
        conformer_i: int, index of initialized conformer to be returned
    returns:
        ase.Atoms of molecule or molecular fragment, alligned relative to the site in [0,0,0]
    """
    return Fragment(SMILES, to_initialize=to_initialize).get_conformer(conformer_i)

def get_ads_slab(slab_atoms: ase.Atoms, fragment_atoms: ase.Atoms, site_dict: dict, height: float = 1.5, n_rotation: float = 0.):
    """Placing a fragment on a slab at a selected site defined by `site_dict`
    Args:
        slab_atoms: ase.Atoms, atoms of slab that should host the fragment
        fragment_atoms: ase.Atoms, molecular fragment obtained from SMILES
        site_dict: dict, information about the selected site geometry
        n_rotation: float, rotation in degree around the site vector provided in site_dict['n_vector']. This can be used to rotate the fragment conformer, to avoid atoms being too close to each other.
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
    """Atomic energy miniization.
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

    relaxed_atoms.constraints = FixAtoms(indices=[atom.index for atom in relaxed_atoms if atom.position[2] < relaxed_atoms.cell[2][2] * .5])
    
    dyn = BFGS(relaxed_atoms, trajectory=os.path.join(output_dir, "relax.traj"), logfile="relax.log")
    dyn.run(fmax=0.01)

    return relaxed_atoms

def md_run_atoms(atoms: ase.Atoms, steps: int = 100, temperature_K: float = 300, output_dir='./'):
    """
    THis function runs molecular dynamics at selected temperature for selected number of steps and returns list of frames as ase atoms.
    Args:
        atoms: ase.Atoms, atoms that need to run MD
        steps: int, number of inonic steps in MD
        temperature_K: float, Temperature in K
        
    returns:
        MD_traj: list of ase.Atoms, frames of MD simulation.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    mace_calculator = mace_mp(model="medium", device=str(device), dispersion=False)

    atoms.calc = mace_calculator
    atoms.constraints = FixAtoms(indices=[atom.index for atom in atoms if atom.position[2] < atoms.cell[2][2] * .5])

    MaxwellBoltzmannDistribution(atoms, temperature_K=300)
    
    dyn = Langevin(
        atoms,
        timestep=1.0 * units.fs,         
        temperature_K = temperature_K,   
        friction = 0.002,                
    )

    traj = Trajectory(os.path.join(output_dir, "md.traj"), 'w', atoms)
    dyn.attach(traj.write, interval=1)

    dyn.run(steps)

    MD_traj = read(os.path.join(output_dir, "md.traj"), index=':')
    write(os.path.join(output_dir, "md_traj.xyz"), MD_traj)

    return MD_traj

def save_ase_atoms(atoms: ase.Atoms, filename):
    """ this functions writes ase.atoms to xyz file
    Args:
        atoms: ase.Atoms tobject to be written
        filename: string of where to write ase atoms. must end in '.xyz'
    """
    write(atoms, filename)