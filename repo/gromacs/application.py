# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

from ramble.appkit import *
from ramble.expander import Expander


class Gromacs(ExecutableApplication):
    '''Define a Gromacs application'''
    name = 'gromacs'

    maintainers('douglasjacobsen')

    tags('molecular-dynamics')

    define_compiler('gcc9', pkg_spec='gcc@9.3.0', package_manager='spack*')
    software_spec('impi2018', pkg_spec='intel-mpi@2018.4.274', package_manager='spack*')
    software_spec('gromacs', pkg_spec='gromacs@2023.3', compiler='gcc12', package_manager='spack*')

    executable('pre-process', 'gmx_mpi grompp ' +
               '-f {input_path}/{type}.mdp ' +
               '-c {input_path}/conf.gro ' +
               '-p {input_path}/topol.top ' +
               '-o exp_input.tpr', use_mpi=False)
    executable('execute-nsteps-gen', 'gmx_mpi mdrun -notunepme ' +
               '-v -resethway -noconfout -nsteps 4000 ' +
               '-s exp_input.tpr', use_mpi=True)
    executable('execute-nsteps', 'gmx_mpi mdrun -notunepme ' +
               '-v -resethway -noconfout -nsteps 4000 ' +
               '-s {input_path}', use_mpi=True)
    executable('execute-adac', 'gmx_mpi mdrun ' +
               '-resethway -noconfout -dlb {dlb} -pin {pin} -nb {nb} -pme {pme} -bonded {bonded} -update {update} ' +
               '-maxh {maxh} -nsteps {nsteps} -notunepme -nstlist {nstlist} -npme {npme} ' +
               '-v -s exp_input.tpr', use_mpi=True)

    input_file('water_gmx50_bare', url='https://ftp.gromacs.org/pub/benchmarks/water_GMX50_bare.tar.gz',
               sha256='2219c10acb97787f80f6638132bad3ff2ca1e68600eef1bc8b89d9560e74c66a',
               description='')
    input_file('water_bare_hbonds', url='https://ftp.gromacs.org/pub/benchmarks/water_bare_hbonds.tar.gz',
               sha256='b2e09d30f5c6b00ecf1c13ea6fa715ad132747863ef89f983f6c09a872cf2776',
               description='')
    input_file('lignocellulose',
               url='https://repository.prace-ri.eu/ueabs/GROMACS/1.2/GROMACS_TestCaseB.tar.gz',
               sha256='8a12db0232465e1d47c6a4eb89f615cdbbdc8fc360a86088b131331bd462f35c',
               description='A model of cellulose and lignocellulosic biomass in an aqueous ' +
                           'solution. This system of 3.3M atoms is inhomogeneous, at ' +
                           'least with GROMACS 4.5. This system uses reaction-field' +
                           'electrostatics instead of PME and therefore should scale well.')
    input_file('HECBioSim',
               url='https://github.com/victorusu/GROMACS_Benchmark_Suite/archive/refs/tags/1.0.0.tar.gz',
               sha256='9cb2ad61ec2a422fc33578047e7cb2fd2c37ae9a75a6162d662fa2b711e9737f',
               description='https://www.hecbiosim.ac.uk/access-hpc/benchmarks')

    input_file('BenchPEP', url='https://www.mpinat.mpg.de/benchPEP.zip',
               sha256='f11745201dbb9e6a29a39cb016ee8123f6b0f519b250c94660f0a9623e497b22',
               description='12M Atoms, Peptides in Water, 2fs time step, all bonds constrained. https://www.mpinat.mpg.de/grubmueller/bench')

    input_file('BenchPEP_h', url='https://www.mpinat.mpg.de/benchPEP-h.zip',
               sha256='3ca8902fd9a6cf005b266f83b57217397b4ba4af987b97dc01e04185bd098bce',
               description='12M Atoms, Peptides in Water, 2fs time step, h-bonds constrained. https://www.mpinat.mpg.de/grubmueller/bench')

    input_file('BenchMEM', url='https://www.mpinat.mpg.de/benchMEM.zip',
               sha256='3c1c8cd4f274d532f48c4668e1490d389486850d6b3b258dfad4581aa11380a4',
               description='82k atoms, protein in membrane surrounded by water, 2 fs time step. https://www.mpinat.mpg.de/grubmueller/bench')

    input_file('BenchRIB', url='https://www.mpinat.mpg.de/benchRIB.zip',
               sha256='39acb014a79ed9a9ff2ad6294a2c09f9b85ea6986dfc204a3639814503eeb60a',
               description='2 M atoms, ribosome in water, 4 fs time step. https://www.mpinat.mpg.de/grubmueller/bench')

    input_file('JCP_benchmarks',
               url='https://zenodo.org/record/3893789/files/GROMACS_heterogeneous_parallelization_benchmark_info_and_systems_JCP.tar.gz?download=1',
               sha256='82449291f44f4d5b7e5c192d688b57b7c2a2e267fe8b12e7a15b5d68f96c7b20',
               description='GROMACS_heterogeneous_parallelization_benchmark_info_and_systems_JCP')

    workload('water_gmx50_adac', executables=['pre-process', 'execute-adac'],
             input='water_gmx50_bare')
    workload('water_gmx50', executables=['pre-process', 'execute-gen'],
             input='water_gmx50_bare')
    workload('water_bare', executables=['pre-process', 'execute-gen'],
             input='water_bare_hbonds')
    workload('lignocellulose', executables=['execute'],
             input='lignocellulose')
    workload('hecbiosim', executables=['execute'],
             input='HECBioSim')
    workload('benchpep', executables=['execute'],
             input='BenchPEP')
    workload('benchpep_h', executables=['execute'],
             input='BenchPEP_h')
    workload('benchmem', executables=['execute'],
             input='BenchMEM')
    workload('benchrib', executables=['execute'],
             input='BenchRIB')
    workload('stmv_rf', executables=['pre-process', 'execute-gen'],
             input='JCP_benchmarks')
    workload('stmv_pme', executables=['pre-process', 'execute-gen'],
             input='JCP_benchmarks')
    workload('rnase_cubic', executables=['pre-process', 'execute-gen'],
             input='JCP_benchmarks')
    workload('ion_channel', executables=['pre-process', 'execute-gen'],
             input='JCP_benchmarks')

    workload_variable('dlb', default='no',
                      description='Dynamic load balancing (with DD): auto, no, yes',
                      workloads=['water_gmx50_adac'])
    workload_variable('pin', default='off',
                      description='Whether mdrun should try to set thread affinities: auto, on, off',
                      workloads=['water_gmx50_adac'])
    workload_variable('nb', default='auto',
                      description='Calculate non-bonded interactions on: auto, cpu, gpu',
                      workloads=['water_gmx50_adac'])
    workload_variable('pme', default='auto',
                      description='Perform PME calculations on: auto, cpu, gpu',
                      workloads=['water_gmx50_adac'])
    workload_variable('bonded', default='auto',
                      description='Perform bonded calculations on: auto, cpu, gpu',
                      workloads=['water_gmx50_adac'])
    workload_variable('update', default='auto',
                      description='Perform update and constraints on: auto, cpu, gpu',
                      workloads=['water_gmx50_adac'])
    workload_variable('maxh', default='0.05',
                      description='Terminate after 0.99 times this time (hours)',
                      workloads=['water_gmx50_adac'])
    workload_variable('nsteps', default='-1',
                      description='Run this number of steps (-1 means infinite, -2 means use mdp option, smaller is invalid)',
                      workloads=['water_gmx50_adac'])
    workload_variable('nstlist', default='200',
                      description='Set nstlist when using a Verlet buffer tolerance (0 is guess)',
                      workloads=['water_gmx50_adac'])
    workload_variable('npme', default='0',
                      description='Number of separate ranks to be used for PME, -1 is guess',
                      workloads=['water_gmx50_adac'])

    workload_variable('size', default='1536',
                      values=['0000.65', '0000.96', '0001.5',
                              '0003', '0006', '0012', '0024',
                              '0048', '0096', '0192', '0384',
                              '0768', '1536', '3072'],
                      description='Workload size',
                      workloads=['water_gmx50', 'water_bare', 'water_gmx50_adac'])
    workload_variable('type', default='pme',
                      description='Workload type.',
                      values=['pme', 'rf'],
                      workloads=['water_gmx50', 'water_bare', 'water_gmx50_adac'])
    workload_variable('input_path', default='{water_gmx50_bare}/{size}',
                      description='Input path for water GMX50',
                      workloads=['water_gmx50', 'water_gmx50_adac'])
    workload_variable('input_path', default='{water_bare_hbonds}/{size}',
                      description='Input path for water bare hbonds',
                      workload='water_bare')
    workload_variable('input_path', default='{lignocellulose}/lignocellulose-rf.tpr',
                      description='Input path for lignocellulose',
                      workload='lignocellulose')
    workload_variable('type', default='Crambin',
                      description='Workload type. Valid values are ''Crambin'', ''Glutamine-Binding-Protein'', ''hEGFRDimer'', ''hEGFRDimerPair'', ''hEGFRDimerSmallerPL'', ''hEGFRtetramerPair''',
                      workload='hecbiosim')
    workload_variable('input_path', default='{HECBioSim}/HECBioSim/{type}/benchmark.tpr',
                      description='Input path for hecbiosim',
                      workload='hecbiosim')
    workload_variable('input_path', default='{BenchPEP}/benchPEP.tpr',
                      description='Input path for Bench PEP workload',
                      workload='benchpep')
    workload_variable('input_path', default='{BenchMEM}/benchMEM.tpr',
                      description='Input path for Bench MEM workload',
                      workload='benchmem')
    workload_variable('input_path', default='{BenchRIB}/benchRIB.tpr',
                      description='Input path for Bench RIB workload',
                      workload='benchrib')
    workload_variable('input_path', default='{BenchPEP_h}/benchPEP-h.tpr',
                      description='Input path for Bench PEP-h workload',
                      workload='benchpep_h')
    workload_variable('type', default='rf_nvt',
                      description='Workload type for JCP_benchmarks',
                      workload='stmv_rf')
    workload_variable('type', default='pme_nvt',
                      description='Workload type for JCP_benchmarks',
                      workload='stmv_pme')
    workload_variable('type', default='grompp',
                      description='Workload type for JCP_benchmarks',
                      workloads=['ion_channel', 'rnase_cubic'])
    workload_variable('input_path', default='{JCP_benchmarks}/stmv',
                      description='Input path for JCP_benchmark {workload_name}',
                      workloads=['stmv_rf', 'stmv_pme'])
    workload_variable('input_path', default='{JCP_benchmarks}/{workload_name}',
                      description='Input path for JCP_benchmark {workload_name}',
                      workloads=['ion_channel', 'rnase_cubic'])

    log_str = os.path.join(Expander.expansion_str('experiment_run_dir'),
                           'md.log')

    figure_of_merit('Core Time', log_file=log_str,
                    fom_regex=r'\s+Time:\s+(?P<core_time>[0-9]+\.[0-9]+).*',
                    group_name='core_time', units='s')

    figure_of_merit('Wall Time', log_file=log_str,
                    fom_regex=r'\s+Time:\s+[0-9]+\.[0-9]+\s+' +
                              r'(?P<wall_time>[0-9]+\.[0-9]+).*',
                    group_name='wall_time', units='s')

    figure_of_merit('Percent Core Time', log_file=log_str,
                    fom_regex=r'\s+Time:\s+[0-9]+\.[0-9]+\s+[0-9]+\.[0-9]+\s+' +
                              r'(?P<perc_core_time>[0-9]+\.[0-9]+).*',
                    group_name='perc_core_time', units='%')

    figure_of_merit('Nanosecs per day', log_file=log_str,
                    fom_regex=r'Performance:\s+' +
                              r'(?P<ns_per_day>[0-9]+\.[0-9]+).*',
                    group_name='ns_per_day', units='ns/day')

    figure_of_merit('Hours per nanosec', log_file=log_str,
                    fom_regex=r'Performance:\s+[0-9]+\.[0-9]+\s+' +
                              r'(?P<hours_per_ns>[0-9]+\.[0-9]+).*',
                    group_name='hours_per_ns', units='hours/ns')
