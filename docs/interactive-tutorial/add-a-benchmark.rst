..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

##################################
 Prereqs for adding an Experiment
##################################

**Glossary terms:** :ref:`Benchmark <beginner-tutorial-glossary-benchmark>`,
:ref:`Package <beginner-tutorial-glossary-package>`, :ref:`Application
<beginner-tutorial-glossary-application>`

Each experiment in Benchmark must have a Spack ``package.py`` for building,
and a Ramble ``application.py`` for run instructions.  This guide demonstrates
how to write them using HPL as an example.   


Spack Package
=============

``package.py`` is a Spack specification that defines how to download, build, and install the benchmark. 
If a Spack package already exists in the `Spack Packages repo <https://packages.spack.io>`_,
Benchpark will use that ``package.py``.  If a ``package.py`` exists in 
``benchpark/repos/spack_repo/benchpark/packages/BenchmarkName``, it will override the
one in the Spack Packages repo.

For our HPL example, create a file named ``package.py`` in ``repos/spack_repo/benchpark/packages/hpl/``
with the following complete contents:

.. literalinclude:: ../../repos/spack_repo/benchpark/packages/hpl/package.py
    :language: python
    :linenos:

For benchmarks that do not already have a Spack ``package.py`` in the `Spack Packages repo
<https://packages.spack.io>`_, see the `Spack Package Creation Tutorial
<https://spack-tutorial.readthedocs.io/en/latest/tutorial_packaging.html>`_ 
to learn how to create and test a Spack ``package.py``. 


Ramble Application
==================

``application.py`` is a Ramble specification that defines the benchmark input and parameters. 
If a Ramble application already exists in the `Ramble Applications repo
<https://github.com/Ramble-Project/ramble/tree/develop/var/ramble/repos/builtin/applications>`_,
Benchpark will use that ``application.py``.  If a ``application.py`` exists in
``benchpark/repos/ramble_applications``, it will override the one in the Ramble Applications repo.

For our HPL example, create a file named ``application.py`` in ``repos/ramble_applications/hpl/``
with the following complete contents:

.. literalinclude:: ../../repos/ramble_applications/hpl/application.py
    :language: python
    :linenos:

This ``application.py`` inherits Ramble's HPL definition and adds Benchpark catalogue tags.

For benchmarks that do not already have an ``application.py`` in the `Ramble Applications repo
<https://github.com/Ramble-Project/ramble/tree/develop/var/ramble/repos/builtin/applications>`_,
see the `Ramble Application Definition Developers Tutorial
<https://ramble.readthedocs.io/en/latest/dev_guides/1_basic_application_definition_tutorial.html>`_.
We recommend testing your ``application.py`` using the `Ramble Testing Application Definitions
<https://ramble.readthedocs.io/en/latest/dev_guides/1_basic_application_definition_tutorial.html#testing-application-definitions>`_
instructions.

***********
 Next Step
***********

.. tutorialcontainer:: tutorial-next-steps

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-experiment

        :doc:`I want to run a new benchmark on my existing system <add-an-experiment>`
