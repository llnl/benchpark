import argparse
import difflib
import itertools
import os
import subprocess
import sys

import benchpark.paths

EXIT_CODE = 0

parser = argparse.ArgumentParser(
    description="Script to compare packages in benchpark against upstream spack packages.",
    usage="benchpark-python diffPackageCommits.py [OPTIONS]",
)
parser.add_argument(
    "--spack-tag",
    default="develop",
    help="Specify the spack version in the format 'vX.Y.Z', e.g., 'v0.23.1'.",
)
parser.add_argument("--print-diff", action="store_true", help="Print file diff")
parser.add_argument(
    "--packages",
    nargs="+",  # Allows one or more package names
    help="Specify one or more packages to compare. If not provided, all packages will be compared.",
)
args = parser.parse_args()

print(f"Comparing benchpark packages to packages in spack {args.spack_tag}")

if "spack" not in os.listdir(os.getcwd()):
    subprocess.run(["git", "clone", "https://github.com/spack/spack.git"])
subprocess.run(["git", "checkout", args.spack_tag], cwd="spack")

sys.path.append("spack/lib/spack")
import llnl.util.tty.color as color  # noqa: E402


def main():
    global EXIT_CODE
    spack_dir = "spack/var/spack/repos/builtin/packages/"
    benchpark_dir = str(benchpark.paths.benchpark_root) + "/repo/"

    # Get the list of packages to process
    if args.packages:
        # Use only the specified packages
        packages_to_compare = []
        for item in args.packages:
            packages_to_compare.extend(item.strip().split())
    else:
        # Process all packages if --packages is not provided
        packages_to_compare = sorted(os.listdir(benchpark_dir))

    for package in packages_to_compare:
        if package not in ["repo.yaml"]:
            spack_package_path = spack_dir + package + "/package.py"
            benchpark_package_path = benchpark_dir + package + "/package.py"

            if not os.path.exists(spack_package_path):
                color.cprint("@*b" + package + "@.")
                color.cprint(
                    "    " + package + "/package.py @*rdoes not@. exist in @*ospack@."
                )
                continue
            elif not os.path.exists(benchpark_package_path):
                # color.cprint("    "+package+" package.py @*rdoes not@. exist in @*obenchpark@.")
                continue

            color.cprint("@*b" + package + "@.")

            # Read the files
            with open(spack_package_path, "r") as file1, open(
                benchpark_package_path, "r"
            ) as file2:
                spack_lines = [
                    line for line in file1 if not line.lstrip().startswith("#")
                ]
                benchpark_lines = [
                    line for line in file2 if not line.lstrip().startswith("#")
                ]

            # Compare the files
            diff = difflib.unified_diff(
                spack_lines,
                benchpark_lines,
                fromfile="spack " + package,
                tofile="benchpark " + package,
                lineterm="",
            )

            diff, dc, dc2 = itertools.tee(diff, 3)

            diff_list = list(diff)
            # Check if there is no diff
            if not diff_list:
                color.cprint(
                    f"    @*gNo differences found. Please delete 'benchpark/repo/{package}/package.py' (use spack upstream)@."
                )
                EXIT_CODE = 1

            # Use difflib.ndiff to compare the lines
            dc3 = difflib.ndiff(spack_lines, benchpark_lines)
            # Count the differing lines (ignoring duplicates)
            differing_lines_count = sum(
                1 for line in dc3 if line.startswith("- ") or line.startswith("+ ")
            )
            print("    ", differing_lines_count // 2, "different lines")

            if args.print_diff:
                # Print the differences
                print("\n".join(dc))

    print(f"EXIT_CODE: {EXIT_CODE}")
    return EXIT_CODE


if __name__ == "__main__":
    exit_code = main()
    sys.exit(EXIT_CODE)
