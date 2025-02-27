import argparse
import difflib
import os
import subprocess
import sys
import itertools

parser = argparse.ArgumentParser(
    description="Script to compare packages in benchpark against upstream spack packages."
)
parser.add_argument(
    "--spack-tag",
    default="develop",
    help="Specify the spack version in the format 'vX.Y.Z', e.g., 'v0.23.1'.",
)
parser.add_argument("--print-diff", action="store_true", help="Print file diff")
args = parser.parse_args()

print(f"Comparing benchpark packages to packages in spack {args.spack_tag}")

if "spack" not in os.listdir(os.getcwd()):
    subprocess.run(["git", "clone", "https://github.com/spack/spack.git"])
subprocess.run(["git", "checkout", args.spack_tag], cwd="spack")

sys.path.append("spack/lib/spack")
import llnl.util.tty.color as color  # noqa: E402


spack_dir = "spack/var/spack/repos/builtin/packages/"
benchpark_dir = "../../repo/"

for package in sorted(os.listdir(benchpark_dir)):
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
            spack_lines = [line for line in file1 if not line.lstrip().startswith("#")]
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
                f"    @*gNo differences found. '{benchpark_package_path}' can be upstreamed to '{spack_package_path}'@."
            )

        # Use difflib.ndiff to compare the lines
        dc3 = difflib.ndiff(spack_lines, benchpark_lines)
        # Count the differing lines (ignoring duplicates)
        differing_lines_count = sum(
            1 for line in dc3 if line.startswith("- ") or line.startswith("+ ")
        )
        print("    ", differing_lines_count // 2, "different lines")
        # print("    ",sum(1 for _ in dc2), "different lines")

        if args.print_diff:
            # Print the differences
            print("\n".join(dc))
