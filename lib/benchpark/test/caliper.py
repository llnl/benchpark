# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import benchpark.experiment
import benchpark.spec


def test_compute_variables_section_caliper(monkeypatch):
    spec = benchpark.spec.ExperimentSpec("saxpy caliper=time").concretize()
    experiment = spec.experiment
    for helper in experiment.helpers:
        if isinstance(helper, benchpark.caliper.Caliper.Helper):
            cali = helper

    vars_section = cali.compute_variables_section()

    assert vars_section == {
        "caliper_metadata": {
            "affinity": "none",
            "hwloc": "none",
            "application_name": "{application_name}",
            "experiment_name": "{experiment_name}",
            "n_nodes": "{n_nodes}",
            "n_ranks": "{n_ranks}",
            "n_threads_per_proc": "{n_threads_per_proc}",
            "benchpark_spec": ["~cuda~openmp~rocm+single_node"],
            "append_path": "'",
            "caliper": "time",
            "package_manager": "spack",
            "version": "1.0.0",
            "workload": "problem",
            "n_resources": "{n_resources}",
            "process_problem_size": "{process_problem_size}",
            "total_problem_size": "{total_problem_size}",
        }
    }
