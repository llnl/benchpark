# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import hashlib
import importlib.util
import os
import pathlib
import sys
import tempfile
import yaml

import benchpark.paths
from benchpark.directives import ExperimentSystemBase
import benchpark.repo
from benchpark.runtime import RuntimeResources

from typing import Dict, Tuple
import benchpark.spec
import benchpark.variant

bootstrapper = RuntimeResources(benchpark.paths.benchpark_home)  # noqa
bootstrapper.bootstrap()  # noqa

import ramble.config as cfg  # noqa
import ramble.language.language_helpers  # noqa
import ramble.language.shared_language  # noqa
import spack.util.spack_yaml as syaml  # noqa

# We cannot import this the normal way because it from modern Spack
# and mixing modern Spack modules with ramble modules that depend on
# ancient Spack will cause errors. This module is safe to load as an
# individual because it is not used by Ramble
# The following code block implements the line
# import spack.schema.packages as packages_schema
schemas = {
    "spack.schema.packages": f"{bootstrapper.spack_location}/lib/spack/spack/schema/packages.py",
    "spack.schema.compilers": f"{bootstrapper.spack_location}/lib/spack/spack/schema/compilers.py",
}


def load_schema(schema_id, schema_path):
    schema_spec = importlib.util.spec_from_file_location(schema_id, schema_path)
    schema = importlib.util.module_from_spec(schema_spec)
    sys.modules[schema_id] = schema
    schema_spec.loader.exec_module(schema)
    return schema


packages_schema = load_schema(
    "spack.schema.packages",
    f"{bootstrapper.spack_location}/lib/spack/spack/schema/packages.py",
)
compilers_schema = load_schema(
    "spack.schema.compilers",
    f"{bootstrapper.spack_location}/lib/spack/spack/schema/compilers.py",
)


_repo_path = benchpark.repo.paths[benchpark.repo.ObjectTypes.systems]


def _hash_id(content_list):
    sha256_hash = hashlib.sha256()
    for x in content_list:
        sha256_hash.update(x.encode("utf-8"))
    return sha256_hash.hexdigest()


class System(ExperimentSystemBase):
    variants: Dict[
        str,
        Tuple["benchpark.variant.Variant", "benchpark.spec.ConcreteSystemSpec"],
    ]

    def __init__(self, spec):
        self.spec: "benchpark.spec.ConcreteSystemSpec" = spec
        super().__init__()

        self.external_resources = None

        self.sys_cores_per_node = None
        self.sys_gpus_per_node = None
        self.sys_mem_per_node = None
        self.scheduler = None
        self.timeout = "120"
        self.queue = None

        self.required = ["sys_cores_per_node", "scheduler", "timeout"]

    def compute_system_id(self):
        return {
            "system": {
                "name": self.__class__.__name__,
                "spec": str(self.spec),
                "config-hash": self.system_uid(),
            }
        }

    # def generate_description(self, output_dir):
    #     output_dir = pathlib.Path(output_dir)

    #     variables_yaml = output_dir / "variables.yaml"
    #     with open(variables_yaml, "w") as f:
    #         f.write(self.variables_yaml())

    #     self.external_packages(output_dir)
    #     self.compiler_description(output_dir)

    def system_uid(self):
        return _hash_id([str(self.spec)])

    # def _merge_config_files(self, schema, selections, dst_path, override=False):
    #     data = cfg.read_config_file(selections[0], schema)
    #     for selection in selections[1:]:
    #         cfg.merge_yaml(data, cfg.read_config_file(selection, schema))

    #     if override:
    #         for top_level_key, _ in data.items():
    #             break
    #         top_level_key.override = True

    #     with open(dst_path, "w") as outstream:
    #         syaml.dump_config(data, outstream)

    def external_pkg_configs(self):
        return None

    def compiler_configs(self):
        return None

    def system_specific_variables(self):
        return {}

    def compute_packages_section(self):
        selections = self.external_pkg_configs()
        return selections

        # self._merge_config_files(packages_schema.schema, selections, aux_packages)

    def compute_compilers_section(self):
        selections = self.compiler_configs()

        return selections

        # self._merge_config_files(
        #     compilers_schema.schema, selections, aux_compilers, override=True
        # )

    def compute_variables_section(self):
        for attr in self.required:
            if not getattr(self, attr, None):
                raise ValueError(f"Missing required info: {attr}")

        optionals = {}
        for opt in ["sys_gpus_per_node", "sys_mem_per_node", "queue"]:
            if getattr(self, opt, None):
                optionals[opt] = getattr(self, opt)

        system_specific = {}
        for k, v in self.system_specific_variables().items():
            system_specific[k] = v

        extra_variables = optionals | system_specific

        return {
            "variables": {
                "timeout": self.timeout,
                "scheduler": self.scheduler,
                "sys_cores_per_node": self.sys_cores_per_node,
                "max_request": "1000",
                "n_ranks": "1000001",
                "n_nodes": "1000001",
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
        return {
            "system_id": self.compute_system_id(),
            "variables": self.compute_variables_section(),
            "software": self.compute_software_section(),
            "auxiliary_software_files": {
                "compilers": self.compute_compilers_section(),
                "packages": self.compute_packages_section(),
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
