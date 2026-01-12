import argparse
import os
import shutil
import subprocess
import sys

import benchpark.paths

sys.path.append(str(benchpark.paths.benchpark_home) + "/spack/lib/spack")
import llnl.util.tty.color as color  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="""Compare experiments between two versions of benchpark. Includes optional functionality to run each experiment.

        Examples:
            - benchpark-python diffExperimentBuilds.py -s llnl-cluster -c ruby -p openmp --commit-hash2 develop
            - benchpark-python diffExperimentBuilds.py -s llnl-sierra -p cuda --commit-hash2 develop
            - benchpark-python diffExperimentBuilds.py -s llnl-elcapitan -c tioga -p rocm --commit-hash2 develop
""",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-s",
        "--system",
        type=str,
        required=True,
        help="Name of system.py to use for the experiment. This should be the system the script is being ran on. See 'benchpark list systems'. (e.g. 'llnl-cluster')",
    )
    parser.add_argument(
        "-p",
        "--programming-model",
        type=str,
        required=True,
        help="Programming model to run experiments. choose from: ('openmp', 'cuda', 'rocm')",
    )
    parser.add_argument(
        "--commit-hash1",
        type=str,
        default="develop",
        help="Commit hash or branch name for the version of Benchpark to compare against (default: develop).",
    )
    parser.add_argument(
        "--commit-hash2",
        type=str,
        required=True,
        help="Second commit hash or branch name for the newer version of Benchpark",
    )
    parser.add_argument(
        "-c",
        "--cluster",
        type=str,
        default=None,
        help="System variant if applicable. This should be the cluster the script is being ran on. See 'benchpark list systems'. (e.g. 'ruby' for 'llnl-cluster')",
    )
    parser.add_argument(
        "--extra-spec",
        default="",
        type=str,
        help="provide additional spec to experiment spec string",
    )
    parser.add_argument(
        "-b",
        "--benchmarks",
        nargs="*",
        default=[],
        help="Subselect benchmarks to run (e.g. amg2023)",
    )
    parser.add_argument("--run-experiment", action="store_true")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Clear directories and re-build if they exist.",
    )

    args = parser.parse_args()

    old_name = f"benchpark-{args.commit_hash1}-{args.programming_model}"
    new_name = f"benchpark-{args.commit_hash2}-{args.programming_model}"

    if args.benchmarks == []:
        experiments_out = subprocess.run(
            [
                "benchpark",
                "list",
                "experiments",
                "-e",
                args.programming_model,
                "--no-title",
            ],
            text=True,
            capture_output=True,
        )
        experiments = experiments_out.stdout.replace(" ", "")
        lines = experiments.split("\n")
        experiments = [
            line.split("+")[0] + "+" + args.programming_model
            for line in lines
            if args.programming_model in line
        ]
    else:
        experiments = []
        for e in args.benchmarks:
            experiments.append(e + "+" + args.programming_model)

    print(f"Running these experiments: {experiments}")

    system = args.system
    cluster = args.cluster
    if not cluster:
        cluster = system
        no_cluster = True
    else:
        no_cluster = False

    if (
        old_name in os.listdir(os.getcwd())
        and new_name in os.listdir(os.getcwd())
        and not args.rebuild
    ):
        pass
    else:
        for name, tag in {
            old_name: args.commit_hash1,
            new_name: args.commit_hash2,
        }.items():
            if name in os.listdir(os.getcwd()):
                print(f"Removing {name}...")
                shutil.rmtree(name)
            subprocess.run(
                ["git", "clone", "https://github.com/LLNL/benchpark.git", name]
            )
            subprocess.run(["git", "checkout", tag], cwd=name)

            for exper in experiments:
                exper, spec = exper.split("+")
                spec = "+" + spec
                var = "cluster"
                if os.path.isdir(f"{name}/{cluster}"):
                    shutil.rmtree(f"{name}/{cluster}")
                sys_list = [
                    "python",
                    f"{name}/lib/main.py",
                    "system",
                    "init",
                    f"--dest={name}/{cluster}",
                    system,
                ]
                if not no_cluster:
                    sys_list.append(f"{var}={cluster}")
                subprocess.run(sys_list)
                if os.path.isdir(f"{name}/{exper}"):
                    shutil.rmtree(f"{name}/{exper}")
                subprocess.run(
                    [
                        "python",
                        f"{name}/lib/main.py",
                        "experiment",
                        "init",
                        f"--dest={name}/{exper}",
                        f"--system={name}/{cluster}",
                        f"{exper}{spec}" + args.extra_spec,
                    ]
                )
                subprocess.run(
                    [
                        "python",
                        f"{name}/lib/main.py",
                        "setup",
                        f"{name}/{exper}",
                        f"{name}/wkp",
                    ]
                )
                # Path to the Spack setup script
                spack_setup_script = f"{name}/wkp/setup.sh"
                # Define the ramble command
                ramble_command = f"{name}/wkp/ramble/bin/ramble --workspace-dir {name}/wkp/{exper}/{cluster}/workspace workspace setup"
                # Combine sourcing the script and running the command
                run_str = f"bash -c 'source {spack_setup_script} && {ramble_command}"
                if args.run_experiment:
                    run_str += f" && {name}/wkp/ramble/bin/ramble --workspace-dir {name}/wkp/{exper}/{cluster}/workspace on"
                run_str += "'"
                subprocess.run(
                    run_str,
                    shell=True,
                    check=True,
                    text=True,
                )
                # Run the `spack find` command to get the hash
                pkg_hash = subprocess.run(
                    [f"{name}/wkp/spack/bin/spack", "find", "--hash", exper],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,  # Capture errors
                )
                spec_result = subprocess.run(
                    [
                        f"{name}/wkp/spack/bin/spack",
                        "spec",
                        "--yaml",
                        pkg_hash.stdout.strip(),
                    ],
                    text=True,
                    stdout=subprocess.PIPE,
                )
                # Write the output to a file
                yaml_file_path = f"{name}-{exper}.yaml"
                if os.path.isfile(yaml_file_path):
                    os.remove(yaml_file_path)
                with open(yaml_file_path, "w") as yaml_file:
                    yaml_file.write(spec_result.stdout)

    for exper in experiments:
        exper = exper.split("+")[0]
        old_file = f"./{old_name}-{exper}.yaml"
        new_file = f"./{new_name}-{exper}.yaml"

        # Path to the Spack setup script
        spack_setup_script = f"{old_name}/wkp/setup.sh"
        # Define the ramble command
        cmd = f"{old_name}/wkp/spack/bin/spack-python diffBuildSpecs.py -t -d {old_file} {new_file}"
        # Combine sourcing the script and running the command
        try:
            diff = subprocess.run(
                f"bash -c 'source {spack_setup_script} && {cmd}'",
                shell=True,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )

            diff_str = diff.stdout

            if "DifferentSpecs=True" in diff_str:
                color.cprint(f"@*rThe specs for {exper} are different.@.")
            elif "DifferentSpecs=False" in diff_str:
                color.cprint(f"@*gThe specs for {exper} are the same.@.")
            else:
                raise ValueError("Expected value in output")
            print(diff_str)
        except:  # noqa
            color.cprint("@*o" + f"The specs for {exper} could not be compared.@.")


if __name__ == "__main__":
    main()
