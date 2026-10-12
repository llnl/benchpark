# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys

import pytest
import yaml

import benchpark.spec


def test_namespaced_experiment_resolution():
    spec = benchpark.spec.ExperimentSpec("hecbench.softmax +rocm").concretize()
    unqualified_spec = benchpark.spec.ExperimentSpec("softmax +rocm").concretize()

    assert spec.fullname == "hecbench.softmax"
    assert unqualified_spec.fullname == spec.fullname
    assert spec.experiment_class.namespace == "hecbench"
    assert spec.experiment_class.__module__ == "benchpark.expr.hecbench.softmax"
    assert spec.satisfies("+rocm")


def test_experiment_repository_lookup_uses_namespace(monkeypatch):
    requested_names = []
    expected_class = object()

    def get_obj_class(name):
        requested_names.append(name)
        return expected_class

    monkeypatch.setattr(benchpark.spec.repo_path, "get_obj_class", get_obj_class)

    spec = benchpark.spec.ExperimentSpec("test.saxpy")
    assert spec.experiment_class is expected_class
    assert requested_names == ["test.saxpy"]


def test_write_yaml(monkeypatch, tmpdir):
    spec = benchpark.spec.ExperimentSpec("saxpy").concretize()
    experiment = spec.experiment

    section_names = ["include", "config"]
    section_wrapper_names = ["modifiers", "applications", "package"]

    for name in section_names + section_wrapper_names:
        monkeypatch.setattr(
            experiment,
            (
                f"compute_{name}_section"
                if name in section_names
                else f"compute_{name}_section_wrapper"
            ),
            lambda: True,
        )

    experiment_path = tmpdir.join("experiment_test")
    experiment.write_ramble_dict(experiment_path)

    with open(experiment_path, "r") as f:
        output = yaml.safe_load(f)

    check_dict = {
        "ramble": {
            "software" if name == "package" else name: True
            for name in section_names
            + section_wrapper_names  # package wrapper adds key as "software"
        }
    }

    assert output == check_dict


def test_compute_ramble_dict(monkeypatch):
    spec = benchpark.spec.ExperimentSpec("saxpy").concretize()
    experiment = spec.experiment

    section_names = ["include", "config"]
    section_wrapper_names = ["modifiers", "applications", "package"]

    for name in section_names + section_wrapper_names:
        monkeypatch.setattr(
            experiment,
            (
                f"compute_{name}_section"
                if name in section_names
                else f"compute_{name}_section_wrapper"
            ),
            lambda: True,
        )

    ramble_dict = experiment.compute_ramble_dict()

    assert ramble_dict == {
        "ramble": {
            "software" if name == "package" else name: True
            for name in section_names + section_wrapper_names
        }
    }


def test_compute_ramble_dict_caliper(monkeypatch):
    spec = benchpark.spec.ExperimentSpec("saxpy caliper=time").concretize()
    experiment = spec.experiment

    section_names = ["include", "config"]
    section_wrapper_names = ["modifiers", "applications", "package", "variables"]

    for name in section_names + section_wrapper_names:
        monkeypatch.setattr(
            experiment,
            (
                f"compute_{name}_section"
                if name in section_names
                else f"compute_{name}_section_wrapper"
            ),
            lambda: True,
        )

    ramble_dict = experiment.compute_ramble_dict()

    assert ramble_dict == {
        "ramble": {
            "software" if name == "package" else name: True
            for name in section_names + section_wrapper_names
        }
    }


def test_default_include_section():
    spec = benchpark.spec.ExperimentSpec("saxpy").concretize()
    experiment = spec.experiment

    include_section = experiment.compute_include_section()

    assert include_section == ["./configs"]


def test_default_config_section():
    spec = benchpark.spec.ExperimentSpec("saxpy").concretize()
    experiment = spec.experiment

    config_section = experiment.compute_config_section()

    the_spec = config_section["spec"]
    del config_section["spec"]

    assert benchpark.spec.ExperimentSpec(the_spec) == spec

    assert config_section == {
        "benchpark_experiment_command": "benchpark "
        + " ".join(sys.argv[1:]),  # Not applicable here
        "deprecated": True,
        "n_repeats": "0",
        "spack_flags": {
            "install": "--add --keep-stage",
            "concretize": "-U -f",
        },
        "system": {},
    }


def test_default_modifiers_section():
    spec = benchpark.spec.ExperimentSpec("saxpy").concretize()
    experiment = spec.experiment

    modifiers_section = experiment.compute_modifiers_section_wrapper()

    assert modifiers_section == [
        {"name": "allocation", "mode": "standard"},
        {"name": "exit-code"},
        {"name": "githash", "mode": "on"},
    ]


def test_multiple_models():
    with pytest.raises(
        benchpark.error.BenchparkError,
        match="spec cannot specify multiple mutually-exclusive programming models",
    ):
        spec = benchpark.spec.ExperimentSpec("saxpy+rocm+openmp").concretize()
        spec.experiment
