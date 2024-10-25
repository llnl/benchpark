.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

==========================
Running on an LLNL System
==========================

.. note

    We might add console outputs for these, so users know what to expect

This tutorial will guide you through the process of using Benchpark on an LLNL
system, this example uses the cuda version of the Saxpy benchmark on Tioga. 
But the steps can be reused for a different system, benchmark or experiment.

First, initialize the system for LLNL's tioga system using the existing
system specification in Benchpark::

    benchpark system init --dest=tioga-system tioga ~gtl

To run the cuda version of the Saxpy benchmark, initialize it for experiments::

    benchpark experiment init --dest=saxpy-benchmark saxpy programming_model=cuda

Then setup the workspace directory for the system and experiment together::

    ./bin/benchpark setup ./saxpy-benchmark ./tioga-system workspace/

Benchpark will provide next steps to the console but they are also provided here.
Run the setup script for dependency software, Ramble and Spack::

    . workspace/setup.sh

Then setup the Ramble experiment workspace, this builds all software and may take some time::

    cd ./workspace/saxpy-benchmark/Tioga-975af3c/workspace/
    ramble --workspace-dir . --disable-progress-bar workspace setup

Next, we run the Saxpy experiments, which will launch jobs through the
scheduler on Tioga::

    ramble --workspace-dir . --disable-progress-bar on
