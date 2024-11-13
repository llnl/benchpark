# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2022-2024 The Ramble Authors
#
# SPDX-License-Identifier: Apache-2.0

import contextlib
import sys
from enum import Enum

import benchpark.paths
import benchpark.runtime

# isort: off

bootstrapper = benchpark.runtime.RuntimeResources(
    benchpark.paths.benchpark_home
)  # noqa
bootstrapper.bootstrap()  # noqa

import llnl.util.lang  # noqa
import ramble.language.language_base  # noqa
import ramble.repository  # noqa

# isort: on

global_namespace = "benchpark"
namespaces = ["benchpark.expr", "benchpark.sys"]

#: Guaranteed unused default value for some functions.
NOT_PROVIDED = object()


####
# Implement type specific functionality between here, and
#     END TYPE SPECIFIC FUNCTIONALITY
####
ObjectTypes = Enum("ObjectTypes", ["experiments", "systems"])

OBJECT_NAMES = [obj.name for obj in ObjectTypes]

default_type = ObjectTypes.experiments

type_definitions = {
    ObjectTypes.experiments: {
        "file_name": "experiment.py",
        "dir_name": "experiments",
        "abbrev": "expr",
        "config_section": "repos",
        "accepted_configs": ["repo.yaml"],
        "singular": "experiment",
    },
    ObjectTypes.systems: {
        "file_name": "system.py",
        "dir_name": "systems",
        "abbrev": "sys",
        "config_section": "repos",
        "accepted_configs": ["repo.yaml"],
        "singular": "system",
    },
}


@contextlib.contextmanager
def override_ramble_hardcoded_globals():
    _old = (
        ramble.repository.type_definitions,
        ramble.repository.global_namespace,
        ramble.language.language_base.namespaces,
    )
    ramble.repository.type_definitions = type_definitions
    ramble.repository.global_namespace = global_namespace
    ramble.language.language_base.namespaces = namespaces

    yield

    ramble.repository.type_definitions = _old[0]
    ramble.repository.global_namespace = _old[1]
    ramble.language.language_base.namespaces = _old[2]


# Experiments
def _exprs():
    """Get the singleton RepoPath instance for Ramble.

    Create a RepoPath, add it to sys.meta_path, and return it.

    TODO: consider not making this a singleton.
    """
    experiments_repo = benchpark.paths.benchpark_root / "experiments"
    return _add_repo(experiments_repo, ObjectTypes.experiments)


def _add_repo(repo_dir, obj_type):
    if repo_dir.exists():
        repo_dirs = [str(repo_dir)]
    else:
        raise ValueError(f"Repo dir does not exist: {repo_dir}")

    with override_ramble_hardcoded_globals():
        path = ramble.repository.RepoPath(*repo_dirs, object_type=obj_type)
    sys.meta_path.append(path)
    return path


# Systems
def _systems():
    systems_repo = benchpark.paths.benchpark_root / "systems"
    return _add_repo(systems_repo, ObjectTypes.systems)


paths = {
    ObjectTypes.experiments: llnl.util.lang.Singleton(_exprs),
    ObjectTypes.systems: llnl.util.lang.Singleton(_systems),
}


#####################################
#     END TYPE SPECIFIC FUNCTIONALITY
#####################################


def all_object_names(object_type=default_type):
    """Convenience wrapper around ``ramble.repository.all_object_names()``."""  # noqa: E501
    return paths[object_type].all_object_names()


def get(spec, object_type=default_type):
    """Convenience wrapper around ``ramble.repository.get()``."""
    return paths[object_type].get(spec)


def set_path(repo, object_type=default_type):
    """Set the path singleton to a specific value.

    Overwrite ``path`` and register it as an importer in
    ``sys.meta_path`` if it is a ``Repo`` or ``RepoPath``.
    """
    global paths
    paths[object_type] = repo

    # make the new repo_path an importer if needed
    append = isinstance(repo, (ramble.repository.Repo, ramble.repository.RepoPath))
    if append:
        sys.meta_path.append(repo)
    return append


@contextlib.contextmanager
def additional_repository(repository, object_type=default_type):
    """Adds temporarily a repository to the default one.

    Parameters:
        repository: repository to be added
    """
    paths[object_type].put_first(repository)
    yield
    paths[object_type].remove(repository)


@contextlib.contextmanager
def use_repositories(*paths_and_repos, object_type=default_type):
    """Use the repositories passed as arguments within the context manager.

    Parameters:
        `*paths_and_repos`: paths to the repositories to be used, or
            already constructed Repo objects

    Returns:
        Corresponding RepoPath object
    """
    global paths

    # Construct a temporary RepoPath object from
    temporary_repositories = ramble.repository.RepoPath(
        *paths_and_repos, object_type=object_type
    )

    # Swap the current repository out
    saved = paths[object_type]
    remove_from_meta = set_path(temporary_repositories, object_type=object_type)

    yield temporary_repositories

    # Restore _path and sys.meta_path
    if remove_from_meta:
        sys.meta_path.remove(temporary_repositories)
    paths[object_type] = saved


# Add the finder to sys.meta_path
REPOS_FINDER = ramble.repository.ReposFinder()
sys.meta_path.append(REPOS_FINDER)
