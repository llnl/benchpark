#!/usr/bin/env python3
# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from pathlib import Path

DEFAULT_SYSTEM = "llnl-cluster cluster=dane"
# Skip experiments
SKIP_EXPR = [
    # System not enough cores/node
    "gromacs+openmp aws-pcluster instance_type=c6g.xlarge",
    "gromacs+openmp aws-pcluster instance_type=c4.xlarge",
    "gromacs+openmp generic-x86",
    "gromacs+openmp fluxtainer",
    "babelstream+openmp aws-pcluster instance_type=c6g.xlarge",
    "babelstream+openmp aws-pcluster instance_type=c4.xlarge",
    "babelstream+openmp generic-x86",
    "stream aws-pcluster instance_type=c6g.xlarge",
    "stream aws-pcluster instance_type=c4.xlarge",
    "stream cscs-daint",
    "stream generic-x86",
    "stream fluxtainer",
    "stream riken-dgx",
    # Broken URL's in application.py going to cause dryrun failure
    "genesis",
    # Not ProgrammingModelType.Mpionly
    "py-scaffold+strong",
    "py-scaffold+weak",
    # Needs package_manager=spack-pip
    "py-scaffold+rocm",
    "py-scaffold+cuda",
]


def run_subprocess_cmd(cmd_list, decode=False):
    try:
        result = subprocess.run(cmd_list, capture_output=True, check=True)
        return result.stdout.decode("utf-8") if decode else result
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Command: {' '.join(cmd_list)}\nOutput: {e.stdout}\nError: {e.stderr}"
        )


def run_single_test(espec, sspec, args, temp_dir=None, original_dir=None):
    """Run a single test and return the result."""
    # Adjust IOR tests with mount_point
    if "ior" in espec and "llnl-cluster" in sspec:
        sspec += " mount_point=/p/lustre1"
    elif "ior" in espec:
        SKIP_EXPR.append(f"{espec} {sspec}")

    expr = f"{espec} {sspec}"

    # Check if test should be skipped
    if expr in SKIP_EXPR or any([expr.split(" ")[0] == se for se in SKIP_EXPR]):
        return {"expr": expr, "status": "skipped", "error": None}

    print(f'Running "{expr}"')

    if args.dryrun:
        return {"expr": expr, "status": "passed", "error": None}

    try:
        # Run from original directory to preserve paths and configs
        env = {**os.environ}
        cwd = original_dir if original_dir else None

        if temp_dir:
            # Create a unique subdirectory for this test to avoid conflicts
            import hashlib
            test_hash = hashlib.md5(expr.encode()).hexdigest()[:8]
            # Extract benchmark and system names for readable directory names
            benchmark_name = espec.replace("+", "-").replace(" ", "_")
            system_name = sspec.split()[0].replace("+", "-")
            test_dir = os.path.join(temp_dir, f"{benchmark_name}-{system_name}-{test_hash}")
            os.makedirs(test_dir, exist_ok=True)

            # Create symlinks to necessary directories so relative paths work
            for item in ["bin", ".github", "benchpark", "lib", "configs", "experiments", "systems"]:
                src = os.path.join(cwd, item)
                dst = os.path.join(test_dir, item)
                if os.path.exists(src) and not os.path.exists(dst):
                    os.symlink(src, dst)

            # Also check for repo directory
            repo_src = os.path.join(cwd, "repo")
            repo_dst = os.path.join(test_dir, "repo")
            if os.path.exists(repo_src) and not os.path.exists(repo_dst):
                os.symlink(repo_src, repo_dst)

            # Run from test directory so outputs go there
            subprocess.run(
                ["bash", ".github/utils/dryrun.sh", espec, sspec],
                env=env,
                cwd=test_dir,
                capture_output=True,
                check=True,
            )
            # Test passed - clean up the test directory immediately
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir, ignore_errors=True)
        else:
            subprocess.run(
                ["bash", ".github/utils/dryrun.sh", espec, sspec],
                env=env,
                cwd=cwd,
                capture_output=True,
                check=True,
            )
        return {"expr": expr, "status": "passed", "error": None}
    except subprocess.CalledProcessError as e:
        return {"expr": expr, "status": "failed", "error": e.stderr.decode()}


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
        "--experiment",
        type=str,
        metavar="NAME",
        help="Only run tests for a specific experiment (e.g., 'amg', 'lammps')",
    )
    parser.add_argument(
        "--system",
        type=str,
        metavar="NAME",
        help="Only run tests for a specific system (e.g., 'llnl-cluster', 'aws-pcluster')",
    )
    parser.add_argument(
        "--dryrun", action="store_true", help="Dry runs this script for testing."
    )
    parser.add_argument(
        "-j", "--jobs",
        type=int,
        default=None,
        metavar="N",
        help="Number of parallel jobs (default: auto-detect CPU count, use 1 for sequential)",
    )
    parser.add_argument(
        "--tmpdir",
        action="store_true",
        help="Run tests in a temporary directory that is automatically cleaned up",
    )
    parser.add_argument(
        "--archive",
        nargs='?',
        const=True,
        type=str,
        metavar="PATH",
        help="Archive the test workspace to a compressed tar.gz file (implies --tmpdir). If no path given, uses temp directory name.",
    )
    args = parser.parse_args()

    # Determine number of parallel jobs
    if args.jobs is None:
        # Auto-detect: use all available CPUs
        args.jobs = cpu_count()
        print(f"Auto-detected {args.jobs} CPUs for parallel execution")
    elif args.jobs < 1:
        print("Error: -j/--jobs must be at least 1")
        sys.exit(1)

    # Get experiment and system information first (from original directory)
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

    # Setup working directory (after collecting test information)
    temp_dir = None
    original_dir = os.getcwd()

    if args.archive:
        # Archive implies tmpdir
        args.tmpdir = True
        # Validate archive path if user provided one
        if args.archive is not True:
            archive_path = Path(args.archive).resolve()
            if archive_path.exists():
                print(f"Error: Archive file already exists: {archive_path}")
                sys.exit(1)
            archive_path.parent.mkdir(parents=True, exist_ok=True)

    if args.tmpdir:
        # Create temporary directory for workspace output
        temp_dir = tempfile.mkdtemp(prefix="benchpark_dryruns_")
        print(f"Test workspaces will be created in: {temp_dir}")
        # Set environment variable to redirect workspace creation
        os.environ["BENCHPARK_WORKSPACE_DIR"] = temp_dir

    total_tests = sum(
        len(expr_spec_list) * len(sys_spec_list)
        for _, expr_spec_list, sys_spec_list in exprs_to_sys
    )
    print(f"Total tests to run: {total_tests}")
    print(f"Running with {args.jobs} parallel job(s)")

    start = time.time()
    errors = {}
    fail_tests = 0
    ran_tests = 0
    skip_tests = 0

    # Build list of all test cases to run
    test_cases = []
    for _, expr_spec_list, sys_spec_list in exprs_to_sys:
        for espec in expr_spec_list:
            for sspec in sys_spec_list:
                test_cases.append((espec, sspec))

    # Filter by experiment name if specified
    if args.experiment:
        test_cases = [
            (espec, sspec)
            for espec, sspec in test_cases
            if espec == args.experiment or espec.startswith(args.experiment + "+") or espec.startswith(args.experiment + " ")
        ]
        print(f"Filtered to experiment '{args.experiment}': {len(test_cases)} tests")

    # Filter by system name if specified
    if args.system:
        test_cases = [
            (espec, sspec)
            for espec, sspec in test_cases
            if sspec == args.system or sspec.startswith(args.system + " ")
        ]
        print(f"Filtered to system '{args.system}': {len(test_cases)} tests")

    # Run tests in parallel
    try:
        if args.jobs == 1:
            # Sequential execution
            results = []
            for espec, sspec in test_cases:
                result = run_single_test(espec, sspec, args, temp_dir, original_dir)
                results.append(result)
        else:
            # Parallel execution
            results = []
            with ThreadPoolExecutor(max_workers=args.jobs) as executor:
                # Submit all tasks
                future_to_test = {
                    executor.submit(run_single_test, espec, sspec, args, temp_dir, original_dir): (espec, sspec)
                    for espec, sspec in test_cases
                }

                # Process results as they complete
                for future in as_completed(future_to_test):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        espec, sspec = future_to_test[future]
                        results.append({
                            "expr": f"{espec} {sspec}",
                            "status": "failed",
                            "error": str(e)
                        })

        # Process results BEFORE cleanup
        for result in results:
            if result["status"] == "skipped":
                skip_tests += 1
                print(f'Skipped "{result["expr"]}"')
            elif result["status"] == "passed":
                ran_tests += 1
            elif result["status"] == "failed":
                ran_tests += 1
                fail_tests += 1
                errors[result["expr"]] = result["error"]

    finally:
        # Handle cleanup and archiving
        if args.tmpdir and temp_dir:
            if args.archive:
                # Determine archive path
                if args.archive is True:
                    # No path given, use temp directory name
                    archive_path = f"{os.path.basename(temp_dir)}.tar.gz"
                else:
                    archive_path = args.archive

                print(f"\nCreating archive: {archive_path}")
                try:
                    with tarfile.open(archive_path, "w:gz") as tar:
                        tar.add(temp_dir, arcname=os.path.basename(temp_dir))
                    print(f"Archive created successfully: {archive_path}")
                except Exception as e:
                    print(f"Warning: Failed to create archive: {e}")

            if os.path.exists(temp_dir):
                print(f"Cleaning up temporary directory: {temp_dir}")
                shutil.rmtree(temp_dir, ignore_errors=True)

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
