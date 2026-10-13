..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

####################
 Adding a Benchmark
####################

**Glossary terms:** :ref:`Benchmark <beginner-tutorial-glossary-benchmark>`, :ref:`Package
<beginner-tutorial-glossary-package>`, :ref:`Application
<beginner-tutorial-glossary-application>`

This guide is intended for application developers who want to add a benchmark so that it
can be run with Benchpark.

************************
 Create a New Benchmark
************************

HPL requires a Spack package definition and a Ramble application definition.

Spack Package
=============

Create the package at
``repos/spack_repo/benchpark/packages/hpl/package.py`` with the following complete
contents:

.. literalinclude:: ../../repos/spack_repo/benchpark/packages/hpl/package.py
    :language: python
    :linenos:

The package defines how Spack downloads, configures, builds, and installs HPL.

Ramble Application
==================

Create the application at ``repos/ramble_applications/hpl/application.py`` with the
following complete contents:

.. literalinclude:: ../../repos/ramble_applications/hpl/application.py
    :language: python
    :linenos:

The application inherits Ramble's HPL definition and adds Benchpark catalogue tags.

For benchmarks that do not already exist upstream, see the `Spack Package Creation
Tutorial <https://spack-tutorial.readthedocs.io/en/latest/tutorial_packaging.html>`_ and
the `Ramble Application Definition Developers Tutorial
<https://ramble.readthedocs.io/en/latest/dev_guides/1_basic_application_definition_tutorial.html>`_.

***********
 Next Step
***********

.. container:: tutorial-next-steps

    .. container:: tutorial-next-step tutorial-goal-experiment

        :doc:`I want to run this new benchmark on my existing system, so I need to add
        an experiment. <add-an-experiment>`
