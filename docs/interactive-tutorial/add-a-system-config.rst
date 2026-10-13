..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

#################
 Adding a System
#################

**Glossary terms:** :ref:`Package <beginner-tutorial-glossary-package>`, :ref:`Spec
<beginner-tutorial-glossary-spec>`, :ref:`Variant
<beginner-tutorial-glossary-variant>`, :ref:`System
<beginner-tutorial-glossary-system>`

This example defines the ``aws-tutorial`` system used throughout the Beginner Tutorial.
Create ``systems/aws-tutorial/system.py`` with the following complete definition:

.. literalinclude:: ../../systems/aws-tutorial/system.py
    :language: python
    :linenos:

*******************************
 Critical Benchpark Components
*******************************

- ``System`` is the base class for a Benchpark system definition.
- ``variant()`` exposes the AWS instance type in the Benchpark system spec.
- ``id_to_resources`` maps each instance type to its processor and memory resources.
- ``programming_models``, ``scheduler``, and ``hardware_key`` describe how Benchpark
  runs experiments on the system.
- ``compute_packages_section()`` declares software already installed on the system.
- ``compute_compilers_section()`` defines the compiler available to Spack.
- ``compute_software_section()`` selects the compiler used by Ramble applications.

Initialize the system to validate the definition:

.. code-block:: console

    $ benchpark system init --dest=aws-tutorial aws-tutorial

For the complete system authoring reference, see :doc:`/add-a-system-config`.

***********
 Next Step
***********

.. container:: tutorial-next-steps

    .. container:: tutorial-next-step tutorial-goal-run

        :doc:`I want to initialize, build, and run an experiment on this new system.
        <build-and-run-experiment>`
