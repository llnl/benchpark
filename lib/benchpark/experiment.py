# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from typing import Dict
import yaml  # TODO: some way to ensure yaml available

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

    def compute_include_section(self):
        return []

    def compute_config_section(self):
        return {}

    def compute_modifiers_section(self):
        return []

    def compute_applications_section(self):
        return {}

    def compute_spack_section(self):
        return {}

    def get_helper_name_prefix(self):
        return None

    def get_spack_variants(self):
        return None


class SingleNode:
    variant(
        "single_node",
        default=True,
        description="Single node execution mode",
    )

    class Helper(ExperimentHelper):
        def get_helper_name_prefix(self):
            return "single_node" if self.spec.satisfies("+single_node") else ""


class Experiment(ExperimentSystemBase, SingleNode):
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
        "extra_spack_specs",
        default=" ",
        description="additional spack specs",
    )

    def __init__(self, spec):
        self.spec: "benchpark.spec.ConcreteExperimentSpec" = spec
        super().__init__()
        self.helpers = []

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

    def compute_include_section(self):
        # include the config directory
        return ["./configs"]

    def compute_config_section(self):
        # default configs for all experiments
        return {
            "deprecated": True,
            "spack_flags": {"install": "--add --keep-stage", "concretize": "-U -f"},
        }

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
        self.variables = {}
        self.zips = {}
        self.matrix = []
        self.excludes = []

        self.compute_applications_section()

        expr_helper_list = []
        for cls in self.helpers:
            helper_prefix = cls.get_helper_name_prefix()
            if helper_prefix:
                expr_helper_list.append(helper_prefix)
        expr_name_suffix = "_".join(expr_helper_list + self.expr_name)

        expr_setup = {
            "variants": {"package_manager": "spack"},
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

    def add_spack_spec(self, package_name, spec=None):
        if spec:
            self.package_specs[package_name] = {
                "pkg_spec": spec[0],
                "compiler": spec[1],
            }
        else:
            self.package_specs[package_name] = {}

    def compute_spack_section(self):
        raise NotImplementedError(
            "Each experiment must implement compute_spack_section"
        )

    def compute_spack_section_wrapper(self):
        for cls in self.helpers:
            cls_package_specs = cls.compute_spack_section()
            if cls_package_specs and "packages" in cls_package_specs:
                self.package_specs |= cls_package_specs["packages"]

        self.compute_spack_section()

        if self.name not in self.package_specs:
            raise BenchparkError(
                f"Spack section must be defined for application package {self.name}"
            )

        spack_variants = list(
            filter(
                lambda v: v is not None,
                (cls.get_spack_variants() for cls in self.helpers),
            )
        )
        self.package_specs[self.name]["pkg_spec"] += " ".join(
            spack_variants + list(self.spec.variants["extra_spack_specs"])
        ).strip()

        return {
            "packages": {k: v for k, v in self.package_specs.items() if v},
            "environments": {self.name: {"packages": list(self.package_specs.keys())}},
        }

    def compute_ramble_dict(self):
        # This can be overridden by any subclass that needs more flexibility
        return {
            "ramble": {
                "include": self.compute_include_section(),
                "config": self.compute_config_section(),
                "modifiers": self.compute_modifiers_section_wrapper(),
                "applications": self.compute_applications_section_wrapper(),
                "software": self.compute_spack_section_wrapper(),
            }
        }

    def write_ramble_dict(self, filepath):
        ramble_dict = self.compute_ramble_dict()
        with open(filepath, "w") as f:
            yaml.dump(ramble_dict, f)
