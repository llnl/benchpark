.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

=====================
Benchpark Modifiers
=====================
In Benchpark, a ``modifier`` follows the `Ramble Modifier
<https://ramble.readthedocs.io/en/latest/tutorials/10_using_modifiers.html>`_
and is an abstract object that can be applied to a large set of reproducible
specifications. Modifiers are intended to encapsulate reusable patterns that
perform a specific configuration of an experiment. This may include injecting
performance analysis or setting up system resources.

Requesting Resources with the Allocation Modifier
---------------------------------------------------
Given:

  - an experiment that requests resources (nodes, cpus, gpus, etc.), and
  - a specification of the resources available on the system (cores_per_node, gpus_per_node, etc.),

the ``Allocation Modifier`` generates the appropriate scheduler request for these resources
(how many nodes are required to run a given experiment, etc.).


.. list-table:: Hardware resources as specified by the system, and requested for the experiment
   :widths: 20 40 40
   :header-rows: 1

   * - Resource
     - Available on the System
     - Requested for the Experiment
   * - Total Nodes
     - (opt) sys_nodes
     - n_nodes
   * - Total MPI Ranks
     -
     - n_ranks
   * - CPU cores per node
     - sys_cores_per_node
     - (opt) n_cores_per_node
   * - GPUs per node
     - sys_gpus_per_node
     - (opt) n_gpus_per_node
   * - Memory per node
     - sys_mem_per_node
     - (opt) n_mem_per_node


The experiment is required to specify:

  - n_ranks it requires
  - n_gpus (if using GPUs)

If the experiment does not specify ``n_nodes``, the modifier will compute
the number of nodes to allocate to provide the ``n_ranks`` and/or ``n_gpus``
required for the experiment.

The system is required to specify:

  - sys_cores_per_node
  - sys_gpus_per_node (if it has GPUs)
  - sys_mem_per_node

The modifier checks the resources requested by the experiment,
computes the values for the unspecified variables, and
checks that the request does not exceed the resources available on the system.

The resource allocation modifier is used by default in your experiment. However, 
it will only calculate values if you have not specified them yourself. 

If you do not specify values, it will assign the default values as listed below.

.. list-table:: Default Values For the Allocation Modifier
   :widths: 20 80
   :header-rows: 1

   * - Variable
     - Default Value
   * - n_nodes
     - (n_ranks / sys_cores_per_node) OR (n_gpus / sys_gpus_per_node) whichever is greater
   * - n_ranks
     - (n_nodes * n_ranks_per_node) OR (n_gpus)
   * - n_gpus
     - 0 
   * - n_threads_per_proc
     - 1 


Profiling with Caliper Modifier
-------------------------------
We have implemented a Caliper modifier to enable profiling of Caliper-instrumented
benchmarks in Benchpark. More documentation on Caliper can be found `here
<https://software.llnl.gov/Caliper>`_.

To turn on profiling with Caliper, add ``caliper=<caliper_variant>`` to the experiment init
setup step::

    benchpark experiment init --dest=</path/to/experiment_root> <benchmark> caliper=<caliper_variant>

Valid values for ``<caliper_variant>`` are found in the **Caliper Variant**
column of the table below.  Benchpark will link the experiment to Caliper,
and inject appropriate Caliper configuration at runtime.  After the experiments
in the workspace have completed running, a ``.cali`` file
is created which contains the collected performance metrics.

.. list-table:: Available caliper variants
   :widths: 20 20 50
   :header-rows: 1

   * - Caliper Variant
     - Where Applicable
     - Metrics Collected
   * - time
     - Platform-independent
     - | - Min/Max/Avg time/rank: Minimum/Maximum/Average time (in seconds) across all ranks
       | - Total time: Aggregated time (in seconds) for all ranks
   * - mpi
     - Platform-independent
     - | - Same as basic caliper modifier above
       | - Profiles MPI functions
   * - cuda
     - NVIDIA GPUs
     - | - CUDA API functions (e.g., time.gpu)
   * - topdown-counters-all
     - x86 Intel CPUs
     - | - Raw counter values for Intel top-down analysis (all levels)
   * - topdown-counters-toplevel
     - x86 Intel CPUs
     - | - Raw counter values for Intel top-down analysis (top level)
   * - topdown-all
     - x86 Intel CPUs
     - | - Top-down analysis for Intel CPUs (all levels)
   * - topdown-toplevel
     - x86 Intel CPUs
     - | - Top-down analysis for Intel CPUs (top level)
   

An experiment must inherit from the Caliper experiment class to make use of 
the Caliper functionality. Most existing experiments should already do this, but if 
adding to a new experiment, it is as simple as adding it to the class definition signature.
For example::
  
  class Amg2023(Experiment, Caliper):

