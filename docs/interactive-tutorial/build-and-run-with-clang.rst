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

.. admonition:: Earlier GCC run (optional)

    In :doc:`Build and Run an Experiment <build-and-run-experiment>`, we initialized the
    default GCC system and HPL experiment with the commands below. That earlier run is
    optional for this page. Here, you will use similar commands to create a separate
    Clang system and HPL experiment.

    The AWS tutorial system was initialized with:

    .. code-block:: console

        benchpark]$ benchpark system init --dest=hpc-tutorial fluxtainer-aws

    .. figure:: /_static/images/fluxtainer-aws-system-spec.png
        :alt: Tutorial system spec
        :width: 90%
        :align: center

    The HPL experiment was initialized with:

    .. code-block:: console

        benchpark]$ benchpark experiment init hpc-tutorial hpl +strong caliper=time,mpi

    .. figure:: /_static/images/fluxtainer-aws-experiment-spec.png
        :alt: Tutorial experiment spec
        :width: 71%
        :align: center

In this example, we show how to replicate an experiment, that is to run the same
application on a different software stack (for example, a system with the same hardware
specs, but software stack is managed by a different organization). We think of a
different software stack as one containing different compiler or library versions,
though the underlying hardware remains the same. Replicating an experiment can also
encompass re-running on the same system (System1) with changes to the software stack,
such as a newer library version. In this case, the application’s performance is expected
to be similar, but not necessarily as close as with a repeat run.

.. figure:: /_static/images/benchpark-replicate-table.png
    :alt: Benchpark replicate specification
    :width: 50%
    :align: center

This use case follows the same workflow as :doc:`build-and-run-experiment`, but changes
the tutorial system's compiler from its default ``gcc`` stack to ``clang``.

**************************
 What Changes in This Run
**************************

The default ``fluxtainer-aws`` compiler is ``gcc``. To build the same HPL experiment
with Clang, initialize a second system instance and select the ``compiler=clang``
variant:

.. code-block:: console

    benchpark]$ benchpark system init --dest=hpc-tutorial-clang fluxtainer-aws compiler=clang

.. figure:: /_static/images/fluxtainer-aws-system-spec-clang.png
    :alt: Tutorial system spec using clang
    :width: 90%
    :align: center

Here ``compiler=clang`` is a Benchpark system variant provided by ``fluxtainer-aws``.

*******************
 Build and Run HPL
*******************

Initialize the HPL experiment against the Clang system instance:

.. code-block:: console

    benchpark]$ benchpark experiment init hpc-tutorial-clang hpl +strong caliper=time,mpi

.. figure:: /_static/images/fluxtainer-aws-experiment-spec-clang.png
    :alt: Tutorial experiment spec using clang
    :width: 68%
    :align: center

Create the experiment workspace:

.. code-block:: console

    benchpark]$ benchpark setup hpc-tutorial-clang/hpl wkp

Activate Benchpark's Spack and Ramble environments:

.. code-block:: console

    benchpark]$ . wkp/setup.sh

Set up the Ramble workspace to build HPL and generate each experiment instance:

.. code-block:: console

    benchpark]$ ramble --workspace-dir wkp/hpc-tutorial-clang/hpl/workspace workspace setup

Then, run the experiments:

.. code-block:: console

    benchpark]$ ramble --workspace-dir wkp/hpc-tutorial-clang/hpl/workspace on

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

    benchpark]$ benchpark analyze --workspace-dir wkp/hpc-tutorial-clang/hpl/workspace

.. figure:: /_static/images/hpl_strong_gcc_clang_compare.png
    :width: 90%
    :align: center

    Left figures show the benchpark system specification and strong-scaling area chart
    for HPL built with gcc in tutorial #4. Right figures show the benchpark system
    specification and strong-scaling area chart for HPL built with clang.

***********************
 Choose Your Next Step
***********************

.. tutorialcontainer:: tutorial-next-steps

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-search

        :ref:`I have run an experiment someone gave me on the same system. I want to
        start another workflow by searching what is available in Benchpark.
        <search-benchpark>`

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-run

        :doc:`I want to return to the default GCC build and run workflow.
        <build-and-run-experiment>`

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-troubleshoot

        :doc:`My experiment did not finish, and I want to diagnose where it failed.
        <troubleshoot-a-failed-run>`
