# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from benchpark.spec import Spec


def test_spec_hashing_and_eq():
    x = Spec("+x")
    y = Spec("+y")

    items = set([x])
    assert y not in items
