..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

#######################
 Configuring Benchpark
#######################

Benchpark offers several options to configure usage. This includes:

1. Configuring the location of the bootstrap directory (default is ``~/.benchpark``).
   This is useful to change from the default value if you do not have much space in your
   home directory, as the bootstrap contains the ``spack``, ``spack-packages``, and
   ``ramble`` repositories.

1. Configuring which repositories benchpark uses for objects in the
   ``experiments/systems/repos`` directories (``experiment.py``, ``system.py``,
   ``package.py``, and ``application.py``).

**********************************************
 Configuring the Benchpark Bootstrap Location
**********************************************

Benchpark clones ``ramble``, ``spack``, and ``spack-packages`` into a centralized
location (by default this is ``~/.benchpark``) to enable building and running
benchmarks. Benchpark workspaces copy over these repositories from the centralized
location to avoid downloading from the internet when initializing a Benchpark workspace.
Keep in mind that the speed of writing a clone of ``ramble``, ``spack``, and
``spack-packages``, as well as the speed of copying what is needed into workspaces, will
depend on the speed of the storage you select for the bootstrap location. The bootstrap
location can be configured in ``<benchpark_root>/config/bootstrap.yaml`` or by running
``benchpark configure --bootstrap-location <location>``.

***********************************************
 Configuring Which Repositories Benchpark Uses
***********************************************

The ``<benchpark_root>/config/repos.yaml`` file is used to fully customize ``system``
and ``experiment`` repositories used by Benchpark, ``application`` repositories used by
Ramble, and package repositories used by Spack. For Spack and Ramble, the builtin
repository is always used (in addition to whatever package repositories are specified).
The order in which repositories appear in ``<benchpark_root>/config/repos.yaml`` will
determine their precedence, so if you desire to use a custom repository, it should be
listed before any other repositories.

**********************************************************************
 Automatically Generating Configurations with ``benchpark configure``
**********************************************************************

``benchpark configure`` is designed to create the ``yaml`` configurations for you. As of
now, it can only generate bootstrap config (``bootstrap.yaml``). If no bootstrap config
is detected in the chosen scope, this will auto-generate it. ``benchpark configure``
cannot generate a ``repos.yaml`` file at the moment, this must be written manually.

**********************
 Configuration Scopes
**********************

Benchpark can pull configurations from one location, with the following priority
(highest first):

- As an argument to ``benchpark``: ``benchpark -C <dir>...``
- If the CWD where you invoke the benchpark executable has ``benchpark-config``
  directory
- If ``<benchpark_root>/user-config`` is a directory; this will be created on the first
  run of benchpark.
- If ``<benchpark_root>/config`` is a directory; this must exist if the first three
  don't

There is no mixing and matching between these tiers. If you are using ``-C``, then the
specified directory must contain a ``bootstrap.yaml`` and a ``repos.yaml`` (you can copy
from ``<benchpark_root>/config`` if you want the same config).
