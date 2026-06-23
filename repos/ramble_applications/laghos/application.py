# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from ramble.appkit import *


class Laghos(ExecutableApplication):
    """Laghos benchmark"""

    name = "laghos"

    tags = [
        "asc",
        "engineering",
        "hypre",
        "solver",
        "mfem",
        "cfd",
        "large-scale",
        "multi-node",
        "single-node",
        "mpi",
        "c++",
        "high-order",
        "hydrodynamics",
        "explicit-timestepping",
        "finite-element",
        "time-dependent",
        "ode",
        "full-assembly",
        "partial-assembly",
        "lagrangian",
        "spatial-discretization",
        "unstructured-grid",
        "network-latency-bound",
        "network-collectives",
        "unstructured-grid",
    ]

    common_args = (
        " -m {mesh}"
        + " {mesh_options}"
        + " -ms {ms}"
        + " -ok {ok} -ot {ot} -oq {oq}"
        + " {nc} --mem --fom {gam}"
        + " --dev-pool-size {pool}"
        + " -d {device}"
        + " -dim {dim}"
        + " {vis}"
        + " {vs}"
        + " {k}"
        + " -tf {tf}"
        + " -s {s}"
        + " {assembly}"
    )

    executable("taylor-green", "laghos" + " -p 0" + common_args, use_mpi=True)

    executable("sedov", "laghos" + " -p 1" + common_args, use_mpi=True)

    executable("1D-sod-shock", "laghos" + " -p 2" + common_args, use_mpi=True)

    executable("triple-point", "laghos" + " -p 3" + common_args, use_mpi=True)

    executable("gresho-vortex", "laghos" + " -p 4" + common_args, use_mpi=True)

    executable("2D-riemann-12", "laghos" + " -p 5" + common_args, use_mpi=True)

    executable("2D-riemann-6", "laghos" + " -p 6" + common_args, use_mpi=True)

    executable("2D-rayleigh-taylor", "laghos" + " -p 7" + common_args, use_mpi=True)

    workload("taylor-green", executables=["taylor-green"])
    workload("sedov", executables=["sedov"])
    workload("1D-sod-shock", executables=["1D-sod-shock"])
    workload("triple-point", executables=["triple-point"])
    workload("gresho-vortex", executables=["gresho-vortex"])
    workload("2D-riemann-12", executables=["2D-riemann-12"])
    workload("2D-riemann-6", executables=["2D-riemann-6"])
    workload("2D-rayleigh-taylor", executables=["2D-rayleigh-taylor"])

    workload_variable(
        "mesh", default="default", description="mesh file", workloads=["*"]
    )

    workload_variable(
        "epm", default="0", description="Elements per MPI rank", workloads=["*"]
    )

    workload_variable(
        "nx", default="2", description="Elements in x-dimension", workloads=["*"]
    )

    workload_variable(
        "ny", default="2", description="Elements in y-dimension", workloads=["*"]
    )

    workload_variable(
        "nz", default="2", description="Elements in z-dimension", workloads=["*"]
    )

    workload_variable(
        "problem", default="3", description="problem number", workloads=["*"]
    )

    workload_variable(
        "rs", default="2", description="number of serial refinements", workloads=["*"]
    )

    workload_variable(
        "rp", default="0", description="number of parallel refinements", workloads=["*"]
    )

    workload_variable(
        "ok",
        default="1",
        description="Order (degree) of the kinematic finite element space",
        workloads=["*"],
    )

    workload_variable(
        "ot",
        default="0",
        description="Order (degree) of the thermodynamic finite element space",
        workloads=["*"],
    )

    workload_variable(
        "oq",
        default="-1",
        description="Order  of the integration rule",
        workloads=["*"],
    )

    workload_variable(
        "pool", default="4", description="Device pool size", workloads=["*"]
    )

    workload_variable(
        "device", default="cpu", description="cpu, cuda or hip", workloads=["*"]
    )

    workload_variable(
        "gam",
        default="--no-gpu-aware-mpi",
        description="--gpu-aware-mpi or --no-gpu-aware-mpi",
        workloads=["*"],
    )

    workload_variable(
        "nc",
        default="-nc",
        description="Use non-conforming meshes. Requires a 2D or 3D mesh.",
        workloads=["*"],
    )

    workload_variable(
        "assembly",
        default="-pa",
        description="Activate 1D tensor-based assembly (partial assembly).",
        workloads=["*"],
    )

    workload_variable(
        "k",
        default="",
        description="Enable -k flag when vis is active",
        workloads=["*"],
    )

    figure_of_merit(
        "Major kernels total time",
        log_file="{experiment_run_dir}/{experiment_name}.out",
        fom_regex=r"Major kernels total time \(seconds\):\s+(?P<fom>[0-9]+\.[0-9]*(e^[0-9]*)?)",
        group_name="fom",
        units="seconds",
    )

    success_criteria(
        "pass",
        mode="string",
        match=r"Major kernels total time",
        file="{experiment_run_dir}/{experiment_name}.out",
    )

    def _make_experiments(self, workspace, app_inst=None):
        """
        When setting up its mesh, Laghos strictly accepts as input either the 
        elements per mpi (epm) or the mesh dimensions and refinement factors 
        (nx/ny/nz/rs/rp), but not both

        Here we select one of the two strategies based on the value of epm
        if epm > 0: use -epm {epm}
        else: use -nx {nx} -ny {ny} -nz {nz} -rs {rs} -rp {rp}

        """
        epm = int(self.expander.expand_var_name("epm"))

        if epm:
            self.variables["mesh_options"] = f"-epm {epm}"
        else:
            nx = int(self.expander.expand_var_name("nx"))
            ny = int(self.expander.expand_var_name("ny"))
            nz = int(self.expander.expand_var_name("nz"))
            rs = int(self.expander.expand_var_name("rs"))
            rp = int(self.expander.expand_var_name("rp"))
            self.variables["mesh_options"] = f"-nx {nx} -ny {ny} -nz {nz} -rs {rs} -rp {rp}"

        super()._make_experiments(workspace)
