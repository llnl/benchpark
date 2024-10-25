.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

==================================
Analyzing Experiments in Benchpark
==================================

Once the experiments completed running, the command::

  ramble --disable-progress-bar --workspace-dir . workspace analyze 

can be used to analyze figures of merit and evaluate 
`success/failure <https://googlecloudplatform.github.io/ramble/success_criteria.html>`_ 
of the experiments. Ramble generates a file with summary of the results in ``$workspace``.
