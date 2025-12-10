..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

###############
 System Mirror
###############

If you build a benchmark on a networked system, you can use `benchpark mirror` to create
a directory that bundles all necessary resources to install and run that benchmark on
another system, such that the destination system does not need network access.

On the networked system, if you created/built the benchmark with:

::

    benchpark system init --dest=def-ruby llnl-cluster cluster=ruby compiler=gcc
    benchpark experiment init --dest=def-raja-perf def-ruby raja-perf
    benchpark setup def-ruby/def-raja-perf/ workspace/
    . `pwd`/workspace/setup.sh
    ramble --workspace-dir `pwd`/workspace/def-raja-perf/def-ruby/workspace workspace setup

You can then create a directory that bundles all the resources needed to build that
benchmark with:

::

    benchpark mirror create `pwd`/workspace/def-raja-perf/def-ruby/workspace/ test-benchpark-mirror/

You can copy `test-bencpark-mirror/` to another system, and on that system, within that
directory you can do:

::

    python3 -m venv mirror-env && . mirror-env/bin/activate
    pip install --no-index --find-links=pip-cache pip-cache/*
    bash first-time.sh
    . `pwd`/setup.sh
    ramble --workspace-dir `pwd`/def-raja-perf/def-ruby/workspace/ workspace setup

this will install the benchmark on the new system, and also configure Ramble to use
mirror resources that were bundled in `test-benchmark-mirror/` (so it does not need
internet access to build the benchmark).

*************
 Limitations
*************

For now, benchpark can only create mirrors that are useful for destination systems that
match the host system in terms of:

- available compilers
- provided external software

Also, `benchpark mirror` can only create mirrors for benchmarks that have been built on
the source system.
