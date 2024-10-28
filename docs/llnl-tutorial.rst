.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

==========================
Running on an LLNL System
==========================

.. note

    We might add console outputs for these, so users know what to expect

This tutorial will guide you through the process of using Benchpark on LLNL
systems. 

------------------------
CTS (Ruby, Dane, Magma)
------------------------

This example uses the openmp version of the Saxpy benchmark on one of our CTS systems (Ruby, Dane, Magma). 
The variant ``cluster`` determines which of the three systems to initialize.
    
First, initialize the desired cluster variant of the LLNL cts ruby (or dane, magma) system using the existing
system specification in Benchpark::

    benchpark system init --dest=ruby-system cts cluster=ruby

To run the cuda version of the AMG20223 benchmark, initialize it for experiments::

    benchpark experiment init --dest=amg2023-benchmark amg2023 programming_model=openmp

Then setup the workspace directory for the system and experiment together::

    benchpark setup ./amg2023-benchmark ./ruby-system workspace/

Benchpark will provide next steps to the console but they are also provided here.
Run the setup script for dependency software, Ramble and Spack::

    . workspace/setup.sh

Then setup the Ramble experiment workspace, this builds all software and may take some time::

    cd ./workspace/amg2023-benchmark/Cts-6d48f81/workspace/
    ramble --workspace-dir . --disable-progress-bar workspace setup

Next, we run the Saxpy experiments, which will launch jobs through the
scheduler on Tioga::

    ramble --workspace-dir . --disable-progress-bar on

------
Tioga
------

This second tutorial will guide you through the process of using the cuda 
version of the Saxpy benchmark on Tioga. 
The parameters for initializing the system are slightly different due to the 
different variants defined for the system. For example, the variant ``~gtl`` turns off gtl-enabled MPI, ``+gtl`` turns it on::

    benchpark system init --dest=tioga-system tioga ~gtl
    benchpark experiment init --dest=saxpy-benchmark saxpy programming_model=cuda
    benchpark setup ./saxpy-benchmark ./tioga-system workspace/
    . workspace/setup.sh
    cd ./workspace/saxpy-benchmark/Tioga-975af3c/workspace/
    ramble --workspace-dir . --disable-progress-bar workspace setup
    ramble --workspace-dir . --disable-progress-bar on
