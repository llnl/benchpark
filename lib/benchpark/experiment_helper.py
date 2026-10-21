# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.variables import VariableDict


class ExperimentHelper:
    """Base interface for experiment feature helpers."""

    def __init__(self, exp):
        self.spec = exp.spec
        self._expr_vars = VariableDict()
        self.env_vars = {
            "set": {},
            "append": [{"paths": {}, "vars": {}}],
            "prepend": [{"paths": {}, "vars": {}}],
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
        """Set value of environment variable."""
        self.env_vars["set"][name] = value

    def append_environment_variable(self, name, value, target="paths"):
        """Append to an environment path or variable."""
        self.env_vars["append"][0][target][name] = value

    def prepend_environment_variable(self, name, value, target="paths"):
        """Prepend to an environment path or variable."""
        self.env_vars["prepend"][0][target][name] = value

    def compute_config_variables(self):
        pass

    def compute_config_variables_wrapper(self):
        self.compute_config_variables()
        return self._expr_vars, self.env_vars
