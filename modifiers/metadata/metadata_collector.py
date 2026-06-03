import argparse
import json
import subprocess
import yaml
from pathlib import Path

def write(metadata, metadata_file_path):
    with open(metadata_file_path, "w") as f:
        json.dump(metadata, f, indent=2)

def extract_benchpark_version(repo_root):
    benchpark_hash = subprocess.check_output(
        ["git", "-C", repo_root, "rev-parse", "--short", "HEAD"],
        text=True,
    ).strip()

    return benchpark_hash
    
def extract_dependencies_version(repo_root):
    dependencies_file = "checkout-versions.yaml"

    with open(Path(repo_root) / dependencies_file, "r", encoding="utf-8") as f:
        version_data = yaml.safe_load(f)

    dependencies_ver_json = version_data.get("versions")

    return {
        "ramble": dependencies_ver_json.get("ramble"),
        "spack": dependencies_ver_json.get("spack"),
        "spack-packages": dependencies_ver_json.get("spack-packages"),
    }

def extract_package_version(package_name):
    package_ver_raw = subprocess.check_output(
        ["spack", "find", "--json", package_name],
        text=True,
    )

    package_ver_json = json.loads(package_ver_raw)[0]

    return {
        "name": package_ver_json.get("name"),
        "version": package_ver_json.get("version"),
        "commit": package_ver_json.get("parameters").get("commit"),
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="write metadata to JSON")

    parser.add_argument(
        "metadata_file_path", type=str
    )
    parser.add_argument(
        "repo_root", type=str
    )
    parser.add_argument(
        "package_name", type=str
    )

    args = parser.parse_args()

    metadata = {
        "benchpark": extract_benchpark_version(args.repo_root),
        "dependencies": extract_dependencies_version(args.repo_root),
        "package": extract_package_version(args.package_name),
    }

    write(metadata, args.metadata_file_path)
