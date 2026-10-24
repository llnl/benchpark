# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType
from benchpark.scaling import Scaling, ScalingMode


class Phloem(
    Experiment,
    ProgrammingModel(
        ProgrammingModelType.Mpionly,
        ProgrammingModelType.Cuda,
        ProgrammingModelType.Rocm,
    ),
    Scaling(ScalingMode.Strong, ScalingMode.Throughput),
):
    variant(
        "workload",
        default="mpiBench_Allreduce",
        values=[
            "com_Latency",
            "com_Bidirectional",
            "com_BidirAsync",
            "com_Unidirectional",
            "com_UnidirAsync",
            "mpiBench_Barrier",
            "mpiBench_Bcast",
            "mpiBench_Alltoall",
            "mpiBench_Allgather",
            "mpiBench_Gather",
            "mpiBench_Scatter",
            "mpiBench_Allreduce",
            "mpiBench_Reduce",
            "mpiBench_Alltoallv",
            "mpiBench_Allgatherv",
            "mpiBench_Gatherv",
            "mpiBench_Ibcast",
            "mpiBench_Ialltoall",
            "mpiBench_Iallgather",
            "mpiBench_Igather",
            "mpiBench_Iscatter",
            "mpiBench_Iallreduce",
            "mpiBench_Ireduce",
            "mpiBench_Ialltoallv",
            "mpiBench_Iallgatherv",
            "mpiBench_Igatherv",
            "sqmr",
            "mpiGraph",
        ],
        multi=True,
        description="workloads available",
    )

    variant(
        "version",
        default="2.0.0",
        values=("latest", "2.0.0"),
        description="app version",
    )

    maintainers("nhanford")

    def __init__(self, spec):
        super().__init__(spec)

        # Bundle mpiBench and com workloads if multiple are selected
        if "workload" in spec.variants:
            # spec.variants["workload"] is already a tuple/list of workload names
            workloads = list(spec.variants["workload"])
            mpibench_workloads = [w for w in workloads if w.startswith("mpiBench_")]
            com_workloads = [w for w in workloads if w.startswith("com_")]

            # Bundle mpiBench workloads
            if len(mpibench_workloads) > 1:
                # Remove individual mpiBench workloads and add bundled one
                workloads = [w for w in workloads if not w.startswith("mpiBench_")]
                # Store the test types for later use (space-separated for mpiBench)
                self._bundled_mpibench_types = [
                    w.replace("mpiBench_", "") for w in mpibench_workloads
                ]
                # Add bundled workload
                workloads.append("mpiBench_bundled")
            else:
                self._bundled_mpibench_types = None

            # Bundle com workloads
            if len(com_workloads) > 1:
                # Remove individual com workloads and add bundled one
                workloads = [w for w in workloads if not w.startswith("com_")]
                # Store the test types for later use (comma-separated for com)
                self._bundled_com_types = [w.replace("com_", "") for w in com_workloads]
                # Add bundled workload
                workloads.append("com_bundled")
            else:
                self._bundled_com_types = None

            # Update the workload variant with bundled workloads
            if self._bundled_mpibench_types or self._bundled_com_types:
                self.workload = workloads

    def compute_applications_section(self):
        # If we have bundled mpiBench workloads, set the test types (space-separated)
        if hasattr(self, "_bundled_mpibench_types") and self._bundled_mpibench_types:
            bundled_types = " ".join(self._bundled_mpibench_types)
            self.add_experiment_variable("bundled_test_types", bundled_types, False)

        # If we have bundled com workloads, set the test types (comma-separated)
        if hasattr(self, "_bundled_com_types") and self._bundled_com_types:
            bundled_com_tests = ",".join(self._bundled_com_types)
            self.add_experiment_variable("bundled_com_tests", bundled_com_tests, False)

        if self.spec.satisfies("exec_mode=test"):
            # All workloads use minimum 4 ranks in test mode
            num_nodes = {"n_nodes": 1, "n_ranks": 4}
            for pk, pv in num_nodes.items():
                self.add_experiment_variable(pk, pv, True)

        if self.spec.satisfies("+rocm"):
            self.add_experiment_variable("additional_args", " -d rocm", False)
        if self.spec.satisfies("+cuda"):
            self.add_experiment_variable("additional_args", " -d cuda", False)

        use_gpus = self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm")
        resource_var = "n_gpus" if use_gpus else "n_ranks"

        # All workloads: use minimum 2 ranks on one node
        sys = self.system_spec.system
        # Use at least 2 ranks, but can fill nodes if system has more resources
        resources_per_node = (
            sys.sys_gpus_per_node if use_gpus else sys.sys_cores_per_node
        )
        # Ensure minimum of 2 ranks for all workloads
        min_resources = 2
        actual_resources = max(min_resources, resources_per_node)
        self.add_experiment_variable(resource_var, actual_resources, True)
        self.add_experiment_variable("n_nodes", 1, True)
        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_nodes": lambda var, itr, dim, scaling_factor: (
                        var.val(dim) * scaling_factor
                    ),
                    resource_var: lambda var, itr, dim, scaling_factor: (
                        var.val(dim) * scaling_factor
                    ),
                    "process_problem_size": "",
                    "total_problem_size": "",
                },
                ScalingMode.Throughput: {
                    "n_nodes": None,
                },
            }
        )

        n_resources = "{" + resource_var + "}"
        self.set_required_variables(
            n_resources=n_resources, process_problem_size="", total_problem_size=""
        )

    def compute_package_section(self):
        self.add_package_spec(self.name, [f"phloem{self.determine_version()}"])
