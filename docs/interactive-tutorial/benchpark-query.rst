..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

########################
 Query Performance Data
########################

**Glossary terms:** :ref:`Benchmark <beginner-tutorial-glossary-benchmark>`,
:ref:`Application <beginner-tutorial-glossary-application>`, :ref:`Experiment
<beginner-tutorial-glossary-experiment>`, :ref:`System
<beginner-tutorial-glossary-system>`, :ref:`Modifier
<beginner-tutorial-glossary-modifier>`

Query the average time for the ``main`` region in the completed HPL workspace:

.. code-block:: console

    $ benchpark query workspace/aws-tutorial/hpl/workspace \
        --metric "Avg time/rank" \
        --query-regions-byname main

The original plotting example uses Matplotlib to create a stacked bar chart from the
queried data:

.. code-block:: python

    import matplotlib.pyplot as plt

    amg_df = bar_df[bar_df["application_name"] == "amg2023"].set_index(
        ["cluster", version_col]
    )

    ax = amg_df[["Computation", "Communication"]].plot.bar(stacked=True)
    ax.set_xlabel("System and ROCm version")
    ax.set_ylabel("Average time per rank (seconds)")
    plt.tight_layout()
    plt.show()

.. note::

    The following figure contains extra styling that is not provided in the simplified
    code snippet above.

.. figure:: /_static/images/query-stacked-barchart-amg2023.png
    :width: 700
    :align: center

    Example visualization created from queried performance data.

For additional metrics, region selection, and CSV options, see :doc:`/benchpark-query`.

***********************
 Choose Your Next Step
***********************

.. container:: tutorial-next-steps

    .. container:: tutorial-next-step tutorial-goal-search

        :ref:`I have generated raw performance data to make my own figures. I want to
        begin another workflow by searching what is available in Benchpark.
        <search-benchpark>`
