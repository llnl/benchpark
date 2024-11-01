.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

=========================
Legacy Benchpark Workflow
=========================

.. warning::
    This page provides legacy instructions for getting started with Benchpark.
    Certain steps (e.g., system and experiment specifications, file hierarchy) in
    this workflow will be deprecated in a future release.

------------------------------
Getting Started with Benchpark
------------------------------

Git is needed to clone Benchpark, and Python 3.8+ is needed to run Benchpark::

    git clone git@github.com:LLNL/benchpark.git
    cd benchpark

Once Benchpark is available on your system, its python dependencies can be
installed using the ``requirements.txt`` file included in the root directory of
Benchpark.

To install this, you can use::

    pip install -r requirements.txt

Now you are ready to look at the benchmarks and systems available in Benchpark,
as described in :ref:`legacy-benchpark-list`.

.. _legacy-benchpark-list:
-------------------
Searching Benchpark
-------------------

The user can search for available system and experiment specifications in Benchpark.

.. list-table:: Searching for specifications in Benchpark
   :widths: 25 25 50
   :header-rows: 1

   * - Command
     - Description
     - Listing in the docs
   * - benchpark list
     - Lists all benchmarks and systems specified in Benchpark
     -
   * - benchpark list systems
     - Lists all system specified in Benchpark
     - :doc:`system-list`
   * - benchmark list benchmarks
     - Lists all benchmarks specified in Benchpark
     -
   * - benchpark list systems
     - Lists all system specified in Benchpark
     - :doc:`system-list`
   * - benchpark tags workspace
     - Lists all tags specified in Benchpark
     -
   * - benchpark tags -a application workspace
     - Lists all tags specified for a given application in Benchpark
     -
   * - benchpark tags -t tag workspace
     - Lists all experiments in Benchpark with a given tag
     -


Once you have decided on a ``system`` you will use, and the ``benchmark/ProgrammingModel``
to run, you can proceed to :ref:`legacy-benchpark-setup`.

For a complete list of options, see the Benchpark help menu::

    $ benchpark --help

.. program-output:: ../bin/benchpark --help

---------------------------------
Editing the experiment (optional)
---------------------------------

Benchpark configuration files are organized as follows::

  $benchpark
  ├── legacy
  │  ├── systems
  │  │  ├── ${SYSTEM1}
  │  │  │  ├── auxiliary_software_files
  │  │  │  │  ├── compilers.yaml
  │  │  │  │  └── packages.yaml
  │  │  │  ├── software.yaml
  │  │  │  └── variables.yaml
  │  └── experiments
  │     ├── ${BENCHMARK1}
  │     │  ├── ${ProgrammingModel1}
  │     │  │  ├── execute_experiment.tpl
  │     │  │  └── ramble.yaml
  │     │  ├── ${ProgrammingModel1}
  │     │  │  ├── execute_experiment.tpl
  │     │  │  └── ramble.yaml
  └── repo
     ├── ${BENCHMARK1}
     │  ├── application.py
     │  └── package.py
     └── repo.yaml

You can edit these configuration files to change the behavior of your experiments.

System Specification
~~~~~~~~~~~~~~~~~~~~
Files under ``benchpark/legacy/systems/${SYSTEM}`` provide the specification
of the software stack on your system
(see :ref:`legacy-add-system` for details).

Benchmark Specification
~~~~~~~~~~~~~~~~~~~~~~~
If you would like to modify a specification of your benchmark,
you can do so by upstreaming changes to Spack and/or Ramble,
or working on your benchmark specification in ``benchpark/repo/${BENCHMARK}``
(see :ref:`legacy-add-benchmark` for details).

Experiment Specification
~~~~~~~~~~~~~~~~~~~~~~~~
Files under ``benchpark/experiments/${BENCHMARK}/${ProgrammingModel}``
provide the specifications for the experiments.
If you would like to make changes to your experiments,  such as enabling
specific tools to measure the performance of your experiments,
you can manually edit the specifications in ``ramble.yaml``
(see :ref:`legacy-add-experiment` for details).

Benchpark Modifiers
~~~~~~~~~~~~~~~~~~~
In Benchpark, a ``modifier`` follows the `Ramble Modifier
<https://googlecloudplatform.github.io/ramble/tutorials/10_using_modifiers.html#modifiers>`_
and is an abstract object that can be applied to a large set of reproducible
specifications. Modifiers are intended to encasulate reusable patterns that
perform a specific configuration of an experiment. This may include injecting
performance analysis or setting up system resources.

Requesting resources with Allocation Modifier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

To use the resource allocation modifier with your experiment,
add the following in your ramble.yaml::

  ramble:
    include:
      - ...
      - ./configs/modifier.yaml
    config:
      ...
    modifiers:
    - name: allocation
    applications:
      ...
    software:
      ...
    environments:
      - ...
      - '{modifier_package_name}'


Profiling with Caliper Modifier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
We have implemented a Caliper modifier to enable profiling of Caliper-instrumented
benchmarks in Benchpark. More documentation on Caliper can be found `here
<https://software.llnl.gov/Caliper>`_.

To turn on profiling with Caliper, add ``--modifier=<caliper_modifier>`` to the Benchpark
setup step::

    ./benchpark setup <Benchmark/ProgrammingModel> <System> --modifier=<caliper_modifier> <workspace-dir>

Valid values for ``<caliper_modifier>`` are found in the **Caliper Modifier**
column of the table below.  Benchpark will link the experiment to Caliper,
and inject appropriate Caliper configuration at runtime.  After the experiments
in the workspace have completed running, a ``.cali`` file
is created which contains the collected performance metrics.

.. list-table:: Available caliper modifiers
   :widths: 20 20 50
   :header-rows: 1

   * - Caliper Modifier
     - Where Applicable
     - Metrics Collected
   * - caliper
     - Platform-independent
     - | - Min/Max/Avg time/rank: Minimum/Maximum/Average time (in seconds) across all ranks
       | - Total time: Aggregated time (in seconds) for all ranks
   * - caliper-mpi
     - Platform-independent
     - | - Same as basic caliper modifier above
       | - Profiles MPI functions
   * - caliper-topdown
     - x86 Intel CPUs
     - | - Retiring
       | - Bad speculation
       | - Front end bound
       | - Back end bound
   * - caliper-cuda
     - NVIDIA GPUs
     - | - CUDA API functions (e.g., time.gpu)

.. _legacy-benchpark-setup:
--------------------
Setting up Benchpark
--------------------

Select a benchmark experiment to run, along with the programming model to use, and a system to run them on.
Also choose a directory for your experiment::

    benchpark setup <Benchmark/ProgrammingModel> <System> </output/path/to/experiments_root>

where:

- ``<Benchmark/ProgrammingModel>``: amg2023/openmp | amg2023/cuda | saxpy/openmp (available choices in ``benchpark/experiments``)
- ``<System>``: use ``benchpark system init``, or a predefined system in :doc:`system-list`)

This command will assemble a Ramble workspace per experiment
with a configuration for the specified benchmark and system
with the following directory structure::

    experiments_root/
        ramble/
        spack/
        <Benchmark/ProgrammingModel>/
            <System>/
                workspace/
                    configs/
                        (everything from system_def_dir)
                        (everything from experiment_def_dir)

``benchpark setup`` will output instructions to follow::

   . <experiments_root>/setup.sh

The ``setup.sh`` script calls the Spack and Ramble setup scripts.  It optionally accepts
parameters to ``ramble workspace setup`` as `documented in Ramble
<https://googlecloudplatform.github.io/ramble/workspace.html#setting-up-a-workspace>`_,
including ``--dry-run`` and ``--phases make_experiments``.

Now you are ready to compile your experiments as described in :ref:`legacy-build-experiment`.

.. _legacy-build-experiment:
-----------------------
Building the experiment
-----------------------

``benchpark setup`` has set up the directory structure for your experiment.
The next step is setting up the Ramble workspace and building the code::

   cd <experiments_root>/<Benchmark/ProgrammingModel>/<System>/workspace
   ramble --disable-progress-bar --workspace-dir . workspace setup


Ramble will build the source code and set up the following workspace directory structure::

    experiments_root/
        ramble/
        spack/
        <Benchmark/ProgrammingModel>/
            <System>/
                workspace/
                    configs/
                        (everything from system_def_dir)
                        (everything from experiment_def_dir>)
                    experiments/
                        <Benchmark>/
                           <Problem>/
                              <Benchmark>_<ProgrammingModel>_<Problem>
                                    execute_experiment

If you edit any of the files, see :doc:`FAQ-what-to-rerun` to determine
whether you need to re-do any of the previous steps.

----------------------------------
Running an Experiment in Benchpark
----------------------------------

To run all of the experiments in the workspace::

   ramble --disable-progress-bar --workspace-dir . on

An output file is generated for each experiment in its unique directory::

  $workspace
  | └── experiments
  |    └── amg2023
  |        └── problem1
  |            ├── amg2023_cuda11.8.0_problem1_1_8_2_2_2_10_10_10
  |            │   ├── execute_experiment
  |            │   ├── amg2023_cuda11.8.0_problem1_1_8_2_2_2_10_10_10.out
  |            │   └── ...
  |            ├── amg2023_cuda11.8.0_problem1_2_4_2_2_2_10_10_10
  |            │   ├── execute_experiment
  |            │   ├── amg2023_cuda11.8.0_problem1_2_4_2_2_2_10_10_10.out
  |            │   └── ...
  |            ├── amg2023_cuda11.8.0_problem1_1_8_2_2_2_20_20_20
  |            │   ├── execute_experiment
  |            │   ├── amg2023_cuda11.8.0_problem1_1_8_2_2_2_20_20_20.out
  |            │   └── ...
  |            └── amg2023_cuda11.8.0_problem1_2_4_2_2_2_20_20_20
  |                ├── execute_experiment
  |                ├── amg2023_cuda11.8.0_problem1_2_4_2_2_2_20_20_20.out
  |                └── ...

An experiment instance can also be executed individually by directly invoking its ``execute_experiment`` script 
(e.g., ``$workspace/experiments/amg2023/problem1/amg2023_cuda11.8.0_problem1_1_8_2_2_2_10_10_10/execute_experiment``).

Note that re-running the experiment may overwrite any existing output files in the directory.
Further, if the benchmark has restart capability, existing output may alter the experiments
benchpark would run in the second run.  Generally, we would advise the user to remove the
``$workspace/experiments`` directory before re-running the experiments using
``ramble --disable-progress-bar --workspace-dir . on``.

----------------------------------
Analyzing Experiments in Benchpark
----------------------------------

Once the experiments completed running, the command::

  ramble --disable-progress-bar --workspace-dir . workspace analyze 

can be used to analyze figures of merit and evaluate 
`success/failure <https://googlecloudplatform.github.io/ramble/success_criteria.html>`_ 
of the experiments. Ramble generates a file with summary of the results in ``$workspace``.
