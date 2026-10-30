#!/usr/bin/env python3
# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

"""Run one memtrace build inside an MPI rank, then validate its output."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def rank_id(env, ranks):
    for name in (
        "FLUX_TASK_RANK",
        "PMIX_RANK",
        "PMI_RANK",
        "OMPI_COMM_WORLD_RANK",
        "SLURM_PROCID",
    ):
        if name in env:
            rank = int(env[name])
            if not 0 <= rank < ranks:
                raise ValueError(
                    f"{name}={rank} is outside the requested {ranks} ranks"
                )
            return rank
    if ranks != 1:
        raise ValueError(
            "Cannot identify this MPI rank; no supported rank variable is set"
        )
    return 0


def benchmark_command(command, original_prefix, build_prefix):
    """Map a benchmark executable, including a Spack view symlink, to this build."""
    if not command:
        raise ValueError("No benchmark command supplied")
    original = Path(original_prefix).resolve()
    build = Path(build_prefix).resolve()
    resolved = shutil.which(command[0])
    if resolved is not None:
        try:
            relative = Path(resolved).resolve().relative_to(original)
        except ValueError:
            raise ValueError(
                f"{command[0]} does not belong to the benchmark prefix {original}"
            )
    elif "/" not in command[0]:
        relative = Path("bin") / command[0]
    else:
        # The ordinary package may not have been installed yet during setup.
        relative = Path(command[0]).resolve().relative_to(original)
    executable = build / relative
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ValueError(
            f"Instrumented executable is missing or not executable: {executable}"
        )
    return [str(executable)] + command[1:]


def load_run(path, mode):
    from memtrace import Run

    run = Run(str(path))
    if not len(run):
        raise ValueError(f"{path}: no kernel launches were collected")
    keys = set()
    for launch in run:
        key = (launch.kernel, launch.index)
        if key in keys:
            raise ValueError(f"{path}: duplicate launch {key}")
        keys.add(key)
        if launch.mode != mode or launch.catalog is None:
            raise ValueError(f"{path}: missing catalog or unexpected mode for {key}")
        launch.offsets()
        if mode == "count":
            launch.counts()
        else:
            problems, _ = launch.check()
            if problems:
                raise ValueError(f"{path}: {key}: {'; '.join(problems)}")
    return run


def check_reader():
    """Fail before launching the benchmark if the reader cannot be imported."""
    try:
        from memtrace import Run

        return Run
    except (ImportError, OSError) as exc:
        raise RuntimeError(f"Cannot load the memtrace reader: {exc}") from exc


def ensure_reader_preload(libraries):
    """Restart with MKL loaded before the Python reader imports NumPy."""
    current = os.environ.get("LD_PRELOAD", "").split()
    if any(path not in current for path in libraries):
        env = os.environ.copy()
        env["LD_PRELOAD"] = " ".join(libraries + current)
        os.execvpe(sys.executable, [sys.executable, *sys.argv], env)


def validate_pair(count_path, trace_path, timing=False):
    count = load_run(count_path, "count")
    trace = load_run(trace_path, "trace")
    counts = {(launch.kernel, launch.index): launch for launch in count}
    traces = {(launch.kernel, launch.index): launch for launch in trace}
    if counts.keys() != traces.keys():
        raise ValueError(
            "Count and trace launch sets differ; traces were skipped or discarded"
        )
    for key, launch in traces.items():
        before = counts[key]
        for field in ("grid", "block", "num_producers", "total_events", "catalog_hash"):
            if launch.info[field] != before.info[field]:
                raise ValueError(f"{key}: count and trace disagree on {field}")
        if not (launch.offsets() == before.offsets()).all():
            raise ValueError(f"{key}: count and trace wave offsets differ")
        if timing and launch.timing() is None:
            raise ValueError(f"{key}: requested timing records are missing")
    return len(trace)


def run(args):
    with open(args.builds) as stream:
        builds = json.load(stream)
    preload = builds.get("reader_preload", [])
    if args.mode != "baseline":
        ensure_reader_preload(preload)
    sys.path[:0] = builds["reader_paths"]
    command = benchmark_command(
        args.command, builds["original"], builds["prefixes"][args.mode]
    )
    env = os.environ.copy()
    if preload:
        remaining = [
            path for path in env.get("LD_PRELOAD", "").split() if path not in preload
        ]
        if remaining:
            env["LD_PRELOAD"] = " ".join(remaining)
        else:
            env.pop("LD_PRELOAD", None)
    # An enclosing profiling session must not override this experiment's settings.
    for name in (
        "MEMTRACE_RUN_OUT",
        "MEMTRACE_COUNT_RUN",
        "MEMTRACE_TIMING",
        "MEMTRACE_CATALOG",
    ):
        env.pop(name, None)
    if args.mode == "baseline":
        return subprocess.run(command, env=env, close_fds=False).returncode

    check_reader()
    rank = rank_id(env, args.ranks)
    output = Path(args.output).resolve() / args.mode / f"rank-{rank}"
    output.mkdir(parents=True, exist_ok=False)
    count = Path(args.output).resolve() / "count" / f"rank-{rank}"
    env["MEMTRACE_RUN_OUT"] = str(output)
    if args.mode == "trace":
        # Validate before launching, too: never silently run without count input.
        load_run(count, "count")
        env["MEMTRACE_COUNT_RUN"] = str(count)
        if args.timing:
            env["MEMTRACE_TIMING"] = "1"

    # PMI implementations can communicate through an inherited descriptor.
    result = subprocess.run(command, env=env, close_fds=False)
    if result.returncode:
        return result.returncode
    if args.mode == "count":
        launches = len(load_run(output, "count"))
    else:
        launches = validate_pair(count, output, args.timing)
    (output / "validated.json").write_text(
        json.dumps({"mode": args.mode, "launches": launches}) + "\n"
    )
    print(
        f"compiler_memtrace: validated {args.mode}, rank {rank}, {launches} launches: {output}",
        flush=True,
    )
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--builds", required=True)
    parser.add_argument("--mode", choices=("baseline", "count", "trace"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ranks", type=int, default=1)
    parser.add_argument("--timing", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.command[:1] == ["--"]:
        args.command = args.command[1:]
    try:
        return run(args)
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print(f"compiler_memtrace: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
