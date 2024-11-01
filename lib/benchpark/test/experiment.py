# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0
import yaml

import benchpark.experiment
import benchpark.spec


def test_write_yaml(monkeypatch, tmpdir):
    spec = benchpark.spec.ExperimentSpec("saxpy").concretize()
    experiment = spec.experiment

    section_names = ["include", "config", "modifiers", "applications", "spack"]

    for name in section_names:
        monkeypatch.setattr(experiment, f"compute_{name}_section", lambda: True)

    experiment_path = tmpdir.join("experiment_test")
    experiment.write_ramble_dict(experiment_path)

    with open(experiment_path, "r") as f:
        output = yaml.safe_load(f)

    assert output == {
        "ramble": {
            "software" if name == "spack" else name: True for name in section_names
        }
    }


def test_compute_ramble_dict(monkeypatch):
    spec = benchpark.spec.ExperimentSpec("saxpy").concretize()
    experiment = spec.experiment

    section_names = ["include", "config", "modifiers", "applications", "spack"]

    for name in section_names:
        monkeypatch.setattr(experiment, f"compute_{name}_section", lambda: True)

    ramble_dict = experiment.compute_ramble_dict()

    assert ramble_dict == {
        "ramble": {
            "software" if name == "spack" else name: True for name in section_names
        }
    }


def test_default_include_section():
    spec = benchpark.spec.ExperimentSpec("saxpy").concretize()
    experiment = benchpark.experiment.Experiment(spec)

    include_section = experiment.compute_include_section()

    assert include_section == ["./configs"]


def test_default_config_section():
    spec = benchpark.spec.ExperimentSpec("saxpy").concretize()
    experiment = benchpark.experiment.Experiment(spec)

    config_section = experiment.compute_config_section()

    assert config_section == {
        "deprecated": True,
        "spack_flags": {
            "install": "--add --keep-stage",
            "concretize": "-U -f",
        },
    }


def test_default_modifiers_section():
    spec = benchpark.spec.ExperimentSpec("saxpy").concretize()
    experiment = benchpark.experiment.Experiment(spec)

    modifiers_section = experiment.compute_modifiers_section()

    assert modifiers_section == [{"name": "allocation"}]
