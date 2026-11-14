..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

#########################
 Analyze a Scaling Study
#########################

**Glossary terms:** :ref:`Benchmark <beginner-tutorial-glossary-benchmark>`,
:ref:`Experiment <beginner-tutorial-glossary-experiment>`, :ref:`System
<beginner-tutorial-glossary-system>`, :ref:`Modifier
<beginner-tutorial-glossary-modifier>`, :ref:`Scaling Study
<beginner-tutorial-glossary-scaling-study>`

.. tutorialcontainer:: tutorial-prerequisite-links

    .. tutorialcontainer:: tutorial-prerequisite-link tutorial-prerequisite-experiment

        :doc:`Prerequisite: Build and Run an Experiment <build-and-run-experiment>`

        :doc:`Prerequisite: Troubleshoot a Failed Experiment <troubleshoot-a-failed-run>`

.. admonition:: Previously completed

    Before starting this page, you should have completed either :doc:`Build and Run an
    Experiment <build-and-run-experiment>` or :doc:`Troubleshoot a Failed Experiment Run
    <troubleshoot-a-failed-run>` and have a completed HPL scaling study. These standard
    initialization commands from the build and run workflow are reminders.

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

Install the analysis dependencies once from the Benchpark repository (this has already
been installed in the container for the hands-on tutorials):

.. code-block:: console

    $ pip install .[analyze]

Analyze the completed HPL scaling study.

First, move back to the Benchpark root directory to continue with the remaining steps:

.. code-block:: console

    benchpark]$ cd benchpark

The completed run from :doc:`step #2 <build-and-run-experiment>` or the repaired run
from :doc:`step #3 <troubleshoot-a-failed-run>` should have produced one Caliper profile
(``.cali`` file) for each scaling configuration. Check that the profiles exist:

.. code-block:: console

    $ find wkp/hpc-tutorial/hpl/workspace/ -name "*.cali"
    wkp/hpc-tutorial/hpl/workspace/experiments/hpl/standard/hpl_standard_test_mpi_caliper_time_mpi_strong_scaling_1_1000_1/261114-000638_8848_p2kDeiLLZOoJ.cali
    wkp/hpc-tutorial/hpl/workspace/experiments/hpl/standard/hpl_standard_test_mpi_caliper_time_mpi_strong_scaling_2_1000_2/261114-000639_8968_JG2xp1S9kIFI.cali
    wkp/hpc-tutorial/hpl/workspace/experiments/hpl/standard/hpl_standard_test_mpi_caliper_time_mpi_strong_scaling_4_1000_4/261114-000640_9089_STBbU0buU6H6.cali
    wkp/hpc-tutorial/hpl/workspace/experiments/hpl/standard/hpl_standard_test_mpi_caliper_time_mpi_strong_scaling_8_1000_8/261114-000642_9225_AP4K3qYsdBsu.cali

The profile filenames contain run-specific identifiers, so your output will differ.

****************
 Strong Scaling
****************

The default stacked area chart shows the exclusive average time per rank for each
instrumented region. The x-axis records the node and MPI-rank counts varied in the
strong-scaling study. Within each profile, ``Calls/rank (max)`` is the largest call
count among its ranks. For each region, the legend shows the largest of these values
across all profiles, so the profile supplying the legend value can differ by region.

.. code-block:: console

    benchpark]$ benchpark analyze --workspace-dir wkp/hpc-tutorial/hpl/workspace

.. figure:: /_static/images/hpl_mpi_strong_raw_exc.png
    :width: 800
    :align: center

    Strong-scaling area chart.

************
 Percentage
************

The percentage chart expresses each region's metric relative to the sum for all regions.
This makes each region's share of total time easier to compare.

.. code-block:: console

    benchpark]$ benchpark analyze --workspace-dir wkp/hpc-tutorial/hpl/workspace --chart-type percentage

.. figure:: /_static/images/hpl_mpi_strong_percentage_exc.png
    :width: 800
    :align: center

    Strong-scaling data shown as a percentage of total time.

*******************
 Inclusive Metrics
*******************

The inclusive chart uses ``Avg time/rank`` instead of ``Avg time/rank (exc)``.

.. code-block:: console

    benchpark]$ benchpark analyze --workspace-dir wkp/hpc-tutorial/hpl/workspace --yaxis-metric "Avg time/rank"

.. figure:: /_static/images/hpl_mpi_strong_raw.png
    :width: 800
    :align: center

    Strong-scaling data using an inclusive metric.

******************
 Region Filtering
******************

This figure combines regions that have the same name, then retains the regions with the
highest metric values. The filtered view emphasizes the regions that contribute most to
the measured time. The sum of the metric for all removed regions is also shown, so you
can see if you removed too many regions.

.. code-block:: console

    benchpark]$ benchpark analyze --workspace-dir wkp/hpc-tutorial/hpl/workspace --group-regions-name --top-n-regions 10

.. figure:: /_static/images/hpl_mpi_strong_raw_exc_region.png
    :width: 800
    :align: center

    Strong-scaling data after filtering regions.

For additional chart types and filtering options, see :doc:`/benchpark-analyze`.

***********************
 Choose Your Next Step
***********************

.. tutorialcontainer:: tutorial-next-steps

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-search

        :ref:`I have generated preconfigured performance figures for an experiment on
        my system. I want to begin another workflow by searching what is available in
        Benchpark. <search-benchpark>`
