..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

###################
 Updating a System
###################

These steps show how to use ``benchpark system external`` to compare the
external packages defined by a Benchpark system against packages detected on
the current machine.

***************************
 Check an Existing System
***************************

Run ``benchpark system external`` with the same system variants that would normally be
passed to ``benchpar system init``. For example, to check the Tioga configuration of
``llnl-elcapitan``:

::

    benchpark system external llnl-elcapitan cluster=tioga

Benchpark processes the supplied system specification, collects the expected
package configuration from the system definition, and runs Spack external
detection for those packages. The detected configuration is then compared
against the configuration defined by Benchpark.

To generate version-update proposals for the system
definition, use ``--propose``:

::

    benchpark system external llnl-elcapitan cluster=tioga --propose

Additional system variants can be supplied in the same way. For example:

::

    ./bin/benchpark system external llnl-elcapitan cluster=tioga --propose

************************
 Save Proposed Changes
************************

Write the proposed changes as a unified diff with ``--patch-file``:

::

    benchpark system external llnl-elcapitan cluster=tioga --patch-file=tioga-externals.patch

Alternatively, write a complete proposed copy of the updated ``system.py``:

::

    benchpark system external llnl-elcapitan cluster=tioga --write-proposed-system=system.py.proposed

These options generate proposed changes without modifying the existing
Benchpark system definition.

*********************
 Apply Local Changes
*********************

After reviewing the proposed updates, use ``--apply`` to apply changes
directly to the system's ``system.py``:

::

    benchpark system external llnl-elcapitan cluster=tioga --apply

Benchpark performs the same external detection and comparison before updating
the system definition. Only changes that can be matched and applied
unambiguously are written automatically. Updates that require manual review are
reported without being applied.

The resulting changes can be inspected with Git before committing:

::

    git diff -- systems/llnl-elcapitan/system.py

************************
 Create a Pull Request
************************

To apply the detected changes and create a pull request containing the update,
use ``--apply`` together with ``--pr``:

::

    benchpark system external llnl-elcapitan cluster=tioga --apply --pr

Benchpark first applies the safe updates to the system definition. It then
creates a Git branch for the update, commits the modified ``system.py``, pushes
the branch to the configured remote, and opens a pull request against the
Benchpark repository.