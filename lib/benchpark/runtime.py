# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from contextlib import contextmanager
import os
import pathlib
import shlex
import subprocess
import sys

import yaml

import benchpark.paths
from benchpark.debug import debug_print


@contextmanager
def working_dir(location):
    initial_dir = os.getcwd()
    try:
        os.chdir(location)
        yield
    finally:
        os.chdir(initial_dir)


def git_clone_commit(url, commit, destination):
    run_command(f"git clone -c feature.manyFiles=true {url} {destination}")

    with working_dir(destination):
        run_command(f"git checkout {commit}")


def run_command(command_str, env=None, stdout=None, stderr=None):
    stdout = stdout or subprocess.PIPE
    stderr = stderr or subprocess.PIPE
    proc = subprocess.Popen(
        shlex.split(command_str),
        env=env,
        stdout=stdout,
        stderr=stderr,
        text=True,
    )
    out, err = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(
            f"Failed command: {command_str}\nOutput: {stdout}\nError: {stderr}"
        )

    return (out, err)


class Command:
    def __init__(self, exe_path, env):
        self.exe_path = exe_path
        self.env = env

    def __call__(self, *args):
        opts_str = " ".join(args)
        cmd_str = f"{self.exe_path} {opts_str}"
        return run_command(cmd_str, env=self.env)


class RuntimeResources:
    def __init__(self, dest, upstream=None):
        self.root = benchpark.paths.benchpark_root
        self.dest = pathlib.Path(dest)
        self.upstream = upstream

        self.ramble_location = self.dest / "ramble"
        self.spack_location = self.dest / "spack"

        checkout_versions_location = self.root / "checkout-versions.yaml"
        with open(checkout_versions_location, "r") as yaml_file:
            data = yaml.safe_load(yaml_file)
            self.ramble_commit = data["versions"]["ramble"]
            self.spack_commit = data["versions"]["spack"]

        # If instance does not have an upstream, it is the upstream
        if not self.upstream:
            self.bootstrap()

    def update_old_bootstrap(self, desired_commit, location):
        # Store first 7 of hash in checkout-versions.yaml
        with working_dir(location):
            current_commit = run_command("git rev-parse HEAD")[0].strip()[:7]
            if current_commit != desired_commit:
                run_command("git fetch --all")
                run_command(f"git checkout {desired_commit}")
                print(
                    f"Updating '{location}' from {current_commit} to {desired_commit}"
                )

    def bootstrap(self):
        if not self.ramble_location.exists():
            self._install_ramble(bootstrap=True)
        else:
            self.update_old_bootstrap(self.ramble_commit, self.ramble_location)
        ramble_lib_path = self.ramble_location / "lib" / "ramble"
        externals = str(ramble_lib_path / "external")
        if externals not in sys.path:
            sys.path.insert(1, externals)
        internals = str(ramble_lib_path)
        if internals not in sys.path:
            sys.path.insert(1, internals)

        # Spack does not go in sys.path, but we will manually access modules from it
        # The reason for this oddity is that spack modules will compete with the internal
        # spack modules from ramble
        if not self.spack_location.exists():
            self._install_spack(bootstrap=True)
        else:
            self.update_old_bootstrap(self.spack_commit, self.spack_location)

    def _install_ramble(self, bootstrap=False):
        print(f"Cloning Ramble to {self.ramble_location}")
        git_clone_commit(
            (
                "https://github.com/GoogleCloudPlatform/ramble.git"
                if bootstrap
                else benchpark.paths.benchpark_home / "ramble"
            ),
            self.ramble_commit,
            self.ramble_location,
        )
        debug_print(f"Done cloning Ramble ({self.ramble_location})")

    def _install_spack(self, bootstrap=False):
        print(f"Cloning Spack to {self.spack_location}")
        git_clone_commit(
            (
                "https://github.com/spack/spack.git"
                if bootstrap
                else benchpark.paths.benchpark_home / "spack"
            ),
            self.spack_commit,
            self.spack_location,
        )
        debug_print(f"Done cloning Spack ({self.spack_location})")

    def _ramble(self):
        first_time = False
        if not self.ramble_location.exists():
            first_time = True
            self._install_ramble()
        return Command(self.ramble_location / "bin" / "ramble", env={}), first_time

    def _spack(self):
        env = {"SPACK_DISABLE_LOCAL_CONFIG": "1"}
        spack = Command(self.spack_location / "bin" / "spack", env)
        spack_cache_location = self.spack_location / "misc-cache"
        first_time = False
        if not self.spack_location.exists():
            first_time = True
            self._install_spack()
            spack(
                "config",
                "--scope=site",
                "add",
                f"config:misc_cache:{spack_cache_location}",
            )
        return spack, first_time

    def spack_first_time_setup(self):
        return self._spack()

    def ramble_first_time_setup(self):
        return self._ramble()

    def spack(self):
        return self._spack()[0]

    def ramble(self):
        return self._ramble()[0]
