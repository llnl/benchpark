import argparse
from collections import defaultdict
import os
import re

def main():
    parser = argparse.ArgumentParser(description="Aggregate experiments from one or more workspaces")
    parser.add_argument("output", help="Directory to generate scripts in")
    parser.add_argument("workspaces", nargs=argparse.REMAINDER, help="One or more benchpark workspaces")

    args = parser.parse_args()

    if os.path.exists(args.output):
        raise ValueError(f"Directory must not already exist: {args.output}")

    experiments = list()
    for workspace_dir in args.workspaces:
        experiments.extend(collect_experiments(workspace_dir))

    opts_to_request = {}
    opts_to_scripts = defaultdict(list)
    for experiment_script in experiments:
        batch_opts, batch_lines = collect_scheduler_options(experiment_script)
        if batch_opts:
            opts_to_scripts[batch_opts].append(experiment_script)
            opts_to_request[batch_opts] = batch_lines
        else:
            raise Exception(f"Not expected: no batch opts in {experiment_script}")

    os.mkdir(args.output)
    script_id = 0
    for opts_group, scripts in opts_to_scripts.items():
        script_path = os.path.join(args.output, f"{script_id}.sh")
        make_aggregate_script(script_path, opts_to_request[opts_group], scripts)
        script_id += 1

def make_aggregate_script(script_path, batch_lines, to_aggregate):
    with open(script_path, "w") as f:
        for line in batch_lines:
            f.write(line + "\n")
        for experiment in to_aggregate:
            f.write(os.path.abspath(experiment) + "\n")

def collect_scheduler_options(experiment_script):
    # Should only take 1 line per scheduler to handle all schedulers
    batch_patterns = [
        r"\s*#\s*(flux:.*$)",
        r"\s*#SBATCH\s+(.*)$",
    ]
    batch_opts = list()
    batch_lines = list()
    with open(experiment_script, "r") as f:
        for line in f.readlines():
            for p in batch_patterns:
                m = re.match(p, line)
                if m:
                    batch_opts.append(tuple(m.group(1).strip().split()))
                    batch_lines.append(line.strip())

    return tuple(sorted(batch_opts)), batch_lines

def collect_experiments(workspace_dir):
    experiments = list()
    for entry in os.listdir(workspace_dir):
        if entry in ["spack", "ramble"] or not os.path.isdir(entry):
            continue
        for dirpath, dirnames, filenames in os.walk(os.path.join(workspace_dir, entry)):
            for fname in filenames:
                if fname == "execute_experiment":
                    experiments.append(os.path.join(dirpath, fname))
    return experiments

if __name__ == "__main__":
    main()
