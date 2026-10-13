..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

######################
 Adding an Experiment
######################

**Glossary terms:** :ref:`Benchmark <beginner-tutorial-glossary-benchmark>`, :ref:`Package
<beginner-tutorial-glossary-package>`, :ref:`Application
<beginner-tutorial-glossary-application>`, :ref:`Spec
<beginner-tutorial-glossary-spec>`, :ref:`Variant
<beginner-tutorial-glossary-variant>`, :ref:`Experiment
<beginner-tutorial-glossary-experiment>`, :ref:`System
<beginner-tutorial-glossary-system>`, :ref:`Modifier
<beginner-tutorial-glossary-modifier>`, :ref:`Scaling Study
<beginner-tutorial-glossary-scaling-study>`

This example defines the HPL experiment used throughout the Beginner Tutorial. Create
``experiments/hpl/experiment.py`` with the following complete definition:

.. literalinclude:: ../../experiments/hpl/experiment.py
    :language: python
    :linenos:

*******************************
 Critical Benchpark Components
*******************************

- ``Experiment`` is the base class for a Benchpark experiment definition.
- ``ProgrammingModel`` declares the programming models supported by HPL.
- ``Caliper`` adds performance measurement variants and Ramble modifiers.
- ``Scaling`` declares the supported strong and weak scaling modes.
- ``variant()`` exposes the HPL workload and version in the experiment spec.
- ``compute_applications_section()`` sets the variables used to generate Ramble
  experiment instances.
- ``set_required_variables()`` records resource and problem-size metadata.
- ``compute_package_section()`` selects the HPL package spec built by Spack.

.. _step-3b-define-scaling-options:

Scaling Configuration
=====================

``register_scaling_config()`` identifies the variables that change during a scaling
study. Strong scaling increases ``n_nodes`` while keeping ``Ns`` constant. Weak scaling
increases both values.

Initialize the experiment with the AWS tutorial system to validate the definition:

.. code-block:: console

    $ benchpark experiment init --dest=hpl aws-tutorial hpl

For the complete experiment authoring reference, see :doc:`/add-an-experiment`.

***********
 Next Step
***********

.. container:: tutorial-next-steps

    .. container:: tutorial-next-step tutorial-goal-run

        :doc:`I want to build and run the new experiment on my existing system.
        <build-and-run-experiment>`
