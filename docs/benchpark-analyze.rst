..
   Copyright 2022 Lawrence Livermore National Security, LLC and other
   Thicket Project Developers. See the top-level LICENSE file for details.

   SPDX-License-Identifier: MIT

#####################################
Canned Analysis for Scaling Studies
#####################################

The ``benchpark analyze`` command can be used to generate pre-configured
charts for analysis of scaling studies using Caliper and Thicket. 
We use `Thicket <https://github.com/LLNL/thicket>`_ to help compose and visualize
Caliper performance data collected from running our experiment with the Caliper modifier.
After running, ``ramble on``, run the ``benchpark analyze`` command on the ramble workspace directory.

.. note::

  This command required optional packages to be installed, which can be achieved with ``pip install .[analyze]`` (assuming you are in the benchpark directory)

How to Run
**********

.. code:: console

   $ benchpark analyze --workspace-dir WORKSPACE_DIR <optional_arguments>

Available Arguments
*******************
.. list-table:: Table of Arguments
   :widths: 50 50
   :header-rows: 1

   * - Argument
     - Description
   * - --workspace-dir
     - Str: Required. Directory of Ramble workspace.
   * - --chart-type
     - Str: Optional. Specify type of output chart. Choices: `"percentage_time"` | `"time"`. Default is `"time"`.
   * - --x_axis-unique-metadata
     - Str: Optional. Parameter that is varied during the experiment. Default is `None`.
   * - --y-axis-metric
     - Str: Optional. Metric to be visualized. Default is `"Avg time/rank (exc)"`.
   * - --filter-nodes-name-prefix
     - Str: Optional. Filters only entries with prefix to be included in the chart. Default is `""`.
   * - --group-nodes-name
     - Bool: Optional. Specify if nodes with the same name are combined. Default is `True`.
   * - --top-n-nodes
     - Int: Optional. Filters only top n longest time entries to be included in the chart. Default is `-1` (no filter).
   * - --chart-title
     - Str: Optional. Title of the output chart. Default is `None`.
   * - --chart-xlabel
     - Str: Optional. X-axis label of the chart.
   * - --chart-ylabel
     - Str: Optional. Y-axis label of the chart.
   * - --chart-file-name
     - Str: Optional. Output chart file name. Default is `"stacked_line_chart"`.
   * - --chart-figsize
     - List of Ints: Optional. Size of the output chart `(xdim, ydim)`. Example: `--chart-figsize 10 6`.
   * - --chart-fontsize
     - Int: Optional. Font size of the output chart.
   * - --no-mpi
     - Bool: Optional. Hide MPI regions in the tree.

Analysis of Strong, Weak, and Throughput Scaling of Kripke
************************************************************

Kripke Calltree

.. code::

   main
  ├─  Generate
  │  ├─  MPI_Allreduce
  │  ├─  MPI_Comm_split
  │  └─  MPI_Scan
  ├─  MPI_Allreduce
  ├─  MPI_Bcast
  ├─  MPI_Comm_dup
  ├─  MPI_Comm_free
  ├─  MPI_Comm_split
  ├─  MPI_Finalize
  ├─  MPI_Finalized
  ├─  MPI_Gather
  ├─  MPI_Get_library_version
  ├─  MPI_Initialized
  └─  Solve
    └─  solve
        ├─  LPlusTimes
        ├─  LTimes
        ├─  Population
        │  └─  MPI_Allreduce
        ├─  Scattering
        ├─  Source
        └─  SweepSolver
          ├─  MPI_Irecv
          ├─  MPI_Isend
          ├─  MPI_Testany
          ├─  MPI_Waitall
          └─  SweepSubdomain

Strong
------

Generate the Strong dataset:

.. code:: console

  $ benchpark experiment init --dest=kripke/cuda/strong kripke+cuda+strong~single_node caliper=time,mpi
  $ benchpark system init --dest=lassen llnl-sierra
  $ benchpark setup kripke/cuda/strong lassen/ wkp
  // Follow instructions for running Ramble ...

Run canned analysis:

.. code:: console

  $ benchpark analyze --workspace-dir wkp/kripke/cuda/strong/lassen/workspace/ --chart-type "percentage_time" --top-n-nodes 10

.. figure:: _static/images/kripke_cuda_strong_percentage_time_exc.png
  :width: 800
  :align: center

.. code:: console

   $ benchpark analyze --workspace-dir wkp/kripke/cuda/strong/lassen/workspace/ --chart-type "time" --top-n-nodes 10


.. figure:: _static/images/kripke_cuda_strong_time_exc.png
  :width: 800
  :align: center

Weak
----

Generate the Weak dataset:

.. code:: console

  $ benchpark experiment init --dest=kripke/cuda/weak kripke+cuda+weak~single_node caliper=time,mpi
  $ benchpark setup kripke/cuda/weak lassen/ wkp
  // Follow instructions for running Ramble ...

Run canned analysis:

.. code:: console

   $ benchpark analyze --workspace-dir wkp/kripke/cuda/weak/lassen/workspace/ --chart-type "percentage_time" --top-n-nodes 10

.. figure:: _static/images/kripke_cuda_weak_percentage_time_exc.png
  :width: 800
  :align: center

.. code:: console

   $ benchpark analyze --workspace-dir wkp/kripke/cuda/weak/lassen/workspace/ --chart-type "time" --top-n-nodes 10

.. figure:: _static/images/kripke_cuda_weak_time_exc.png
  :width: 800
  :align: center

Throughput
----------

Generate the Throughput dataset:

.. code:: console

  $ benchpark experiment init --dest=kripke/cuda/throughput kripke+cuda+throughput~single_node caliper=time,mpi
  $ benchpark setup kripke/cuda/throughput lassen/ wkp
  // Follow instructions for running Ramble ...

Run canned analysis:

.. code:: console

   $ benchpark analyze --workspace-dir wkp/kripke/cuda/throughput/lassen/workspace/ --chart-type "percentage_time" --top-n-nodes 10

.. figure:: _static/images/kripke_cuda_throughput_percentage_time_exc.png
  :width: 800
  :align: center

.. code:: console

   $ benchpark analyze --workspace-dir wkp/kripke/cuda/throughput/lassen/workspace/ --chart-type "time" --top-n-nodes 10

.. figure:: _static/images/kripke_cuda_throughput_time_exc.png
  :width: 800
  :align: center

Inclusive Metrics
-----------------

.. code:: console

  $ benchpark analyze --workspace-dir wkp/kripke/cuda/strong/lassen/workspace/ --chart-type "time" --y-axis-metric "Avg time/rank" --top-n-nodes 10

We can also visualize any inclusive metrics by selecting them as the ``y_axis_metric``. Here we use ``Avg time/rank`` instead of ``Avg time/rank (exc)``.
The ``main`` node is automatically removed from the figure, because this information is redundant for the inclusive metric.

.. figure:: _static/images/kripke_cuda_strong_time_inc.png
  :width: 800
  :align: center