#!/usr/bin/env python3
# pylint: disable=redefined-outer-name

"""" OTF Test Case - Bulk Al with a vacancy

Simon Batzner
"""
import os, sys
import json

print("cwd: ", os.getcwd())
sys.path.append('../../modules')
sys.path.append('../../otf_engine')

import numpy as np

from ase.build import *
from ase.spacegroup import crystal
from qe_input import QEInput

from qe_parsers import parse_md_output
from otf import OTF
from parse_relax import parse_pos_relax


def create_structure(el, alat, size, perturb=False, pass_relax=False, pass_pos=None):
    """ Create bulk structure with vacancy, return cell, position, number of atoms"""

    # create bulk cell
    unit_cell = crystal(el, [(0, 0, 0)], spacegroup=225, cellpar=[alat, alat, alat, 90, 90, 90])

    # size of initial perturbation
    pert_size = 0.05 * alat

    # make supercell
    multiplier = np.identity(3) * size
    supercell = make_supercell(unit_cell, multiplier)

    # remove atom
    supercell.pop(supercell.get_number_of_atoms() // 2)

    # get unpertubed positions
    al_pos = np.asarray(supercell.positions)

    if pass_relax:
        al_pos = pass_pos

    if perturb:
        for atom in range(al_pos.shape[0]):
            for coord in range(3):
                al_pos[atom][coord] += np.random.uniform(-pert_size, pert_size)

    cell = supercell.get_cell()
    nat = supercell.get_number_of_atoms()

    return cell, al_pos, nat


def run_test_md(input_file, output_file):
    """ Run test QE MD run """

    input_file_name = '../datasets/Al_vac/Al_scf.in'
    output_file_name = '../datasets/Al_vac/Al_scf.out'
    pw_loc = os.environ['PWSCF_COMMAND']

    qe_command = '{0} < {1} > {2}'.format(pw_loc, input_file_name, output_file_name)
    os.system(qe_command)

    return parse_md_output(output_file_name)


def relax_vac(input_file, output_file):
    """ Relax structure with vacancy """

    pw_loc = os.environ['PWSCF_COMMAND']

    qe_command = '{0} < {1} > {2}'.format(pw_loc, input_file, output_file)
    os.system(qe_command)


def run_otf_md(input_file, output_file):
    """ Run OTF engine with specified QE input file """

    # setup run from QE input file
    al_otf = OTF(qe_input=input_file, dt=0.001, number_of_steps=3, kernel='two_body', cutoff=5)

    # run otf
    al_otf.run()

    return parse_md_output(output_file)


def write_scf_input(input_file, output_file, nat, ecut, cell, pos, nk):
    """ Write QE scf input file from structure and QE params """
    calculation = 'scf'
    pw_loc = os.environ['PWSCF_COMMAND']

    scf_inputs = dict(pseudo_dir=os.environ['ESPRESSO_PSEUDO'],
                      outdir='.',
                      nat=nat,
                      ntyp=1,
                      ecutwfc=ecut,
                      ecutrho=ecut * 4,
                      cell=cell,
                      species=['Al'] * nat,
                      positions=pos,
                      kvec=np.array([nk] * 3),
                      ion_names=['Al'],
                      ion_masses=[26.981539],
                      ion_pseudo=['Al.pz-vbc.UPF'])

    QEInput(input_file, output_file, pw_loc, calculation, scf_inputs)


if __name__ == '__main__':
    workdir = os.getcwd()
    print(os.environ['ESPRESSO_PSEUDO'])
    print(os.environ['PWSCF_COMMAND'])
    print(workdir)

    # params
    el = 'Al'
    size = 2
    ecut = 30
    alat = 3.978153546
    nk = 4

    output_file_name_otf = '../datasets/Al_vac/Al_OTF_pert.out'
    output_file_name_scf = '../datasets/Al_vac/Al_scf_pert.out'
    output_file_name_scf_relax = '../datasets/Al_vac/Al_scf_relax.out'
    input_file_name_scf = '../datasets/Al_vac/Al_scf.in'
    input_file_name_scf_pert = '../datasets/Al_vac/Al_scf_pert.in'
    input_file_name_scf_relax = '../datasets/Al_vac/Al_scf_relax.in'

    # # debug mode
    # local = True
    # ecut = 5
    # nk = 1

    # pos_relax = parse_pos_relax(filename='/Users/simonbatzner1/Desktop/Research/Research_Code/otf/datasets/Al_vac/relaxpos.txt')
    #
    # cell, al_pos, nat = create_structure(el=el, alat=alat, size=size, perturb=True, pass_relax=True, pass_pos=pos_relax)
    #
    # write_scf_input(input_file=input_file_name_scf_pert, output_file=output_file_name_scf, nat=nat, ecut=ecut, cell=cell, pos=al_pos, nk=nk)

    # relax vacancy structure
    # relax_vac(input_file=input_file_name_scf, output_file=output_file_name_scf_relax)

    # run otf
    results = run_otf_md(input_file=input_file_name_scf_pert, output_file=output_file_name_otf)

    with open('al_results.json', 'w') as fp:
        json.dump(results, fp)

