# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import re
import subprocess
import sys
import time

DEFAULT_SYSTEM = "llnl-cluster cluster=dane"
# Skip experiments
SKIP_EXPR = [
    # System not enough cores/node
    "gromacs+openmp aws-pcluster instance_type=c6g.xlarge",
    "gromacs+openmp aws-pcluster instance_type=c4.xlarge",
    "gromacs+openmp generic-x86",
    "stream aws-pcluster instance_type=c6g.xlarge",
    "stream aws-pcluster instance_type=c4.xlarge",
    "stream cscs-daint",
    "stream generic-x86",
    # Broken URL's in application.py going to cause dryrun failure
    "genesis",
]


def run_subprocess_cmd(cmd_list, decode=False):
    try:
        result = subprocess.run(cmd_list, capture_output=True, check=True)
        return result.stdout.decode("utf-8") if decode else result
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Command: {' '.join(cmd_list)}\nOutput: {e.stdout}\nError: {e.stderr}"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test",
        choices=[
            "mpi",
            "cuda",
            "rocm",
            "openmp",
            "strong",
            "weak",
            "throughput",
            "modifiers",
        ],
        help="Only run tests of this type",
    )
    parser.add_argument(
        "--dryrun", action="store_true", help="Dry runs this script for testing."
    )
    args = parser.parse_args()

    expr_str = run_subprocess_cmd(
        ["./bin/benchpark", "list", "experiments", "--no-title"], decode=True
    )
    experiments = [
        e for e in expr_str.replace(" ", "").replace("\t", "").split("\n") if e != ""
    ]

    mpi_only_expr = set()
    cuda_expr = []
    rocm_expr = []
    openmp_expr = []
    strong_expr = []
    weak_expr = []
    throughput_expr = []

    for e in experiments:
        benchmark = e.split("+")[0]

        if "mpi" in e:
            mpi_only_expr.add(benchmark)
        if "cuda" in e:
            cuda_expr.append(benchmark + "+cuda")
        if "rocm" in e:
            rocm_expr.append(benchmark + "+rocm")
        if "openmp" in e:
            openmp_expr.append(benchmark + "+openmp")
        if "strong" in e:
            strong_expr.append(benchmark + "+strong")
        if "weak" in e:
            weak_expr.append(benchmark + "+weak")
        if "throughput" in e:
            throughput_expr.append(benchmark + "+throughput")

    str_dict = {}
    for pmodel in ["mpi", "cuda", "rocm", "openmp"]:
        cmd = ["./bin/benchpark", "list", "systems", "--no-title"]
        if pmodel != "mpi":
            cmd += ["-p", pmodel]
        output = run_subprocess_cmd(cmd, decode=True)
        lines = output.splitlines()
        expanded_lines = []
        for line in lines:
            # Match patterns like key= [a|b|c]
            match = re.search(r"(.*?)(\w+)=\[(.*?)\]", line)
            if match:
                prefix, key, values = match.groups()
                for v in values.split("|"):
                    expanded_lines.append(f"{prefix}{key}={v}")
            else:
                expanded_lines.append(line)
        str_dict[pmodel] = [
            i
            for i in [j.replace(" " * 4, "").replace("\t", "") for j in expanded_lines]
            if i != ""
        ]

    mods_str = run_subprocess_cmd(
        ["./bin/benchpark", "list", "modifiers", "--no-title"], decode=True
    )
    nmods = [i for i in mods_str.replace(" " * 4, "").split("\n") if i != ""]
    print(nmods)
    modifiers_expr = []
    exclude_mods = ["allocation"]
    i = 0
    while i < len(nmods):
        if nmods[i] in exclude_mods:
            # Skip modifier and "(all benchmarks) line"
            i += 2
            continue
        if not nmods[i].startswith("\t"):
            curmod = nmods[i]
            print(curmod)
            end = "=on" if curmod != "caliper" else "=time"
            if "(all benchmarks)" in nmods[i + 1]:
                for b in mpi_only_expr:
                    modifiers_expr.append(b + " " + curmod + end)
                i += 2
                continue
            else:
                i += 1
                while nmods[i].startswith("\t"):
                    bmark = nmods[i].lstrip("\t")
                    if bmark in mpi_only_expr:
                        modifiers_expr.append(bmark + " " + curmod + end)
                    i += 1

    exprs_to_sys = [
        ("mpi", mpi_only_expr, str_dict["mpi"]),
        ("cuda", cuda_expr, str_dict["cuda"]),
        ("rocm", rocm_expr, str_dict["rocm"]),
        ("openmp", openmp_expr, str_dict["openmp"]),
        ("strong", strong_expr, str_dict["mpi"]),
        ("weak", weak_expr, str_dict["mpi"]),
        ("throughput", throughput_expr, str_dict["mpi"]),
        ("modifiers", modifiers_expr, [DEFAULT_SYSTEM]),
    ]

    if args.test:
        exprs_to_sys = [tup for tup in exprs_to_sys if tup[0] == args.test]

    total_tests = sum(
        len(expr_spec_list) * len(sys_spec_list)
        for _, expr_spec_list, sys_spec_list in exprs_to_sys
    )
    print(f"Total tests to run: {total_tests}")

    start = time.time()
    errors = {}
    fail_tests = 0
    ran_tests = 0
    skip_tests = 0
    for _, expr_spec_list, sys_spec_list in exprs_to_sys:
        for espec in expr_spec_list:
            for sspec in sys_spec_list:
                if "ior" in espec and "llnl-cluster" in sspec:
                    sspec += " mount_point=/p/lustre1"
                elif "ior" in espec:
                    SKIP_EXPR.append(f"{espec} {sspec}")
                expr = f"{espec} {sspec}"
                # If (1) entire spec in SKIP_EXPR or (2) just the experiment name is specified, e.g. skip all systems
                if expr in SKIP_EXPR or any([expr.split(" ")[0] == se for se in SKIP_EXPR]):
                    skip_tests += 1
                    print(f'Skipping "{expr}"')
                    continue
                ran_tests += 1
                print(f'Running "{expr}"')
                if args.dryrun:
                    continue
                try:
                    subprocess.run(
                        ["bash", ".github/utils/dryrun.sh", espec, sspec],
                        env={**os.environ},
                        capture_output=True,
                        check=True,
                    )
                except subprocess.CalledProcessError as e:
                    errors[f"{espec} {sspec}"] = e.stderr.decode()
                    fail_tests += 1
    end = time.time()

    for i, (key, value) in enumerate(errors.items()):
        print("=" * 100)
        print(str(i + 1) + ". " + key)
        print(value)

    print(f"Elapsed: {(end - start) / 60:.2f} minutes")
    print(
        f"{ran_tests - fail_tests} Passing. {fail_tests} Failing. {skip_tests} Skipped."
    )

    sys.exit(1 if fail_tests > 0 else 0)


if __name__ == "__main__":
    main()
