..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

############################################
 Explore Benchpark's Configuration Language
############################################

Benchpark uses *specs* to select a system or experiment definition and configure its
variants. You pass these specs to ``benchpark system init`` and ``benchpark experiment
init``. For example:

.. code-block:: console

    $ benchpark system init --dest=dane llnl-cluster cluster=dane compiler=gcc
    $ benchpark experiment init dane kripke +openmp +strong caliper=time,mpi

The first command selects the ``llnl-cluster`` system definition and sets its
``cluster`` and ``compiler`` variants. The second command selects the ``kripke``
experiment definition and configures its programming model, scaling mode, and Caliper
services.

A Benchpark spec describes a Benchpark object. It is distinct from the Spack package
specs that Benchpark later writes into the generated configuration. A system spec
selects a definition under ``systems/``, while an experiment spec selects a definition
under ``experiments/``.

****************************
 Inspect Available Variants
****************************

Each system and experiment defines its own variants, allowed values, and defaults.
Inspect them before constructing a spec:

.. code-block:: console

    $ benchpark info system --variants llnl-cluster
    $ benchpark info experiment --variants kripke

The ``benchpark info`` output includes variants inherited from reusable Benchpark
components, such as programming models and scaling modes. Benchpark applies default
values for omitted variants when it initializes the object. It rejects unknown variants,
unsupported values, and invalid combinations.

************************
 Write a Benchpark Spec
************************

Place the system or experiment name first, followed by zero or more variants:

.. list-table:: Benchpark spec forms
    :header-rows: 1
    :widths: 24 30 46

    - - Purpose
      - Form
      - Example
    - - Select an object
      - ``name``
      - ``kripke``
    - - Select a namespaced experiment
      - ``namespace.name``
      - ``hecbench.softmax``
    - - Enable a Boolean variant
      - ``+name``
      - ``+openmp``
    - - Disable a Boolean variant
      - ``~name``
      - ``~openmp``
    - - Select one value
      - ``name=value``
      - ``exec_mode=perf``
    - - Select multiple values
      - ``name=value1,value2``
      - ``caliper=time,mpi``

Boolean variants can follow the object name without a space, as in
``kripke+openmp+strong``. This form also prevents a shell from interpreting a disabled
variant such as ``~openmp`` as a home-directory expression:

.. code-block:: console

    $ benchpark experiment init dane kripke~openmp

For a multi-valued Benchpark variant, the comma-separated values are the selected
values. For example, ``caliper=time,mpi`` selects the ``time`` and ``mpi`` Caliper
services.

*****************************
 Relationship to Spack Specs
*****************************

Benchpark's parser is derived from Spack's spec parser and uses the same basic syntax
for `Boolean, single-valued, and multi-valued variants
<https://spack.readthedocs.io/en/latest/spec_syntax.html#variants>`_. The complete
`Spack spec syntax <https://spack.readthedocs.io/en/latest/spec_syntax.html>`_ is not a
Benchpark language reference because Benchpark implements only the object-name and
variant subset described on this page.

In particular, Benchpark does not implement Spack's version (``@``), compiler (``%``),
architecture, dependency (``^``), or installed-spec hash (``/hash``) constraint
semantics. It also does not accept exact multi-value constraints (``:=``) or variant
propagation (``++`` and ``==``).

These related forms have different meanings in the two tools:

.. list-table:: Benchpark and Spack differences
    :header-rows: 1
    :widths: 27 36 37

    - - Goal
      - Benchpark
      - Spack
    - - Select a version
      - Use a definition's variant, such as ``version=2025.12.0``.
      - Use a version constraint, such as ``@2025.12.0``.
    - - Select multiple values exactly
      - Use ``name=value1,value2``. Benchpark preserves the specified set.
      - Use ``name:=value1,value2``. In Spack, ``=`` permits additional values.

***********************
 Choose Your Next Step
***********************

Continue with the step that matches your goal:

- I want to run an experiment someone gave me, but on :doc:`my system that has different
  hardware/software <add-a-system-config>`.
- I want to run a :doc:`new benchmark <add-a-benchmark>` on the system I have benchmarked
  before (this also requires :doc:`adding an experiment <add-an-experiment>`).
