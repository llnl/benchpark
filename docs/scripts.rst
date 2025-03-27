.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

==================
Benchpark Scripts
==================

There are several scripts available in ``lib/scripts``.

Differentiate Two Spack Specs
-----------------------------
``lib/scripts/diffSpecs.py``

This script enables the user to compare packages and versions of two spack builds.

TO DO: Directions on how to use the script. Provide an example including output

This script takes two yaml package specs (use ``spack spec --yaml``) and outputs which components of the packages are different.
In this example, we see the difference of ``dray`` built with and without ``mpi``.
The difference between the specs ``dray+mpi`` and ``dray~mpi`` is indicated in the output by ``-> [openmpi]`` and the console output highlights the package differences in red.

.. code-block:: console

   $ spack spec --yaml dray+mpi > dray-mpi.yaml
   $ spack spec --yaml dray~mpi > dray-nompi.yaml
   $ spack-python lib/scripts/diffSpecs.py ./dray-mpi.yaml ./dray-nompi.yaml

   dray@0.1.8%apple-clang@=16.0.0+blt_find_mpi build_system=generic~cuda~logging+mpi+openmp+shared~stats+test+utils arch=darwin-macos-m1
   -> [openmpi]
      apcomp@0.0.4%apple-clang@=16.0.0+blt_find_mpi build_system=generic+mpi+openmp+shared arch=darwin-macos-m1
      -> [openmpi]
         llvm-openmp@18.1.0%apple-clang@=16.0.0 build_system=cmake build_type=Release generator=make~ipo+multicompat arch=darwin-macos-m1
   ...

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
from ``experiment init ...`` from two commits in benchpark.  experiment builts between two versions of benchpark (leverages ``diffSpecs.py``).

Question to Michael: why are you mentioning system.py here?  system.py and experiment.py get mapped by ``benchpark setup`` and not before.

TO DO: Directions on how to use the script. Provide an example including output.

For example, running on Ruby::

    benchpark-python diffExperiments.py -s llnl-cluster -c ruby -p openmp
