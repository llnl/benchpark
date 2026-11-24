..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

####################
 Run on LLNL System
####################

..
    note

    We might add console outputs for these, so users know what to expect

This tutorial will guide you through the process of using Benchpark on LLNL systems.

To run Benchpark, you will need to install its requirements:

1. Clone LLNL/Benchpark official repo

You need git and Python 3.8+:

::

    git clone https://github.com/LLNL/benchpark.git
    cd benchpark
    . setup-env.sh
    benchpark --version

2. Install Dependencies

Create virtual env. and install dependencies:

::

    python3 -m venv my-env
    . my-env/bin/activate
    pip install -r requirements.txt

*************************
 CTS (Ruby, Dane, Magma)
*************************

This example uses the openmp version of the Saxpy benchmark on one of our CTS systems
(Ruby, Dane, Magma). The variant ``cluster`` determines which of the three systems to
initialize.

First, initialize the desired cluster variant of the LLNL cts ruby (or dane, magma)
system using the existing system specification in Benchpark:

::

    benchpark system init --dest=ruby-system llnl-cluster cluster=ruby

To run the openmp, single node scaling version of the AMG20223 benchmark, initialize it
for experiments:

::

    benchpark experiment init --dest=amg2023-benchmark ruby-system amg2023 +openmp

Then setup the workspace directory for the system and experiment together:

::

    benchpark setup ./ruby-system/amg2023-benchmark workspace/

Benchpark will provide next steps to the console but they are also provided here. Run
the setup script for dependency software, Ramble and Spack:

::

    . workspace/setup.sh

Then setup the Ramble experiment workspace, this builds all software and may take some
time:

::

    cd ./workspace/amg2023-benchmark/ruby-system/workspace/
    ramble --workspace-dir . workspace setup

Next, we run the AMG2023 experiments, which will launch jobs through the scheduler on
the CTS system:

::

    ramble --workspace-dir . on

*******
 Tioga
*******

This second tutorial will guide you through the process of using the ROCm version of the
Saxpy benchmark on Tioga. The parameters for initializing the system are slightly
different due to the different variants defined for the system. For example, the variant
``~gtl`` turns off gtl-enabled MPI, ``+gtl`` turns it on:

::

    benchpark system init --dest=tioga-system llnl-elcapitan cluster=tioga ~gtl
    benchpark experiment init --dest=saxpy-benchmark tioga-system saxpy +rocm
    benchpark setup ./tioga-system/saxpy-benchmark workspace/
    . workspace/setup.sh
    cd ./workspace/saxpy-benchmark/Tioga-975af3c/workspace/
    ramble --workspace-dir . workspace setup
    ramble --workspace-dir . on
