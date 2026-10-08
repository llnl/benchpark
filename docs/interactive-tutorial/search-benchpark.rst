..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

#########################################
 Search What Is Available in Benchpark
#########################################

Start by finding the system, benchmark, experiment, and modifiers that match your
goal. The ``benchpark list`` command accepts one of four categories:

.. code-block:: console

    $ benchpark list systems
    $ benchpark list benchmarks
    $ benchpark list experiments
    $ benchpark list modifiers

The generated :doc:`system catalogue </system-list>` and :doc:`benchmark catalogue
</benchmark-list>` provide the same system and experiment information in the
documentation.

Use experiment filters to find experiments that support one or more programming
models. For example, this command finds experiments that support OpenMP or ROCm:

.. code-block:: console

    $ benchpark list experiments --experiment openmp rocm

After choosing a system or experiment, inspect its variants and other configuration
details:

.. code-block:: console

    $ benchpark info system <system>
    $ benchpark info experiment <experiment>

Run the command help to see all supported filters and arguments:

.. code-block:: console

    $ benchpark list --help
    $ benchpark info --help

For a complete command reference, see :doc:`Benchpark Commands
</benchpark-commands>`.

***********
 Next Step
***********

After selecting a system and experiment, :doc:`set up a workspace
<setup-workspace>`.
