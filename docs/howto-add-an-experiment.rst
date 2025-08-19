.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

====================
Adding an Experiment
====================

This guide is intended for those wanting to add a new experiment for a given benchmark.

Similar to systems, Benchpark also provides an API where you can represent experiments
as objects and customize their description with command line arguments.

Experiment specifications are defined in ``experiment.py`` files located in the experiment repo for
each benchmark: ``benchpark/experiments/<benchmark>``.

* If you are adding experiments to an existing benchmark, you should extend the current
  ``experiment.py`` for that benchmark in the experiments directory.

* If you are adding experiments to a new benchmark, create a directory for your benchmark in the
  experiments directory, and move your ``experiment.py`` to this directory.

These ``experiment.py`` files inherit from the Experiment base class in
``lib/benchpark/experiment.py``, and when used in conjunction with the system configuration files
and package/application repositories, are used to generate a set of concrete Ramble experiments for
the target system and programming model.

-----------------------------
Step 1: Create the Experiment
-----------------------------

Create the ``experiment.py`` file under ``benchpark/experiments/<benchmark>/experiment.py``. At
minimum, your experiment should inherit from the base ``Experiment`` class.

.. code::

  from benchpark.experiment import Experiment

  class MyExperiment(
    Experiment,
  ):

Optionally your experiment can be configured to support different Benchpark experiment variants, which include:

#. programming models
#. scaling modes (if the experiment will support scaling studies)
#. modifiers

In the following example experiment, we assume the benchmark supports the ``CUDA`` programming
model, the benchmark can be strong scaled (using ``strong`` scaling option), and the benchmark can
be profiled with the ``Caliper`` instrumentation and performance profiling library.  For more
details on the configurability of experiment variants, see :ref:`experiment-variants`.

.. code::

  from benchpark.experiment import Experiment
  from benchpark.cuda import CudaExperiment
  from benchpark.scaling import ScalingMode, Scaling
  from benchpark.caliper import Caliper

  class MyExperiment(
    Experiment,
    CudaExperiment,
    Scaling(ScalingMode.Strong),
    Caliper,
  ):

------------------------------------
Step 2: Add Variants and Maintainers
------------------------------------

Next, we add:

#. variants - which will provide configurability to the Spack package manager and Ramble
#. maintainer - the GitHub username of the person responsible of maintaining the experiment (likely you!)

Continuing with our example, we add two variants. The first is a ``workload`` variant to configure
which Ramble workload we are going to use. The second is a version of our benchmark, which should
take the possible values (e.g., ``"NAME_OF_DEVELOPMENT_BRANCH"``, ``"latest"``, ``"rc1"``,
``"rc2"``). ``latest`` is a keyword that will automatically choose the latest release version from
the ``package.py``. Additionally, we add our GitHub username, or multiple usernames in the tuple,
to record the ``maintainers`` of this experiment.

.. code::

  from benchpark.experiment import Experiment
  from benchpark.cuda import CudaExperiment
  from benchpark.scaling import ScalingMode, Scaling
  from benchpark.caliper import Caliper
  from benchpark.directives import variant, maintainers

  class MyExperiment(
    Experiment,
    CudaExperiment,
    Scaling(ScalingMode.Strong),
    Caliper,
  ):

  variant(
    "workload",
    default="problem1",
    values=("problem1", "problem2"),
    description="Which ramble workload to execute.",
  )

  variant(
    "version",
    default="v2025",
    values=("develop", "latest", "v2025"),
    description="Which benchmark version to use.",
  )

  maintainers("your_github_username")

----------------------------------------
Step 3: Add a Ramble Application Section
----------------------------------------

The ``def compute_applications_section()`` is for defining experiment variables necessary for the
programming model (``CUDA``, ``ROCm``, or ``OpenMP``). One such variable is ``arch``, which may be
used by the benchmark to perform scaling runs (``strong``, ``weak``, or ``throughput``) using
Ramble.

Continuing with our example, we will be using the ``CUDA`` programming model and ``strong``
scaling. :ref:`This section <scaling-configs>` contains more information on how to write Benchpark scaling
configurations.

We can specify experiment variables to Benchpark using the ``Experiment.add_experiment_variable()`` member function.
*One* of ``n_ranks``, ``n_nodes``, ``n_gpus`` must be set, using ``add_experiment_variable()`` for Benchpark to allocate the correct amount of resources for the experiment.

Additionally, all of ``n_resources``, ``process_problem_size``, and ``total_problem_size`` must be set, which can be accomplished using ``Experiment.set_required_variables()``.
How you set ``process_problem_size`` or ``total_problem_size`` depends on how your benchmark defines problem size (either per-process or a global problem size that is divided among the processes in the application). For an example of a per-process problem size benchmark see ``amg2023/experiment.py``, and for total problem size see ``kripke/experiment.py``. For our example benchmark, we will assume a total problem size.

.. code::

  from benchpark.experiment import Experiment
  from benchpark.cuda import CudaExperiment
  from benchpark.scaling import ScalingMode, Scaling
  from benchpark.caliper import Caliper
  from benchpark.directives import variant, maintainers

  class MyExperiment(
    Experiment,
    CudaExperiment,
    Scaling(ScalingMode.Strong),
    Caliper,
  ):

  variant(
    "workload",
    default="problem1",
    values=("problem1", "problem2"),
    description="Which ramble workload to execute.",
  )

  variant(
    "version",
    default="v2025",
    values=("develop", "latest", "v2025"),
    description="Which benchmark version to use.",
  )

  maintainers("your_github_username")

  def compute_applications_section(self):
    ### Add experiment variables and required variables
    self.add_experiment_variable("n_procs", 1)
    
    # exec_mode is a variant available for every experiment.
    # This can be used to define a "testing" and "performance" set of experiment variables.
    # The "performance" set of variables are usually a significantly larger workload.
    # The default setting is "exec_mode=test".
    if self.spec.satisfies("exec_mode=test"):
      self.add_experiment_variable("my_problemsize", 1024)
    # Must be exec_mode=perf
    else:
      self.add_experiment_variable("my_problemsize", 1024**2)

    # Set the variables required by the experiment
    self.set_required_variables(
      n_resources="{n_procs}",
      process_problem_size="{my_problemsize}/{n_procs}",
      total_problem_size="{my_problemsize}",
    )

    ### Add strong scaling definition
    # Register the scaling variables and their respective scaling functions
    # required to correctly scale the experiment for the given scaliing policy
    # Strong scaling scales up n_procs by the specified scaling_factor
    self.register_scaling_config(
      {
          ScalingMode.Strong: {
            "n_procs": lambda var, itr, dim, scaling_factor: var.val(dim)
            * scaling_factor,
          },
      }
    )

    ### CUDA specific logic
    if self.spec.satisfies("+cuda"):
      self.add_experiment_variable("n_gpus", "{n_resources}", named=True)
      # Benchmark-specific variable
      # Your benchmark may not need this
      self.add_experiment_variable("arch", "CUDA")
    else:
      self.add_experiment_variable("n_ranks", "{n_resources}")
      # Benchmark-specific variable
      # Your benchmark may not need this
      self.add_experiment_variable("arch", "Sequential")

For more details on the ``add_experiment_variable`` function, see :ref:`add-expr-var`.

----------------------------------------
Step 4: Add a Package Manager Section
----------------------------------------

In ``def compute_package_section()``, add the benchmark's package spec. Required packages for the benchmark should be defined in one of two ways:
  
#. in the ``package.py``, either in Spack or ``benchpark/repo/`` (if using Spack).
#. in the ``pyproject.toml`` or ``setup.py`` of the Python project (if using pip).

.. code::

  from benchpark.experiment import Experiment
  from benchpark.cuda import CudaExperiment
  from benchpark.scaling import ScalingMode, Scaling
  from benchpark.caliper import Caliper
  from benchpark.directives import variant, maintainers

  class MyExperiment(
    Experiment,
    CudaExperiment,
    Scaling(ScalingMode.Strong),
    Caliper,
  ):

    variant(
      "workload",
      default="problem1",
      values=("problem1", "problem2"),
      description="Which ramble workload to execute.",
    )

    variant(
      "version",
      default="v2025",
      values=("develop", "latest", "v2025"),
      description="Which benchmark version to use.",
    )

    maintainers("your_github_username")

    def compute_applications_section(self):
      ...
    
    def compute_package_section(self):
      # ADDITIONAL_SPECS is optional
      self.add_package_spec(self.name, [f"my-experiment{self.determine_version()}"])

-------------------------------------------
Step 5: Validating the Benchmark/Experiment
-------------------------------------------

To manually validate your new experiment works, you should start by initializing your experiment::

  benchpark experiment init --dest=my-experiment --system=my-system my-experiment

If this completes without errors, you can continue testing by setting up a benchpark workspace as described in :doc:`testing-your-contribution`.

--------
Appendix
--------

.. _experiment-variants:

More on Inherited Experiment Variants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Variants of the experiment can be added to utilize different programming models used for on-node parallelization,
e.g., ``benchpark/experiments/amg2023/experiment.py`` can be updated to inherit from different experiments, which can be
set to ``cuda`` for an experiment using CUDA (on an NVIDIA GPU),
or ``openmp`` for an experiment using OpenMP (on a CPU).::

    class Amg2023(
      Experiment,
      OpenMPExperiment,
      CudaExperiment,
      ROCmExperiment,
      Scaling(ScalingMode.Strong, ScalingMode.Weak, ScalingMode.Throughput),
      Caliper,
    ):

Multiple types of experiments can be created using variants as well (e.g., strong scaling, weak scaling). See AMG2023 or Kripke for examples.
When implementing scaling, the following variants are available to the experiment

- ``scaling`` defines the scaling mode e.g. ``strong``, ``weak`` and ``throughput``
- ``scaling-factor`` defines the factor by which a variable should be scaled
- ``scaling-iterations`` defines the number of scaling experiments to be generated

Once an experiment class has been written, an experiment is initialized with the following command, with any boolean variants with +/~ or 
string variants defined in your experiment.py passed in as key-value pairs: 
``benchpark experiment init --dest {path/to/dest} {benchmark_name} +/~{boolean variant} {string variant}={value} ``

For example, to run the AMG2023 strong scaling experiment for problem 1, using CUDA the command would be:
``benchpark experiment init --dest amg2023_experiment amg2023 +cuda workload=problem1 scaling=strong scaling-factor=2 scaling-iterations=4``

Initializing an experiment generates the following yaml files:

- ``ramble.yaml`` defines the `Ramble specs <https://ramble.readthedocs.io/en/latest/workspace_config.html#>`_ for building, running, analyzing and archiving experiments.
- ``execution_template.tpl`` serves as a template for the final experiment script that will be concretized and executed.

A detailed description of Ramble configuration files is available at `Ramble workspace_config <https://ramble.readthedocs.io/en/latest/workspace_config.html#>`_.

For more advanced usage, such as customizing hardware allocation or performance profiling see :doc:`modifiers`.

.. _add-expr-var:

More on add_experiment_variable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The method ``add_experiment_variable`` is used to add a variable to the experiment's ``ramble.yaml``. It has the following signature::

  def add_experiment_variable(self, name, value, named, matrixed)

where,

- ``name`` is the name of the variable
- ``value`` is the value of the variable
- ``named`` indicates if the variable's name should appear in the experiment name (default ``False``)
- ``matrixed`` indicates if the variable must be matrixed in ``ramble.yaml`` (default ``False``)

``add_experiment_variable`` can be used to define multi-dimensional and scalar variables. e.g.::

  self.add_experiment_variable("n_resources_dict", {"px": 2, "py": 2, "pz": 1}, named=True, matrix=True)
  self.add_experiment_variable("groups", 16, named=True, matrix=True)
  self.add_experiment_variable("n_gpus", 8, named=False, matrix=False)

In the above example, ``n_resources_dict`` is added as 3D variable with dimensions ``px``, ``py`` and ``pz`` and assigned the values ``2``, ``2``, and ``1`` respectively.
``groups`` and ``n_gpus`` are scalar variables with values ``16`` and ``8`` respectively.
If ``named`` is set to ``True``, unexpanded variable name (individual dimension names for multi-dimensional variables) is appended to the experiment name in ``ramble.yaml``

Every multi-dimensional experiment variable is defined as a zip in the ``ramble.yaml``.
If ``matrixed`` is set to ``True``, the variable (or the zip iin case of a multi-dimensional variable) is declared as a matrix in ``ramble.yaml``.
The generated ``ramble.yaml`` for the above example would be look like::

  experiments:
    amg2023_{px}_{py}_{pz}_{groups}:
      ...
      variables:
          px: 2
          py: 2
          pz: 2
          groups: 16
          n_gpus: 8
      zips:
        n_resources_dict:
        - px
        - py
        - pz
      matrix:
        - n_resources_dict
        - groups


A variable also can be assigned a list of values, each individual value corresponding to a single experiment.
Refer to the Ramble documentation for a detailed explanation of zip and matrix.

.. _scaling-configs:

More on Scaling Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each scaling mode supported by an application, the ``def register_scaling_config()`` method
must define the scaled variables and their corresponding scaling function. The input to
``def register_scaling_config()`` is a dictionary of the following form.::

  {
    ScalingMode.Strong: {
      "v1": strong_scaling_function1,
      "v2": strong_scaling_function2,
      ...
    },
    ScalingMode.Weak: {
      "v1": weak_scaling_function1,
      "v2": weak_scaling_function2,
      ...
    },
    ...
  }

Scaled variables can be multi-dimensional or one-dimensional. All multi-dimensional variables in a
scaling mode must have the same dimensionality. The scaling function for each variable takes the
following form.::

  def scaling_function(var, i, dim, sf):
    # scale var[dim] for the i-th experiment
    scaled_val = ...
    return scaled_val

where,

- ``var`` is the ``benchpark.Variable`` instance corresponding to the scaled variable
- ``i`` is the i-th experiment in the specified number of ``scaling-iterations``
- ``dim`` is the current dimension that is being scaled (in any given experiment iteration the same
  dimension of each variable is scaled)
- ``sf`` is the value by which the variable must be scaled, as specified by ``scaling-factor``

In the list of variables defined for each scaling mode, scaling starts from the dimension that has
the minimum value for the first variable and proceeds through the dimensions in a round-robin
manner till the specified number of experiments are generated. That is, if the scaling config is
defined as::

  register_scaling_config ({
    ScalingMode.Strong: {
      "n_resources_dict": lambda var, i, dim, sf: var.val(dim) * sf,
      "process_problem_size_dict": lambda var, i, dim, sf: var.val(dim) * sf,
    }
  })

and the initial values of the variables are::

  "n_resources_dict" : {
    "px": 2, # dim 0
    "py": 2, # dim 1
    "pz": 1, # dim 2
  },
  "process_problem_size_dict" : {
    "nx": 16, # dim 0
    "ny": 32, # dim 1
    "nz": 32, # dim 2
  },

then after 4 scaling iterations (i.e. 3 scalings), the final values of the scaled variables will be::

    "n_resources_dict" : {
        "px": [2, 2, 4, 4]
        "py": [2, 2, 2, 4]
        "pz": [1, 2, 2, 2]
    },
    "process_problem_size_dict" : {
        "nx": [16, 16, 32, 32]
        "ny": [32, 32, 32, 64]
        "nz": [32, 64, 64, 64]
    },

Note that scaling starts from the minimum value dimension (``pz``) of the first variable
(``n_resources_dict``) and proceeds in a round-robin manner through the other dimensions.
See AMG2023 or Kripke for examples of different scaling configurations.