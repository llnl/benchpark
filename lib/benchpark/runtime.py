# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib
import shlex
import subprocess
import sys
from contextlib import contextmanager

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
            f"Failed command: {command_str}\nOutput: {out}\nError: {err}"
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
        self.dest = pathlib.Path(dest)
        self.upstream = upstream

        self.ramble_location, self.spack_location, self.pkgs_location = (
            self.dest / "ramble",
            self.dest / "spack",
            self.dest / "spack-packages",
        )

        # Read pinned versions of ramble and spack
        with open(benchpark.paths.checkout_versions, "r") as yaml_file:
            data = yaml.safe_load(yaml_file)["versions"]
            self.ramble_commit, self.spack_commit, self.pkgs_commit = (
                data["ramble"],
                data["spack"],
                data["spack-packages"],
            )

        # Read remote urls for ramble and spack
        with open(benchpark.paths.remote_urls, "r") as yaml_file:
            data = yaml.safe_load(yaml_file)["urls"]
            remote_ramble_url, remote_spack_url, remote_pkgs_url = (
                data["ramble"],
                data["spack"],
                data["spack-packages"],
            )

        # If this does not have an upstream, then we will be cloning from the URLs indicated in remote-urls.yaml
        if self.upstream is None:
            self.ramble_url, self.spack_url, self.pkgs_url = (
                remote_ramble_url,
                remote_spack_url,
                remote_pkgs_url,
            )
        else:
            # Clone from local "upstream" repository
            self.ramble_url, self.spack_url, self.pkgs_url = (
                self.upstream.ramble_location,
                self.upstream.spack_location,
                self.upstream.pkgs_location,
            )

    def _check_and_update_bootstrap(self, desired_commit, location):
        with working_dir(location):
            # length of hash is 7 in checkout-versions.yaml
            current_commit = run_command("git rev-parse HEAD")[0].strip()[:7]
            if current_commit != desired_commit:
                run_command("git fetch --all")
                run_command(f"git checkout {desired_commit}")
                print(
                    f"Updating '{location}' from {current_commit} to {desired_commit}"
                )

    def bootstrap(self):
        if not self.ramble_location.exists():
            self._install_ramble()
        else:
            self._check_and_update_bootstrap(self.ramble_commit, self.ramble_location)
        ramble_lib_path = self.ramble_location / "lib" / "ramble"
        externals = str(ramble_lib_path / "external")
        if externals not in sys.path:
            sys.path.insert(1, externals)
        internals = str(ramble_lib_path)
        if internals not in sys.path:
            sys.path.insert(1, internals)

        if not self.pkgs_location.exists():
            self._install_packages()
        else:
            self._check_and_update_bootstrap(self.pkgs_commit, self.pkgs_location)

        # Spack does not go in sys.path, but we will manually access modules from it
        # The reason for this oddity is that spack modules will compete with the internal
        # spack modules from ramble
        if not self.spack_location.exists():
            self._install_spack()
        else:
            self._check_and_update_bootstrap(self.spack_commit, self.spack_location)

    def _install_ramble(self):
        print(f"Cloning Ramble to {self.ramble_location}")
        git_clone_commit(
            self.ramble_url,
            self.ramble_commit,
            self.ramble_location,
        )
        debug_print(f"Done cloning Ramble ({self.ramble_location})")

    def _install_spack(self):
        print(f"Cloning Spack to {self.spack_location}")
        git_clone_commit(
            self.spack_url,
            self.spack_commit,
            self.spack_location,
        )
        debug_print(f"Done cloning Spack ({self.spack_location})")

    def _install_packages(self):
        print(f"Cloning packages to {self.pkgs_location}")
        git_clone_commit(
            self.pkgs_url,
            self.pkgs_commit,
            self.pkgs_location,
        )
        debug_print(f"Done cloning spack-packages ({self.pkgs_location})")

    def _ramble(self):
        first_time = False
        if not self.ramble_location.exists():
            first_time = True
            self._install_ramble()
        return Command(self.ramble_location / "bin" / "ramble", env={}), first_time

    def _spack(self):
        if not self.pkgs_location.exists():
            self._install_packages()

        env = {"SPACK_DISABLE_LOCAL_CONFIG": "1"}
        spack = Command(self.spack_location / "bin" / "spack", env)
        spack_cache_location = self.spack_location / "misc-cache"
        bootstrap_cache_location = self.dest / "sbc"
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
            spack(
                "config",
                "--scope=site",
                "add",
                f"bootstrap:root:{bootstrap_cache_location}",
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
