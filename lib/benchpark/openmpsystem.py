# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.directives import system_provides


class OpenMPSystem:
    system_provides("openmp")

    def system_specific_variables(self, system):
        return {}
