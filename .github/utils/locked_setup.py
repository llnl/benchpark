# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

"""Initialize shared runtime repositories once, then allow concurrent setups."""

import fcntl
from pathlib import Path
import subprocess
import sys

import yaml


def package_manager(config):
    if isinstance(config, dict):
        if "package_manager" in config:
            return config["package_manager"]
        for value in config.values():
            result = package_manager(value)
            if result is not None:
                return result
    return None


def main():
    workspace_root = Path(sys.argv[1])
    with open(sys.argv[2]) as config_file:
        needs_spack = "spack" in (package_manager(yaml.safe_load(config_file)) or "")

    ramble_ready = workspace_root / ".dryrun-ramble-ready"
    spack_ready = workspace_root / ".dryrun-spack-ready"

    def ready():
        return ramble_ready.exists() and (not needs_spack or spack_ready.exists())

    if ready():
        return subprocess.run(sys.argv[3:]).returncode

    # Only repository initialization needs the lock. Each setup writes its own
    # experiment workspace, so later calls can run concurrently.
    with open(workspace_root / ".dryrun-setup.lock", "a") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        if not ready():
            result = subprocess.run(sys.argv[3:]).returncode
            if result == 0:
                ramble_ready.touch()
                if needs_spack:
                    spack_ready.touch()
            return result

    return subprocess.run(sys.argv[3:]).returncode


if __name__ == "__main__":
    sys.exit(main())
