# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from typing import Dict
import yaml  # TODO: some way to ensure yaml available
import sys
from enum import Enum

from benchpark.error import BenchparkError
from benchpark.directives import ExperimentSystemBase
from benchpark.directives import variant
import benchpark.spec
import benchpark.paths
import benchpark.repo
import benchpark.runtime
import benchpark.variant

bootstrapper = benchpark.runtime.RuntimeResources(benchpark.paths.benchpark_home)
bootstrapper.bootstrap()

import ramble.language.language_base  # noqa
import ramble.language.language_helpers  # noqa


class ExperimentHelper:
    def __init__(self, exp):
        self.spec = exp.spec
        self.variables = {}
        self.env_vars = {
            "set": {},
            "append": [{"paths": {}, "vars": {}}],
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
        """Append to existing environment variable PATH ('paths') or other variable ('vars')
        Matches expected ramble format. Example:
        https://ramble.readthedocs.io/en/latest/workspace_config.html#environment-variable-control
        """
        self.env_vars["append"][0][target][name] = value

    def compute_config_variables(self):
        pass

    def compute_config_variables_wrapper(self):
        self.compute_config_variables()
        return self.variables, self.env_vars


class SingleNode:
    variant(
        "single_node",
        default=True,
        description="Single node execution mode",
    )

    class Helper(ExperimentHelper):
        def get_helper_name_prefix(self):
            return "single_node" if self.spec.satisfies("+single_node") else ""


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
                    package_specs["affinity"]["pkg_spec"] += "+rocm"

            return {
                "packages": {k: v for k, v in package_specs.items() if v},
                "environments": {"affinity": {"packages": list(package_specs.keys())}},
            }


class HwlocVariantValues(str, Enum):
    NONE = "none"
    ON = "on"


class Hwloc:
    variant(
        "hwloc",
        default=HwlocVariantValues.NONE.value,
        values=tuple(v.value for v in HwlocVariantValues),
        multi=False,
        description="Get underlying infrastructure topology",
    )

    class Helper(ExperimentHelper):
        def compute_modifiers_section(self):
            modifier_list = []

            if not self.spec.satisfies(f"hwloc={HwlocVariantValues.NONE.value}"):
                affinity_modifier_modes = {}
                affinity_modifier_modes["name"] = "hwloc"
                affinity_modifier_modes["mode"] = self.spec.variants["hwloc"][0]
                modifier_list.append(affinity_modifier_modes)

            return modifier_list


class Experiment(ExperimentSystemBase, SingleNode, Affinity, Hwloc):
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
        values=("spack", "environment-modules", "None"),
        description="package manager to use",
    )

    variant(
        "append_path",
        default=" ",
        description="Append to environment PATH during experiment execution",
    )

    def __init__(self, spec):
        self.spec: "benchpark.spec.ConcreteExperimentSpec" = spec
        # Device type must be set before super with absence of mpionly experiment type
        self.device_type = "cpu"
        super().__init__()
        self.helpers = []
        self._spack_name = None
        self._ramble_name = None
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
        # default configs for all experiments
        default_config = {
            "deprecated": True,
            "benchpark_command": "benchpark " + " ".join(sys.argv[1:]),
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

    def add_experiment_name_prefix(self, prefix):
        self.expr_name = [prefix] + self.expr_name

    def add_experiment_variable(self, name, values, use_in_expr_name=False):
        self.variables[name] = values
        if use_in_expr_name:
            self.expr_name.append(f"{{{name}}}")

    def set_environment_variable(self, name, values):
        """Set value of environment variable"""
        self.env_vars["set"][name] = values

    def append_environment_variable(self, name, values, target="paths"):
        """Append to existing environment variable PATH ('paths') or other variable ('vars')
        Matches expected ramble format. Example:
        https://ramble.readthedocs.io/en/latest/workspace_config.html#environment-variable-control
        """
        if target not in ["paths", "vars"]:
            raise ValueError("Invalid target specified. Must be 'paths' or 'vars'.")

        self.env_vars["append"][0][target][name] = values

    def zip_experiment_variables(self, name, variable_names):
        self.zips[name] = list(variable_names)

    def matrix_experiment_variables(self, variable_names):
        if isinstance(variable_names, str):
            self.matrix.append(variable_names)
        elif isinstance(variable_names, list):
            self.matrix.extend(variable_names)
        else:
            raise ValueError("Variable list must be of type str or list[str].")

    def add_experiment_exclude(self, exclude_clause):
        self.excludes.append(exclude_clause)

    def compute_applications_section(self):
        raise NotImplementedError(
            "Each experiment must implement compute_applications_section"
        )

    def compute_applications_section_wrapper(self):
        self.expr_name = []
        self.env_vars = {
            "set": {},
            "append": [{"paths": {}, "vars": {}}],
        }
        self.variables = {}
        self.zips = {}
        self.matrix = []
        self.excludes = []

        for cls in self.helpers:
            variables, env_vars = cls.compute_config_variables_wrapper()
            self.variables |= variables
            self.env_vars["set"] |= env_vars["set"]
            self.env_vars["append"][0] |= env_vars["append"][0]

        self.compute_applications_section()

        expr_helper_list = []
        for cls in self.helpers:
            helper_prefix = cls.get_helper_name_prefix()
            if helper_prefix:
                expr_helper_list.append(helper_prefix)
        expr_name_suffix = "_".join(expr_helper_list + self.expr_name)

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

        if "append_path" in self.spec.variants:
            self.append_environment_variable(
                "PATH", self.spec.variants["append_path"][0]
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
