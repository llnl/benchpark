#!/usr/bin/env python3
# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

"""Query and update the active Spack environment for compiler_memtrace."""

import argparse
import json
import os

import spack.builder
from spack.active_environment import active_environment
from spack.spec import Spec


def root_info(name):
    spec = next(s for s in active_environment().concrete_roots() if s.name == name)
    data = {
        "prefix": str(spec.prefix),
        "hash": spec.dag_hash(),
        "compiler": spec["cxx"].dag_hash(),
        "flags": {
            key: [str(flag) for flag in flags]
            for key, flags in spec.compiler_flags.items()
        },
        "rocm": spec.satisfies("+rocm"),
    }
    if "hip" in spec:
        data["hip"] = str(spec["hip"].prefix)
    if "amdgpu_target" in spec.variants:
        data["targets"] = list(spec.variants["amdgpu_target"].value)
    if spec.satisfies("build_system=cmake"):
        root = str(spack.builder.create(spec.package).root_cmakelists_dir)
        data["cmake_root"] = (
            os.path.relpath(root, spec.package.stage.source_path) if os.path.isabs(root) else root
        )
    if spec.name == "memtrace-llvm":
        data["python"] = spec["python"].command.path
        data["reader_paths"] = spec.package.reader_paths()
        data["reader_preload"] = spec.package.reader_preload()
    return data


def use_builtin_numpy():
    """Replace the removed Benchpark override in an existing concrete DAG."""
    env = active_environment()
    with env.write_transaction():
        root = next(s for s in env.concrete_roots() if s.name == "memtrace-llvm")
        numpy = root["py-numpy"]
        if numpy.namespace != "builtin":
            env.mutate(
                selectors=[Spec("/" + numpy.dag_hash())],
                mutators=[Spec("builtin.py-numpy")],
            )
            print("compiler_memtrace: selected builtin NumPy for the reader")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    info = subparsers.add_parser("root-info")
    info.add_argument("name")
    subparsers.add_parser("use-builtin-numpy")
    args = parser.parse_args()
    if args.command == "root-info":
        print(json.dumps(root_info(args.name)))
    else:
        use_builtin_numpy()


if __name__ == "__main__":
    main()
