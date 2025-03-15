import argparse
import os
import subprocess
import sys
import shutil

import benchpark.paths

sys.path.append(str(benchpark.paths.benchpark_home) + "/spack/lib/spack")
import llnl.util.tty.color as color # noqa: E402

def main():
    parser = argparse.ArgumentParser(
        description="""Compare YAMLs generated from 'system init' between two different commits of Benchpark.
        (check if the output of system init was changed between commits).
        
        Usage: benchpark-python diffExperimentBuilds.py""",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-o",
        "--old",
        type=str,
        default="develop",  # develop from 3/4/25
        help="Commit hash or branch name for the old version of Benchpark (default: develop).",
    )
    parser.add_argument(
        "-n",
        "--new",
        type=str,
        default="pearce8-patch-3",
        help="Commit hash or branch name for the new version of Benchpark",
    )
    parser.add_argument(
        "-s",
        "--system",
        type=str,
        default="ruby",
        help="System being ran on",
    )

    args = parser.parse_args()

    # Use the arguments provided by the user or the defaults
    bp = {
        "benchpark-old": args.old,
        "benchpark-new": args.new,
    }

    sysd = {
        "ruby": "llnl-cluster"
    }

    experiments = {
        #"saxpy": "+openmp",
        #"amg2023": "+openmp",
        "lammps": ""
    }

    for name, tag in bp.items():

        if name not in os.listdir(os.getcwd()):
            subprocess.run(
                ["git", "clone", "https://github.com/LLNL/benchpark.git", name]
            )
        subprocess.run(["git", "checkout", tag], cwd=name)

        for exper, spec in experiments.items():
            system = sysd[args.system]
            cluster = args.system
            var="cluster"
            if os.path.isdir(f"{name}/{cluster}"):
                shutil.rmtree(f"{name}/{cluster}")
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
            if os.path.isdir(f"{name}/{exper}"):
                shutil.rmtree(f"{name}/{exper}")
            subprocess.run(
                [
                    "python",
                    f"{name}/lib/main.py",
                    "experiment",
                    "init",
                    f"--dest={name}/{exper}",
                    f"{exper}{spec}",
                ]
            )
            subprocess.run(
                [
                    "python",
                    f"{name}/lib/main.py",
                    "setup",
                    f"{name}/{exper}",
                    f"{name}/{cluster}",
                    f"{name}/wkp"
                ]
            )
            # Path to the Spack setup script
            spack_setup_script = f"{name}/wkp/spack/share/spack/setup-env.sh"
            # Define the ramble command
            ramble_command = f"{name}/wkp/ramble/bin/ramble --workspace-dir {name}/wkp/{name}/{exper}/{name}/{cluster}/workspace workspace setup"
            # Combine sourcing the script and running the command
            subprocess.run(
                f"bash -c 'source {spack_setup_script} && {ramble_command}'",
                shell=True,
                check=True,
                text=True
            )
            # Run the `spack find` command to get the hash
            pkg_hash = subprocess.run(
                [
                    f"{name}/wkp/spack/bin/spack",
                    "find",
                    "--hash",
                    exper
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE  # Capture errors
            )
            spec_result = subprocess.run([
                f"{name}/wkp/spack/bin/spack", 
                "spec",
                "--yaml",
                pkg_hash.stdout.strip(),
            ], text=True, stdout=subprocess.PIPE)
            # Write the output to a file
            yaml_file_path = f"{name}-{exper}.yaml"
            if os.path.isfile(yaml_file_path):
                os.remove(yaml_file_path)
            with open(yaml_file_path, "w") as yaml_file:
                yaml_file.write(spec_result.stdout)

    for exper in experiments.keys():
        old_file = f"./benchpark-old-{exper}.yaml"
        new_file = f"./benchpark-new-{exper}.yaml"

        # Path to the Spack setup script
        spack_setup_script = f"benchpark-old/wkp/spack/share/spack/setup-env.sh"
        # Define the ramble command
        cmd = f"benchpark-old/wkp/spack/bin/spack-python altdiff.py -t {old_file} {new_file}"
        # Combine sourcing the script and running the command
        diff = subprocess.run(
            f"bash -c 'source {spack_setup_script} && {cmd}'",
            shell=True,
            check=True,
            text=True,
            stdout=subprocess.PIPE
        )
        
        diff_str = diff.stdout
        if "DifferentSpecs=True" in diff_str:
            color.cprint(f"@*rThe specs for {exper} are different.@.")
        elif "DifferentSpecs=False" in diff_str:
            color.cprint(f"@*gThe specs for {exper} are the same.@.")
        else:
            raise ValueError("Expected value in output")
        print(diff_str)

if __name__ == "__main__":
    main()