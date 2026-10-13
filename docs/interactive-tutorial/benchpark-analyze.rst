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

.. figure:: /_static/images/kripke_cuda_strong_raw_exc.png
    :width: 800
    :align: center

    Strong-scaling area chart.

**************
 Weak Scaling
**************

.. figure:: /_static/images/kripke_cuda_weak_raw_exc.png
    :width: 800
    :align: center

    Weak-scaling area chart.

************
 Throughput
************

.. figure:: /_static/images/kripke_cuda_throughput_raw_exc.png
    :width: 800
    :align: center

    Throughput-scaling area chart.

************
 Percentage
************

.. figure:: /_static/images/kripke_cuda_strong_percentage_exc.png
    :width: 800
    :align: center

    Strong-scaling data shown as a percentage of total time.

*******************
 Inclusive Metrics
*******************

.. figure:: /_static/images/kripke_cuda_strong_raw_inc.png
    :width: 800
    :align: center

    Strong-scaling data using an inclusive metric.

******************
 Region Filtering
******************

.. figure:: /_static/images/kripke_cuda_strong_raw_exc-2.png
    :width: 800
    :align: center

    Strong-scaling data after filtering regions.

*****************************
 Visualize a Metadata Column
*****************************

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
