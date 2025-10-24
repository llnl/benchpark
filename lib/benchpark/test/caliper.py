# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import json
import sys
import tempfile

from ramble.expander import Expander

import benchpark.caliper
import benchpark.paths
import benchpark.spec


def get_caliper_vars_section(expr_spec):
    experiment = expr_spec.experiment
    for helper in experiment.helpers:
        if isinstance(helper, benchpark.caliper.Caliper.Helper):
            cali = helper
            break
    return cali.compute_variables_section()


def test_experiment_compute_variables_section_caliper(monkeypatch):
    expr_spec = benchpark.spec.ExperimentSpec("saxpy caliper=time").concretize()
    vars_section = get_caliper_vars_section(expr_spec)

    assert vars_section == {
        "caliper_metadata": {
            "affinity": "none",
            "hwloc": "none",
            "application_name": "{application_name}",
            "experiment_name": "{experiment_name}",
            "n_nodes": "{n_nodes}",
            "n_ranks": "{n_ranks}",
            "n_repeats": "0",
            "n_threads_per_proc": "{n_threads_per_proc}",
            "benchpark_spec": ["~cuda+mpi~openmp~rocm"],
            "append_path": "'",
            "caliper": "time",
            "exec_mode": "test",
            "package_manager": "spack",
            "prepend_path": "'",
            "version": "1.0.0",
            "workload": "problem",
            "n_resources": "{n_resources}",
            "process_problem_size": "{process_problem_size}",
            "total_problem_size": "{total_problem_size}",
        }
    }


def test_caliper_modifier(monkeypatch):

    expr_spec = benchpark.spec.ExperimentSpec("saxpy caliper=time").concretize()
    expr_vars_section = get_caliper_vars_section(expr_spec)

    # Append path to enable import of modifier and application
    sys.path.append(str(benchpark.paths.benchpark_root))
    from modifiers.caliper.modifier import Caliper as CaliperModifier
    from repo.saxpy.application import Saxpy

    app_inst = Saxpy("")

    sys_spec = benchpark.spec.SystemSpec("llnl-elcapitan cluster=tuolumne").concretize()
    system = sys_spec.system
    sys_vars_section = system.compute_variables_section()

    variables = sys_vars_section["variables"]

    setattr(app_inst, "variables", variables)
    setattr(app_inst, "expander", Expander(expr_vars_section, ["Saxpy"]))

    cm = CaliperModifier("")
    setattr(
        cm, "expander", Expander({**sys_vars_section, **expr_vars_section}, ["Saxpy"])
    )

    # Run Caliper modifier and generate json file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        cm._caliper_metadata_file = tmp.name
        cm._build_metadata(workspace=object(), app_inst=app_inst)
        with open(cm._caliper_metadata_file, "r") as f:
            data = json.load(f)

    # Check file
    assert data == {
        "sys_cores_per_node": 84,
        "scheduler": "flux",
        "rocm_arch": "gfx942",
        "sys_cores_os_reserved_per_node": 12,
        "sys_cores_os_reserved_per_node_list": [
            0,
            8,
            16,
            24,
            32,
            40,
            48,
            56,
            64,
            72,
            80,
            88,
        ],
        "sys_gpus_per_node": 4,
        "sys_mem_per_node_GB": 512,
        "application_name": "{application_name}",
        "experiment_name": "{experiment_name}",
        "n_nodes": "{n_nodes}",
        "n_ranks": "{n_ranks}",
        "n_repeats": "0",
        "n_threads_per_proc": "{n_threads_per_proc}",
        "n_resources": "{n_resources}",
        "process_problem_size": "{process_problem_size}",
        "total_problem_size": "{total_problem_size}",
        "benchpark_spec": "['~cuda+mpi~openmp~rocm']",
        "affinity": "none",
        "append_path": "'",
        "caliper": "time",
        "exec_mode": "test",
        "hwloc": "none",
        "package_manager": "spack",
        "prepend_path": "'",
        "version": "1.0.0",
        "workload": "problem",
    }
