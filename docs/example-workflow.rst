.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

=========================
Hello Benchpark Example
=========================

This tutorial will guide you through the process of using Benchpark in a
container.  In this case, the ``system``, and the ``benchmark``
and ``experiment`` are already configured and just need to be setup and run.

.. note:

    Add steps to init, setup, build, run analyze on existing system (container
    ideally)

First, initialize the variant of the AWS system using the existing system
specification in Benchpark::

    benchpark system init --dest=aws-system aws-cluster

To run the openmp, single node scaling version of the Kripke benchmark, initialize it for experiments::

    benchpark experiment init --dest=kripke-benchmark kripke +openmp+strong~single_node caliper=time

Then setup the workspace directory for the system and experiment together::

    benchpark setup ./kripke-benchmark ./aws-system workspace/

Benchpark will provide next steps to the console but they are also provided here.
Run the setup script for dependency software, Ramble and Spack::

    . workspace/setup.sh

Then setup the Ramble experiment workspace, this builds all software and may take some time::

    cd ./workspace/kripke-benchmark/aws-system/workspace/
    ramble --workspace-dir . --disable-progress-bar workspace setup

Next, we run the Kripke experiments, which will launch jobs through the
scheduler on the AWS system::

    ramble --workspace-dir . --disable-progress-bar on

After running the experiments, conduct pre-defined analyses with Benchpark::

    benchpark analyze --workspace-dir workspace/kripke/openmp/aws/workspace/
