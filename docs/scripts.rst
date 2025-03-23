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

This script enables the user to compare packages and versions of two builds.

TO DO: Directions on how to use the script. Provide an example including output.


Compare System Configurations
-----------------------------
``lib/scripts/diffSystems.py``

This script enables the user to compare the result of initializing a ``system.py``
by comparing ``.yaml`` files generated from ``system init ...`` from two commits in benchpark.

TO DO: Directions on how to use the script. Provide an example including output.


Compare Experiment Builds
-------------------------
``lib/scripts/diffExperiments.py``

This script enables the user to compare the results of initializing an ``experiment.py``
from ``experiment init ...`` from two commits in benchpark.  experiment builts between two versions of benchpark (leverages ``altdiff.py``).

Question to Michael: why are you mentioning system.py here?  system.py and experiment.py get mapped by ``benchpark setup`` and not before.

TO DO: Directions on how to use the script. Provide an example including output.

For example, running on Ruby::

    benchpark-python diffExperiments.py -s llnl-cluster -c ruby -p openmp
