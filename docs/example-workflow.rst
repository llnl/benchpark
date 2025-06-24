.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

=========================
Hello Benchpark Example
=========================

Containerized Benchpark Coming Soon!

This tutorial will guide you through the process of using Benchpark in a
container.  In this case, the ``system``, and the ``benchmark``
and ``experiment`` are already configured and just need to be setup and run.

.. note:

    Add steps to init, setup, build, run analyze on existing system (container
    ideally)

First, initialize the variant of the AWS system using the existing system
specification in Benchpark::

    benchpark system init --dest=aws-system llnl-cluster cluster=ruby

To run the openmp, single node scaling version of the AMG2023 benchmark, initialize it for experiments::

    benchpark experiment init --dest=amg2023-benchmark amg2023 +openmp caliper=time

Then setup the workspace directory for the system and experiment together::

    benchpark setup ./amg2023-benchmark ./aws-system workspace/

Benchpark will provide next steps to the console but they are also provided here.
Run the setup script for dependency software, Ramble and Spack::

    . workspace/setup.sh

Then setup the Ramble experiment workspace, this builds all software and may take some time::

    cd ./workspace/amg2023-benchmark/aws-system/workspace/
    ramble --workspace-dir . --disable-progress-bar workspace setup

Next, we run the AMG2023 experiments, which will launch jobs through the
scheduler on the AWS system::

    ramble --workspace-dir . --disable-progress-bar on

After running the experiments, conduct pre-defined analyses with Benchpark::

    benchpark analyze --workspace-dir workspace/amg2023/openmp/aws/workspace/
