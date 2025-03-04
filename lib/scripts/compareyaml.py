# Usage: benchpark-python compareyaml.py 

import argparse
import os
import subprocess
import yaml
import sys

from deepdiff import DeepDiff

import benchpark.paths

sys.path.append(str(benchpark.paths.benchpark_home) + "/spack/lib/spack")
import llnl.util.tty.color as color  # noqa: E402


def load_yaml(file_path):
    """Load a YAML file and return its content as a Python object."""
    try:
        with open(file_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse YAML file: {file_path}\n{e}")
        return None


def compare_yaml(file1, file2):
    """Compare two YAML files and print the differences."""

    def normalize_types(data):
        """fix to compare strings to int '56' == 56 for yaml purposes"""
        if isinstance(data, dict):
            return {
                (k if k != "compilers:" else "compilers"): normalize_types(v)
                for k, v in data.items()
            }  # Fix for way "'compilers':": is generated in old yaml
        elif isinstance(data, list):
            return [normalize_types(v) for v in data]
        elif isinstance(data, str) and data.isdigit():
            return int(data)  # Convert numeric strings to integers
        else:
            return data

    data1 = normalize_types(load_yaml(file1))
    data2 = normalize_types(load_yaml(file2))

    if data1 is None or data2 is None:
        print("\t\tComparison aborted due to file loading errors.")
        return

    # Use DeepDiff to find differences
    diff = DeepDiff(
        data1,
        data2,
        verbose_level=1,
        ignore_type_in_groups=[(int, str)],
        ignore_string_type_changes=True,
    )

    if not diff:
        color.cprint(f"\t\t@*gThe YAML files {file1} and {file2} are identical.@.")
    else:
        color.cprint(
            f"\t\t@*rThe YAML files {file1} and {file2} are different. Here are the differences:@."
        )
        print("\t\t\t" + str(diff))


if __name__ == "__main__":
    # # Set up argument parser
    # parser = argparse.ArgumentParser(
    #     description="Compare two YAML files for differences."
    # )
    # parser.add_argument("file1", help="Path to the first YAML file")
    # parser.add_argument("file2", help="Path to the second YAML file")

    # # Parse arguments
    # args = parser.parse_args()

    bp = {
        "benchpark-legacy": "6d06ea8cbf6ffd494b30ece1a2e924fd48dd7018", # develop from 3/4/25
        "benchpark-new": "refactor/systems-i654",
    }

    sysd = {
        "aws-pcluster": ["c6g.xlarge", "c4.xlarge", "hpc7a.48xlarge", "hpc6a.48xlarge"],
        # "csc-lumi": None,
        "llnl-cluster": ["ruby"],
    }

    for name, tag in bp.items():

        if name not in os.listdir(os.getcwd()):
            subprocess.run(
                ["git", "clone", "https://github.com/LLNL/benchpark.git", name]
            )
        subprocess.run(["git", "checkout", tag], cwd=name)

        for system in sysd.keys():
            if not sysd[system]:
                subprocess.run(
                    [
                        "python",
                        f"{name}/lib/main.py",
                        "system",
                        "init",
                        f"--dest={name}/{system}",
                        system,
                    ]
                )
            else:
                var = "cluster"
                if system == "aws-pcluster":
                    var = "instance_type"
                for cluster in sysd[system]:
                    subprocess.run(
                        [
                            "python",
                            f"{name}/lib/main.py",
                            "system",
                            "init",
                            f"--dest={name}/{cluster}",
                            system,
                            f"{var}={cluster}",
                        ]
                    )

    # Compare the YAML files
    for system in sysd.keys():
        color.cprint("@*y" + system + "@.")
        for cluster in sysd[system]:
            for root, dirs, files in os.walk(f"benchpark-legacy/{cluster}"):
                loc = "/".join(root.split("/")[1:])
                for file in files:
                    color.cprint("\t@*b" + loc + "/" + file + "@.")
                    compare_yaml(
                        f"benchpark-legacy/{loc}/{file}",
                        f"benchpark-new/{loc}/{file}",
                    )
