..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

####################
 Adding a Benchmark
####################

This guide is intended for application developers who want to add a benchmark so that it
can be run with Benchpark.

************************
 Create a New Benchmark
************************

The following system-independent specification is required for each ${Benchmark1}:

- ``package.py`` is a Spack specification that defines how to build and install
  ${Benchmark1}. See the `Spack Package Creation Tutorial
  <https://spack-tutorial.readthedocs.io/en/latest/tutorial_packaging.html>`_ to learn
  how to create and test a Spack ``package.py``. If your benchmark already exists in
  Spack, benchpark will use that version of the ``package.py``, unless you define a
  version in ``benchpark/repo/``.
- ``application.py`` is a Ramble specification that defines the ${Benchmark1} input and
  parameters. See the `Ramble Application Definition Developers Guide
  <https://ramble.readthedocs.io/en/latest/dev_guides/application_dev_guide.html>`_ to
  learn how to create a Ramble ``application.py``. We recommend testing your
  ``application.py`` using the `Ramble Usage While Developing
  <https://ramble.readthedocs.io/en/latest/dev_guides/application_dev_guide.html#usage-while-developing>`_
  instructions. If your benchmark already exists in Ramble, benchpark will use that
  version of the ``application.py``, unless you define a version in ``benchpark/repo/``.

Again, by default Benchpark will use ${Benchmark1} specifications (``application.py``
and ``package.py``) provided in the Spack and Ramble upstream repositories. Overwrite
the upstream definitions by adding the ``application.py`` and/or ``package.py`` to
``benchpark/repo/${Benchmark1}``, see :doc:`FAQ` for details.

After satisfying the above prerequisites, in order to use your benchmark in Benchpark,
you will need to create an experiment as described in :doc:`add-an-experiment`.
