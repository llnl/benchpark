# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib
import re
import sys

import benchpark.paths
import benchpark.repo

import benchpark.system as system
from benchpark.runtime import RuntimeResources

bootstrapper = RuntimeResources(benchpark.paths.benchpark_home)  # noqa
bootstrapper.bootstrap()  # noqa

import ramble.config as cfg  # noqa


sys_repo = benchpark.repo.paths[benchpark.repo.ObjectTypes.systems]
exp_repo = benchpark.repo.paths[benchpark.repo.ObjectTypes.experiments]


def setup_parser(subparser):
    pass


def audit_experiment(exp_cls):
    required_methods = ["compute_applications_section", "compute_spack_section"]

    if exp_cls.__name__ == "Caliper":
        # Caliper is an abstract class, and is never directly instantiated
        return []

    errors = list()

    for method in required_methods:
        if method not in exp_cls.__dict__:
            errors.append(f"{exp_cls.__name__} does not implement {method}")

    return errors


def _find_yaml_files(d):
    yaml_files = list()
    for root, dirs, files in os.walk(d):
        root = pathlib.Path(root)
        yaml_files.extend((root / f) for f in files if f.endswith(".yaml"))
    return yaml_files


# TODO: when .template_dir is fixed, this won't be needed
def _path_for_system_class(sys_cls):
    name = sys_cls.__name__
    component = ""
    components = []
    for letter in name:
        if re.match("[A-Z]", letter):
            if component:
                components.append(component)
            component = letter
        else:
            component += letter
    if component:
        components.append(component)
    system_dirname = "-".join(x.lower() for x in components)
    basedir = pathlib.Path(
        sys_repo.filename_for_object_name(sys_cls.__name__)
    ).parent.parent
    assert basedir.exists()
    return basedir / system_dirname


def audit_system(sys_cls):
    errors = list()
    basedir = _path_for_system_class(sys_cls)
    externals = basedir / "externals"
    if externals.exists():
        for f in _find_yaml_files(externals):
            cfg.read_config_file(f, system.packages_schema.schema)

    compilers = basedir / "compilers"
    if compilers.exists():
        for f in _find_yaml_files(compilers):
            cfg.read_config_file(f, system.compilers_schema.schema)
    return errors


def command(args):
    all_errors = list()

    for exp_name in exp_repo.all_object_names():
        exp_cls = exp_repo.get_obj_class(exp_name)
        all_errors.extend(audit_experiment(exp_cls))

    for sys_name in sys_repo.all_object_names():
        sys_cls = sys_repo.get_obj_class(sys_name)
        all_errors.extend(audit_system(sys_cls))

    for error in all_errors:
        print(error)

    if all_errors:
        sys.exit(1)
