# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from enum import Enum

from benchpark.directives import variant
from benchpark.error import BenchparkError
from benchpark.experiment import ExperimentHelper


class ScalingMode(Enum):
    Strong = "strong"
    Weak = "weak"
    Throughput = "throughput"


def Scaling(*modes):
    for mode in modes:
        if not isinstance(mode, ScalingMode):
            raise ValueError(f"Invalid scaling mode: {mode}")

    # Base scaling class
    class BaseScaling:
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

        variant(
            "strong",
            default=False,
            description="Strong scaling",
        )
        variant(
            "weak",
            default=False,
            description="Weak scaling",
        )
        variant(
            "throughput",
            default=False,
            description="Throughput scaling",
        )

    scaling_calls = []

    for mode in modes:
        if mode == ScalingMode.Strong:
            scaling_calls.append(
                (
                    lambda self: self.spec.satisfies("+" + ScalingMode.Strong.value),
                    lambda self: self.scale_params(
                        self.scaling_config[ScalingMode.Strong]
                    ),
                )
            )

        if mode == ScalingMode.Weak:
            scaling_calls.append(
                (
                    lambda self: self.spec.satisfies("+" + ScalingMode.Weak.value),
                    lambda self: self.scale_params(
                        self.scaling_config[ScalingMode.Weak]
                    ),
                )
            )

        if mode == ScalingMode.Throughput:
            scaling_calls.append(
                (
                    lambda self: self.spec.satisfies(
                        "+" + ScalingMode.Throughput.value
                    ),
                    lambda self: self.scale_params(
                        self.scaling_config[ScalingMode.Throughput]
                    ),
                )
            )

    def scale(self):
        for check, action in scaling_calls:
            if check(self):
                return action(self)
        raise RuntimeError("No valid scaling mode matched")

    BaseScaling.scale = scale

    def scale_params(self, scaling_config):
        """
        scaling_config is a dictionary of the form variable -> scaling_func
        This method scales the problem by applying scaling_function to each variable in scaling_config
        Starting with the smallest value dimension for the first variable in scaling_config,
        the scaling proceeds in a round-robin manner for the specified number of iterations
        """

        scaling_vars = [getattr(self.expr_vars, v) for v in scaling_config.keys()]

        dim_set = set()
        for v in scaling_vars:
            if v.ndims != 1:
                dim_set.add(v.ndims)

        if dim_set and len(dim_set) > 1:
            raise BenchparkError(
                "All scaling variables must either have the same number of dimensions, or only one dimension"
            )

        start_dim = scaling_vars[0].min_dim
        ndims = dim_set.pop() if dim_set else 1

        num_exprs = int(self.spec.variants["scaling-iterations"][0]) - 1
        scaling_factor = int(self.spec.variants["scaling-factor"][0])

        for itr in range(num_exprs):
            dim = (start_dim + itr) % ndims
            for var_name, scaling_func in scaling_config.items():
                if scaling_func:
                    getattr(self.expr_vars, var_name).scale_dim(
                        itr, dim, scaling_func, scaling_factor
                    )

    BaseScaling.scale_params = scale_params

    # The register_scaling_config method defines the scaled variables and their
    # scaling function for each scaling mode supported in the experiment
    # The input to register_scaling_config is a dictionary of the form
    # ScalingMode -> { scaled_var: scaling_function }
    # An entry is required for each ScalingMode supported in the experiment
    # For a multi-dimensional variable of the form:
    # num_procs -> { "px": 2, "py": 2, "pz": 1 }, the value of scaled_var is "num_procs"
    # For a scalar variable, the value of scaled_var is the name of the variable
    # Each scaled_var specified in register_scaling_config must be added to the
    # list of experiment variables using add_experiment_variable
    #
    # The scaling function has the following form
    # def scaling_function(var, itr, dim, scaling_factor):
    #    return ...
    # The arguments for the scaling_function are:
    # var: benchpark.Variable instance of the scaled variable
    # itr: The current iteration in the specified number of scaling iterations
    # dim: The current dimension that is being scaled
    # scaling_factor: The factor by which the variable dimension must be scaled
    # The scaling_function must return the new scaled value for the variable dimension
    #
    # scaling starts from the dimension with the minimum value for the first variable
    # in the list of variables and proceeds through the dimensions in a round-robin
    # manner for the specified number of scaling iterations
    # e.g. if the scaling config is defined as:
    # ScalingMode.Strong: {
    #     "np": lambda var, itr, dim, sf: var.val(dim) * sf,
    #     "probs": lambda var, itr, dim, sf: var.val(dim) * sf,
    # }, and the starting values of the variables are
    # "np" : { "px": 2,
    #          "py": 2,
    #          "pz": 1 } and,
    # "probs" : { "nx": 16,
    #             "ny": 32,
    #             "nz": 32 },
    # then after 4 scaling iterations (3 scalings), the
    # final values of the scaled variables will be
    # "np" : { "px": [2,2,4,4]
    #          "py": [2,2,2,4]
    #          "pz": [1,2,2,2] } and,
    # "probs" : { "nx": [16,16,32,32]
    #             "ny": [32,32,32,64]
    #             "nz": [32,64,64,64] },
    # Note that scaling starts with the minimum value dimension (pz) of the
    # first variable (np) and proceeds in a round-robin manner

    def register_scaling_config(self, scaling_config):
        unimplemented_modes = []
        for mode in modes:
            if mode not in scaling_config.keys():
                unimplemented_modes.append(mode)
        if unimplemented_modes:
            raise ValueError(
                f"Experiment supports scaling modes {', '.join(m.value for m in unimplemented_modes)}, but does not define a config for them"
            )

        for var in scaling_config.keys():
            if var not in modes:
                raise ValueError(
                    f"Unsupported scaling config '{var}', this experiment only supports {', '.join(m.value for m in modes)}"
                )
        self.scaling_config = scaling_config

    BaseScaling.register_scaling_config = register_scaling_config

    # Helper class
    class Helper(ExperimentHelper):
        def get_helper_name_prefix(self):
            for s in [
                ScalingMode.Strong.value,
                ScalingMode.Weak.value,
                ScalingMode.Throughput.value,
            ]:
                if self.spec.satisfies("+" + s):
                    return s + "_scaling"
            return "no_scaling"

    return type(
        "ExperimentScaling",
        (BaseScaling,),
        {
            "Helper": Helper,
        },
    )
