..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

##############
 Run a Binary
##############

If you have a pre-built binary of your application, you can use it in your Benchpark
experiment using the ``user-managed`` Ramble-defined package manager (`see docs
<https://ramble.readthedocs.io/en/latest/package_manager_list.html#user-managed>`_).
When initializing your experiment, provide the path to the binary using ``prepend_path``
which will add the binary path to ``PATH``, and specify ``user-managed`` as the package
manager. System setup does not change.

Example running the ``osu-micro-benchmarks`` workload ``osu_latency`` on the ``ruby``
system:

::

    benchpark system init --dest=ruby llnl-cluster cluster=ruby
    benchpark experiment init --dest=osumb ruby osu-micro-benchmarks \
        package_manager="user-managed" \
        workload="osu_latency" \
        prepend_path="/usr/myuser/osu-micro-benchmarks/mpi/pt2pt"
    benchpark setup ./ruby/osumb/ osumb-ruby/
    # Follow Ramble execution instructions ...

This will execute using the ``osu_latency`` binary located at
``osu-micro-benchmarks/mpi/pt2pt/osu_latency``.

Or for example, if we have a build ``kripke`` with spack on ``dane`` and then used that
binary (``bin/kripke.exe``):

::

    benchpark system init --dest=dane llnl-cluster cluster=dane
    benchpark experiment init --dest=kripke dane kripke \
        package_manager="user-managed" \
        prepend_path="/usr/myuser/benchpark/wkp/spack/opt/spack/linux-rhel8-sapphirerapids/oneapi-2023.2.1/kripke-develop-ehvoc6dzdprgm3lhaghh7uoiqsc5xcf6/bin"
    benchpark setup ./dane/kripke/ kripke-dane/
    # Follow Ramble execution instructions ...

Using the spack built binary.
