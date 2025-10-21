# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import hashlib
import os
import sys
from typing import Dict, Tuple

import packaging.version
import yaml

import benchpark.spec
import benchpark.variant
from benchpark.directives import ExperimentSystemBase, provides, variant


def _hash_id(content_list):
    sha256_hash = hashlib.sha256()
    for x in content_list:
        sha256_hash.update(x.encode("utf-8"))
    return sha256_hash.hexdigest()


class MPISystem:
    provides("mpi")

    name = "mpi"

    def system_specific_variables(self, system):
        return {}


class JobQueue:
    def __init__(self, name, time_limit, max_nodes):
        self.name = name
        self.time_limit = time_limit
        self.max_nodes = max_nodes

    def satisfies_time_limit(self, time):
        if int(time) > self.time_limit:
            raise ValueError(
                f"timeout={time} is unsatisfiable for the selected queue '{self.name}'. Max timeout is {self.time_limit}"
            )
        return True


class System(ExperimentSystemBase):
    variants: Dict[
        str,
        Tuple["benchpark.variant.Variant", "benchpark.spec.ConcreteSystemSpec"],
    ]

    variant(
        "timeout",
        default="120",
        multi=False,
        description="Set job timeout limit (in minutes). Has to be under the limit for selected 'queue'.",
    )

    def __init__(self, spec):
        self.spec: "benchpark.spec.ConcreteSystemSpec" = spec
        super().__init__()

        self.external_resources = None

        self.sys_cores_per_node = None
        self.sys_cores_os_reserved_per_node = None
        self.sys_cores_os_reserved_per_node_list = None
        self.sys_gpus_per_node = None
        self.sys_mem_per_node_GB = None
        self.scheduler = None
        self.timeout = "120"
        self.queue = None
        self.bank = None
        self.config_hash = self.system_uid()
        self.destdir = None

        # Assume every system is an MPI system
        self._programming_models = [MPISystem()]

        self.required = ["sys_cores_per_node", "scheduler", "timeout"]

    def compute_system_id(self):
        return {
            "system": {
                "name": self.__class__.__name__,
                "spec": str(self.spec),
                "config-hash": self.config_hash,
                "benchpark_system_command": "benchpark " + " ".join(sys.argv[1:]),
                "destdir": self.spec.destdir,
            }
        }

    def system_uid(self):
        return _hash_id([str(self.spec)])

    def external_pkg_configs(self):
        return None

    def compiler_configs(self):
        return None

    @property
    def programming_models(self):
        return self._programming_models

    @programming_models.setter
    def programming_models(self, pm_list):
        if not isinstance(pm_list, list):
            raise ValueError("Value must be a list")
        self._programming_models.extend(pm_list)

    def verify(self):
        for pm in self.programming_models:
            pm.verify(self)

    def enforce(self, attr):
        if attr not in self.provides:
            raise AttributeError(f'{self.spec.name} does not provide "{attr}"')

    def system_specific_variables(self):
        vars = {}
        for pm in self.programming_models:
            for x, y in pm.system_specific_variables(self).items():
                # Note: if you put an object into a yaml file there is an
                # attempt to represent the object, whereas we want the string.
                # We make use of the Version behavior on e.g. 'cuda_version'
                # in some places, so cannot generally store it as a string, and
                # instead just convert it here where it goes into yaml
                if isinstance(y, packaging.version.Version):
                    y = str(y)
                vars[x] = y
        return vars

    def compute_packages_section(self):
        selections = self.external_pkg_configs()
        return selections

    def compute_compilers_section(self):
        selections = self.compiler_configs()

        return selections

    def compute_variables_section(self):
        for attr in self.required:
            if not getattr(self, attr, None):
                raise ValueError(f"Missing required info: {attr}")

        optionals = {}
        for opt in [
            "sys_cores_os_reserved_per_node",
            "sys_cores_os_reserved_per_node_list",
            "sys_gpus_per_node",
            "sys_mem_per_node_GB",
        ]:
            if getattr(self, opt, None):
                optionals[opt] = getattr(self, opt)

        system_specific = {}
        for k, v in self.system_specific_variables().items():
            system_specific[k] = v

        job_configuration_options = {}
        self.timeout = job_configuration_options["timeout"] = self.spec.variants[
            "timeout"
        ][0]
        # Set bank
        if "bank" in self.spec.variants and self.spec.variants["bank"][0] != "none":
            self.bank = job_configuration_options["bank"] = self.spec.variants["bank"][
                0
            ]
        # Set queue
        if "queue" in self.spec.variants and self.spec.variants["queue"][0] != "none":
            self.queue = job_configuration_options["queue"] = queue_name = (
                self.spec.variants["queue"][0]
            )
            queue_obj = [q for q in self.queues if q.name == queue_name][0]
            self.max_nodes = job_configuration_options["max_nodes"] = (
                queue_obj.max_nodes
            )
            assert queue_obj.satisfies_time_limit(self.timeout)

        extra_variables = optionals | system_specific | job_configuration_options

        return {
            "variables": {
                "timeout": self.timeout,
                "scheduler": self.scheduler,
                "sys_cores_per_node": self.sys_cores_per_node,
                "n_ranks": 2**64 - 1,
                "n_nodes": 2**64 - 1,
                "batch_submit": "placeholder",
                "mpi_command": "placeholder",
            }
            | extra_variables
        }

    def compute_software_section(self):
        return NotImplementedError(
            "Each system must implement compute_externals_section"
        )

    def compute_dict(self):
        # This can be overridden by any subclass that needs more flexibility
        pkg_cfg = self.compute_packages_section() or {}
        compiler_cfg = self.compute_compilers_section()
        if compiler_cfg:
            pkg_cfg = merge_dicts(pkg_cfg, compiler_cfg)
        # "'packages:':" syntax is required to enforce spack to use benchpark-defined
        # compilers instead of external compilers defined by spack compiler search (from ramble).
        if pkg_cfg:
            pkg_cfg = {"packages:": pkg_cfg["packages"]}
        else:
            pkg_cfg = {"packages": {}}
        return {
            "system_id": self.compute_system_id(),
            "variables": self.compute_variables_section(),
            "software": self.compute_software_section(),
            "auxiliary_software_files": {
                "packages": pkg_cfg,
            },
        }

    def write_system_dict(self, destdir):
        def _write_key_file(destdir, key, sys_dict):
            with open(f"{destdir}/{key}.yaml", "w") as f:
                yaml.dump(sys_dict[key], f)

        system_dict = self.compute_dict()
        for key in system_dict.keys():
            if key == "auxiliary_software_files":
                os.makedirs(destdir + "/" + key)
                for k in system_dict[key]:
                    _write_key_file(destdir + "/" + key, k, system_dict[key])
            else:
                _write_key_file(destdir, key, system_dict)


def merge_dicts(*dicts):
    current = {}
    for d in dicts:
        if not d:
            continue
        current = _merge_dicts(current, d)
    return current


def _merge_dicts(d1, d2):
    result = dict(d1)
    for k, v2 in d2.items():
        if k in result:
            v1 = result[k]
            if all(isinstance(x, dict) for x in (v1, v2)):
                result[k] = _merge_dicts(v1, v2)
            elif all(isinstance(x, list) for x in (v1, v2)):
                result[k] = v1 + v2
            else:
                raise ValueError(f"{k} merge mismatch: {v1}/{v2}")
        else:
            result[k] = v2
    return result


def hybrid_compiler_requirements(c_cmp, f_cmp):
    return {
        "packages": {
            "all": {
                "require": [
                    {
                        "spec": rf"%[virtuals=c] {c_cmp}",
                        "when": r"%c",
                    },
                    {"spec": rf"%[virtuals=cxx] {c_cmp}", "when": r"%cxx"},
                    {"spec": rf"^[virtuals=fortran] {f_cmp}", "when": r"^fortran"},
                ]
            }
        }
    }


def compiler_section_for(name, entries):
    return {"packages": {name: {"externals": entries, "buildable": False}}}


def compiler_def(
    spec,
    prefix,
    exes,
    env=None,
    extra_rpaths=None,
    modules=None,
    flags=None,
    compilers_use_relative_paths=False,
):
    lang_map = {}
    for lang, exe in exes.items():
        if os.path.isabs(exe) or compilers_use_relative_paths:
            lang_map[lang] = exe
        else:
            lang_map[lang] = os.path.join(prefix, "bin", exe)
    entry = {
        "spec": spec,
        "prefix": prefix,
        "extra_attributes": {"compilers": lang_map},
    }
    if env:
        entry["extra_attributes"]["environment"] = env
    if extra_rpaths:
        entry["extra_attributes"]["extra_rpaths"] = extra_rpaths
    if modules:
        entry["modules"] = modules
    if flags:
        entry["extra_attributes"]["flags"] = flags
    return entry
