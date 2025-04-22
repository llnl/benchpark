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
        raise AttributeError(f"'DictWrapper' object has no attribute '{name}'")

    # values must be a dict of type str->type or str->list(type)
    def add_dimensional_variable(self, name, values, named=False, scalable=False):
        if scalable:
            self._vars[name] = ScaledVariable(values, named)
        else:
            self._vars[name] = Variable(values, named)

    # values must be a non-dict type or list(type)
    def add_scalar_variable(self, name, values, named=False, scalable=False):
        if scalable:
            self._vars[name] = ScaledVariable({name:values}, named)
        else:
            self._vars[name] = Variable({name:values}, named)

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
    def __init__(self, var, named=False):
        if not isinstance(var, dict):
            raise TypeError("Input argument to a variable constructor must be a dictionary")

        for k, v in var.items():
            if not isinstance(k, str):
                raise TypeError(f"Labels of a scaling variable must be strings")

        values = list(var.values())
        has_list = any(isinstance(v, list) for v in values)

        if has_list:
            if not all(isinstance(v, list) for v in values):
                raise ValueError("If one dim is specified as a list, all dims must be a list")

            lengths = {len(v) for v in values}
            if len(lengths) > 1:
                raise ValueError("All lists must have the same length")

        if has_list:
            self._var = { k: v for k,v in var.items() }
        else:
            self._var = { k: [v] for k,v in var.items() }

        self._dims = list(self._var.keys())
        self._ndims = len(self._var)
        self._named = named

    def __getitem__(self, key):
        return self._var[key]
    
    def __setitem__(self, key, value):
        if key in self._var:
            self._var[key].append(value)
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
        self._var[key].append(value)

    @property
    def is_named(self):
        return self._named

    @property
    def prod(self):
        return self.reduce(lambda x, y: x * y)

    def reduce(self, func):
        return [reduce(func, col) for col in zip(*self._var.values())]

    @property
    def min_dim(self):
        last_values = [v[-1] for v in self._var.values()]
        return last_values.index(min(last_values))
    
    @property
    def ndims(self):
        return self._ndims


class ScaledVariable(Variable):
    def __init__(self, var, named=False):
        if not isinstance(var, dict):
            raise TypeError("scaling variable must be a dictionary")

        for k, v in var.items():
            if not isinstance(v, (int, float)) and not (isinstance(v, list) and all(isinstance(x, (int, float)) for x in v)):
                raise TypeError(f"Values of a scaling variable must be a numeric type")

        super().__init__(var, named)

    # appends an entry for each dimension by applying a scaling function
    # to the specified index of that dimension
    # scales the last index of each dimension if no index is specified
    def scale_dim(self, dim, func, idx=-1):
        key = self._dims[dim]
        for k in self._dims:
            if k == key:
                self._var[k].append(func(self._var[k][idx]))
            else:
                self._var[k].append(self._var[k][idx])
