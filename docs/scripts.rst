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

.. note::
   If you are trying to compare benchpark benchmarks, try using ``diffExperimentBuilds.py``.

Example: dray with/without MPI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
by comparing ``.yaml`` files generated from ``benchpark system init ...``.
This script is helpful when it is unclear if changes made to ``system.py`` will affect the resulting system configuration.

Stages that occur during this script:
   - ``benchpark system init``

Example: Identical System
~~~~~~~~~~~~~~~~~~~~~~~~~

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

Example: Different CMake Version 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Compare Experiment Configurations
---------------------------------
``lib/scripts/diffExperiments.py``

This script enables the user to compare changes to a ``experiment.py`` between commits
by comparing ``.yaml`` files generated from ``benchpark experiment init ...``.
This script is helpful when it is unclear if changes made to ``experiment.py`` will affect the resulting experiment configuration.

Stages that occur during this script:
   - ``benchpark experiment init``

Example: Change n_ranks in Saxpy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example, we modify the ``saxpy+openmp`` experiment to see how the script identifies the differences.
On the branch ``myBranch``, we change ``self.add_experiment_variable("n_ranks", "8")`` to ``self.add_experiment_variable("n_ranks", "4")``. 

.. code-block:: console

   $ benchpark-python diffExperiments.py -n myBranch -e saxpy+openmp

   saxpy+openmp
         saxpy/openmp/ramble.yaml
                  The YAML files benchpark-old/saxpy/openmp/ramble.yaml and benchpark-new/saxpy/openmp/ramble.yaml are different. Here are the differences:
                     {'values_changed': {"root['ramble']['applications']['saxpy']['workloads']['problem']['experiments']['saxpy_problem_single_node_openmp_caliper_none_{n_nodes}_{n_threads_per_proc}_{n}']['variables']['n_ranks']": {'new_value': 4,
                                                                                                                                                                                                                                       'old_value': 8}}}

Compare Experiment Builds
-------------------------
``lib/scripts/diffExperimentBuilds.py``

This script builds the benchmarks that are available for the specified ``programmming-model`` on the target cluster
and compares the differences (leveraging ``diffSpecs.py``) for two different versions of benchpark. 

Stages that occur during this script:
   - ``benchpark experiment init``
   - ``benchpark system init``
   - ``benchpark setup``
   - ``ramble workspace setup``
   - ``ramble on`` (optional) 

.. note::
   This script *must* be ran on the target system and cluster to work correctly.

Example: amg2023~mpi
~~~~~~~~~~~~~~~~~~~~

For example, we can compare the builds for different benchpark branches of ``amg2023`` on the ``ruby`` cluster.
``myBranch`` is a branch of benchpark where we have configured ``~mpi``.

.. code-block:: console

   $ benchpark-python diffExperimentBuilds.py -s llnl-cluster -c ruby -p openmp -b amg2023 --commit-hash2 myBranch

   # Develop build
   ==> Streaming details to log:
   ==>   /usr/WS1/mckinsey/benchpark/lib/scripts/benchpark-develop-openmp/wkp/benchpark-develop-openmp/amg2023/benchpark-develop-openmp/ruby/workspace/logs/setup.2025-03-27_13.19.33.out
   ==>   Setting up 1 out of 1 experiments:
   ==> Experiment #1 (1/1):
   ==>     name: amg2023.problem1.amg2023_problem1_single_node_openmp_caliper_none_2_2_2_80_80_80_8_1
   ==>     root experiment_index: 1
   ==>     log file: /usr/WS1/mckinsey/benchpark/lib/scripts/benchpark-develop-openmp/wkp/benchpark-develop-openmp/amg2023/benchpark-develop-openmp/ruby/workspace/logs/setup.2025-03-27_13.19.33/amg2023.problem1.amg2023_problem1_single_node_openmp_caliper_none_2_2_2_80_80_80_8_1.out
   ==>   Returning to log file: /usr/WS1/mckinsey/benchpark/lib/scripts/benchpark-develop-openmp/wkp/benchpark-develop-openmp/amg2023/benchpark-develop-openmp/ruby/workspace/logs/setup.2025-03-27_13.19.33.out

   # myBranch build
   ==> Streaming details to log:
   ==>   /usr/WS1/mckinsey/benchpark/lib/scripts/benchpark-myBranch-openmp/wkp/benchpark-myBranch-openmp/amg2023/benchpark-myBranch-openmp/ruby/workspace/logs/setup.2025-03-27_13.28.29.out
   ==>   Setting up 1 out of 1 experiments:
   ==> Experiment #1 (1/1):
   ==>     name: amg2023.problem1.amg2023_problem1_single_node_openmp_caliper_none_2_2_2_80_80_80_8_1
   ==>     root experiment_index: 1
   ==>     log file: /usr/WS1/mckinsey/benchpark/lib/scripts/benchpark-myBranch-openmp/wkp/benchpark-myBranch-openmp/amg2023/benchpark-myBranch-openmp/ruby/workspace/logs/setup.2025-03-27_13.28.29/amg2023.problem1.amg2023_problem1_single_node_openmp_caliper_none_2_2_2_80_80_80_8_1.out
   ==>   Returning to log file: /usr/WS1/mckinsey/benchpark/lib/scripts/benchpark-myBranch-openmp/wkp/benchpark-myBranch-openmp/amg2023/benchpark-myBranch-openmp/ruby/workspace/logs/setup.2025-03-27_13.28.29.out

   The specs for amg2023 are different.
      amg2023+mpi [develop]
      -> [openmpi]
         hypre+mpi
            openblas
            openmpi
      amg2023~mpi [myBranch]
         hypre~mpi
            openblas
      DifferentSpecs=True

Compare Benchpark Packages Against Spack
----------------------------------------
``lib/scripts/diffPackages.py``

This script is used to check if packages (``package.py``) in ``benchpark/repo/`` can be deleted. 
We can delete the benchpark ``package.py`` if it is the exact same as the ``package.py`` in ``spack/var/spack/repos/builtin/packages/``.
This script runs in the benchpark CI and will fail if a package should be deleted in benchpark.

Example: amg2023 and raja-perf
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example, we made ``benchpark/repo/amg2023/package.py`` the same as the spack ``amg2023/package.py`` and equivalently 
``benchpark/repo/raja-perf/package.py`` the same as spack ``raja-perf/package.py``.

.. code-block:: console

   $ benchpark-python diffPackages.py --packages amg2023 raja-perf

   Comparing benchpark packages to packages in spack develop
   amg2023
      No differences found. Please delete 'benchpark/repo/amg2023/package.py' (use spack upstream)
      0 different lines
   raja-perf
      No differences found. Please delete 'benchpark/repo/raja-perf/package.py' (use spack upstream)
      0 different lines