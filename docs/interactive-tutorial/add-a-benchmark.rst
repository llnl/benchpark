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

Each benchmark requires two system-independent definitions:

- ``package.py`` is a Spack specification that defines how to build and install
  the benchmark. See the `Spack Package Creation Tutorial
  <https://spack-tutorial.readthedocs.io/en/latest/tutorial_packaging.html>`_ to learn
  how to create and test a Spack ``package.py``. If your benchmark already exists in
  Spack, Benchpark will use that ``package.py`` unless you provide a Benchpark-specific
  definition.
- ``application.py`` is a Ramble specification that defines the benchmark input and
  parameters. See the `Ramble Application Definition Developers Tutorial
  <https://ramble.readthedocs.io/en/latest/dev_guides/1_basic_application_definition_tutorial.html>`_
  to learn how to create a Ramble ``application.py``. We recommend testing your
  ``application.py`` using the `Ramble Testing Application Definitions
  <https://ramble.readthedocs.io/en/latest/dev_guides/1_basic_application_definition_tutorial.html#testing-application-definitions>`_
  instructions. If your benchmark already exists in Ramble, Benchpark will use that
  ``application.py`` unless you provide a Benchpark-specific definition.

By default, Benchpark uses definitions provided by the upstream Spack and Ramble
repositories. Override an upstream definition by adding a package to
``repos/spack_repo/benchpark/packages/<benchmark-name>/package.py`` or an application to
``repos/ramble_applications/<benchmark-name>/application.py``. See :doc:`/FAQ` for
details.

After satisfying the above prerequisites, create an experiment for the new benchmark.

***********
 Next Step
***********

I want to run this new benchmark on my existing system, so I need to :doc:`add an
experiment <add-an-experiment>`.
