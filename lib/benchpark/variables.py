# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


from functools import reduce


class VariableDict:
    def __init__(self):
        self._vars = {}

    def __getattr__(self, name):
        if name in self._vars:
            return self._vars[name]
        raise AttributeError(f"'{__class__.__name__}' object has no attribute '{name}'")

    # values must be a dict of type str->type or str->list(type)
    def add_dimensional_variable(
        self, name, values, named=False, zipped=True, matrixed=False
    ):
        self._vars[name] = Variable(values, named, zipped, matrixed)

    # values must be a non-dict type or list(type)
    def add_scalar_variable(
        self, name, values, named=False, zipped=False, matrixed=False
    ):
        self._vars[name] = Variable({name: values}, named, zipped, matrixed)

    def extend(self, vardict):
        if not vardict:
            return
        if not isinstance(vardict, VariableDict):
            raise TypeError("input variable must be of type VariableDict")
        else:
            for k, v in vardict.items():
                self.assign_variable(k, v)

    def assign_variable(self, name, var):
        if not isinstance(var, Variable):
            raise TypeError("input variable must be of type Variable")
        else:
            self._vars[name] = var

    def __iter__(self):
        return iter(self._vars)

    def items(self):
        return self._vars.items()

    def keys(self):
        return self._vars.keys()

    def values(self):
        return self._vars.values()

    def __repr__(self):
        return f"{self.__class__.__name__}({self._vars})"


class Variable:
    def __init__(self, var, named=False, zipped=False, matrixed=False):
        if not isinstance(var, dict):
            raise TypeError(
                "Input argument to a variable constructor must be a dictionary"
            )

        for k, v in var.items():
            if not isinstance(k, str):
                raise TypeError("Labels of a variable must be strings")

        values = list(var.values())
        has_list = any(isinstance(v, list) for v in values)

        if has_list:
            if not all(isinstance(v, list) for v in values):
                raise ValueError(
                    "If one dim is specified as a list, all dims must be a list"
                )

            lengths = {len(v) for v in values}
            if len(lengths) > 1:
                raise ValueError("All lists must have the same length")

        if has_list:
            self._var = {k: v for k, v in var.items()}
        else:
            self._var = {k: [v] for k, v in var.items()}

        self._dims = list(self._var.keys())
        self._ndims = len(self._var)
        self._named = named
        self._zipped = zipped
        self._matrixed = matrixed

    def __getitem__(self, key):
        return self._var[key]

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
        self._var[key].append(value)

    @property
    def is_named(self):
        return self._named

    @property
    def is_matrixed(self):
        return self._matrixed

    @property
    def is_zipped(self):
        return self._zipped

    def reduce(self, func):
        return [reduce(func, col) for col in zip(*self._var.values())]

    # This method checks the last value for each dimension
    # and returns the dimension that has the minimum value
    # for its last entry
    # e.g. px: [1,1,2], py: [1,2,2] and pz: [1,1,1]
    # the last values are px: 2, py: 2 and pz: 1
    # hence the method returns 2 (the index of pz)
    @property
    def min_dim(self):
        last_values = [v[-1] for v in self._var.values()]
        return last_values.index(min(last_values))

    @property
    def ndims(self):
        return self._ndims

    def val(self, key):
        return self[key][-1]

    def scale_dim(self, itr, dim, scaling_func, sf):
        key = self._dims[0] if self.ndims == 1 else self._dims[dim]

        next_val = scaling_func(self, itr, key, sf)

        if not next_val:
            return
        elif isinstance(next_val, list):
            idx = 0
            for k in self._dims:
                self._var[k].append(next_val[idx])
                idx += 1
        else:
            for k in self._dims:
                if k == key:
                    self._var[k].append(scaling_func(self, itr, k, sf))
                else:
                    self._var[k].append(self.val(k))
