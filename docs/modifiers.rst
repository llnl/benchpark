..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

#####################
 Benchpark Modifiers
#####################

In Benchpark, a ``modifier`` follows the `Ramble Modifier
<https://ramble.readthedocs.io/en/latest/tutorials/10_using_modifiers.html>`_ and is an
abstract object that can be applied to a large set of reproducible specifications.
Modifiers are intended to encapsulate reusable patterns that perform a specific
configuration of an experiment. This may include injecting performance analysis or
setting up system resources.

*************************
 Affinity: Threads, GPUs
*************************

We are using (with permission) the following implementation of `Linux thread and GPU
affinity checks <https://github.com/bcumming/affinity>`_. The following checks are
possible:

- ``affinity.mpi`` : for testing thread affinity of each rank in an MPI job
- ``affinity.rocm`` : for testing AMD GPU affinity of each rank an MPI job
- ``affinity.cuda`` : for testing NVIDIA GPU affinity of each rank in an MPI job

To use the Affinity modifier:

- When you initialize your experiment, add ``affinity=on`` to ``experiment init``.
- A small, separate run will execute in your allocation to record the information.
- The Affinity modifier will output a text file in the experiment directory which will
  look like this for ``benchpark experiment init --dest=saxpy system-name saxpy+openmp
  affinity=on`` on 8 ranks, 2 threads/proc, 1 node:

.. code-block:: console

    affinity.mpi.out

    affinity test for 8 MPI ranks
    rank      0 @ dane1514
      thread   0 on cores [112]
      thread   1 on cores [119]
    rank      1 @ dane1514
      thread   0 on cores [126]
      thread   1 on cores [133]
    rank      2 @ dane1514
      thread   0 on cores [140]
      thread   1 on cores [147]
    rank      3 @ dane1514
      thread   0 on cores [154]
      thread   1 on cores [161]
    rank      4 @ dane1514
      thread   0 on cores [168]
      thread   1 on cores [175]
    rank      5 @ dane1514
      thread   0 on cores [182]
      thread   1 on cores [189]
    rank      6 @ dane1514
      thread   0 on cores [196]
      thread   1 on cores [203]
    rank      7 @ dane1514
      thread   0 on cores [210]
      thread   1 on cores [217]

If also running with the ``caliper`` modifier, ``affinity`` information will be included
in the Caliper metadata.

********************
 Caliper: Profiling
********************

`Caliper <https://github.com/LLNL/Caliper/>`_ is an instrumentation and performance
profiling library. We have implemented a Caliper modifier to enable profiling of
Caliper-instrumented benchmarks in Benchpark.

To turn on profiling with Caliper, add ``caliper=<caliper_variant>`` to the experiment
init setup step:

::

    benchpark experiment init --dest=</path/to/experiment_root> </path/to/system> <benchmark> caliper=<caliper_variant>

Valid values for ``<caliper_variant>`` are found in the **Caliper Variant** column of
the table below. Benchpark will link the experiment to Caliper, and inject appropriate
Caliper configuration at runtime. After the experiments in the workspace have completed
running, a ``.cali`` file is created which contains the collected performance metrics.

.. list-table:: Available caliper variants
    :widths: 20 20 50
    :header-rows: 1

    - - Caliper Variant
      - Where Applicable
      - Metrics Collected
    - - time
      - Platform-independent
      - |   - Min/Max/Avg time/rank: Minimum/Maximum/Average time (in seconds) across
            all ranks
        |   - Total time: Aggregated time (in seconds) for all ranks
    - - mpi
      - Platform-independent
      - |   - Same as basic caliper modifier above
        |   - Profiles MPI functions
    - - cuda
      - NVIDIA GPUs
      - |   - CUDA API functions
        |   - GPU time
    - - rocm
      - AMD GPUs
      - |   - HIP API functions
        |   - GPU time
    - - topdown-counters-all
      - x86 Intel CPUs
      - |   - Raw counter values for Intel top-down analysis (all levels)
    - - topdown-counters-toplevel
      - x86 Intel CPUs
      - |   - Raw counter values for Intel top-down analysis (top level)
    - - topdown-all
      - x86 Intel CPUs
      - |   - Top-down analysis for Intel CPUs (all levels)
    - - topdown-toplevel
      - x86 Intel CPUs
      - |   - Top-down analysis for Intel CPUs (top level)

An experiment must inherit from the Caliper experiment class to make use of the Caliper
functionality. Most existing experiments should already do this, but if adding to a new
experiment, it is as simple as adding it to the class definition signature. For example:

::

    class Amg2023(Experiment, Caliper):

***********************
 Allocation: Resources
***********************

Given:

    - an experiment that requests resources (nodes, cpus, gpus, etc.), and
    - a specification of the resources available on the system (cores_per_node,
      gpus_per_node, etc.),

the ``Allocation Modifier`` generates the appropriate scheduler request for these
resources (how many nodes are required to run a given experiment, etc.).

.. list-table:: Hardware resources as specified by the system, and requested for the experiment
    :widths: 20 40 40
    :header-rows: 1

    - - Resource
      - Available on the System
      - Requested for the Experiment
    - - Total Nodes
      - (opt) sys_nodes
      - n_nodes
    - - Total MPI Ranks
      -
      - n_ranks
    - - CPU cores per node
      - sys_cores_per_node
      - (opt) n_cores_per_node
    - - GPUs per node
      - sys_gpus_per_node
      - (opt) n_gpus_per_node
    - - Memory per node
      - sys_mem_per_node_GB
      - (opt) n_mem_per_node

The experiment is required to specify:

    - n_ranks it requires
    - n_gpus (if using GPUs)

If the experiment does not specify ``n_nodes``, the modifier will compute the number of
nodes to allocate to provide the ``n_ranks`` and/or ``n_gpus`` required for the
experiment.

The system is required to specify:

    - sys_cores_per_node
    - sys_gpus_per_node (if it has GPUs)
    - sys_mem_per_node_GB

The modifier checks the resources requested by the experiment, computes the values for
the unspecified variables, and checks that the request does not exceed the resources
available on the system.

The resource allocation modifier is used by default in your experiment. However, it will
only calculate values if you have not specified them yourself.

If you do not specify values, it will assign the default values as listed below.

.. list-table:: Default Values For the Allocation Modifier
    :widths: 20 80
    :header-rows: 1

    - - Variable
      - Default Value
    - - n_nodes
      - (n_ranks / sys_cores_per_node) OR (n_gpus / sys_gpus_per_node) whichever is
        greater
    - - n_ranks
      - (n_nodes * n_ranks_per_node) OR (n_gpus)
    - - n_gpus
      - 0
    - - n_threads_per_proc
      - 1

*********************
 Hwloc: Hardware Map
*********************

The hwloc modifier enables using `hwloc <https://github.com/open-mpi/hwloc>`_ in
Benchpark to record the hierarchical map of key computing elements on the given system,
such as: NUMA memory nodes, shared caches, processor sockets, processor cores, and
processor threads.

To use the hwloc modifier, add ``hwloc=on`` to the experiment init setup step. This
modifier is disabled by default (``hwloc=none``).:

::

    benchpark experiment init --dest=</path/to/experiment_root> </path/to/system> <benchmark> caliper=<caliper_variant> hwloc=on

The hwloc modifier will output the hardware information in a flattened JSON file in the
experiment directory.

If also running with the ``caliper`` modifier, ``hwloc`` information will be included in
the Caliper metadata.
