..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

###############
 Configuration
###############

********************
 Bootstrap Location
********************

Benchpark clones Ramble to use as a library automatically as part of
running. It clones both Ramble and Spack to allow building and running
benchmarks. Benchmarks are organized into workspaces, which have their
own clones of Spack/Ramble, and these are staged from a centralized
location. The default is in ~/.benchpark, but you can pick another
location if desired. This default can be set in
``<benchpark_root>/config/bootstrap.yaml``.

*******
 Repos
*******

See ``<benchpark_root>/config/repos.yaml``: with this you can fully
customize system/experiment repos used by Benchpark, application repos
used by Ramble, and package repositories used by Spack. Note in the
case of Spack, the builtin repository is always used (in addition to
whatever package repositories are specified).

********************
 Scopes
********************

Benchpark can pull config from one location, with the following
priority (highest first):

* ``benchpark -C <dir>...``
* If CWD where you call benchpark has benchpark-config directory
* If ``<benchpark_root>/config`` is a directory (this must exist if the
  first two don't)

There is no mixing and matching between these tiers: if you are using
``-C``, then the specified directory must contain a ``bootstrap.yaml``
and a ``repos.yaml`` (you can copy from ``<benchpark_root>/config``
if you want the same config).