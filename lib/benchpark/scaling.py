# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.error import BenchparkError
from benchpark.directives import variant
from benchpark.experiment import ExperimentHelper


class Scaling:
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

    def scale_variables(self, input_vars):
        if not input_vars:
            return

        scaled_variable = input_vars[0]
        if not isinstance(scaled_variable, dict):
            raise BenchparkError(f"Input vars must be a dictionary of type str->int")
        else:
            num_dims = len(scaled_variable)
        start_dim_key = min(scaled_variable, key=scaled_variable.get)
        start_dim = list(scaled_variable.keys()).index(start_dim_key)

        for var in input_vars:
            if len(var) != num_dims:
                raise BenchparkError(
                    f"Number of variable dimensions {len(var)} does not match the total number of dimensions {num_dims}"
                )

        scaling_vectors = self.setup_scaling_vectors(num_dims, start_dim)

        variables = {}

        for var in input_vars:
            for sv, (vk, vv) in zip(scaling_vectors, var.items()):
                variables[vk] = f"{{{sv}}}*{vv}"

        return variables

    def setup_scaling_vectors(self, num_dims, start_dim):
        scaling_vectors = {f"sf{n}": [1] for n in range(num_dims)}
        values = [1] * num_dims

        if start_dim:
            if start_dim >= num_dims:
                raise BenchparkError(
                    f"Start dim for scaling {start_dim} cannot be greater than the total number of dimensions {num_dims}"
                )

        num_exprs = int(self.spec.variants["scaling-iterations"][0]) - 1
        scaling_factor = int(self.spec.variants["scaling-factor"][0])

        for itr in range(num_exprs):
            idx = (start_dim + itr) % num_dims
            values[idx] *= scaling_factor
            for i in range(num_dims):
                scaling_vectors[f"sf{i}"].append(values[i])

        for p, sv in scaling_vectors.items():
            self.add_experiment_variable(p, sv)

        return list(scaling_vectors.keys())

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


class StrongScaling(Scaling):
    variant(
        "strong",
        default=False,
        description="Strong scaling",
    )

    def compute_strong_scaling_expr_config(self):
        raise NotImplementedError(
            "Experiment must provide a strong scaling configuration"
        )

    def generate_strong_scaling_params(
        self, resource_variable, scaling_factor, num_exprs
    ):
        return self.scale_experiment_variables(
            resource_variable, scaling_factor, num_exprs
        )

    class Helper(ExperimentHelper):
        def get_helper_name_prefix(self):
            return "strong_scaling" if self.spec.satisfies("+strong") else ""


class WeakScaling(Scaling):
    variant(
        "weak",
        default=False,
        description="Weak scaling",
    )

    def compute_weak_scaling_expr_config(self):
        raise NotImplementedError(
            "Experiment must provide a weak scaling configuration"
        )

    def generate_weak_scaling_params(
        self, resource_variable, problem_size_variables, scaling_factor, num_exprs
    ):
        scaling_variable = next(iter(resource_variable))
        return self.scale_experiment_variables(
            resource_variable | problem_size_variables,
            scaling_factor,
            num_exprs,
            scaling_variable,
        )

    class Helper(ExperimentHelper):
        def get_helper_name_prefix(self):
            return "weak_scaling" if self.spec.satisfies("+weak") else ""


class ThroughputScaling(Scaling):
    variant(
        "throughput",
        default=False,
        description="Throughput scaling",
    )

    def compute_throughput_scaling_expr_config(self):
        raise NotImplementedError(
            "Experiment must provide a throughput scaling configuration"
        )

    def generate_throughput_scaling_params(
        self, problem_size_variables, scaling_factor, num_exprs
    ):
        return self.scale_experiment_variables(
            problem_size_variables, scaling_factor, num_exprs
        )

    class Helper(ExperimentHelper):
        def get_helper_name_prefix(self):
            return "throughput_scaling" if self.spec.satisfies("+throughput") else ""
