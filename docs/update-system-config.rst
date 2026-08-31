..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

############################################
 Updating the System Software Specification
############################################

These steps show how to use ``benchpark system external`` to compare and update the
external packages defined by a Benchpark system against packages detected on the current
machine. For adding a new system, please see :ref:`add-a-system-config`

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

Benchpark collects the current system software specification and detects external
packages available on the current system. The detected packages are then compared
against the current configuration defined by Benchpark.

To generate version-update proposals for the system definition, use ``--propose``:

::

    benchpark system external llnl-elcapitan cluster=tioga --propose

Additional system variants can be specified in the same way. For example:

::

    benchpark system external llnl-elcapitan cluster=tioga rocm=7.2.0 --propose

These proposed changes are written to standard output. Changes that cannot be updated
cleanly are reported for manual review.

**************************************
 2. Apply Local Changes to the System
**************************************

After reviewing the proposed updates, use ``--apply`` to apply eligible changes directly
to the system's ``system.py``:

::

    benchpark system external llnl-elcapitan cluster=tioga --apply

Benchpark validates the detected changes before updating the system definition. Only
changes that can be matched and applied unambiguously are written automatically. Updates
that require manual review are reported without being applied.

The resulting changes can be inspected with Git before committing:

::

    git diff -- systems/llnl-elcapitan/system.py

The updated system definition can then be committed and upstreamed through the normal
Benchpark contribution workflow.
