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

Caliper services can also be enabled independently of the main ``caliper`` mode by
adding ``caliper_services=<service>`` to the experiment spec:

::

    benchpark experiment init --dest=</path/to/experiment_root> </path/to/system> <benchmark> caliper_services=<service>

Available services are:

- ``nvtx`` for CUDA systems
- ``rocprofiler`` for ROCm systems

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

***************************
 GitHash: Version Metadata
***************************

The ``githash`` modifier records version metadata for the Benchpark repository, the
pinned Benchpark dependencies, and the application package plus any dependencies.

The ``githash`` modifier is enabled by default (``githash=on``). You can specify
``githash=none`` to disable usage.

::

    benchpark experiment init --dest=</path/to/experiment_root> </path/to/system> <benchmark> caliper=<caliper_variant> githash=on

The ``githash`` modifier writes this information to ``githash_metadata.json`` in the
experiment directory.

If also running with the ``caliper`` modifier, Benchpark adds ``githash_metadata.json``
to the Caliper metadata.

*************************************
 Compiler Memtrace: HIP Memory Access
*************************************

The ``compiler_memtrace`` modifier uses `memtrace-llvm
<https://github.com/llnl/benchpark-llvm>`_ to catalog and trace memory operations
in HIP kernels. Enable it on a ROCm experiment:

.. code-block:: console

    benchpark experiment init --dest=raja-memtrace /path/to/system \
        raja-perf+rocm compiler_memtrace=trace n_resources=1 process_problem_size=1024

The modifier requires ``package_manager=spack``, one ``amdgpu_target``, and a
Clang compiler with LLVM 19 or newer development files. The benchmark and
``memtrace-llvm`` must use the same C++ compiler and HIP installation. The
package builds against that compiler's LLVM, and installs the pass, HIP runtime,
device headers, Python reader, and ``memtrace`` command. Version ``0.1.0`` is
pinned to commit ``e229827a58479ba87a1efd0b1255a8ad6eb911d5`` from PR #8.

Setup checks that the Python reader imports before building the benchmark.
Count and trace runs repeat this check before launching. The NumPy dependency
uses Benchpark's NumPy recipe, which disables Meson's ``b_asneeded`` option
for MKL builds to retain its interface, threading, and core libraries with lld.
For existing environments, setup uses Spack's concrete-spec update API to select
the corrected NumPy recipe and replace the affected dependency
builds while preserving unrelated package selections.

The modes are:

- ``none`` (default): disable this modifier.
- ``baseline``: build with the pass and write static catalogs without device
  instrumentation.
- ``count``: build and run a count executable.
- ``trace``: build count and trace executables, run count first, then run trace
  with the same command-line arguments and the recorded counts.

Setup creates separate Spack environments and installation prefixes for the
instrumented builds. Compiler flags identify the mode and tracing options in
the Spack spec. Dependencies are installed without the tracing environment;
only the benchmark root is instrumented. Catalogs and ``builds.json`` are under
``{env_path}/compiler-memtrace/<configuration>/``. The latter records executable
prefixes, reader paths, and collection options. Count and trace must use the
same sources and inputs. Applications that modify input files during execution
must restore those inputs between runs or use separate experiment workflows.

For CMake packages, setup adds MemTrace compile and link options to targets
in the staged benchmark source tree. CMake's compiler checks run without these
options, including the host-only HIP check that cannot link device definitions.
The package install preserves the prepared stage with ``--dont-restage``.
Setup requires a catalog containing benchmark memory operations for the selected
mode and GPU target; compiler-probe catalogs do not satisfy this check.

Each execution creates a fresh directory beneath the experiment run directory:

.. code-block:: text

    compiler_memtrace.run.<unique suffix>/
        count/rank-0/
        trace/rank-0/

Each rank writes its own manifest, catalogs, and binary files. Count and trace
use separate MPI launches. Rank identification supports Flux, PMI, PMIx,
Open MPI, and Slurm. A multi-rank run fails if its rank cannot be identified.
The output filesystem must be visible to every rank.

Collection fails if no launches are recorded, a catalog or data file is missing,
the trace is invalid, or the count and trace launch sets differ. Successful
validation writes ``validated.json`` in each rank directory. Count output goes
to ``compiler_memtrace.<executable>.count.out``; trace output uses the
application's normal log. To inspect one rank's output with the package loaded:

.. code-block:: console

    memtrace summary /path/to/trace/rank-0
    memtrace check /path/to/trace/rank-0
    memtrace csv /path/to/trace/rank-0 accesses.csv

These Ramble variables can be supplied through ``experiment init`` or in the
generated YAML:

.. list-table:: Compiler memtrace variables
    :header-rows: 1
    :widths: 35 15 50

    - - Variable
      - Default
      - Meaning
    - - ``compiler_memtrace_executables``
      - ``run``
      - Space-separated executable name patterns. Change this for applications
        whose benchmark executable has a different Ramble name.
    - - ``compiler_memtrace_addrspaces``
      - ``1:0``
      - Colon-separated AMDGPU address spaces. Add ``3`` for LDS.
    - - ``compiler_memtrace_prevectorize``
      - ``0``
      - Set to ``1`` to merge adjacent accesses before instrumentation.
        LLVM 20 or newer also supplies the ``amdgpu_noclobber`` annotation.
    - - ``compiler_memtrace_waves_per_eu``
      - empty
      - Path to an occupancy file containing a mangled kernel name and waves per
        execution unit on each line. Use occupancy from an uninstrumented build.
    - - ``compiler_memtrace_timing``
      - ``0``
      - Set to ``1`` in trace mode to collect clocks and placement on gfx94x or
        gfx95x. Enables both the compile-time define and runtime option.

Selected Ramble executables must each contain one direct benchmark command.
Shell pipelines, compound commands, and launcher wrappers inside that command
are unsupported; use Ramble's ``mpi_command`` for the launcher. The executable
must reside in the benchmark package prefix or its Spack view. Use separate
experiments for ``compiler_attribution`` and ``compiler_memtrace``.

The upstream runtime traces ``hipLaunchKernel`` outside stream capture. Other
launch APIs, device functions that remain uninlined, and device memory intrinsics
are outside its trace coverage. One launch's trace must fit in GPU memory, at
528 bytes per wave record, plus optional timing data. Use small workloads when
establishing a collection configuration. Instrumented launches are serialized;
their execution times are unsuitable for baseline performance comparisons.
