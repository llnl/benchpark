import argparse
import json
import subprocess
import traceback
from pathlib import Path

import yaml


def write(metadata, metadata_file_path):
    with open(metadata_file_path, "w") as f:
        json.dump(metadata, f, indent=2)


def extract_benchpark_hash(repo_root):
    benchpark_hash = subprocess.check_output(
        ["git", "-C", repo_root, "rev-parse", "--short", "HEAD"],
        text=True,
    ).strip()

    return benchpark_hash


def extract_benchpark_dependencies_hash(repo_root):
    dependencies_file = "checkout-versions.yaml"

    with open(Path(repo_root) / dependencies_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    dependencies_hash_json = data.get("versions")

    return {
        "ramble": dependencies_hash_json.get("ramble"),
        "spack": dependencies_hash_json.get("spack"),
        "spack-packages": dependencies_hash_json.get("spack-packages"),
    }


def spack_find_json(name):
    raw = subprocess.check_output(
        ["spack", "find", "--json", name],
        text=True,
    )
    return json.loads(raw)[0]


def extract_package_hash(pkg_json):
    params = pkg_json.get("parameters", {})
    return {
        "name": pkg_json.get("name"),
        "version": pkg_json.get("version"),
        "commit": params.get("commit"),
    }


def collect_package_info(application_name):
    pkg_json = spack_find_json(application_name)

    application = extract_package_hash(pkg_json)
    dependencies = {}
    for dep in pkg_json.get("dependencies"):
        dep_info = extract_package_hash(spack_find_json(dep["name"]))
        # Ignore packages without commit information, as they are not useful for comparing versions
        if dep_info["commit"] is not None:
            dependencies[dep["name"]] = dep_info
    return {
        "application": application,
        "dependencies": dependencies,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="write git hash metadata to JSON")

    parser.add_argument("githash_metadata_file_path", type=str)
    parser.add_argument("repo_root", type=str)
    parser.add_argument("application_name", type=str)

    args = parser.parse_args()

    try:
        metadata = {
            "benchpark": extract_benchpark_hash(args.repo_root),
            "benchpark_dependencies": extract_benchpark_dependencies_hash(
                args.repo_root
            ),
            "packages": collect_package_info(args.application_name),
        }

    except Exception as e:
        with open("githash_error_log", "w", encoding="utf-8") as f:
            f.write(f"{type(e).__name__}: {e}\n")
            f.write(traceback.format_exc())
        raise

    write(metadata, args.githash_metadata_file_path)
