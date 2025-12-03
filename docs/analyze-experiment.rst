..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

######################
 Experiment pass/fail
######################

Once the experiments completed running, the command:

::

    ramble --workspace-dir . workspace analyze

can be used to analyze figures of merit and evaluate `success/failure
<https://ramble.readthedocs.io/en/latest/success_criteria.html#success-criteria>`_ of
the experiments. Ramble generates a file with summary of the results in ``$workspace``.
