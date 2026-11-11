# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.repo import ObjectTypes, paths

Fluxtainer = paths[ObjectTypes.systems].get_obj_class("fluxtainer")


class FluxtainerAws(Fluxtainer):
    """Fluxtainer configuration for AWS instances with 32 cores per node."""

    def __init__(self, spec):
        super().__init__(spec)
        self.sys_cores_per_node = 32
