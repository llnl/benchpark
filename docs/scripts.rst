.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

==================
Benchpark Scripts
==================

There are several scripts available in ``lib/scripts``.

Compare Spack Package Specifications
-----------------------------
``lib/scripts/diffSpecs.py``

This script enables the user to compare packages and versions of two spack builds.
Given two yaml package specs (use ``spack spec --yaml``), the script outputs which components of the packages are different.

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

.. note::
   If ``spack-python`` is not already in your environment, you can use the benchpark bootstrapped spack using ``. . ~/.benchpark/spack/share/spack/setup-env.sh``.
   This is helpful if you are running into the error ``bash: spack-python: command not found``. 

Compare System Configurations
-----------------------------
``lib/scripts/diffSystems.py``

This script enables the user to compare changes to a ``system.py`` between commits
by comparing ``.yaml`` files generated from ``system init ...``.
This script is helpful when it is unclear if changes made to ``system.py`` will affect the resulting system configuration.

In this example, we compare the ``llnl-sierra/system.py`` on the ``develop`` branch against the ``develop`` branch.
As we expect, the generated system configuraiton files are identical, since no changes were made to the system.py

.. code-block:: console

   $ benchpark-python diffSystems.py -n develop -s llnl-sierra

   llnl-sierra
        llnl-sierra/system_id.yaml
                The YAML files benchpark-old/llnl-sierra/system_id.yaml and benchpark-new/llnl-sierra/system_id.yaml are identical.
        llnl-sierra/software.yaml
                The YAML files benchpark-old/llnl-sierra/software.yaml and benchpark-new/llnl-sierra/software.yaml are identical.
        llnl-sierra/variables.yaml
                The YAML files benchpark-old/llnl-sierra/variables.yaml and benchpark-new/llnl-sierra/variables.yaml are identical.
        llnl-sierra/auxiliary_software_files/packages.yaml
                The YAML files benchpark-old/llnl-sierra/auxiliary_software_files/packages.yaml and benchpark-new/llnl-sierra/auxiliary_software_files/packages.yaml are identical.
        llnl-sierra/auxiliary_software_files/compilers.yaml
                The YAML files benchpark-old/llnl-sierra/auxiliary_software_files/compilers.yaml and benchpark-new/llnl-sierra/auxiliary_software_files/compilers.yaml are identical.

In another example, we have modified the ``cmake`` package version from ``3.29.2`` to ``3.23.1``. 

.. code-block:: python
   
   # llnl-sierra/system.py
   "cmake": {
      "externals": [
         {
               "spec": "cmake@3.23.1",
               "prefix": "/usr/tce/packages/cmake/cmake-3.23.1",
         }
      ],
      "buildable": False,
   },

The script will appropriately identify the change to the package version:

.. code-block:: console

   $ benchpark-python diffSystems.py -n changeCMakeBranch -s llnl-sierra

   llnl-sierra
        llnl-sierra/system_id.yaml
                The YAML files benchpark-old/llnl-sierra/system_id.yaml and benchpark-new/llnl-sierra/system_id.yaml are identical.
        llnl-sierra/software.yaml
                The YAML files benchpark-old/llnl-sierra/software.yaml and benchpark-new/llnl-sierra/software.yaml are identical.
        llnl-sierra/variables.yaml
                The YAML files benchpark-old/llnl-sierra/variables.yaml and benchpark-new/llnl-sierra/variables.yaml are identical.
        llnl-sierra/auxiliary_software_files/packages.yaml
                The YAML files benchpark-old/llnl-sierra/auxiliary_software_files/packages.yaml and benchpark-new/llnl-sierra/auxiliary_software_files/packages.yaml are different. Here are the differences:
                  {'values_changed': {"root['packages']['cmake']['externals'][0]['prefix']": {'new_value': '/usr/tce/packages/cmake/cmake-3.23.1',
                                                                                             'old_value': '/usr/tce/packages/cmake/cmake-3.29.2'},
                                    "root['packages']['cmake']['externals'][0]['spec']": {'new_value': 'cmake@3.23.1',
                                                                                          'old_value': 'cmake@3.29.2'}}}
        llnl-sierra/auxiliary_software_files/compilers.yaml
                The YAML files benchpark-old/llnl-sierra/auxiliary_software_files/compilers.yaml and benchpark-new/llnl-sierra/auxiliary_software_files/compilers.yaml are identical.

.. note::
   This script *does not* need to be ran on the target system to work correctly, e.g. the above example for ``llnl-sierra`` can be ran from your local machine.

Compare Experiment Builds
-------------------------
``lib/scripts/diffExperiments.py``

This script enables the user to compare the results of initializing an ``experiment.py``
from ``experiment init ...`` from two commits in benchpark.  experiment builts between two versions of benchpark (leverages ``diffSpecs.py``).

Question to Michael: why are you mentioning system.py here?  system.py and experiment.py get mapped by ``benchpark setup`` and not before.

TO DO: Directions on how to use the script. Provide an example including output.

For example, running on Ruby::

    benchpark-python diffExperiments.py -s llnl-cluster -c ruby -p openmp
