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

    benchpark system init --dest=tutorial aws-tutorial instance_type=c7i.24xlarge

To run the openmp, single node scaling version of the Kripke benchmark, initialize it for experiments::

    benchpark experiment init --dest kripke-benchmark kripke scaling=strong caliper=time,mpi

Then setup the workspace directory for the system and experiment together::

    benchpark setup kripke-benchmark/ tutorial/ wkp/

Benchpark will provide next steps to the console but they are also provided here.
Run the setup script for dependency software, Ramble and Spack::

    . /home/jovyan/benchpark/wkp/setup.sh

Then setup the Ramble experiment workspace, this builds all software and may take some time::

    ramble --disable-progress-bar --workspace-dir /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace workspace setup

Next, we run the Kripke experiments, which will launch jobs through the
scheduler on the AWS system::

    ramble --disable-progress-bar --workspace-dir /home/jovyan/benchpark/wkp/kripke-benchmark/tutorial/workspace on

After running the experiments, conduct pre-defined analyses with Benchpark::

    benchpark analyze --workspace-dir ~/benchpark/wkp/kripke-benchmark/tutorial/workspace

Navigate to benchpark/wkp/kripke-benchmark/tutorial/workspace/analyze and there should be a .PNG file of the graph after analysis

    .. image:: ./kripke_mpi_strong_raw_exc.png
       :alt: Kripke Analysis Graph
       :width: 800px
       :align: center