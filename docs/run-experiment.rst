..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

###################
 Run an Experiment
###################

To run all of the experiments in the workspace:

::

    ramble --workspace-dir . on

An output file is generated for each experiment in its unique directory:

::

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

An experiment instance can also be executed individually by directly invoking its
``execute_experiment`` script (e.g.,
``$workspace/experiments/amg2023/problem1/amg2023_cuda11.8.0_problem1_1_8_2_2_2_10_10_10/execute_experiment``).

Note that re-running the experiment may overwrite any existing output files in the
directory. Further, if the benchmark has restart capability, existing output may alter
the experiments benchpark would run in the second run. Generally, we would advise the
user to remove the ``$workspace/experiments`` directory before re-running the
experiments using ``ramble --workspace-dir . on``.

Running Different Experiments in the Same Allocation
====================================================

The ``benchpark aggregate`` command provides the functionality to batch experiments from
the same workspace or multiple workspaces together. To use ``benchpark aggregate``,
provide a destination for the job script, and the workspaces as positional arguments:

::

    $ benchpark aggregate --dest agg/ workspace1/ workspace2/ ...

Then, submit the newly created job script to the scheduler:

::
    $ flux batch agg/0.sh

Output from the experiments will still be written to the respective experiment
directory.

Once you have run your experiment you can try :doc:`analyze-experiment`.
