..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

###############################
 Updating Software in a System
###############################

**Glossary terms:** :ref:`Package <beginner-tutorial-glossary-package>`, :ref:`Variant
<beginner-tutorial-glossary-variant>`, :ref:`System <beginner-tutorial-glossary-system>`

These steps show how to use ``benchpark system external`` to compare and update the
external packages defined by a Benchpark system against packages detected on the current
machine. For adding a new system, please see :doc:`add-a-system-config`.

Detection includes both the general Spack search and searches at declared prefixes. When
an existing version is detected with different spec details, Benchpark proposes updating
that entry. Newly detected versions are added independently. Versions that are not
detected remain declared unchanged and are reported as ``NOT_FOUND`` in the terminal;
detecting a newer version does not prove that an older version is absent. Ambiguous
matches within one version are reported for review.

Edits to declarations shared by multiple clusters apply to all of those clusters,
assuming a shared software installation. The report lists the affected clusters.

Terminal output highlights confirmed entries in green, updates in blue, additions in
cyan, review findings in yellow, and validator failures in red. Redirected output is
plain text by default. Set ``SPACK_COLOR=always`` or ``SPACK_COLOR=never`` to override
automatic color selection.

.. note::

    You must run the following commands in the Fluxtainer environment. Software is
    detected for the current environment.

****************************
 Spack Repository and Cache
****************************

``benchpark system external`` uses the Spack and ``spack-packages`` checkouts in
Benchpark's configured bootstrap location. The command selects the pinned
``spack-packages`` repository for each Spack invocation, so detection does not depend on
package repositories downloaded into ``~/.spack`` or on the user's Spack configuration.

Spack's cache for this command is located at ``<bootstrap-location>/spack-user-cache``.
Spack creates this directory when the command first needs it; ``benchpark bootstrap``
does not create it in advance. The bootstrap location can be set with ``benchpark
configure -bl <path>``.

***********************************
 1. Lower the Recorded Tar Version
***********************************

The Fluxtainer definition created in :doc:`add-a-system-config` records ``tar@1.35`` as
an external package. In ``systems/fluxtainer/system.py``, change that entry to an older
version:

.. code-block:: python

    "tar": {
        "externals": [
            {"spec": "tar@=1.34", "prefix": "/usr"},
        ],
        "buildable": False,
    },

The system definition now differs from the Fluxtainer environment, which provides
``tar@1.35``.

********************************
 2. Preview the Detected Update
********************************

Run external detection from the Fluxtainer environment and request a proposed source
change:

.. code-block:: console

    $ benchpark system external fluxtainer --propose

``--propose`` reports eligible changes without modifying the file. If detection finds
``tar@1.35`` and does not find ``tar@1.34``, the proposal adds the detected version and
retains the unconfirmed declaration unchanged:

.. code-block:: diff

      "externals": [
          {"spec": "tar@=1.34", "prefix": "/usr"},
    +     {"spec": "tar@=1.35", "prefix": "/usr"},
      ],

******************************
 3. Apply the Detected Update
******************************

Apply the proposed change to ``systems/fluxtainer/system.py``:

.. code-block:: console

    $ benchpark system external fluxtainer --apply

Benchpark validates the detected change before writing it. After the command completes,
the external ``tar`` list contains both versions. The unconfirmed ``tar@1.34`` entry
remains available for review. Changes that cannot be matched and applied unambiguously
are reported for manual review.

***********
 Next Step
***********

.. tutorialcontainer:: tutorial-next-steps

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-run

        :doc:`I want to initialize, build, and rerun my experiment using the updated
        system software stack. <build-and-run-experiment>`
