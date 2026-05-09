# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

from ramble.appkit import *
from ramble.expander import Expander


class Hpcg(ExecutableApplication):
    """Define HPCG application"""

    name = "hpcg"

    maintainers("douglasjacobsen")

    tags = ['synthetic',
            'conjugate-gradient','solver','sparse-linear-algebra',
            'large-scale',
            'mpi','network-point-to-point',
            'c++']

    executable("execute", "xhpcg", use_mpi=True)

    executable("move-log", "mv {experiment_run_dir}/HPCG-Benchmark*.txt {out_file}", use_mpi=False)

    workload("standard", executables=["execute", "move-log"])

    workload_variable(
        "matrix_size",
        default="104 104 104",
        description="Dimensions of the matrix to use",
        workloads=["standard"],
    )

    workload_variable(
        "iterations",
        default="60",
        description="Number of iterations to perform",
        workloads=["standard"],
    )

    workload_variable(
        "out_file",
        default="{experiment_run_dir}/{experiment_name}.out",
        description="Output file for results",
        workloads=["standard"],
    )

    log_str = Expander.expansion_str("out_file")

    figure_of_merit(
        "Status",
        log_file=log_str,
        fom_regex=r"Final Summary::HPCG result is (?P<status>[a-zA-Z]+) with a GFLOP/s rating of=(?P<gflops>[0-9]+\.[0-9]+)",
        group_name="status",
        units="",
    )

    figure_of_merit(
        "Gflops",
        log_file=log_str,
        fom_regex=r"Final Summary::HPCG result is (?P<status>[a-zA-Z]+) with a GFLOP/s rating of=(?P<gflops>[0-9]+\.[0-9]+)",
        group_name="gflops",
        units="GFLOP/s",
    )

    figure_of_merit(
        "Time",
        log_file=log_str,
        fom_regex=r"Final Summary::Results are.* execution time.*is=(?P<exec_time>[0-9]+\.[0-9]*)",
        group_name="exec_time",
        units="s",
    )

    figure_of_merit(
        "ComputeDotProductMsg",
        log_file=log_str,
        fom_regex=r"Final Summary::Reference version of ComputeDotProduct used.*=(?P<msg>.*)",
        group_name="msg",
        units="",
    )

    figure_of_merit(
        "ComputeSPMVMsg",
        log_file=log_str,
        fom_regex=r"Final Summary::Reference version of ComputeSPMV used.*=(?P<msg>.*)",
        group_name="msg",
        units="",
    )

    figure_of_merit(
        "ComputeMGMsg",
        log_file=log_str,
        fom_regex=r"Final Summary::Reference version of ComputeMG used.*=(?P<msg>.*)",
        group_name="msg",
        units="",
    )

    figure_of_merit(
        "ComputeWAXPBYMsg",
        log_file=log_str,
        fom_regex=r"Final Summary::Reference version of ComputeWAXPBY used.*=(?P<msg>.*)",
        group_name="msg",
        units="",
    )

    figure_of_merit(
        "HPCG 2.4 Rating",
        log_file=log_str,
        fom_regex=r"Final Summary::HPCG 2\.4 rating.*=(?P<rating>[0-9]+\.*[0-9]*)",
        group_name="rating",
        units="",
    )

    def _make_experiments(self, workspace, app_inst=None):
        super()._make_experiments(workspace)

        input_path = os.path.join(
            self.expander.expand_var_name("experiment_run_dir"), "hpcg.dat"
        )

        with open(input_path, "w+") as f:
            f.write("HPCG benchmark input file\n")
            f.write(
                "Sandia National Laboratories; University of Tennessee, Knoxville\n"
            )
            f.write(self.expander.expand_var_name("matrix_size") + "\n")
            f.write(self.expander.expand_var_name("iterations") + "\n")
