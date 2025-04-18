# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from benchpark.directives import variant
from benchpark.experiment import ExperimentHelper
from enum import Enum
import math


class ScalingVar:
    def __init__(self, var):
        if not isinstance(var, dict):
            raise TypeError("scaling variable must be a dictionary")

        for k, v in var.items():
            if not isinstance(k, str):
                raise TypeError(f"Labels of a scaling variable must be strings")
            if not isinstance(v, (int, float)):
                raise TypeError(f"Values of a scaling variable must be ints")

        self._var = var
        self._dims = list(self._var.keys())
        self._ndims = len(self._var)

    def __getitem__(self, key):
        return self._var[key]
    
    def __setitem__(self, key, value):
        if key in self._var:
            self._var[key] = value
        else:
            raise KeyError(f"Cannot add new dimension: '{key}'.")
    
    def __iter__(self):
        return iter(self._var)
    
    def __len__(self):
        return self._ndims
    
    def __contains__(self, key):
        return key in self._var
    
    def dims(self):
        return self._dims
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self._var})"

    def set_dim(self, dim, value):
        key = self._dims[dim]
        self._var[key] = value
    
    def scale_dim(self, dim, func):
        key = self._dims[dim]
        self._var[key] = func(self._var[key])
    
    @property
    def prod(self):
        return math.prod(self._var.values())

    @property
    def min_dim(self):
        return list(self._var.values()).index(min(self._var.values()))

    @property
    def ndims(self):
        return self._ndims


class NumProcs(ScalingVar):
    def __init__(self, var):
        if isinstance(var, NumProcs):
            super().__init__({k: var._var[k] for k in var.dims()})
        else:
            super().__init__(var)


class ProblemSizes(ScalingVar):
    def __init__(self, var):
        if isinstance(var, ProblemSizes):
            super().__init__({k: var._var[k] for k in var.dims()})
        else:
            super().__init__(var)


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

    def strong_scale(self):
        """
        Strong scales the problem by increasing the number of processes along one axis
        and decreasing the per-process size accordingly to keep the total problem size constant.
        Raises an error if scaling down the per-process size does not conserve the global problem size.
        """

        if not hasattr(self, 'num_procs') and not isinstance(self.num_procs, NumProcs):
            raise AttributeError("Experiment must define attribute 'num_procs' of type NumProcs")

        if not hasattr(self, 'problem_sizes') and not isinstance(self.problem_sizes, ProblemSizes):
            raise AttributeError("Experiment must define attribute 'problem_sizes' of type ProblemSizes")

        num_procs = NumProcs(self.num_procs)
        problem_sizes = ProblemSizes(self.problem_sizes)
        ndims = num_procs.ndims

        if problem_sizes.ndims != num_procs.ndims:
            raise BenchparkError(
                f"problem_sizes dimensions {self.problem_sizes.dims} do not match num_procs dimensions {self.num_procs.dims}"
            )

        orig_global_prob_size = num_procs.prod * problem_sizes.prod
       
        num_exprs = int(self.spec.variants["scaling-iterations"][0]) - 1
        scaling_factor = int(self.spec.variants["scaling-factor"][0])

        result = {}
        for k in num_procs.dims():
            result[k] = [num_procs[k]]
        for k in problem_sizes.dims():
            result[k] = [problem_sizes[k]]
        result["nprocs"] = [num_procs.prod]
        result["process_problem_size"] = [problem_sizes.prod]
        result["total_problem_size"] = [orig_global_prob_size]

        start_dim = num_procs.min_dim
 
        for itr in range(num_exprs):
            idx = (start_dim + itr) % ndims

            num_procs.scale_dim(idx, lambda v: v * scaling_factor)
            problem_sizes.scale_dim(idx, lambda v: v // scaling_factor)

            new_global_prob_size = num_procs.prod * problem_sizes.prod

            if new_global_prob_size != orig_global_prob_size:
                errMsg = f"""
Global problem size not conserved:
Original size: {orig_global_prob_size}
New size: {new_global_prob_size}
                """
                raise BenchparkError(errMsg)

            for k in num_procs.dims():
                result[k].append(num_procs[k])
            for k in problem_sizes.dims():
                result[k].append(problem_sizes[k])

            result["nprocs"].append(num_procs.prod)
            result["process_problem_size"].append(problem_sizes.prod)
            result["total_problem_size"].append(new_global_prob_size)

        return result

    def check_output_variables(self):
        if not hasattr(self, 'variables'):
            raise AttributeError("Missing 'variables' attribute in self.")

        required_keys = ['nprocs', 'process_problem_size', 'total_problem_size']
        for key in required_keys:
            if key not in self.variables:
                raise AttributeError(f"'variables' dictionary is missing required key '{key}'.")

    setattr(ScalingType, 'strong_scale', strong_scale)
    setattr(ScalingType, 'check_output_variables', check_output_variables)

    return ScalingType

def UsesGlobalDomains(*modes):
    ScalingType = Scaling(*modes)

    setattr(ScalingType, 'strong_scale', strong_scale)

    return ScalingType
