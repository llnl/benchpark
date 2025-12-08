..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

#########################
 Compare Package Commits
#########################

``lib/scripts/diffPackageCommits.py``

Compare a commit of a Spack package in Benchpark/repo with the package upstreamed to
Spack. If the comparison of the ``package.py`` in ``benchpark/repo/`` is identical to
the ``package.py`` in ``spack/var/spack/repos/builtin/packages/``, ``package.py`` in
``benchpark/repo/`` can be safely deleted without changing how the benchmark is built;
this scenario occurs if ``package.py`` has been upstreamed to Spack. This script runs in
the benchpark CI and will fail if a package should be deleted in benchpark.

********************************
 Example: amg2023 and raja-perf
********************************

In this example, we made ``benchpark/repo/amg2023/package.py`` the same as the spack
``amg2023/package.py`` and equivalently ``benchpark/repo/raja-perf/package.py`` the same
as spack ``raja-perf/package.py``.

.. code-block:: console

    $ benchpark-python diffPackageCommits.py --packages amg2023 raja-perf

    Comparing benchpark packages to packages in spack develop
    amg2023
       No differences found. Please delete 'benchpark/repo/amg2023/package.py' (use spack upstream)
       0 different lines
    raja-perf
       No differences found. Please delete 'benchpark/repo/raja-perf/package.py' (use spack upstream)
       0 different lines
