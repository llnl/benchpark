..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

.. _search-benchpark:

#######################################
 Search What Is Available in Benchpark
#######################################

**Glossary terms:** :ref:`Benchmark <beginner-tutorial-glossary-benchmark>`,
:ref:`Variant <beginner-tutorial-glossary-variant>`, :ref:`Experiment
<beginner-tutorial-glossary-experiment>`, :ref:`System
<beginner-tutorial-glossary-system>`, :ref:`Modifier
<beginner-tutorial-glossary-modifier>`

All of the systems, benchmarks, experiments, and modifiers that are available in
Benchpark can be searched on the command line. The ``benchpark list`` command accepts
one of four categories:

.. code-block:: console

    $ benchpark list systems
    $ benchpark list benchmarks
    $ benchpark list experiments
    $ benchpark list modifiers

The Benchpark Catalogue shows detailed information on :doc:`Benchpark Systems
</system-list>` and :doc:`Benchpark Experiments </benchmark-list>` in tabular form.

Use the filter to find experiments with your targeted programming model or specific type
of scaling. For example, this command will display only the CUDA experiments:

.. code-block:: console

    $ benchpark list experiments --experiment cuda

We can also search for systems:

.. code-block:: console

    $ benchpark list systems

After choosing a system or experiment, inspect its variants and configuration details:

.. code-block:: console

    $ benchpark info system aws-tutorial
    $ benchpark info experiment hpl

For a complete command reference, see :doc:`Benchpark Commands </benchpark-commands>`.

**********************
 Return to Start Here
**********************

.. tutorialcontainer:: tutorial-next-steps

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-start

        :doc:`I want to return to the start page. <start-here>`
