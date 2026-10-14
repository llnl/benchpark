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

Install the analysis dependencies once from the Benchpark repository:

.. code-block:: console

    $ pip install .[analyze]

Analyze the completed HPL scaling study from :doc:`build-and-run-experiment`:

.. code-block:: console

    $ benchpark analyze --workspace-dir workspace/aws-tutorial/hpl/workspace

****************
 Strong Scaling
****************

The default stacked area chart shows the exclusive average time per rank for each
instrumented region. The x-axis records the node and MPI-rank counts varied in the
strong-scaling study.

.. code-block:: console

    $ benchpark analyze --workspace-dir wkp/kripke/cuda/strong/lassen/workspace/

.. figure:: /_static/images/kripke_cuda_strong_raw_exc.png
    :width: 800
    :align: center

    Strong-scaling area chart.

**************
 Weak Scaling
**************

The weak-scaling chart shows the exclusive average time per rank as the problem size
and allocated resources increase together. A constant total time indicates ideal
weak-scaling behavior.

.. code-block:: console

    $ benchpark analyze --workspace-dir wkp/kripke/cuda/weak/lassen/workspace/

.. figure:: /_static/images/kripke_cuda_weak_raw_exc.png
    :width: 800
    :align: center

    Weak-scaling area chart.

************
 Throughput
************

The throughput chart uses the same stacked-region view for a throughput scaling study.
It shows how region timing changes across the study's node and MPI-rank configurations.

.. code-block:: console

    $ benchpark analyze --workspace-dir wkp/kripke/cuda/throughput/lassen/workspace/

.. figure:: /_static/images/kripke_cuda_throughput_raw_exc.png
    :width: 800
    :align: center

    Throughput-scaling area chart.

************
 Percentage
************

The percentage chart expresses each region's metric relative to the sum for all
regions. This makes each region's share of total time easier to compare.

.. code-block:: console

    $ benchpark analyze --workspace-dir wkp/kripke/cuda/strong/lassen/workspace/ --chart-type percentage

.. figure:: /_static/images/kripke_cuda_strong_percentage_exc.png
    :width: 800
    :align: center

    Strong-scaling data shown as a percentage of total time.

*******************
 Inclusive Metrics
*******************

The inclusive chart uses ``Avg time/rank`` instead of ``Avg time/rank (exc)``. It
removes the ``main`` region because its value would redundantly contain all child-region
time.

.. code-block:: console

    $ benchpark analyze --workspace-dir wkp/kripke/cuda/strong/lassen/workspace/ --yaxis-metric "Avg time/rank"

.. figure:: /_static/images/kripke_cuda_strong_raw_inc.png
    :width: 800
    :align: center

    Strong-scaling data using an inclusive metric.

******************
 Region Filtering
******************

This figure combines regions that have the same name, then retains the regions with the
highest metric values. The filtered view emphasizes the regions that contribute most
to the measured time.

.. code-block:: console

    $ benchpark analyze --workspace-dir wkp/kripke/cuda/strong/lassen/workspace/ --group-regions-name --top-n-regions 10

.. figure:: /_static/images/kripke_cuda_strong_raw_exc-2.png
    :width: 800
    :align: center

    Strong-scaling data after filtering regions.

*****************************
 Visualize a Metadata Column
*****************************

``benchpark analyze`` can visualize a metadata column instead of a performance-data
column. This is useful for figures of merit that have one value per profile.

.. code-block:: console

    $ benchpark analyze --workspace-dir problem1/ --yaxis-metric Final-FOM --chart-kind line --disable-legend

.. figure:: /_static/images/amg2023_rocm_weak_raw_exc.png
    :width: 800
    :align: center

    Metadata values shown as a line chart.

For additional chart types and filtering options, see :doc:`/benchpark-analyze`.

***********************
 Choose Your Next Step
***********************

.. container:: tutorial-next-steps

    .. container:: tutorial-next-step tutorial-goal-search

        :ref:`I have generated preconfigured performance figures for an experiment on
        my system. I want to begin another workflow by searching what is available in
        Benchpark. <search-benchpark>`
