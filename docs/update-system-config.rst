..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

############################################
 Updating the System Software Specification
############################################

These steps show how to use ``benchpark system external`` to compare and update the
external packages defined by a Benchpark system against packages detected on the current
machine. the current machine. For adding a new system, please see
:ref:`add-a-system-config`

.. note::

    You must run the following commands on the target system. Software is detected for
    the current environment.

***************************************************************************
 1. Compare the Existing Software Specification to the Current Environment
***************************************************************************

Run ``benchpark system external`` with the same system variants that would normally be
passed to ``benchpark system init``. For example, to check the Tioga configuration of
``llnl-elcapitan``:

::

    benchpark system external llnl-elcapitan cluster=tioga

Benchpark collects the current system software specification, and runs ``spack external
find`` to detect new versions for each package. The detected configuration is then
compared against the current configuration defined by Benchpark.

To generate version-update proposals for the system definition, use ``--propose``:

::

    benchpark system external llnl-elcapitan cluster=tioga --propose

Additional system variants can be specified in the same way. For example:

::

    benchpark system external llnl-elcapitan cluster=tioga rocm=7.2.0 --propose

This proposed changes will be written to standard output. If you want to save these
changes to a file, proceed to the next step.

******************************************
 2. Save Proposed Changes to a Patch File
******************************************

Write the proposed changes as a unified diff with ``--patch-file``:

::

    benchpark system external llnl-elcapitan cluster=tioga --patch-file=tioga-externals.patch

**************************************
 3. Apply Local Changes to the System
**************************************

After reviewing the proposed updates, use ``--apply`` to apply changes directly to the
system's ``system.py``:

::

    benchpark system external llnl-elcapitan cluster=tioga --apply

Benchpark performs the same external detection and comparison independently before
updating the system definition. Only changes that can be matched and applied
unambiguously are written automatically. Updates that require manual review are reported
without being applied.

The resulting changes can be inspected with Git before committing:

::

    git diff -- systems/llnl-elcapitan/system.py

*************************************************
 4. Upstream Changes to the Benchpark Repository
*************************************************

To apply the detected changes and create a pull request containing the update, use
``--apply`` together with ``--pr``:

::

    benchpark system external llnl-elcapitan cluster=tioga --apply --pr

Benchpark first applies the safe updates to the system definition. It then creates a Git
branch for the update, commits the modified ``system.py``, pushes the branch to the
configured remote, and opens a pull request against the Benchpark repository.
