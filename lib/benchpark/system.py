# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import hashlib
import importlib.util
import os
import pathlib
import sys

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

    def initialize(self):
        self.external_resources = None

        self.sys_cores_per_node = None
        self.sys_gpus_per_node = None
        self.sys_mem_per_node = None
        self.scheduler = None
        self.timeout = "120"
        self.queue = None

        self.required = ["sys_cores_per_node", "scheduler", "timeout"]

    def generate_description(self, output_dir):
        self.initialize()
        output_dir = pathlib.Path(output_dir)

        variables_yaml = output_dir / "variables.yaml"
        with open(variables_yaml, "w") as f:
            f.write(self.variables_yaml())

        self.external_packages(output_dir)
        self.compiler_description(output_dir)

        spec_hash = self.system_uid()

        system_id_path = output_dir / "system_id.yaml"
        with open(system_id_path, "w") as f:
            f.write(
                f"""\
system:
  name: {self.__class__.__name__}
  spec: {str(self.spec)}
  config-hash: {spec_hash}
"""
            )

    def system_uid(self):
        return _hash_id([str(self.spec)])

    def _merge_config_files(self, schema, selections, dst_path):
        data = cfg.read_config_file(selections[0], schema)
        for selection in selections[1:]:
            cfg.merge_yaml(data, cfg.read_config_file(selection, schema))

        with open(dst_path, "w") as outstream:
            syaml.dump_config(data, outstream)

    def external_pkg_configs(self):
        return None

    def compiler_configs(self):
        return None

    def external_packages(self, output_dir):
        selections = self.external_pkg_configs()
        if not selections:
            return

        aux = output_dir / "auxiliary_software_files"
        os.makedirs(aux, exist_ok=True)
        aux_packages = aux / "packages.yaml"

        self._merge_config_files(packages_schema.schema, selections, aux_packages)

    def compiler_description(self, output_dir):
        selections = self.compiler_configs()
        if not selections:
            return

        aux = output_dir / "auxiliary_software_files"
        os.makedirs(aux, exist_ok=True)
        aux_compilers = aux / "compilers.yaml"

        self._merge_config_files(compilers_schema.schema, selections, aux_compilers)

    def system_specific_variables(self):
        return {}

    def variables_yaml(self):
        for attr in self.required:
            if not getattr(self, attr, None):
                raise ValueError(f"Missing required info: {attr}")

        optionals = list()
        for opt in ["sys_gpus_per_node", "sys_mem_per_node", "queue"]:
            if getattr(self, opt, None):
                optionals.append(f"{opt}: {getattr(self, opt)}")

        system_specific = list()
        for k, v in self.system_specific_variables().items():
            system_specific.append(f"{k}: {v}")

        extra_variables = optionals + system_specific
        indent = " " * 2
        extras_as_cfg = ""
        if extra_variables:
            extras_as_cfg = f"\n{indent}".join(extra_variables)

        return f"""\
# SPDX-License-Identifier: Apache-2.0

variables:
  timeout: "{self.timeout}"
  scheduler: "{self.scheduler}"
  sys_cores_per_node: "{self.sys_cores_per_node}"
  {extras_as_cfg}
  max_request: "1000"  # n_ranks/n_nodes cannot exceed this
  n_ranks: '1000001'  # placeholder value
  n_nodes: '1000001'  # placeholder value
  batch_submit: "placeholder"
  mpi_command: "placeholder"
"""
