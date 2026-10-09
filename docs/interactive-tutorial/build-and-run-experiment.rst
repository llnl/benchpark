..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

#############################
 Build and Run an Experiment
#############################

This page continues from :doc:`workspace setup <setup-workspace>`. The generated
``setup.sh`` script activates Benchpark's Spack and Ramble environments and sets up each
Ramble workspace:

.. code-block:: console

    $ . <experiments-root>/setup.sh

You can also set up a Ramble workspace directly. Change to the workspace directory
created by ``benchpark setup`` and run:

.. code-block:: console

    $ cd <experiments-root>/<system>/<benchmark>/<programming-model>/workspace
    $ ramble --workspace-dir . workspace setup

Ramble builds the benchmark and creates an ``execute_experiment`` script for each
experiment instance. The resulting structure resembles:

.. code-block:: text

    workspace/
    |-- configs/
    `-- experiments/
        `-- <benchmark>/
            `-- <workload>/
                `-- <experiment-instance>/
                    `-- execute_experiment

Run every experiment instance in the workspace:

.. code-block:: console

    $ ramble --workspace-dir . on

Each experiment directory receives its own output files. To run one instance instead,
invoke its generated script directly:

.. code-block:: console

    $ ./experiments/<benchmark>/<workload>/<experiment-instance>/execute_experiment

Re-running an experiment can overwrite its output. A benchmark with restart support can
also use files left by the previous run, which changes the subsequent execution. Use a
new workspace when you need to preserve results or guarantee a clean run.

.. _run-multiple-workspaces-one-allocation:

*******************************************
 Run Multiple Workspaces in One Allocation
*******************************************

Use ``benchpark aggregate`` to combine experiments from one or more workspaces into
submission scripts:

.. code-block:: console

    $ benchpark aggregate --dest <output-directory> <workspace> [<workspace> ...]

Submit the generated script with the scheduler for your system. For example, a Flux
system can use:

.. code-block:: console

    $ flux batch <output-directory>/0.sh

The experiment output remains in each source workspace.

Choose Your Next Step
=====================

- If your goal was to repeat an experiment on a system, the workflow is complete. To
  start another workflow, :doc:`search what is available in Benchpark
  <search-benchpark>`.
- If your goal is to analyze the performance results, :doc:`use benchpark analyze
  <benchpark-analyze>`.
- To perform custom analysis or export Caliper data, use :doc:`benchpark query
  <benchpark-query>`.
