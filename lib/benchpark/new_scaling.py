# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant
from benchpark.experiment import ExperimentHelper, requires_experiment_variables
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

        def strong_scale(self):
            raise NotImplementedError(
                f"Experiment must implement strong scaling"
            )

        def weak_scale(self):
            raise NotImplementedError(
                f"Experiment must implement weak scaling"
            )

        def throughput_scale(self):
            raise NotImplementedError(
                f"Experiment must implement throughput scaling"
            )

        def scale(self):
            if self.spec.satisfies("scaling=strong"):
                return self.strong_scale() 
            elif self.spec.satisfies("scaling=weak"): 
                return self.weak_scale() 
            elif self.spec.satisfies("scaling=throughput"): 
                return self.throughput_scale() 

    # Helper class
    class Helper(ExperimentHelper):
        def get_helper_name_prefix(self):
            return (
                f"{self.spec.variants['scaling'][0]}_scaling"
                if not self.spec.satisfies("scaling=off")
                else ""
            )

    return type(
        "ExperimentScaling",
        (BaseScaling,),
        {
            "Helper": Helper,
        },
    )


def UsesPerProcessDomains(*modes):
    ScalingType = Scaling(*modes)

    @requires_experiment_variables("num_procs", "problem_sizes")
    def strong_scale(self):
        """
        Strong scales the problem by increasing the number of processes along each dimension in a
        round-robin manner and decreasing the corresponding per-process size to keep the total problem
        size constant.
        Raises an error if scaling down the per-process size does not conserve the global problem size.
        """

        num_procs = self.expr_vars.num_procs
        problem_sizes = self.expr_vars.problem_sizes

        if problem_sizes.ndims != num_procs.ndims:
            raise BenchparkError(
                f"problem_sizes dimensions {problem_sizes.dims} do not match num_procs dimensions {num_procs.dims}"
            )

        num_exprs = int(self.spec.variants["scaling-iterations"][0]) - 1
        scaling_factor = int(self.spec.variants["scaling-factor"][0])

        orig_global_prob_size = num_procs.prod[-1] * problem_sizes.prod[-1]
       
        start_dim = num_procs.min_dim
        ndims = num_procs.ndims

        total_problem_size = [orig_global_prob_size]
 
        for itr in range(num_exprs):
            dim = (start_dim + itr) % ndims

            num_procs.scale_dim(dim, lambda v: v * scaling_factor)
            problem_sizes.scale_dim(dim, lambda v: v // scaling_factor)

            new_global_prob_size = num_procs.prod[-1] * problem_sizes.prod[-1]
            total_problem_size.append(new_global_prob_size)

            if new_global_prob_size != orig_global_prob_size:
                errMsg = f"""
Global problem size not conserved:
Original size: {orig_global_prob_size}
New size: {new_global_prob_size}
                """
                raise BenchparkError(errMsg)

        result = VariableDict()
        result.add_scalar_variable("nprocs", num_procs.prod)
        result.add_scalar_variable("process_problem_size", problem_sizes.prod)
        result.add_scalar_variable("total_problem_size", total_problem_size)

        return result

    @requires_experiment_variables("num_procs", "problem_sizes")
    def weak_scale(self):
        """
        Weak scales the problem by increasing the number of processes along each dimension in a
        round-robin manner.
        There are no changes to the per process sizes
        """

        num_procs = self.expr_vars.num_procs
        problem_sizes = self.expr_vars.problem_sizes

        if problem_sizes.ndims != num_procs.ndims:
            raise BenchparkError(
                f"problem_sizes dimensions {problem_sizes.dims} do not match num_procs dimensions {num_procs.dims}"
            )

        num_exprs = int(self.spec.variants["scaling-iterations"][0]) - 1
        scaling_factor = int(self.spec.variants["scaling-factor"][0])

        start_dim = num_procs.min_dim
        ndims = num_procs.ndims
 
        total_problem_size = [num_procs.prod[-1] * problem_sizes.prod[-1]]

        for itr in range(num_exprs):
            dim = (start_dim + itr) % ndims

            num_procs.scale_dim(dim, lambda v: v * scaling_factor)
            total_problem_size.append(num_procs.prod[-1] * problem_sizes.prod[-1])

        result = VariableDict()
        result.add_scalar_variable("nprocs", num_procs.prod)
        result.add_scalar_variable("process_problem_size", problem_sizes.prod)
        result.add_scalar_variable("total_problem_size", total_problem_size)

        return result

    def check_output_variables(self):
        if not hasattr(self, 'expr_vars'):
            raise AttributeError("Missing 'expr_vars' attribute in self.")

        required_keys = ['nprocs', 'process_problem_size', 'total_problem_size']
        for key in required_keys:
            if key not in self.expr_vars:
                raise AttributeError(f"'expr_vars' dictionary is missing required key '{key}'.")

    setattr(ScalingType, 'strong_scale', strong_scale)
    setattr(ScalingType, 'weak_scale', weak_scale)
    setattr(ScalingType, 'check_output_variables', check_output_variables)

    return ScalingType

def UsesGlobalDomains(*modes):
    ScalingType = Scaling(*modes)

    setattr(ScalingType, 'strong_scale', strong_scale)

    return ScalingType
