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
        return ""

    def get_spack_variants(self):
        raise NotImplementedError("Each helper must implement get_spack_variants")


class Experiment(ExperimentSystemBase):
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

    variant(
        "scaling-factor",
        default="2",
        values=int,
        description="Factor by which to scale values of problem variables",
    )

    variant(
        "scaling-iterations",
        default="4",
        values=int,
        description="Number of experiments to be generated",
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
            self.workload = self.spec.variants["workload"][0]
        else:
            self.workload = self.name

        self.package_specs = {}

    # input parameters:
    # 1. input_variables: dictionary with key value pairs of type str: int or tuple(str): list(int)
    # For the value in input_variables corresponding to scaling_variable,
    # if the value is a list, select the index of its smallest element, 0 otherwise
    # Beginning with this index, generate a list of indexes of length equal to
    # the number of dimensions in an (ascending) round-robin order
    # 2. scaling_variable: variable of type str or tuple(str). The scaling order is determined by
    # the value in input_variables corresponding to scaling_variable.
    #
    # output:
    # scaling_order: list[int]. list of indices, with one value for each dimension,
    # starting with the minimum value of the first element in input_variables arranged
    # in an ascending round-robin order
    def configure_scaling_policy(self, input_variables, scaling_variable):
        # compute the number of dimensions
        n_dims = 1
        for param in input_variables.values():
            if isinstance(param, list):
                n_dims = len(param)
                break

        # starting with the minimum value dim of the scaling_variable
        # compute the remaining n_dims-1 values in a round-robin manner
        val = input_variables[scaling_variable]
        min_dim = val.index(min(val)) if isinstance(val, list) else 0

        return [(min_dim + i) % n_dims for i in range(n_dims)]

    # input parameters:
    # 1. input_variables: dict[str, int | tuple(str), list[int]]. Dictionary of all variables
    # that need to be scaled. All variables are ordered as per the ordering policy of
    # the first element in input_variables. By default, this policy is to scale the
    # values beginning with the smallest dimension and proceeding in a RR manner through
    # the other dimensions
    #
    # 2. scaling_factor: int. Factor by which to scale the variables. All entries in
    # input_variables are scaled by the same factor
    #
    # 3. num_exprs: int. Number of experiments to be generated
    #
    # 4. scaling_variable: variable of type str or tuple(str). The scaling order is determined by
    # the value in input_variables corresponding to scaling_variable. If no scaling_variable is
    # specified, the scaling order is defined using the first element in input_variables
    #
    # output:
    # scaling_order: list[int]. list of indices, with one value for each dimension,
    # output:
    # output_variables: dict[str, int | list[int]]. num_exprs values for each
    # dimension of the input variable scaled by the scaling_factor according to the
    # scaling policy
    def scale_experiment_variables(
        self, input_variables, scaling_factor, num_exprs, scaling_variable=None
    ):
        # check if variable list is not empty
        if not input_variables:
            return {}

        # if undefined, set scaling_variable to the first param in the input_params dict
        if not scaling_variable:
            scaling_variable = next(iter(input_variables))

        # check if scaling_variable is a valid key into the input_variables dictionary
        if scaling_variable not in input_variables:
            raise RuntimeError("Invalid ordering variable")

        # check if:
        # 1. input_variables key value pairs are either of type str: int or tuple(str): list(int)
        # 2. the length of key: tuple(str) is equal to length of value: list(int)
        # 3. all values of type list(int) have the same length i.e. the same number of dimensions
        n_dims = None
        for k, v in input_variables.items():
            if isinstance(k, str):
                if not isinstance(v, int):
                    raise RuntimeError("Invalid key-value pair. Expected type str->int")
            elif isinstance(k, tuple) and all(isinstance(s, str) for s in k):
                if isinstance(v, list) and all(isinstance(i, int) for i in v):
                    if len(k) != len(v):
                        raise RuntimeError(
                            "Invalid value. Length of key {k} does not match the length of value {v}"
                        )
                    else:
                        if not n_dims:
                            n_dims = len(v)
                        if len(v) != n_dims:
                            raise RuntimeError(
                                "Variables to be scaled have different dimensions"
                            )
                else:
                    raise RuntimeError(
                        "Invalid key-value pair. Expected type tuple(str)->list[int]"
                    )
            else:
                raise RuntimeError("Invalid key. Expected type str or tuple(str)")

        # compute the scaling order based on the scaling_variable
        scaling_order_index = self.configure_scaling_policy(
            input_variables, scaling_variable
        )

        scaled_variables = {}
        for key, val in input_variables.items():
            scaled_variables[key] = (
                [[v] for v in val] if isinstance(val, list) else [[val]]
            )

        # Take initial parameterized vector for experiment, for each experiment after the first, scale one
        # dimension of that vector by the scaling factor; cycle through the dimensions in round-robin fashion.
        for exp_num in range(num_exprs - 1):
            for param in scaled_variables.values():
                if len(param) == 1:
                    param[0].append(param[0][-1] * scaling_factor)
                else:
                    for p_idx, p_val in enumerate(param):
                        p_val.append(
                            p_val[-1] * scaling_factor
                            if p_idx
                            == scaling_order_index[exp_num % len(scaling_order_index)]
                            else p_val[-1]
                        )

        output_variables = {}
        for k, v in scaled_variables.items():
            if isinstance(k, tuple):
                for i in range(len(k)):
                    output_variables[k[i]] = v[i] if len(v[i]) > 1 else v[i][0]
            else:
                output_variables[k] = v[0] if len(v[0]) > 1 else v[0][0]
        return output_variables

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
        modifier_list = [{"name": "allocation"}]
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

        expr_name_list = [self.name, self.workload]
        for cls in self.helpers:
            helper_prefix = cls.get_helper_name_prefix()
            if helper_prefix:
                expr_name_list.append(helper_prefix)
        expr_name = "_".join(expr_name_list + self.expr_name)

        return {
            self.name: {
                "workloads": {
                    self.workload: {
                        "experiments": {
                            expr_name: {
                                "variants": {"package_manager": "spack"},
                                "variables": self.variables,
                                "zips": self.zips,
                                "matrix": self.matrix,
                                "exclude": (
                                    {"where": self.excludes} if self.excludes else {}
                                ),
                            }
                        }
                    }
                }
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

        spack_variants = [cls.get_spack_variants() for cls in self.helpers]
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
