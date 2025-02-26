.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0


==========================================
Comparing two Experiments Within Benchpark
==========================================

This tutorial will guide you through the process of building and comparing distinct binaries of the same benchmark. 
As an example, we will be using an experiment comparing two builds of the quicksilver benchmark, compiled with the ``gcc`` and ``intel`` compiler variants on LLNL's Ruby cluster.i

An example script to complete all experiment setup is loacted at ``examples/multiple-binaries/daneSetup.sh``

Building Multiple Binaries:
---------------------------

Create separate system instances.
Parameters could include: compiler, mpi, etc.
In this case, we are changing the compiler variant

``benchpark system init --dest=ruby-gcc  llnl-cluster cluster=ruby compiler=gcc``

``benchpark system init --dest=ruby-intel  llnl-cluster cluster=ruby compiler=intel``

Creating experiment ramble.yaml:
---------------------------

Create the experiment description
Parameters could include: version, scaling, etc.

In this example, we are only changing the compiler. Because all experiment variables will be the same, we only need to generate a single experiment description.
In this command we are intializing a quicksilver experiment in the quicksilver directory. We are doing weak scaling with openMP, and measuring MPI metrics with Caliper. 

``benchpark experiment init --dest=quicksilver  quicksilver caliper=mpi +weak +openmp ~single_node``


Note: Running a benchmark repeatedly will overwrite the existing output. A way to keep prevent this is to create multiple duplicate experiments, change the experiment name ({experiment1}, {experiment2}). 

Running multiple experiments:
---------------------------

Now that both the system and experiment parameters have been defined, we can setup each experiment directory. 
This step will install the binary, and create the execute_experiment shell script::

  benchpark setup quicksilver ruby-gcc workspace
  benchpark setup quicksilver ruby-intel workspace

  
Now, we generate an execute_experiment shell script for each run, and install the benchmark along with all dependencies::

  ramble -P -D workspace/quicksilver/ruby-gcc/workspace workspace setup
  ramble -P -D workspace/quicksilver/ruby-intel/workspace workspace setup

Completing these steps will result in the following structure::

   experiments_root/
        ramble/
        spack/
        quicksilver/
            ruby-gcc/
            	workspace/
                    experiments/
                        ..../
                        execute_experiment
            ruby-intel/
                workspace/
                    experiments/
                    ..../
                    execute_experiment



 
Verifying build details, differences between builds
---------------------------------------------------

Benchpark offers two ways to double check that each binary has built according to the specifications:

``spack find -L quicksilver``

This returns the following output::

   -- linux-rhel8-sapphirerapids / gcc@12.1.1 ----------------------
   fubnce7wzgjxhkim2cylijt4cbpfhxi6 quicksilver@master

   -- linux-rhel8-sapphirerapids / intel@2021.6.0-classic ----------
   qwev4yodp2joikf2oxvlo224ksjcqve3 quicksilver@master
   ==> 2 installed packages

This output shows each installed binary, along with their associated hashes. We can use these hashes to independently double-check the details of each build.


In this case, we can check the quicksilver spec, along with its dependencies by running spack spec for each binary

``spack spec quicksilver/{hash}``

Each spec will generate a dependency tree, showing which variants and compilers were used for each compiler. The output from both commands is below ::
    
   [+]  quicksilver@master%gcc@12.1.1~cuda+mpi+openmp build_system=makefile arch=linux-rhel8-sapphirerapids
   [+]      ^gcc-runtime@12.1.1%gcc@12.1.1 build_system=generic arch=linux-rhel8-sapphirerapids
   [e]      ^glibc@2.28%gcc@12.1.1 build_system=autotools arch=linux-rhel8-sapphirerapids
   [e]      ^gmake@4.2.1%gcc@12.1.1~guile build_system=generic patches=ca60bd9,fe5b60d arch=linux-rhel8-sapphirerapids
   [e]      ^mvapich2@2.3.7-gcc1211%gcc@12.1.1~alloca~cuda~debug~hwloc_graphics~hwlocv2+regcache+wrapperrpath build_system=autotools ch3_rank_bits=32 fabrics=mrail file_systems=auto patches=d98d8e7 process_managers=auto threads=multiple arch=linux-rhel8-sapphirerapids 


   [+]  quicksilver@master%intel@2021.6.0-classic~cuda+mpi+openmp build_system=makefile arch=linux-rhel8-sapphirerapids
   [e]      ^glibc@2.28%intel@2021.6.0-classic build_system=autotools arch=linux-rhel8-sapphirerapids
   [e]      ^gmake@4.2.1%intel@2021.6.0-classic~guile build_system=generic patches=ca60bd9,fe5b60d arch=linux-rhel8-sapphirerapids
   [e]      ^mvapich2@2.3.7-intel202160classic%intel@2021.6.0-classic~alloca~cuda~debug~hwloc_graphics~hwlocv2+regcache+wrapperrpath build_system=autotools ch3_rank_bits=32 fabrics=mrail file_systems=auto patches=d98d8e7 process_managers=auto threads=multiple arch=linux-rhel8-sapphirerapids

Notice that each dependency tree differs in the compilers used (gcc@12.1.1 vs. intel@2021.6.0)

This can also be done in a single command by the altdiff command built into benchmark, highlighting all differences in red.

``spack-python  lib/scripts/altdiff.py quicksilver/{hash1}  quicksilver/{hash2}``

the output will look like this:

   quicksilver@master**%gcc@=12.1.1** build_system=makefile~cuda+mpi+openmp arch=linux-rhel8-sapphirerapids
   **-> [gcc-runtime]
     gcc-runtime**
       glibc@2.28**%gcc@=12.1.1** build_system=autotools arch=linux-rhel8-sapphirerapids
     mvapich2**@2.3.7-gcc1211%gcc@=12.1.1**~alloca build_system=autotools ch3_rank_bits=32~cuda~debug fabrics=mrail file_systems=auto~hwloc_graphics~hwlocv2 patches=d98d8e7 process_managers=auto+regcache threads=multiple+wrapperrpath arch=linux-rhel8-sapphirerapids 


Running Experiments
-------------------

To run each binary on different nodes, run the following commands::

  ramble -P -D workspace/quicksilver/ruby-gcc/workspace on
  ramble -P -D workspace/quicksilver/ruby-intel/workspace on

However, we can manually combine each ``execute_experiment`` file into a single script, allowing us to run both binaries on the same node. An example script for this is available at ``examples/multiple_binaries/combine_executable.py``

Collecting FOMs
---------------
Most benchmarks within benchpark generate a figure of merit, which can be easily extracted to measure performance at a glance.
This can be done by running::

    ramble -P -D workspace/quicksilver/ruby-gcc/workspace workspace analyze
    ramble -P -D workspace/quicksilver/ruby-intel/workspace workspace analyze 

Collecting Data with Caliper
----------------------------
Enabling the Caliper modifier gives us a much more detailed picture about any performance differences, beyond looking at runtimes we can generate a profile to see which functions are contributing to a performance difference.

To read the caliper output, run ``cali-query -t {experiment_name}.cali``

To further analyze the caliper data, it is also possible to generate a call tree using Thicket

For more information on Caliper and Thicket, refer to https://software.llnl.gov/Caliper/ and https://thicket.readthedocs.io/en/latest/
