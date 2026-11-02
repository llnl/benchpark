# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType
from benchpark.scaling import Scaling, ScalingMode


class SandiaMicroBenchmarks(
    Experiment,
    ProgrammingModel(
        ProgrammingModelType.Mpionly,
        ProgrammingModelType.Cuda,
        ProgrammingModelType.Rocm,
    ),
    Scaling(ScalingMode.Strong, ScalingMode.Weak),
):
    """Sandia Micro Benchmarks experiment with support for msgrate 9-point and 27-point stencil patterns.

    Scaling modes:
    - Strong: Scale from 1 node to multiple nodes with fixed problem size (message size)
    - Weak: Scale number of peers (9-point uses 8 peers, 27-point uses 26 peers)
    """

    variant(
        "workload",
        default="msgrate_9pt",
        values=("mpi_overhead", "msgrate_9pt", "msgrate_27pt", "rma_mt"),
        description="Workload: msgrate_9pt (8 peers), msgrate_27pt (26 peers)",
    )

    variant(
        "version",
        default="master",
        values=("master", "latest", "1.1"),
        description="app version",
    )

    maintainers("nhanford")

    def compute_applications_section(self):
        # MPI overhead is a 2-rank point-to-point test
        if self.spec.satisfies("workload=mpi_overhead"):
            self.add_experiment_variable("n_ranks", 2, True)
            self.add_experiment_variable("n_nodes", 1)
            self.add_experiment_variable("peers", 1)
            self.add_experiment_variable("message_size", 8, True)

        # msgrate_9pt: 9-point stencil (8 peers)
        elif self.spec.satisfies("workload=msgrate_9pt"):
            if self.spec.satisfies("exec_mode=test"):
                # CI test mode: single node, 8 cores
                self.add_experiment_variable("n_nodes", 1)
                self.add_experiment_variable(
                    "n_ranks", "{n_nodes}*{sys_cores_per_node}", True
                )
                self.add_experiment_variable("peers", 8, True)
                # Sweep a few message sizes in test mode
                self.add_experiment_variable("message_size", [8, 256, 4096], True, True)
            else:
                # Performance mode: scale as configured
                self.add_experiment_variable("n_nodes", 1)
                self.add_experiment_variable(
                    "n_ranks", "{n_nodes}*{sys_cores_per_node}", True
                )
                self.add_experiment_variable("peers", 8, True)
                # Start with medium message size
                self.add_experiment_variable("message_size", 1024, True)

        # msgrate_27pt: 27-point stencil (26 peers)
        elif self.spec.satisfies("workload=msgrate_27pt"):
            if self.spec.satisfies("exec_mode=test"):
                # CI test mode: single node, 8 cores
                self.add_experiment_variable("n_nodes", 1)
                self.add_experiment_variable(
                    "n_ranks", "{n_nodes}*{sys_cores_per_node}", True
                )
                self.add_experiment_variable("peers", 26, True)
                # Sweep a few message sizes in test mode
                self.add_experiment_variable("message_size", [8, 256, 4096], True, True)
            else:
                # Performance mode: scale as configured
                self.add_experiment_variable("n_nodes", 1)
                self.add_experiment_variable(
                    "n_ranks", "{n_nodes}*{sys_cores_per_node}", True
                )
                self.add_experiment_variable("peers", 26, True)
                # Start with medium message size
                self.add_experiment_variable("message_size", 1024, True)

        # RMA multi-threaded test
        elif self.spec.satisfies("workload=rma_mt"):
            self.add_experiment_variable("n_nodes", 1)
            self.add_experiment_variable(
                "n_ranks", "{n_nodes}*{sys_cores_per_node}", True
            )
            self.add_experiment_variable("peers", 8, True)
            self.add_experiment_variable("message_size", 8, True)

        # Set required problem size variables (msgrate doesn't have traditional problem sizes)
        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="",  # No per-process problem size
            total_problem_size="",  # Message rate is the FOM, not problem size
        )

        # Configure scaling behavior
        # Strong scaling: increase nodes/ranks with fixed message size
        # Weak scaling: increase peer count (from 9-point to 27-point pattern)
        if self.spec.satisfies("+strong") or self.spec.satisfies("+weak"):
            self.register_scaling_config(
                {
                    ScalingMode.Strong: {
                        # Strong: scale n_nodes, keep message_size constant
                        "n_nodes": lambda var, itr, dim, sf: var.val(dim) * sf,
                        "message_size": lambda var, itr, dim, sf: var.val(dim),
                    },
                    ScalingMode.Weak: {
                        # Weak: scale peers (communication complexity)
                        # Starts at 8 peers (9-pt), scale factor doubles peer count
                        "peers": lambda var, itr, dim, sf: var.val(dim) * sf,
                        "n_nodes": lambda var, itr, dim, sf: var.val(dim) * sf,
                    },
                }
            )

    def compute_package_section(self):
        # Use sandia-micro-benchmarks package (matches upstream Spack)
        spec_string = f"sandia-micro-benchmarks{self.determine_version()}"
        if self.spec.satisfies("workload=rma_mt"):
            spec_string += " +rma"
        self.add_package_spec(self.name, [spec_string])
