# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant
from benchpark.experiment import ExperimentHelper
from benchpark.variables import VariableDict
from enum import Enum
from functools import reduce


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
            "scaling",
            default="off",
            values=("off",) + tuple(m.value for m in modes),
            description="Scaling modes",
        )

    scaling_calls = []

    for mode in modes:
        if mode == ScalingMode.Strong:
            scaling_calls.append(
                (
                    lambda self: self.spec.satisfies("scaling=strong"),
                    lambda self: self.scale_params(
                        self.scaling_config[ScalingMode.Strong]
                    ),
                )
            )
 
        if mode == ScalingMode.Weak:
            scaling_calls.append(
                (
                    lambda self: self.spec.satisfies("scaling=weak"),
                    lambda self: self.scale_params(
                        self.scaling_config[ScalingMode.Weak]
                    ),
                )
            )

        if mode == ScalingMode.Throughput:
            scaling_calls.append(
                (
                    lambda self: self.spec.satisfies("scaling=throughput"),
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
                f"All scaling variables must either have the same number of dimensions, or only one dimension"
            )

        start_dim = scaling_vars[0].min_dim
        ndims = dim_set.pop() if dim_set else 1

        num_exprs = int(self.spec.variants["scaling-iterations"][0]) - 1
        scaling_factor = int(self.spec.variants["scaling-factor"][0])

        for itr in range(num_exprs):
            dim = (start_dim + itr) % ndims
            for var_name, scaling_func in scaling_config.items():
                getattr(self.expr_vars, var_name).scale_dim(
                    itr, dim, scaling_func, scaling_factor
                )

    BaseScaling.scale_params = scale_params

    def register_scaling_config(self, scaling_config):
        unimplemented_modes = []
        for mode in modes:
            if mode not in scaling_config.keys():
                unimplemented_modes.append(mode)
        if unimplemented_modes:
            raise ValueError(
                f"Experiment supports scaling modes {', '.join(m.value for m in unimplemented_modes)}, but does not define a config for them"
            )

        scaling_vars = []
        scaling_funcs = []
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
            return (
                f"{self.spec.variants['scaling'][0]}_scaling"
                if not self.spec.satisfies("scaling=off")
                else "no_scaling"
            )

    return type(
        "ExperimentScaling",
        (BaseScaling,),
        {
            "Helper": Helper,
        },
    )
