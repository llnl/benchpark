..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

#########################
 Compare Package Commits
#########################

``lib/scripts/diffPackageCommits.py``

Compare a commit of a Spack package in Benchpark with the package upstreamed to Spack.
If the comparison of the ``package.py`` in ``repos/spack_repo/benchpark/packages/`` is
identical to the ``package.py`` in
``spack-packages/repos/spack_repo/builtin/packages/``, ``package.py`` in
``repos/spack_repo/benchpark/packages/`` can be safely deleted without changing how the
benchmark is built; this scenario occurs if ``package.py`` has been upstreamed to Spack.
This script runs in the benchpark CI and will fail if a package should be deleted in
benchpark.

********************************
 Example: amg2023 and raja-perf
********************************

In this example, we made ``repos/spack_repo/benchpark/packages/amg2023/package.py`` the
same as the spack ``amg2023/package.py`` and equivalently
``repos/spack_repo/benchpark/packages/raja_perf/package.py`` the same as spack
``raja_perf/package.py``.

.. code-block:: console

    $ benchpark-python diffPackageCommits.py --packages amg2023 raja_perf

    Comparing benchpark packages to packages in spack develop
    amg2023
       No differences found. Please delete 'repos/spack_repo/benchpark/packages/amg2023/package.py' (use spack upstream)
       0 different lines
    raja_perf
       No differences found. Please delete 'repos/spack_repo/benchpark/packages/raja_perf/package.py' (use spack upstream)
       0 different lines
