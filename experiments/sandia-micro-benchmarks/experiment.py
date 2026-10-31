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
        # Determine resources per node based on programming model
        # For GPU-enabled runs, use GPUs per node; otherwise use cores
        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            resources_per_node_expr = "{sys_gpus_per_node}"
        else:
            resources_per_node_expr = "{sys_cores_per_node}"

        # MPI overhead is a 2-rank point-to-point test
        if self.spec.satisfies("workload=mpi_overhead"):
            self.add_experiment_variable("n_ranks", 2, True)
            self.add_experiment_variable("n_nodes", 1)
            self.add_experiment_variable("peers", 1)
            self.add_experiment_variable("message_size", 8, True)

        # msgrate_9pt: 9-point stencil (8 peers) - requires minimum 9 ranks
        elif self.spec.satisfies("workload=msgrate_9pt"):
            stencil_size = 9

            if self.spec.satisfies("exec_mode=test"):
                # CI test mode: use minimum configuration
                # Fill nodes in multiples of stencil_size (9, 18, 27, etc.)
                # If resources_per_node < stencil_size, use multiple nodes
                # n_ranks = max(stencil_size, n_nodes * floor(resources_per_node / stencil_size) * stencil_size)
                self.add_experiment_variable("n_nodes", 1)
                self.add_experiment_variable(
                    "n_ranks",
                    f"max({stencil_size}, {{n_nodes}} * (({resources_per_node_expr}) // {stencil_size}) * {stencil_size})",
                    True
                )
                self.add_experiment_variable("peers", 8, True)
                # Sweep a few message sizes in test mode
                self.add_experiment_variable("message_size", [8, 256, 4096], True, True)
            else:
                # Performance mode: scale as configured
                # Fill nodes in multiples of stencil_size
                # Calculate ranks per node: floor(resources_per_node / 9) * 9
                # If resources_per_node < 9, spread across multiple nodes
                self.add_experiment_variable("n_nodes", 1)
                self.add_experiment_variable(
                    "n_ranks",
                    f"max({stencil_size}, {{n_nodes}} * (({resources_per_node_expr}) // {stencil_size}) * {stencil_size})",
                    True
                )
                # Peers fixed at 8 for 9-point stencil (not scaled)
                self.add_experiment_variable("peers", 8, False)
                # Start with small message size for exponential scaling
                self.add_experiment_variable("message_size", 8, True)

        # msgrate_27pt: 27-point stencil (26 peers) - requires minimum 27 ranks
        elif self.spec.satisfies("workload=msgrate_27pt"):
            stencil_size = 27

            if self.spec.satisfies("exec_mode=test"):
                # CI test mode: use minimum configuration
                # Fill nodes in multiples of stencil_size (27, 54, 81, etc.)
                # If resources_per_node < stencil_size, use multiple nodes
                # n_ranks = max(stencil_size, n_nodes * floor(resources_per_node / stencil_size) * stencil_size)
                self.add_experiment_variable("n_nodes", 1)
                self.add_experiment_variable(
                    "n_ranks",
                    f"max({stencil_size}, {{n_nodes}} * (({resources_per_node_expr}) // {stencil_size}) * {stencil_size})",
                    True
                )
                self.add_experiment_variable("peers", 26, True)
                # Sweep a few message sizes in test mode
                self.add_experiment_variable("message_size", [8, 256, 4096], True, True)
            else:
                # Performance mode: scale as configured
                # Fill nodes in multiples of stencil_size
                # Calculate ranks per node: floor(resources_per_node / 27) * 27
                # If resources_per_node < 27, spread across multiple nodes
                self.add_experiment_variable("n_nodes", 1)
                self.add_experiment_variable(
                    "n_ranks",
                    f"max({stencil_size}, {{n_nodes}} * (({resources_per_node_expr}) // {stencil_size}) * {stencil_size})",
                    True
                )
                # Peers fixed at 26 for 27-point stencil (not scaled)
                self.add_experiment_variable("peers", 26, False)
                # Start with small message size for exponential scaling
                self.add_experiment_variable("message_size", 8, True)

        # RMA multi-threaded test (uses 9-point stencil pattern)
        elif self.spec.satisfies("workload=rma_mt"):
            stencil_size = 9
            # Fill nodes in multiples of stencil_size
            # If resources_per_node < stencil_size, use multiple nodes
            self.add_experiment_variable("n_nodes", 1)
            self.add_experiment_variable(
                "n_ranks",
                f"max({stencil_size}, {{n_nodes}} * (({resources_per_node_expr}) // {stencil_size}) * {stencil_size})",
                True
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
        # Both strong and weak scaling scale n_nodes and message_size independently
        # Strong uses 8 peers (9-point stencil), weak uses 26 peers (27-point stencil)
        # message_size scales exponentially to 2MiB for both modes
        if self.spec.satisfies("+strong") or self.spec.satisfies("+weak"):
            # Maximum message size: 2MiB = 2 * 1024 * 1024 = 2097152 bytes
            max_message_size = 2097152

            def scale_n_nodes_until_saturated(var, itr, dim, sf):
                """Scale n_nodes by sf, always filling nodes with stencil multiples.

                Scaling logic:
                1. n_ranks is calculated as: n_nodes * floor(resources_per_node / stencil_size) * stencil_size
                2. This ensures nodes are always filled in multiples of the stencil size
                3. Nodes scale exponentially until system resources are saturated
                """
                return var.val(dim) * sf

            def scale_message_size_exponentially(var, itr, dim, sf):
                """Scale message_size exponentially until reaching 2MiB"""
                current_size = var.val(dim)
                new_size = current_size * sf
                # Cap at 2MiB
                return min(new_size, max_message_size)

            self.register_scaling_config(
                {
                    ScalingMode.Strong: {
                        # Strong: 8 peers (9-point), scale n_nodes and message_size
                        "n_nodes": scale_n_nodes_until_saturated,
                        "message_size": scale_message_size_exponentially,
                    },
                    ScalingMode.Weak: {
                        # Weak: 26 peers (27-point), scale n_nodes and message_size
                        "n_nodes": scale_n_nodes_until_saturated,
                        "message_size": scale_message_size_exponentially,
                    },
                }
            )

    def compute_package_section(self):
        # Use sandia-micro-benchmarks package (matches upstream Spack)
        spec_string = f"sandia-micro-benchmarks{self.determine_version()}"
        if self.spec.satisfies("workload=rma_mt"):
            spec_string += " +rma"
        self.add_package_spec(self.name, [spec_string])
