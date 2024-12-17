# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

#: at what level we should write stack traces or short error messages
#: this is module-scoped because it needs to be set very early
debug = 0


class BenchparkError(Exception):
    """This is the superclass for all Benchpark errors.
    Subclasses can be found in the modules they have to do with.
    """
