# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import sys

from ramble.appkit import *


class Lammps(ExecutableApplication):
    """Define LAMMPS application"""

    name = "lammps"

    maintainers("douglasjacobsen")

    tags('chemistry','material-science','molecular-dynamics',
         'fft','particles','nbody','spatial-discretization',
         'large-scale','multi-node','single-node','sub-node',
         'mpi','network-collectives','network-point-to-point',
         'c++','python','kokkos','vectorization')

    define_compiler("gcc9", pkg_spec="gcc@9.3.0")

    with when("package_manager_family=spack"):
        software_spec("impi2018", pkg_spec="intel-mpi@2018.4.274")

        software_spec(
            "lammps",
            pkg_spec="lammps@20220623.4 +opt+manybody+molecule+kspace+rigid+openmp+openmp-package+asphere+dpd-basic+dpd-meso+dpd-react+dpd-smooth",
            compiler="gcc9",
        )

        required_package("lammps")

    input_file(
        "leonard-jones",
        url="https://www.lammps.org/inputs/in.lj.txt",
        expand=False,
        sha256="874b4c63b6fcbb6ede76522df19087acf2f49b6bc96794cf0aa3218c66ff7e06",
        description="Atomic fluid. 32k atoms. 100 timesteps. https://www.lammps.org/bench.html#lj",
    )
    input_file(
        "eam",
        url="https://www.lammps.org/inputs/in.eam.txt",
        expand=False,
        sha256="2fa09183c626c34570cc367384fe4c297ab153521adb3ea44ff7e265d451ad75",
        description="Cu metallic solid with embedded atom method potential. 32k atoms. https://www.lammps.org/bench.html#eam",
    )
    input_file(
        "polymer-chain-melt",
        url="https://www.lammps.org/inputs/in.chain.txt",
        expand=False,
        sha256="97676f19d2d791c42415698c354a18b26a3cbe4006cd2161cf8924415d9f7c82",
        description="Bead-spring polymer melt with 100-mer chains and FENE bonds. 32k atoms. 100 timesteps. https://www.lammps.org/bench.html#chain",
    )
    input_file(
        "chute",
        url="https://www.lammps.org/inputs/in.chute.txt",
        expand=False,
        sha256="91e1743cc39365b32757cfb3c76399f5ed8debad0b890cb36ee7bdf47d2dfd2d",
        description="Chute flow of packed granular particles with frictional history potential. 32k atoms. 100 timeteps. https://www.lammps.org/bench.html#chute",
    )
    input_file(
        "rhodo",
        url="https://www.lammps.org/inputs/in.rhodo.txt",
        expand=False,
        sha256="4b6cc70db1b8fe269c48b8e06749f144f400e9a4054bf180ac9b1b9a5a5bb07f",
        description="All-atom rhodopsin protein in solvated lipid bilayer with CHARMM force field, long-range Coulombics via PPPM (particle-particle particle mesh), SHAKE constraints. This model contains counter-ions and a reduced amount of water to make a 32K atom system. 32k atoms. 100 timesteps. https://www.lammps.org/bench.html#rhodo",
    )

    executable(
        "copy",
        template=["cp {input_path} {experiment_run_dir}/input.txt"],
        use_mpi=False,
    )
    executable(
        "set-size",
        template=[
            "sed -i -e 's/xx equal .*/xx equal {xx}/g' -i input.txt",
            "sed -i -e 's/yy equal .*/yy equal {yy}/g' -i input.txt",
            "sed -i -e 's/zz equal .*/zz equal {zz}/g' -i input.txt",
        ],
        use_mpi=False,
    )
    executable(
        "set-timesteps",
        template=["sed 's/run.*[0-9]+/run\t\t{timesteps}/g' -i input.txt"],
        use_mpi=False,
    )

    exec_path = os.path.join("{lammps_path}", "bin", "lmp")
    executable(
        "execute",
        f"{exec_path}" + " -i input.txt {lammps_flags}",
        use_mpi=True,
    )

    executable(
        "set-data-path",
        template=[
            r"sed 's|data\.|"
            + os.path.join("{lammps}/src", "bench", "data.")
            + "|g' -i input.txt"
        ],
        use_mpi=False,
    )

    workload(
        "lj",
        executables=["copy", "set-size", "set-timesteps", "execute"],
        input="leonard-jones",
    )
    workload(
        "eam",
        executables=["copy", "set-size", "set-timesteps", "execute"],
        input="eam",
    )
    workload(
        "chain",
        executables=["copy", "set-timesteps", "set-data-path", "execute"],
        inputs=["polymer-chain-melt"],
    )
    workload(
        "chute",
        executables=["copy", "set-timesteps", "execute"],
        input="chute",
    )
    workload(
        "rhodo",
        executables=["copy", "set-timesteps", "set-data-path", "execute"],
        inputs=["rhodo"],
    )

    workload_variable(
        "xx",
        default="20*$x",
        description="Number of atoms in the x direction",
        workloads=["lj", "eam"],
    )
    workload_variable(
        "yy",
        default="20*$y",
        description="Number of atoms in the y direction",
        workloads=["lj", "eam"],
    )
    workload_variable(
        "zz",
        default="20*$z",
        description="Number of atoms in the z direction",
        workloads=["lj", "eam"],
    )
    workload_variable(
        "timesteps",
        default="100",
        description="Number of timesteps",
        workloads=["lj", "eam", "chain", "chute", "rhodo"],
    )

    workload_variable(
        "input_path",
        default="{workload_input_dir}/in.{workload_name}.txt",
        description="Path for the workload input file.",
        workloads=["lj", "eam", "chain", "chute", "rhodo"],
    )

    workload_variable(
        "lammps_flags",
        default="",
        description="Additional execution flags for lammps",
        workloads=["lj", "eam", "chain", "chute", "rhodo"],
    )

    intel_wl_names = [
        "airebo",
        "dpd",
        "eam",
        "lc",
        "lj",
        "rhodo",
        "sw",
        "tersoff",
        "water",
    ]

    executable(
        "change-root",
        template=[
            "sed 's|${root}|{lammps}/src" + os.path.sep + "|g' -i input.txt"
        ],
        use_mpi=False,
    )
    intel_test_path = os.path.join("{lammps}/src", "src", "INTEL", "TEST")
    executable(
        "copy-cube",
        template=[
            "cp "
            + os.path.join(intel_test_path, "mW*.data")
            + " {experiment_run_dir}"
            + os.path.sep
            + "."
            "cp "
            + os.path.join(intel_test_path, "mW.sw")
            + " {experiment_run_dir}"
            + os.path.sep
            + "."
        ],
        use_mpi=False,
    )

    for wl_name in intel_wl_names:
        workload_name = f"intel.{wl_name}"
        if wl_name in ["water"]:
            workload(
                workload_name,
                executables=["copy", "copy-cube", "change-root", "execute"],
            )
        elif wl_name in ["rhodo", "chain"]:
            workload(
                workload_name,
                executables=[
                    "copy",
                    "set-data-path",
                    "change-root",
                    "execute",
                ],
            )
        else:
            workload(
                workload_name,
                executables=["copy", "change-root", "execute"],
            )

        workload_variable(
            "input_path",
            default=os.path.join(f"{intel_test_path}", f"in.{workload_name}"),
            description=f"Path to input file for {workload_name} workload",
            workloads=[workload_name],
        )

        workload_variable(
            "lammps_flags",
            default="",
            description="Additional execution flags for lammps",
            workloads=[workload_name],
        )

    intel_test_path = os.path.join(
        "{lammps}/src", "examples", "reaxff", "HNS"
    )
    executable(
        "copy-contents",
        template=[
            "cp {input_path}/* {experiment_run_dir}/.",
            "cp {input_file} input.txt",
        ],
        use_mpi=False,
    )

    workload(
        "hns-reaxff",
        executables=["copy-contents", "set-timesteps", "execute"],
    )

    workload_variable(
        "input_file",
        default="in.reaxff.hns",
        description="hns-reaxff input file name",
        workloads=["hns-reaxff"],
    )

    workload_variable(
        "input_path",
        default=os.path.join(f"{intel_test_path}"),
        description="Path to input directory for hns-reaxff workload",
        workloads=["hns-reaxff"],
    )
    workload_variable(
        "lammps_flags",
        default="",
        description="Additional execution flags for lammps",
        workloads=["hns-reaxff"],
    )

    pace_input_test_path = os.path.join(
        "{lammps}/src", "examples", "PACKAGES", "pace"
    )

    executable(
        "set-lattice",
        template=[
            "sed -i -e 's/a equal .*/a equal {lc}/g' -i input.txt",
            "sed -i -e 's/lattice .*/lattice {lattice} $a/g' -i input.txt",
        ],
        use_mpi=False,
    )

    executable(
        "set-size",
        template=[
            "sed -i -e 's/box block .*/box block 0 {x} 0 {y} 0 {z}/g' -i input.txt",
        ],
        use_mpi=False,
    )

    workload(
        "pace",
        executables=["copy-contents", "set-lattice", "set-size", "set-timesteps", "execute"],
    )

    workload_variable(
        "lc",
        default="3.597",
        description="Lattice constant",
        workloads=["pace"],
    )

    workload_variable(
        "lattice",
        default="fcc",
        description="Lattice type",
        workloads=["pace"],
    )

    workload_variable(
        "x",
        default="4",
        description="Unit cells in the x direction",
        workloads=["pace"],
    )

    workload_variable(
        "y",
        default="4",
        description="Unit cells in the y direction",
        workloads=["pace"],
    )

    workload_variable(
        "z",
        default="4",
        description="Unit cells in the z direction",
        workloads=["pace"],
    )

    workload_variable(
        "input_file",
        default="in.pace.product",
        description="PACE input file name",
        workloads=["pace"],
    )

    workload_variable(
        "input_path",
        default=os.path.join(f"{pace_input_test_path}"),
        description="Path to input directory for pace workload",
        workloads=["pace"],
    )

    workload_variable(
        "timesteps",
        default="100",
        description="Number of timesteps",
        workloads=["pace"],
    )

    workload_variable(
        "lammps_flags",
        default="",
        description="Additional execution flags for lammps",
        workloads=["pace"],
    )

    success_criteria(
        "walltime",
        mode="string",
        match=r"\s*Total wall time",
        file="{log_file}",
    )

    figure_of_merit(
        "Total wall time",
        fom_regex=r"Total wall time.*\s+(?P<walltime>[0-9:]+)",
        group_name="walltime",
        units="",
        fom_type=FomType.TIME,
    )
    figure_of_merit(
        "Nanoseconds per day",
        fom_regex=r"Performance.*?\s+(?P<nspd>[0-9\.]+) (ns|tau)/day",
        group_name="nspd",
        units="ns/day",
        fom_type=FomType.THROUGHPUT,
    )
    figure_of_merit(
        "Hours per nanosecond",
        fom_regex=r"Performance.*?\s+(?P<hpns>[0-9\.]+) hours/ns",
        group_name="hpns",
        units="hours/ns",
        fom_type=FomType.TIME,
    )
    figure_of_merit(
        "Timesteps per second",
        fom_regex=r"Performance.*?\s+(?P<tsps>[0-9\.]+) timesteps/s",
        group_name="tsps",
        units="timesteps/s",
        fom_type=FomType.THROUGHPUT,
    )

    for func_name in ["Pair", "Neigh", "Comm", "Output", "Modifier"]:
        func_time_regex = (
            func_name
            + r"\s+\|\s+(?P<min_time>\S+)\s+\|\s+(?P<avg_time>\S+)\s+\|\s+(?P<max_time>\S+)\s+\|\s+(?P<avg_var>\S+)\s+\|\s+(?P<total_pct>\S+)"
        )
        figure_of_merit(
            f"{func_name} min time",
            fom_regex=func_time_regex,
            group_name="min_time",
            units="s",
        )

        figure_of_merit(
            f"{func_name} avg time",
            fom_regex=func_time_regex,
            group_name="avg_time",
            units="s",
        )

        figure_of_merit(
            f"{func_name} max time",
            fom_regex=func_time_regex,
            group_name="max_time",
            units="s",
        )

        figure_of_merit(
            f"{func_name} avg. variance",
            fom_regex=func_time_regex,
            group_name="avg_var",
            units="",
        )

        figure_of_merit(
            f"{func_name} percent of runtime",
            fom_regex=func_time_regex,
            group_name="total_pct",
            units="%",
        )
