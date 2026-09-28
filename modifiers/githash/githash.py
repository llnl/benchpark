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


def load_spack_json(raw):
    json_start = raw.find("{")
    if json_start < 0:
        raise ValueError("Spack did not emit JSON output")
    return json.loads(raw[json_start:])


def spack_spec_json(name):
    raw = subprocess.check_output(
        ["spack", "spec", "--json", name],
        text=True,
    )
    return load_spack_json(raw)["spec"]["nodes"]


def extract_package_hash(pkg_json):
    params = pkg_json.get("parameters", {})
    external = pkg_json.get("external") or params.get("external", {})
    return {
        "name": pkg_json.get("name"),
        "version": pkg_json.get("version"),
        "commit": params.get("commit"),
        "external_path": external.get("path"),
    }


def collect_package_info(application_name):
    specs = spack_spec_json(application_name)
    specs_by_hash = {spec["hash"]: spec for spec in specs}
    pkg_json = next(spec for spec in specs if spec["name"] == application_name)

    application = extract_package_hash(pkg_json)
    dependencies = {}
    for dep in pkg_json.get("dependencies"):
        dep_info = extract_package_hash(specs_by_hash[dep["hash"]])
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
