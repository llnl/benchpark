# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

DEBUG = False


def debug_print(message):
    if DEBUG:
        print("(debug) " + str(message))
