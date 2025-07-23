# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from inspect import currentframe, getframeinfo

DEBUG = False


def get_linenumber():
    cf = currentframe()
    return cf.f_back.f_back.f_lineno


def get_filename():
    cf = currentframe()
    return os.path.basename(getframeinfo(cf.f_back).filename)


def debug_print(message):
    if DEBUG:
        print(
            "(debug) " + get_filename() + "::" + str(get_linenumber()) + " " + message,
            file=sys.stderr,
        )
