# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

from ramble.appkit import *
from ramble.expander import Expander


class Gromacs(ExecutableApplication):
    """Define a Gromacs application"""

    name = "gromacs"

    maintainers("douglasjacobsen")

    tags("molecular-dynamics")

    with when("package_manager_family=spack"):
        define_compiler("gcc9", pkg_spec="gcc@9.3.0")

        software_spec(
            "impi2018",
            pkg_spec="intel-mpi@2018.4.274",
        )

        with default_args(compiler="gcc9"):
            software_spec(
                "spack_gromacs",
                pkg_spec="gromacs@2020.5",
            )

    software_spec(
        "eessi_gromacs",
        pkg_spec="GROMACS/2024.1-foss-2023b",
        when=["package_manager_family=eessi"],
    )

    executable(
        "pre-process",
        "{grompp} "
        + "-f {input_path}/{type}.mdp "
        + "-c {input_path}/conf.gro "
        + "-p {input_path}/topol.top "
        + "-o exp_input.tpr",
        use_mpi=False,
        output_capture=OUTPUT_CAPTURE.ALL,
    )
    executable(
        "execute-gen",
        "{mdrun} {notunepme} -dlb {dlb} "
        + "{verbose} -resetstep {resetstep} -noconfout -nsteps {nsteps} "
        + "-s exp_input.tpr {additional_args}",
        use_mpi=True,
        output_capture=OUTPUT_CAPTURE.ALL,
    )
    executable(
        "execute",
        "{mdrun} {notunepme} -dlb {dlb} "
        + "{verbose} -resetstep {resetstep} -noconfout -nsteps {nsteps} "
        + "-s {input_path} {additional_args}",
        use_mpi=True,
        output_capture=OUTPUT_CAPTURE.ALL,
    )

    input_file(
        "water_gmx50_bare",
        url="https://ftp.gromacs.org/pub/benchmarks/water_GMX50_bare.tar.gz",
        sha256="2219c10acb97787f80f6638132bad3ff2ca1e68600eef1bc8b89d9560e74c66a",
        description="",
    )
    input_file(
        "water_bare_hbonds",
        url="https://ftp.gromacs.org/pub/benchmarks/water_bare_hbonds.tar.gz",
        sha256="b2e09d30f5c6b00ecf1c13ea6fa715ad132747863ef89f983f6c09a872cf2776",
        description="",
    )
    input_file(
        "lignocellulose",
        url="https://repository.prace-ri.eu/ueabs/GROMACS/1.2/GROMACS_TestCaseB.tar.gz",
        sha256="8a12db0232465e1d47c6a4eb89f615cdbbdc8fc360a86088b131331bd462f35c",
        description="A model of cellulose and lignocellulosic biomass in an aqueous "
        + "solution. This system of 3.3M atoms is inhomogeneous, at "
        + "least with GROMACS 4.5. This system uses reaction-field"
        + "electrostatics instead of PME and therefore should scale well.",
    )
    input_file(
        "HECBioSim",
        url="https://github.com/victorusu/GROMACS_Benchmark_Suite/archive/refs/tags/1.0.0.tar.gz",
        sha256="9cb2ad61ec2a422fc33578047e7cb2fd2c37ae9a75a6162d662fa2b711e9737f",
        description="https://www.hecbiosim.ac.uk/access-hpc/benchmarks",
    )

    input_file(
        "BenchPEP",
        url="https://www.mpinat.mpg.de/benchPEP.zip",
        sha256="f11745201dbb9e6a29a39cb016ee8123f6b0f519b250c94660f0a9623e497b22",
        description="12M Atoms, Peptides in Water, 2fs time step, all bonds constrained. https://www.mpinat.mpg.de/grubmueller/bench",
    )

    input_file(
        "BenchPEP_h",
        url="https://www.mpinat.mpg.de/benchPEP-h.zip",
        sha256="3ca8902fd9a6cf005b266f83b57217397b4ba4af987b97dc01e04185bd098bce",
        description="12M Atoms, Peptides in Water, 2fs time step, h-bonds constrained. https://www.mpinat.mpg.de/grubmueller/bench",
    )

    input_file(
        "BenchMEM",
        url="https://www.mpinat.mpg.de/benchMEM.zip",
        sha256="3c1c8cd4f274d532f48c4668e1490d389486850d6b3b258dfad4581aa11380a4",
        description="82k atoms, protein in membrane surrounded by water, 2 fs time step. https://www.mpinat.mpg.de/grubmueller/bench",
    )

    input_file(
        "BenchRIB",
        url="https://www.mpinat.mpg.de/benchRIB.zip",
        sha256="39acb014a79ed9a9ff2ad6294a2c09f9b85ea6986dfc204a3639814503eeb60a",
        description="2 M atoms, ribosome in water, 4 fs time step. https://www.mpinat.mpg.de/grubmueller/bench",
    )

    input_file(
        "JCP_benchmarks",
        url="https://zenodo.org/record/3893789/files/GROMACS_heterogeneous_parallelization_benchmark_info_and_systems_JCP.tar.gz?download=1",
        sha256="82449291f44f4d5b7e5c192d688b57b7c2a2e267fe8b12e7a15b5d68f96c7b20",
        description="GROMACS_heterogeneous_parallelization_benchmark_info_and_systems_JCP",
    )

    workload(
        "water_gmx50",
        executables=["pre-process", "execute-gen"],
        input="water_gmx50_bare",
    )
    workload(
        "water_bare",
        executables=["pre-process", "execute-gen"],
        input="water_bare_hbonds",
    )
    workload("lignocellulose", executables=["execute"], input="lignocellulose")
    workload("hecbiosim", executables=["execute"], input="HECBioSim")
    workload("benchpep", executables=["execute"], input="BenchPEP")
    workload("benchpep_h", executables=["execute"], input="BenchPEP_h")
    workload("benchmem", executables=["execute"], input="BenchMEM")
    workload("benchrib", executables=["execute"], input="BenchRIB")
    workload(
        "stmv_rf",
        executables=["pre-process", "execute-gen"],
        input="JCP_benchmarks",
    )
    workload(
        "stmv_pme",
        executables=["pre-process", "execute-gen"],
        input="JCP_benchmarks",
    )
    workload(
        "rnase_cubic",
        executables=["pre-process", "execute-gen"],
        input="JCP_benchmarks",
    )
    workload(
        "ion_channel",
        executables=["pre-process", "execute-gen"],
        input="JCP_benchmarks",
    )
    workload(
        "adh_dodec",
        executables=["pre-process", "execute-gen"],
        input="JCP_benchmarks",
    )

    workload_group(
        "all_workloads",
        workloads=[
            "water_gmx50",
            "water_bare",
            "lignocellulose",
            "hecbiosim",
            "benchpep",
            "benchpep_h",
            "benchmem",
            "benchrib",
            "stmv_rf",
            "stmv_pme",
            "rnase_cubic",
            "ion_channel",
            "adh_dodec",
        ],
    )

    workload_variable(
        "single_rank_mpi_command",
        default="",
        description="Job scheduler command for running on a single mpi rank",
        workload_group="all_workloads",
    )

    workload_variable(
        "additional_args",
        default="",
        description="Additiaonl Exec Args",
        workload_group="all_workloads",
    )
    workload_variable(
        "gmx",
        default="gmx_mpi",
        description="Name of the gromacs binary",
        workload_group="all_workloads",
    )
    workload_variable(
        "grompp",
        default="{single_rank_mpi_command} {gmx} grompp",
        description="How to run grompp",
        workload_group="all_workloads",
    )
    workload_variable(
        "mdrun",
        default="{gmx} mdrun",
        description="How to run mdrun",
        workload_group="all_workloads",
    )
    workload_variable(
        "nsteps",
        default=str(20000),
        description="Simulation steps",
        workload_group="all_workloads",
    )
    workload_variable(
        "resetstep",
        default="{str(int(0.9*{nsteps}))}",
        description="Reset performance counters at this step",
        workload_group="all_workloads",
    )
    workload_variable(
        "verbose",
        default="",
        values=["", "-v"],
        description="Set to empty string to run without verbose mode",
        workload_group="all_workloads",
    )
    workload_variable(
        "notunepme",
        default="-notunepme",
        values=["", "-notunepme"],
        description="Whether to set -notunepme for mdrun",
        workload_group="all_workloads",
    )
    workload_variable(
        "dlb",
        default="yes",
        values=["yes", "no", "auto"],
        description="Whether to use dynamic load balancing for mdrun",
        workload_group="all_workloads",
    )

    workload_variable(
        "size",
        default="1536",
        values=[
            "0000.65",
            "0000.96",
            "0001.5",
            "0003",
            "0006",
            "0012",
            "0024",
            "0048",
            "0096",
            "0192",
            "0384",
            "0768",
            "1536",
            "3072",
        ],
        description="Workload size",
        workloads=["water_gmx50", "water_bare"],
        expandable=False,
    )
    workload_variable(
        "type",
        default="pme",
        description="Workload type.",
        values=["pme", "rf"],
        workloads=["water_gmx50", "water_bare"],
    )
    workload_variable(
        "input_path",
        default="{water_gmx50_bare}/{size}",
        description="Input path for water GMX50",
        workload="water_gmx50",
    )
    workload_variable(
        "input_path",
        default="{water_bare_hbonds}/{size}",
        description="Input path for water bare hbonds",
        workload="water_bare",
    )
    workload_variable(
        "input_path",
        default="{lignocellulose}/lignocellulose-rf.tpr",
        description="Input path for lignocellulose",
        workload="lignocellulose",
    )
    workload_variable(
        "type",
        default="Crambin",
        description="Workload type. Valid values are "
        "Crambin"
        ", "
        "Glutamine-Binding-Protein"
        ", "
        "hEGFRDimer"
        ", "
        "hEGFRDimerPair"
        ", "
        "hEGFRDimerSmallerPL"
        ", "
        "hEGFRtetramerPair"
        "",
        workload="hecbiosim",
    )
    workload_variable(
        "input_path",
        default="{HECBioSim}/HECBioSim/{type}/benchmark.tpr",
        description="Input path for hecbiosim",
        workload="hecbiosim",
    )
    workload_variable(
        "input_path",
        default="{BenchPEP}/benchPEP.tpr",
        description="Input path for Bench PEP workload",
        workload="benchpep",
    )
    workload_variable(
        "input_path",
        default="{BenchMEM}/benchMEM.tpr",
        description="Input path for Bench MEM workload",
        workload="benchmem",
    )
    workload_variable(
        "input_path",
        default="{BenchRIB}/benchRIB.tpr",
        description="Input path for Bench RIB workload",
        workload="benchrib",
    )
    workload_variable(
        "input_path",
        default="{BenchPEP_h}/benchPEP-h.tpr",
        description="Input path for Bench PEP-h workload",
        workload="benchpep_h",
    )
    workload_variable(
        "type",
        default="rf_nvt",
        description="Workload type for JCP_benchmarks",
        workload="stmv_rf",
    )
    workload_variable(
        "type",
        default="pme_nvt",
        description="Workload type for JCP_benchmarks",
        workload="stmv_pme",
    )
    workload_variable(
        "type",
        default="grompp",
        description="Workload type for JCP_benchmarks",
        workloads=["ion_channel", "rnase_cubic"],
    )
    workload_variable(
        "input_path",
        default="{JCP_benchmarks}/stmv",
        description="Input path for JCP_benchmark {workload_name}",
        workloads=["stmv_rf", "stmv_pme"],
    )
    workload_variable(
        "input_path",
        default="{JCP_benchmarks}/{workload_name}",
        description="Input path for JCP_benchmark {workload_name}",
        workloads=["ion_channel", "rnase_cubic"],
    )
    workload_variable(
        "input_path",
        default="{JCP_benchmarks}/{workload_name}",
        description="Input path for JCP_benchmark {workload_name}",
        workloads=["adh_dodec"],
    )
    workload_variable(
        "type",
        default="pme_verlet",
        description="Workload type for JCP_benchmarks",
        workloads=["adh_dodec"],
    )

    log_str = os.path.join(
        Expander.expansion_str("experiment_run_dir"), "md.log"
    )

    figure_of_merit(
        "Core Time",
        log_file=log_str,
        fom_regex=r"\s+Time:\s+(?P<core_time>[0-9]+\.[0-9]+)",
        group_name="core_time",
        units="s",
        fom_type=FomType.TIME,
    )

    figure_of_merit(
        "Wall Time",
        log_file=log_str,
        fom_regex=r"\s+Time:\s+[0-9]+\.[0-9]+\s+"
        + r"(?P<wall_time>[0-9]+\.[0-9]+)",
        group_name="wall_time",
        units="s",
        fom_type=FomType.TIME,
    )

    figure_of_merit(
        "Percent Core Time",
        log_file=log_str,
        fom_regex=r"\s+Time:\s+[0-9]+\.[0-9]+\s+[0-9]+\.[0-9]+\s+"
        + r"(?P<perc_core_time>[0-9]+\.[0-9]+)",
        group_name="perc_core_time",
        units="%",
        fom_type=FomType.MEASURE,
    )

    figure_of_merit(
        "Nanosecs per day",
        log_file=log_str,
        fom_regex=r"Performance:\s+" + r"(?P<ns_per_day>[0-9]+\.[0-9]+)",
        group_name="ns_per_day",
        units="ns/day",
        fom_type=FomType.THROUGHPUT,
    )

    figure_of_merit(
        "Hours per nanosec",
        log_file=log_str,
        fom_regex=r"Performance:\s+[0-9]+\.[0-9]+\s+"
        + r"(?P<hours_per_ns>[0-9]+\.[0-9]+)",
        group_name="hours_per_ns",
        units="hours/ns",
        fom_type=FomType.INFO,
    )
