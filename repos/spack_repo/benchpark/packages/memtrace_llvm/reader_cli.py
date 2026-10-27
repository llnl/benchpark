#!/usr/bin/env python3
# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

"""Launch the installed memtrace reader with its Python and BLAS dependencies."""

import json
import os
import sys
from pathlib import Path


def main():
    config = json.loads(Path(__file__).with_name("reader.json").read_text())
    preload = config["preload"]
    current = os.environ.get("LD_PRELOAD", "").split()
    if any(path not in current for path in preload):
        env = os.environ.copy()
        env["LD_PRELOAD"] = " ".join(preload + current)
        os.execvpe(sys.executable, [sys.executable, *sys.argv], env)
    sys.path[:0] = config["paths"]
    from memtrace.cli import main as reader_main

    return reader_main()


if __name__ == "__main__":
    sys.exit(main())
