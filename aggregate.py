import argparse
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

    import pdb; pdb.set_trace()

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
