# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2022-2024 The Ramble Authors
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

import yaml

import benchpark.base_paths


class RequiredClassAttr:
    def __init__(self, name):
        self.name = name

    def __get__(self, obj, owner):
        raise NotImplementedError(
            f"{owner.__name__} must define class attribute '{self.name}'"
        )


class ConfigSection:
    def __init__(self, data, path):
        self.data = data
        self.path = pathlib.Path(path)

    filename = RequiredClassAttr("filename")
    name = RequiredClassAttr("name")

    @classmethod
    def try_load(cls, cfg_dir):
        cfg_path = pathlib.Path(cfg_dir) / cls.filename
        if cfg_path.exists():
            with open(cfg_path, "r") as f:
                data = yaml.safe_load(f)[cls.name]
        else:
            data = {}
        return cls(data, cfg_path)

    def resolve_path(self, value):
        path = pathlib.Path(value)
        if not path.is_absolute():
            return (self.path.parents[0] / path).resolve()


class PropertyDict:
    def __getattr__(self, name):
        val = self.data[name]
        if isinstance(val, dict):
            return PropertyDict(val)
        return val


class Repos(ConfigSection, PropertyDict):
    filename = "repos.yaml"
    name = "repos"


class Bootstrap(ConfigSection, PropertyDict):
    filename = "bootstrap.yaml"
    name = "bootstrap"


_section_types = [Repos, Bootstrap]


class Configuration:
    section_names = [st.name for st in _section_types]

    def __init__(self, cfg_dir):
        self.sections = {}
        for st in _section_types:
            attempt = st.try_load(cfg_dir)
            if attempt:
                self.sections[st.name] = attempt

    def __getattr__(self, name):
        if name in self.sections:
            return self.sections[name]
        elif name in Configuration.section_names:
            raise Exception("This section is not present in this config")
        else:
            raise AttributeError("No such section")


_configuration = None


def configuration():
    global _configuration
    if not _configuration:
        _configuration = Configuration(benchpark.base_paths.determine_config_dir())

    return _configuration
