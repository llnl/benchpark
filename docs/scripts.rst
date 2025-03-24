.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

==================
Benchpark Scripts
==================

There are several scripts available in ``lib/scripts``.

Differentiate Two Spack Specs
-----------------------------
``lib/scripts/altdiff.py``

Diff spack specs (packages and versions). 
This is helpful to compare if changes made in benchpark result in a different Spack concretization.

.. literalinclude:: ../lib/scripts/altdiff.py
   :language: python


Compare System Configurations
-----------------------------
``lib/scripts/diffSystems.py``

Compare ``.yaml`` files between two different commits of benchpark, generated from ``system init ...``.
This is helpful to compare how changes made in ``system.py`` change the resulting system configuration.

.. literalinclude:: ../lib/scripts/diffSystems.py
   :language: python


Compare Experiment Builds
-------------------------
``lib/scripts/diffExperiments.py``

Compare experiment builts between two versions of benchpark (leverages ``altdiff.py``).
This is helpful to compare changes to either ``experiment.py`` or ``system.py``, as changes to either may result in a different experiment build.
This requires the user to specify which ``system`` and ``cluster`` they are running on. For example, running on Ruby::

    benchpark-python diffExperiments.py -s llnl-cluster -c ruby -p openmp

.. literalinclude:: ../lib/scripts/diffExperiments.py
   :language: python