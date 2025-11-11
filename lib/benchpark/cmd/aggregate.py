# Copyright 2025 Lawrence Livermore National Security, LLC
# and other Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import re
from collections import defaultdict

from benchpark.error import BenchparkError


def _make_aggregate_script(script_path, batch_lines, to_aggregate):
    with open(script_path, "w") as f:
        for line in batch_lines:
            f.write(line.rstrip("\n") + "\n")
        for experiment in to_aggregate:
            f.write(os.path.abspath(experiment) + "\n")


def _collect_scheduler_options(experiment_script):
    batch_patterns = [
        r"\s*#\s*(flux:.*$)",   # flux-style header (kept verbatim)
        r"\s*#SBATCH\s+(.*)$",  # SLURM
    ]

    batch_opts = []
    batch_lines = []

    with open(experiment_script, "r") as f:
        for line in f:
            for p in batch_patterns:
                m = re.match(p, line)
                if m:
                    batch_opts.append(tuple(m.group(1).strip().split()))
                    batch_lines.append(line.strip())

    return tuple(sorted(batch_opts)), batch_lines


def _collect_experiments(workspace_dir):
    if not os.path.isdir(workspace_dir):
        raise BenchparkError(
            f"Workspace path does not exist or is not a directory: {workspace_dir}"
        )

    experiments = []
    skip_roots = {"spack", "ramble"}

    for entry in os.listdir(workspace_dir):
        entry_path = os.path.join(workspace_dir, entry)
        if entry in skip_roots or not os.path.isdir(entry_path):
            continue

        for dirpath, _dirnames, filenames in os.walk(entry_path):
            for fname in filenames:
                if fname == "execute_experiment":
                    experiments.append(os.path.join(dirpath, fname))

    return experiments


def _aggregate(args):
    output_dir = args.dest
    workspaces = args.workspaces

    if not workspaces:
        raise BenchparkError("No workspaces provided.")

    if os.path.exists(output_dir):
        raise BenchparkError(f"Directory must not already exist: {output_dir}")

    experiments = []
    for ws in workspaces:
        experiments.extend(_collect_experiments(ws))

    if not experiments:
        raise BenchparkError(
            "No 'execute_experiment' scripts found in the given workspaces."
        )

    opts_to_request = {}
    opts_to_scripts = defaultdict(list)

    for experiment_script in experiments:
        batch_opts, batch_lines = _collect_scheduler_options(experiment_script)
        if not batch_opts:
            raise BenchparkError(f"Not expected: no batch opts in {experiment_script}")

        opts_to_scripts[batch_opts].append(experiment_script)
        if batch_opts not in opts_to_request:
            opts_to_request[batch_opts] = batch_lines

    os.mkdir(output_dir)
    script_id = 0
    for opts_group, scripts in opts_to_scripts.items():
        script_path = os.path.join(output_dir, f"{script_id}.sh")
        _make_aggregate_script(script_path, opts_to_request[opts_group], scripts)
        script_id += 1

def setup_parser(root_parser):
    """
    Register arguments for `benchpark aggregate` directly (no subcommands).
    Usage:
        benchpark aggregate --dest OUTDIR WS1 [WS2 ...]
    """
    root_parser.add_argument(
        "--dest",
        required=True,
        help="Directory to generate aggregate scripts in",
    )
    root_parser.add_argument(
        "workspaces",
        nargs="+",
        help="One or more Benchpark workspace directories",
    )


def command(args):
    _aggregate(args)
