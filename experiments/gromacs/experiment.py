# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType


class Gromacs(
    Experiment,
    ProgrammingModel(
        ProgrammingModelType.Mpionly,
        ProgrammingModelType.Openmp,
        ProgrammingModelType.Cuda,
        ProgrammingModelType.Rocm,
    ),
):
    variant(
        "workload",
        default="water_gmx50",
        description="workload name",
    )

    variant(
        "version",
        default="2025.2",
        values=("2025.2", "2024", "2023.3"),
        description="app version",
    )

    maintainers("pszi1ard")

    # off: turn off GPU-aware MPI
    # on: turn on, but allow groamcs to disable it if GPU-aware MPI is not supported
    # force: turn on and force gromacs to use GPU-aware MPI. May result in error if unsupported
    variant(
        "direct-gpu-comm",
        default="on",
        values=("on", "off", "force"),
        description="Use GPU-aware MPI",
    )

    variant(
        "sycl",
        default=True,
        values=(True, False),
        description="Enable GPU-aware MPI",
    )

    def compute_applications_section(self):
        # MPI-only defaults
        self.add_experiment_variable("n_ranks", 8, True)
        target = "cpu"
        bonded_target = "cpu"
        npme = "0"

        if self.spec.satisfies("+openmp"):
            self.set_environment_variable("OMP_PROC_BIND", "close")
            self.set_environment_variable("OMP_PLACES", "cores")
            self.add_experiment_variable("n_threads_per_proc", 8, True)
            self.add_experiment_variable("n_ranks", 8, True)
            target = "cpu"
            bonded_target = "cpu"
            npme = "0"

        # Overrides +openmp settings
        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("n_gpus", 8, True)
            target = "gpu"
            bonded_target = "cpu"
            npme = "1"
        elif self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", 8, True)
            target = "gpu"
            bonded_target = "cpu"
            npme = "1"

        input_variables = {
            "target": f"{target}",
            "size": "1536",
            "dlb": "no",
            "pin": "off",
            "maxh": "0.05",
            "nsteps": "1000",
            "nstlist": "200",
            "npme": f"{npme}",
        }

        other_input_variables = {
            "nb": f"{target}",
            "pme": "auto",
            "bonded": f"{bonded_target}",
            "update": f"{target}",
            "additional_args": " -pin {pin} -nb {nb} -pme {pme} -bonded {bonded} -update {update} -maxh {maxh} -nstlist {nstlist} -npme {npme} ",
        }

        for k, v in input_variables.items():
            self.add_experiment_variable(k, v, True)
        for k, v in other_input_variables.items():
            self.add_experiment_variable(k, v)

        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{size}/{n_ranks}",
            total_problem_size="{size}",
        )

    def compute_package_section(self):
        spack_specs = "+mpi~hwloc"
        spack_specs += "+sycl" if self.spec.satisfies("+sycl") else "~sycl"

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            spack_specs += f" direct-gpu-comm={self.spec.variants['direct-gpu-comm'][0]} "
            spack_specs += " ~double "
        else:
            spack_specs += " direct-gpu-comm=off "

        self.add_package_spec(
            self.name,
            [f"gromacs{self.determine_version()} {spack_specs}"],
        )
