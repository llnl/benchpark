..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

#############################
 Adding a Ramble Application
#############################

**Glossary terms:** :ref:`Benchmark <beginner-tutorial-glossary-benchmark>`,
:ref:`Application <beginner-tutorial-glossary-application>`

A Ramble ``application.py`` defines a benchmark's inputs and runtime parameters. If an
application already exists in the `Ramble Applications repository
<https://github.com/Ramble-Project/ramble/tree/develop/var/ramble/repos/builtin/applications>`_,
Benchpark uses that definition. An application in
``repos/ramble_applications/<benchmark-name>/application.py`` overrides the corresponding
upstream application.

For the HPL example, create ``repos/ramble_applications/hpl/application.py`` with the
following complete contents:

.. literalinclude:: ../../repos/ramble_applications/hpl/application.py
    :language: python
    :linenos:

This ``application.py`` inherits Ramble's HPL definition and adds Benchpark catalogue
tags.

For a benchmark without an upstream application, follow the `Ramble Application
Definition Developers Tutorial
<https://ramble.readthedocs.io/en/latest/dev_guides/1_basic_application_definition_tutorial.html>`_.
Test the resulting ``application.py`` using the `Ramble Testing Application Definitions
instructions
<https://ramble.readthedocs.io/en/latest/dev_guides/1_basic_application_definition_tutorial.html#testing-application-definitions>`_.

Before adding the experiment, create its :doc:`Spack package <add-a-spack-package>` if
one is also missing.

**********
 Next Step
**********

.. tutorialcontainer:: tutorial-next-steps

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-experiment

        :doc:`My Spack package and Ramble application are defined. I want to add the
        experiment. <add-an-experiment>`
