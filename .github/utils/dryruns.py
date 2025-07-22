# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
import time
import sys
import argparse

import benchpark.paths

sys.path.append(str(benchpark.paths.benchpark_home) + "/spack/lib/spack")
from lib.benchpark.accounting import benchpark_experiments

DEFAULT_SYSTEM="llnl-cluster cluster=dane"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test",
        choices=["cuda", "rocm", "openmp", "mpi", "strong", "weak", "throughput", "modifiers"],
        help="Only run tests of this type",
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Dry runs this script for testing."
    )
    args = parser.parse_args()

    try:
        expr_cmd = subprocess.run(
            [
                "./bin/benchpark",
                "list",
                "experiments",
                "--no-title",
            ],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Output: {e.stdout}\nError: {e.stderr}")
    expr_str = expr_cmd.stdout.decode("utf-8")
    experiments = expr_str.replace(" ", "").replace("\t", "").split("\n")
    experiments = [item for item in experiments if "+" in item]

    mpi_only_expr = set()
    cuda_expr = []
    rocm_expr = []
    openmp_expr = []
    strong_expr = []
    weak_expr = []
    throughput_expr = []

    for e in experiments:
        name = e.split("+")[0]
        mpi_only_expr.add(name)

        if "cuda" in e:
            cuda_expr.append(name)
        elif "rocm" in e:
            rocm_expr.append(name)
        elif "openmp" in e:
            openmp_expr.append(name)

        elif "strong" in e:
            strong_expr.append(name)
        elif "weak" in e:
            weak_expr.append(name)
        elif "throughput" in e:
            throughput_expr.append(name)

    sys_dict = {}
    try:
        sys_dict["mpi"] = subprocess.run(
            [
                "./bin/benchpark",
                "list",
                "systems",
                "--no-title",
            ],
            capture_output=True,
            check=True,
        )
        for pmodel in ["cuda", "rocm", "openmp"]:
            sys_dict[pmodel] = subprocess.run(
                [
                    "./bin/benchpark",
                    "list",
                    "systems",
                    "--no-title",
                    "-p",
                    pmodel,
                ],
                capture_output=True,
                check=True,
            )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Output: {e.stdout}\nError: {e.stderr}")
    str_dict = {}
    for key in sys_dict:
        temp_str = sys_dict[key].stdout.decode("utf-8")
        str_dict[key] = [
            i
            for i in temp_str.replace(" " * 4, "").replace("\t", "").split("\n")
            if i != ""
        ]

    try:
        mods = subprocess.run(
            [
                "./bin/benchpark",
                "list",
                "modifiers",
                "--no-title",
            ],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Output: {e.stdout}\nError: {e.stderr}")
    temp_mods = mods.stdout.decode("utf-8")
    nmods = [
            i
            for i in temp_mods.replace(" " * 4, "").replace("\t", "").split("\n")
            if i != "" and i not in ["allocation", "caliper"]
        ]

    caliper_exp = [e for e in benchpark_experiments(exclude_variants=[]) if "+caliper" in e]
    modifiers_expr = caliper_exp + [e+"+"+m for e in mpi_only_expr for m in nmods]

    # Map test types to (expr_list, sys_list)
    exprs_to_sys = [
        ("mpi", mpi_only_expr, str_dict["mpi"]),
        ("cuda", cuda_expr, str_dict["cuda"]),
        ("rocm", rocm_expr, str_dict["rocm"]),
        ("openmp", openmp_expr, str_dict["openmp"]),
        ("strong", strong_expr, str_dict["mpi"]),
        ("weak", weak_expr, str_dict["mpi"]),
        ("throughput", throughput_expr, str_dict["mpi"]),
        ("modifiers", modifiers_expr, [DEFAULT_SYSTEM])
    ]

    # Filter based on --test argument
    if args.test:
        exprs_to_sys = [tup for tup in exprs_to_sys if tup[0] == args.test]

    # Calculate total number of tests before running
    total_tests = sum(
        len(expr_spec_list) * len(sys_spec_list)
        for _, expr_spec_list, sys_spec_list in exprs_to_sys
    )
    print(f"Total tests to run: {total_tests}")

    start = time.time()
    errors = {}
    fail_tests = 0
    ran_tests = 0
    for _, expr_spec_list, sys_spec_list in exprs_to_sys:
        for espec in expr_spec_list:
            for sspec in sys_spec_list:
                ran_tests += 1
                print(f"Running '{espec}' '{sspec}'")
                if args.dryrun:
                    pass
                else:
                    try:
                        cmd = f'source .github/utils/dryrun.sh "{sspec}" "{espec}"'
                        subprocess.run(
                            ["bash", "-c", cmd],
                            capture_output=True,
                            check=True,
                        )
                    except subprocess.CalledProcessError as e:
                        errors[f"{espec} {sspec}"] = e.stderr.decode()
                        fail_tests += 1
    end = time.time()
    print(f"Elapsed: {(end-start)/60:.2f} minutes")

    print(f"{ran_tests-fail_tests} Passing. {fail_tests} Failing.")
    for key, value in errors.items():
        print(key)
        print(value)

    if fail_tests > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
