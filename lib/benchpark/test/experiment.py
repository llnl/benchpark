# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import pickle
import subprocess
import sys

import pytest
import yaml

import benchpark.spec
from benchpark.paths import paths


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


@pytest.fixture
def init_experiment(tmp_path):
    system_spec = benchpark.spec.SystemSpec(
        "llnl-elcapitan cluster=tuolumne"
    ).concretize()
    system_spec.destdir = str(tmp_path)
    with (tmp_path / "system.pkl").open("wb") as stream:
        pickle.dump(system_spec, stream)

    def initialize(*spec):
        # Each CLI invocation loads its experiment in a fresh process, avoiding
        # the existing import-order dependency of the Caliper mixin directives.
        config = benchpark.config.configuration().repos.path.parent
        subprocess.run(
            [
                sys.executable,
                str(paths.benchpark_root / "bin/benchpark"),
                "-C",
                str(config),
                "experiment",
                "init",
                "--dest=experiment",
                str(tmp_path),
                *spec,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        output = yaml.safe_load((tmp_path / "experiment/ramble.yaml").read_text())
        application = next(iter(output["ramble"]["applications"].values()))
        workload = next(iter(application["workloads"].values()))
        name, experiment = next(iter(workload["experiments"].items()))
        return name, experiment

    return initialize


@pytest.mark.parametrize("benchmark", ["raja-perf+rocm", "saxpy+openmp", "kripke"])
def test_variable_overrides(benchmark, init_experiment):
    spec = benchpark.spec.ExperimentSpec(
        f"{benchmark} n_nodes=384 n_resources=1536 n_cores_per_rank=21"
    ).concretize()
    _, experiment = init_experiment(
        benchmark, "n_nodes=384", "n_resources=1536", "n_cores_per_rank=21"
    )

    assert experiment["variables"]["n_nodes"] == 384
    assert experiment["variables"]["n_resources"] == 1536
    assert experiment["variables"]["n_cores_per_rank"] == 21
    assert benchpark.spec.ExperimentSpec(str(spec)).concretize() == spec
    assert (
        pickle.loads(pickle.dumps(spec)).variable_overrides == spec.variable_overrides
    )
    assert spec != benchpark.spec.ExperimentSpec(benchmark).concretize()


def test_overrides_preserve_matrix_and_names(init_experiment):
    name, experiment = init_experiment(
        "saxpy+openmp", "n=2048,4096", "n_threads_per_proc=21"
    )

    assert experiment["variables"]["n"] == [2048, 4096]
    assert experiment["variables"]["n_threads_per_proc"] == [21]
    assert experiment["matrix"] == ["n_threads_per_proc", "n"]
    assert "{n}" in name
    assert "{n_threads_per_proc}" in name


def test_overrides_preserve_zipped_dimensions(init_experiment):
    _, experiment = init_experiment("kripke", "npx=4,8", "npy=3")

    assert experiment["variables"]["npx"] == [4, 8]
    assert experiment["variables"]["npy"] == [3, 3]
    assert experiment["variables"]["npz"] == [1, 1]
    assert experiment["zips"]["n_resources_dict"] == ["npx", "npy", "npz"]


def test_overrides_supply_scaling_inputs(init_experiment):
    _, experiment = init_experiment(
        "raja-perf+rocm+strong",
        "n_resources=8",
        "process_problem_size=1024",
        "scaling-iterations=3",
    )

    assert experiment["variables"]["n_resources"] == [8, 16, 32]
    assert experiment["variables"]["process_problem_size"] == [1024, 512, 256]


def test_overrides_replace_helper_defaults():
    experiment = (
        benchpark.spec.ExperimentSpec(
            "saxpy helper_parameter=2.5 total_problem_size='{n_resources}*2048'"
        )
        .concretize()
        .experiment
    )
    experiment.helpers[0]._expr_vars.add_scalar_variable("helper_parameter", 1)
    experiment.compute_applications_section_wrapper()

    assert experiment.variables["helper_parameter"] == 2.5
    assert experiment.variables["total_problem_size"] == "{n_resources}*2048"


@pytest.mark.parametrize(
    "assignment,match",
    [
        ("+unknown_flag", "unknown_flag is not a valid variant"),
        ("exec_mode=invalid", "is not valid for variant 'exec_mode'"),
        ("n_nodes=2 n_nodes=4", "Cannot specify variant n_nodes twice"),
    ],
)
def test_overrides_keep_variant_validation(assignment, match):
    with pytest.raises(Exception, match=match):
        benchpark.spec.ExperimentSpec(f"raja-perf {assignment}").concretize()


def test_systems_reject_unknown_parameters():
    with pytest.raises(Exception, match="n_resources is not a valid variant"):
        benchpark.spec.SystemSpec("llnl-elcapitan n_resources=1536").concretize()


def test_experiment_init_variable_overrides(init_experiment):
    _, experiment = init_experiment(
        "raja-perf+rocm",
        "n_nodes=384",
        "n_resources=1536",
        "n_cores_per_rank=21",
        "extra_cmd_opts=--label --verbose",
    )
    variables = experiment["variables"]
    assert variables["n_nodes"] == 384
    assert variables["n_resources"] == 1536
    assert variables["n_cores_per_rank"] == 21
    assert variables["n_gpus"] == "{n_resources}"
    assert variables["extra_cmd_opts"] == "--label --verbose"
