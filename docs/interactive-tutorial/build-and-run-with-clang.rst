..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

##########################
 Build and Run with Clang
##########################

**Glossary terms:** :ref:`Benchmark <beginner-tutorial-glossary-benchmark>`,
:ref:`Experiment <beginner-tutorial-glossary-experiment>`, :ref:`System
<beginner-tutorial-glossary-system>`

.. figure:: /_static/images/benchpark-replicate-table.png
    :alt: Benchpark replicate specification
    :width: 50%
    :align: center

.. tutorialcontainer:: tutorial-prerequisite-links

    .. tutorialcontainer:: tutorial-prerequisite-link tutorial-prerequisite-experiment

        :doc:`Prerequisite: Build and Run an Experiment <build-and-run-experiment>`

This use case follows the same workflow as :doc:`build-and-run-experiment`, but changes
the tutorial system's compiler from its default ``gcc`` stack to ``clang``.

**************************
 What Changes in This Run
**************************

The default ``fluxtainer-aws`` compiler is ``gcc``. To build the same HPL experiment
with Clang, initialize a second system instance and select the ``compiler=clang``
variant:

.. code-block:: console

    ~/benchpark]$ benchpark system init --dest=hpc-tutorial-clang fluxtainer-aws compiler=clang

Here ``compiler=clang`` is a Benchpark system variant provided by ``fluxtainer-aws``. It
is not a Spack ``%clang`` constraint.

*******************
 Build and Run HPL
*******************

Initialize the HPL experiment against the Clang system instance:

.. code-block:: console

    ~/benchpark]$ benchpark experiment init hpc-tutorial-clang hpl +strong caliper=time,mpi

Create the experiment workspace:

.. code-block:: console

    ~/benchpark]$ benchpark setup hpc-tutorial-clang/hpl wkp

Activate Benchpark's Spack and Ramble environments:

.. code-block:: console

    ~/benchpark]$ . wkp/setup.sh

Set up the Ramble workspace to build HPL and generate each experiment instance:

.. code-block:: console

    ~/benchpark]$ ramble --workspace-dir wkp/hpc-tutorial-clang/hpl/workspace workspace setup

Then, run the experiments:

.. code-block:: console

    ~/benchpark]$ ramble --workspace-dir wkp/hpc-tutorial-clang/hpl/workspace on

The generated workspace is separate from the default GCC run because the system instance
is named ``hpc-tutorial-clang``. That keeps the Clang build, run scripts, and results
side by side with the original ``hpc-tutorial`` workspace.

************************
 Analyze Strong Scaling
************************

The default stacked area chart shows the exclusive average time per rank for each
instrumented region. The x-axis records the node and MPI-rank counts varied in the
strong-scaling study.

.. code-block:: console

    ~/benchpark]$ benchpark analyze --workspace-dir wkp/hpl-tutorial-clang/hpl/workspace

.. figure:: /_static/images/hpl_mpi_strong_raw_exc_clang.png
    :width: 800
    :align: center

    Strong-scaling area chart.

We can also use `benchpark query
<https://software.llnl.gov/benchpark/benchpark-query.html>`_ to search one or more
directories for particular metadata or performance data in the Caliper .cali files. The
data of interest is written to a CSV file. Here, we query our HPL+clang workspace and
our HPL+gcc workspace for the execution time of the ``main`` region. The resulting query
generates the execution time at each rank count.

.. figure:: /_static/images/benchpark-query-clang.png
    :width: 800
    :align: center

    Performance of HPL built with clang compiler at different rank counts.

.. figure:: /_static/images/benchpark-query-gcc.png
    :width: 800
    :align: center

    Performance of HPL built with gcc compiler at different rank counts.

***********************
 Choose Your Next Step
***********************

.. tutorialcontainer:: tutorial-next-steps

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-run

        :doc:`I want to return to the default GCC build and run workflow.
        <build-and-run-experiment>`

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-analyze

        :doc:`I want to analyze the performance of this experiment by generating
        preconfigured performance figures. <benchpark-analyze>`
