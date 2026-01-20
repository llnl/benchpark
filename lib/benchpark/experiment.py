# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import sys
from typing import Dict

import ramble.language.language_base  # noqa
import ramble.language.language_helpers  # noqa
import yaml  # TODO: some way to ensure yaml available

import benchpark.spec
import benchpark.variant
from benchpark.directives import ExperimentSystemBase, variant
from benchpark.error import BenchparkError
from benchpark.variables import VariableDict


class ExperimentHelper:
    def __init__(self, exp):
        self.spec = exp.spec
        self._expr_vars = VariableDict()
        self.env_vars = {
            "set": {},
            "append": [{"paths": {}, "vars": {}}],
            "prepend": [{"paths": {}, "vars": {}}],
        }

    def compute_include_section(self):
        return []

    def compute_config_section(self):
        return {}

    def compute_modifiers_section(self):
        return []

    def compute_applications_section(self):
        return {}

    def compute_package_section(self):
        return {}

    def get_helper_name_prefix(self):
        return None

    def get_spack_variants(self):
        return None

    def compute_variables_section(self):
        return {}

    def set_environment_variable(self, name, value):
        """Set value of environment variable"""
        self.env_vars["set"][name] = value

    def append_environment_variable(self, name, value, target="paths"):
        """Append to existing environment variable PATH ('paths') or other variable ('vars')"""
        self.env_vars["append"][0][target][name] = value

    def prepend_environment_variable(self, name, value, target="paths"):
        """Prepend to existing environment variable PATH ('paths') or other variable ('vars')"""
        self.env_vars["prepend"][0][target][name] = value

    def compute_config_variables(self):
        pass

    def compute_config_variables_wrapper(self):
        self.compute_config_variables()
        return self._expr_vars, self.env_vars


class ExecMode:
    variant(
        "exec_mode",
        default="test",
        values=("test", "perf"),
        description="Execution mode",
    )

    class Helper(ExperimentHelper):
        def get_helper_name_prefix(self):
            return self.spec.variants["exec_mode"][0]


class Affinity:
    variant(
        "affinity",
        default="none",
        values=(
            "none",
            "on",
        ),
        multi=False,
        description="Build and run the affinity package",
    )

    class Helper(ExperimentHelper):
        def compute_modifiers_section(self):
            modifier_list = []
            if not self.spec.satisfies("affinity=none"):
                affinity_modifier_modes = {}
                affinity_modifier_modes["name"] = "affinity"
                if self.spec.satisfies("+cuda"):
                    affinity_modifier_modes["mode"] = "cuda"
                elif self.spec.satisfies("+rocm"):
                    affinity_modifier_modes["mode"] = "rocm"
                else:
                    affinity_modifier_modes["mode"] = "mpi"
                modifier_list.append(affinity_modifier_modes)
            return modifier_list

        def compute_package_section(self):
            # set package versions
            affinity_version = "master"

            # get system config options
            # TODO: Get compiler/mpi/package handles directly from system.py
            system_specs = {}
            system_specs["compiler"] = "default-compiler"
            if self.spec.satisfies("+cuda"):
                system_specs["cuda_arch"] = "{cuda_arch}"
            if self.spec.satisfies("+rocm"):
                system_specs["rocm_arch"] = "{rocm_arch}"

            # set package spack specs
            package_specs = {}

            if not self.spec.satisfies("affinity=none"):
                package_specs["affinity"] = {
                    "pkg_spec": f"affinity@{affinity_version}+mpi",
                    "compiler": system_specs["compiler"],
                }
                if self.spec.satisfies("+cuda"):
                    package_specs["affinity"]["pkg_spec"] += "+cuda"
                elif self.spec.satisfies("+rocm"):
                    package_specs["affinity"][
                        "pkg_spec"
                    ] += "+rocm amdgpu_target={rocm_arch}"

            return {
                "packages": {k: v for k, v in package_specs.items() if v},
                "environments": {"affinity": {"packages": list(package_specs.keys())}},
            }


class Hwloc:
    variant(
        "hwloc",
        default="none",
        values=(
            "none",
            "on",
        ),
        multi=False,
        description="Get underlying infrastructure topology",
    )

    class Helper(ExperimentHelper):
        def compute_modifiers_section(self):
            hwloc_modifier_list = []

            if not self.spec.satisfies("hwloc=none"):
                hwloc_modifier_modes = {}
                hwloc_modifier_modes["name"] = "hwloc"
                hwloc_modifier_modes["mode"] = self.spec.variants["hwloc"][0]
                hwloc_modifier_list.append(hwloc_modifier_modes)

            return hwloc_modifier_list


class Experiment(ExperimentSystemBase, ExecMode, Affinity, Hwloc):
    """This is the superclass for all benchpark experiments.

    ***The Experiment class***

    Experiments are written in pure Python.

    There are two main parts of a Benchpark experiment:

      1. **The experiment class**.  Classes contain ``directives``, which are
         special functions, that add metadata (variants) to packages (see
         ``directives.py``).

      2. **Experiment instances**. Once instantiated, an experiment is
         essentially a collection of files defining an experiment in a
         Ramble workspace.
    """

    #
    # These are default values for instance variables.
    #

    # This allows analysis tools to correctly interpret the class attributes.
    variants: Dict[
        "benchpark.spec.Spec",
        Dict[str, benchpark.variant.Variant],
    ]

    variant(
        "package_manager",
        default="spack",
        values=("spack", "environment-modules", "user-managed"),
        description="package manager to use",
    )

    variant(
        "append_path",
        default=" ",
        description="Append to environment PATH during experiment execution",
    )

    variant(
        "prepend_path",
        default=" ",
        description="Prepend to environment PATH during experiment execution",
    )

    variant(
        "n_repeats",
        default="0",
        description="Number of experiment repetitions",
    )

    def __init__(self, spec):
        self.spec: "benchpark.spec.ConcreteExperimentSpec" = spec
        # Device type must be set before super with absence of mpionly experiment type
        self.device_type = "cpu"
        self.programming_models = []
        super().__init__()
        self.helpers = []
        self._spack_name = None
        self._ramble_name = None
        self._expr_vars = VariableDict()
        self.req_vars = [
            "n_resources",
            "process_problem_size",
            "total_problem_size",
            "device_type",
        ]

        for cls in self.__class__.mro()[1:]:
            if cls is not Experiment and cls is not object:
                if hasattr(cls, "Helper"):
                    helper_instance = cls.Helper(self)
                    self.helpers.append(helper_instance)

        self.name = self.spec.name

        if "workload" in self.spec.variants:
            self.workload = self.spec.variants["workload"]
        else:
            raise BenchparkError(f"No workload variant defined for package {self.name}")

        self.package_specs = {}

        # Explicitly ordered list. "mpi" first
        models = ["mpi"] + ["openmp", "cuda", "rocm"]
        invalid_models = []
        for model in models:
            # Experiment specifying model in add_package_spec that it doesn't implement
            if (
                self.spec.satisfies("+" + model)
                and model not in self.programming_models
            ):
                invalid_models.append(model)
        # Case where there are no experiments specified in experiment.py
        if len(self.programming_models) == 0:
            raise NotImplementedError(
                f"Please specify a programming model in your {self.name}/experiment.py (e.g. MpiOnlyExperiment, OpenMPExperiment, CudaExperiment, ROCmExperiment). See other experiments for examples."
            )
        elif len(invalid_models) > 0:
            raise NotImplementedError(
                f'{invalid_models} are not valid programming models for "{self.name}". Choose from {self.programming_models}.'
            )
        # Check if experiment is trying to run in MpiOnly mode without being an MpiOnlyExperiment
        elif "mpi" not in str(self.spec) and not any(
            self.spec.satisfies("+" + model) for model in models[1:]
        ):
            raise NotImplementedError(
                f'"{self.name}" cannot run with MPI only without inheriting from MpiOnlyExperiment. Choose from {self.programming_models}'
            )

        if (
            sum([self.spec.satisfies(s) for s in ["+strong", "+weak", "+throughput"]])
            > 1
        ):
            raise BenchparkError(
                f"spec cannot specify multiple scaling options. {self.spec}"
            )
        if sum([self.spec.satisfies(s) for s in ["+cuda", "+rocm", "+openmp"]]) > 1:
            raise BenchparkError(
                f"spec cannot specify multiple mutually-exclusive programming models. {self.spec}"
            )

    @property
    def spack_name(self):
        """The name of the spack package that is used to build this benchmark"""
        return self._spack_name

    @spack_name.setter
    def spack_name(self, value: str):
        self._spack_name = value

    @property
    def ramble_name(self):
        """The name of the ramble application associated with this benchmark"""
        return self._ramble_name

    @ramble_name.setter
    def ramble_name(self, value: str):
        self._ramble_name = value

    @property
    def expr_vars(self):
        """Dictionary of experiment variables"""
        return self._expr_vars

    def set_required_variables(self, **kwargs):
        """Helper function to set required variables."""
        self.add_experiment_variable("device_type", self.device_type, False)
        for var in kwargs.keys():
            if var not in self.req_vars:
                raise ValueError(f"Unexpected experiment variable provided '{var}'")
            self.add_experiment_variable(var, kwargs[var], False)

    def check_required_variables(self):
        """Raises error if any of the self.req_vars variables are not set in derived classes."""
        unset_vars = [v for v in self.req_vars if v not in self.variables.keys()]
        if len(unset_vars) > 0:
            raise NotImplementedError(
                f"The following experiment variables must be set with 'self.add_experiment_variable': {', '.join([v for v in unset_vars])}."
            )

    def compute_include_section(self):
        # include the config directory
        return ["./configs"]

    def compute_config_section(self):
        system_dict = {}
        # Avoid needing system_spec when initializing from library
        if hasattr(self, "system_spec"):
            # i.e. the user ran `experiment init` with `--system`
            for when, needs in self.requires.items():
                if self.spec.satisfies(when):
                    for need in needs:
                        self.system_spec.system.enforce(need)

            system_dict = {
                "config-hash": self.system_spec.system.config_hash,
                "name": str(self.system_spec.system.__class__.__name__),
                "destdir": self.system_spec.destdir,
            }
        # default configs for all experiments
        default_config = {
            "n_repeats": self.spec.variants["n_repeats"][0],
            "deprecated": True,
            "benchpark_experiment_command": "benchpark " + " ".join(sys.argv[1:]),
            "system": system_dict,
            "spec": str(self.spec),
        }
        if self.spec.variants["package_manager"][0] == "spack":
            default_config["spack_flags"] = {
                "install": "--add --keep-stage",
                "concretize": "-U -f",
            }
        return default_config

    def compute_modifiers_section(self):
        return []

    def compute_modifiers_section_wrapper(self):
        # by default we use the allocation modifier and no others
        modifier_list = [{"name": "allocation"}, {"name": "exit-code"}]
        modifier_list += self.compute_modifiers_section()
        for cls in self.helpers:
            modifier_list += cls.compute_modifiers_section()
        return modifier_list

    def add_experiment_variable(self, name, values, named=False, matrixed=False):
        if isinstance(values, dict):
            self.expr_vars.add_dimensional_variable(name, values, named, True, matrixed)
            self.zips[name] = list(values.keys())
            if matrixed:
                self.matrix.append(name)
        else:
            self.expr_vars.add_scalar_variable(name, values, named, False, matrixed)
            if matrixed:
                self.matrix.append(name)

    def set_environment_variable(self, name, values):
        """Set value of environment variable"""
        self.env_vars["set"][name] = values

    def append_environment_variable(self, name, values, target="paths"):
        """Append to existing environment variable PATH ('paths') or other variable ('vars')"""
        if target not in ["paths", "vars"]:
            raise ValueError("Invalid target specified. Must be 'paths' or 'vars'.")

        self.env_vars["append"][0][target][name] = values

    def prepend_environment_variable(self, name, values, target="paths"):
        """Prepend to existing environment variable PATH ('paths') or other variable ('vars')"""
        if target not in ["paths", "vars"]:
            raise ValueError("Invalid target specified. Must be 'paths' or 'vars'.")

        self.env_vars["prepend"][0][target][name] = values

    def add_experiment_exclude(self, exclude_clause):
        self.excludes.append(exclude_clause)

    def compute_applications_section(self):
        raise NotImplementedError(
            "Each experiment must implement compute_applications_section"
        )

    def compute_applications_section_wrapper(self):
        self.expr_var_names = []
        self.env_vars = {
            "set": {},
            "append": [{"paths": {}, "vars": {}}],
            "prepend": [{"paths": {}, "vars": {}}],
        }
        self.variables = {}
        self.zips = {}
        self.matrix = []
        self.excludes = []

        for cls in self.helpers:
            variables, env_vars = cls.compute_config_variables_wrapper()
            self.expr_vars.extend(variables)
            self.env_vars["set"] |= env_vars["set"]
            self.env_vars["append"][0] |= env_vars["append"][0]
            self.env_vars["prepend"][0] |= env_vars["prepend"][0]

        # Set required variable for package manager (we are not using this variable)
        if self.spec.variants["package_manager"][0] == "user-managed":
            self.add_experiment_variable(self.name + "_path", "None")

        self.compute_applications_section()

        if any([self.spec.satisfies(s) for s in ["+strong", "+weak", "+throughput"]]):
            self.expr_vars.extend(self.scale())

        for var in self.expr_vars.values():
            for dim in var.dims():
                if var.is_named:
                    self.expr_var_names.append(f"{{{dim}}}")
                if len(var[dim]) == 1 and not var.is_zipped and not var.is_matrixed:
                    self.variables[dim] = var[dim][0]
                else:
                    self.variables[dim] = var[dim]

        expr_helper_list = []
        for cls in self.helpers:
            helper_prefix = cls.get_helper_name_prefix()
            if helper_prefix:
                expr_helper_list.append(helper_prefix)
        expr_name_suffix = "_".join(expr_helper_list + self.expr_var_names)

        self.check_required_variables()

        expr_setup = {
            "variants": {"package_manager": self.spec.variants["package_manager"][0]},
            "env_vars": self.env_vars,
            "variables": self.variables,
            "zips": self.zips,
            "matrix": self.matrix,
            "exclude": ({"where": self.excludes} if self.excludes else {}),
        }

        workloads = {}
        for workload in self.workload:
            expr_name = f"{self.name}_{workload}_{expr_name_suffix}"
            workloads[workload] = {
                "experiments": {
                    expr_name: expr_setup,
                }
            }

        return {
            self.name: {
                "workloads": workloads,
            }
        }

    def add_package_spec(self, package_name, spec=None):
        if spec:
            self.package_specs[package_name] = {
                "pkg_spec": spec[0],
            }
        else:
            self.package_specs[package_name] = {}

    def determine_version(self):
        app_variant = self.spec.variants["version"][0]
        return "" if app_variant == "latest" else "@" + app_variant

    def compute_package_section(self):
        raise NotImplementedError(
            "Each experiment must implement compute_package_section"
        )

    def compute_package_section_wrapper(self):
        pkg_manager = self.spec.variants["package_manager"][0]

        for cls in self.helpers:
            cls_package_specs = cls.compute_package_section()
            if cls_package_specs and "packages" in cls_package_specs:
                self.package_specs |= cls_package_specs["packages"]

        self.compute_package_section()

        if self.name not in self.package_specs:
            raise BenchparkError(
                f"Package section must be defined for application package {self.name}"
            )

        if pkg_manager == "spack":
            spack_variants = list(
                filter(
                    lambda v: v is not None,
                    (cls.get_spack_variants() for cls in self.helpers),
                )
            )
            self.package_specs[self.name]["pkg_spec"] += " ".join(
                spack_variants
            ).strip()

        if "append_path" in self.spec.variants and (
            # Don't append " " to path (default value)
            self.spec.variants["append_path"][0]
            != " "
        ):
            self.append_environment_variable(
                "PATH", self.spec.variants["append_path"][0]
            )
        if "prepend_path" in self.spec.variants and (
            # Don't append " " to path (default value)
            self.spec.variants["prepend_path"][0]
            != " "
        ):
            self.prepend_environment_variable(
                "PATH", self.spec.variants["prepend_path"][0]
            )

        return {
            "packages": {k: v for k, v in self.package_specs.items() if v},
            "environments": {self.name: {"packages": list(self.package_specs.keys())}},
        }

    def compute_variables_section(self):
        return {}

    def compute_variables_section_wrapper(self):
        # For each helper class compute any additional variables
        additional_vars = {}
        for cls in self.helpers:
            additional_vars.update(cls.compute_variables_section())
        return additional_vars

    def compute_ramble_dict(self):
        # This can be overridden by any subclass that needs more flexibility
        ramble_dict = {
            "ramble": {
                "include": self.compute_include_section(),
                "config": self.compute_config_section(),
                "modifiers": self.compute_modifiers_section_wrapper(),
                "applications": self.compute_applications_section_wrapper(),
                "software": self.compute_package_section_wrapper(),
            }
        }
        # Add any variables from helper classes if necessary
        additional_vars = self.compute_variables_section_wrapper()
        if additional_vars:
            ramble_dict["ramble"].update({"variables": additional_vars})

        return ramble_dict

    def write_ramble_dict(self, filepath):
        ramble_dict = self.compute_ramble_dict()
        with open(filepath, "w") as f:
            yaml.dump(ramble_dict, f)
