..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

#######################################
 Search What Is Available in Benchpark
#######################################

All of the systems, benchmarks, experiments, and modifiers that are available in
benchpark can be searched on the command line. The ``benchpark list`` command accepts
one of four categories:

.. code-block:: console

    $ benchpark list systems
    $ benchpark list benchmarks
    $ benchpark list experiments
    $ benchpark list modifiers

The generated :doc:`system catalogue </system-list>` and :doc:`benchmark catalogue
</benchmark-list>` provide detailed information for systems and benchmarks in a tabular
form.

For searching experiments, use the filter to find your targeted programming model. For
example, this command only shows experiments that support ROCm:

.. code-block:: console

    $ benchpark list experiments --experiment rocm

The same search can be performed for ROCm systems:

.. code-block:: console

    $ benchpark list systems --programming-model rocm

After choosing a system or experiment, inspect its variants and other configuration
details:

.. code-block:: console

    $ benchpark info system <system>
    $ benchpark info experiment <experiment>

Run the command help to see all supported filters and arguments:

.. code-block:: console

    $ benchpark list --help
    $ benchpark info --help

For a complete command reference, see :doc:`Benchpark Commands </benchpark-commands>`.

***********
 Next Step
***********

After selecting a system and experiment, :doc:`set up a workspace <setup-workspace>`.
