..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

######################
 Adding an Experiment
######################

This guide is intended for those who would like to add a new experiment for a specific
benchmark.

.. rubric:: Video

For the last recorded video of this tutorial, see the `Benchpark Tutorial starting at
1:47:00 <https://www.youtube.com/watch?v=AeaUfpybJfg>`_.

Similar to the systems API, Benchpark provides an API for representing experiments as
objects and customizing their options with command line arguments. Experiment
specifications are defined in ``experiment.py`` files located in the experiment
directory for each benchmark: ``benchpark/experiments/<benchmark>``.

- If you are adding experiments to an existing benchmark, you should extend the current
  ``experiment.py`` for that benchmark in the experiments directory.
- If you are adding experiments to a new benchmark, create a directory for your
  benchmark in the experiments directory, and put your ``experiment.py`` in this
  directory.

These ``experiment.py`` files inherit from the Experiment base class in
``lib/benchpark/experiment.py``, and when used in conjunction with the system
configuration files and package/application repositories, are used to generate a set of
concrete Ramble experiments for the target system and programming model.

In this example, we will show how to create an experiment for the `High Performance
Computing Linpack Benchmark <https://www.netlib.org/benchmark/hpl/>`__. This benchmark
has a `Spack package
<https://github.com/LLNL/benchpark/blob/develop/repo/hpl/package.py>`__ and `Ramble
application <https://github.com/LLNL/benchpark/blob/develop/repo/hpl/application.py>`__
defined in Benchpark, so Benchpark will use these over the upstream `Spack package
<https://github.com/spack/spack-packages/blob/develop/repos/spack_repo/builtin/packages/hpl/package.py>`__
and `Ramble application
<https://github.com/GoogleCloudPlatform/ramble/blob/develop/var/ramble/repos/builtin/applications/hpl/application.py>`__.
For clarity, if ``benchpark/repo/hpl`` did not exist, Benchpark would use the upstream
versions. Additionally, the Benchpark HPL ``application.py`` inherits from the Ramble
upstream, so they are equivalent aside from an extra Benchpark tag definition. Notice
the HPL application in Ramble also inherits from a `base HPL application
<https://github.com/GoogleCloudPlatform/ramble/blob/develop/var/ramble/repos/builtin/base_applications/hpl/base_application.py>`__,
which is relevant because it contains the workload variables that we will need to define
in our Benchpark experiment.

*************************************
 Step 1: Create the Experiment class
*************************************

We create the ``experiment.py`` file under ``benchpark/experiments/hpl/experiment.py``.
The naming of this directory will affect how the experiment is initialized, e.g.,
``benchpark experiment init ... hpl``. There are multiple scaling options, modifiers,
and programming models we can inherit from, but at minimum our experiment should inherit
from the base ``Experiment`` class and ``MpiOnlyExperiment`` indicating that our
experiment can be executed with MPI.

::

    from benchpark.experiment import Experiment
    from benchpark.mpi import MpiOnlyExperiment

    class Hpl(
      Experiment,
      MpiOnlyExperiment,
    ):

Looking at the `HPL package
<https://github.com/LLNL/benchpark/blob/develop/repo/hpl/package.py>`__, we see that
there are ``OpenMP`` and ``Caliper`` variants defined in the build specification. The
HPL package.py defines the ``OpenMP`` variant because the source of the HPL benchmark
supports the ``OpenMP`` programming model. The HPL package.py defines the ``Caliper``
variant because the HPL source code is instrumented with the ``Caliper`` performance
profiling library (via a `fork <https://github.com/daboehme/HPL-caliper.git>`__ of the
source code) and the build links to Caliper. Enabling these variants in our Benchpark
experiment only requires inheritance from the pre-defined ``OpenMPExperiment`` and
``Caliper`` classes. For more details on the configurability of experiment variants, see
:ref:`experiment-variants`.

::

    from benchpark.experiment import Experiment
    from benchpark.mpi import MpiOnlyExperiment
    from benchpark.openmp import OpenMPExperiment
    from benchpark.caliper import Caliper

    class Hpl(
      Experiment,
      MpiOnlyExperiment,
      OpenMPExperiment,
      Caliper,
    ):

**************************************
 Step 2: Add Variants and Maintainers
**************************************

Next, we add experiment variants and a maintainer:

1. variants - provide configurability to options in Spack and Ramble
2. maintainer - the GitHub username of the person responsible of maintaining the
   experiment (likely you!)

For HPL, we add two variants. The first is a ``workload`` variant to configure which
Ramble workload we are going to use. The second is a version of our benchmark, which
should take the possible values (e.g., ``"NAME_OF_DEVELOPMENT_BRANCH"``, ``"latest"``,
``"rc1"``, ``"rc2"``). ``latest`` is a keyword that will automatically choose the latest
release version from the ``package.py``. For HPL, the source is a ``tar.gz`` instead of
a repository, so we are not able to list a development branch. Additionally, we add our
GitHub username, or multiple GitHub usernames, to record the ``maintainers`` of this
experiment.

::

    from benchpark.experiment import Experiment
    from benchpark.mpi import MpiOnlyExperiment
    from benchpark.openmp import OpenMPExperiment
    from benchpark.caliper import Caliper
    from benchpark.directives import variant, maintainers

    class Hpl(
      Experiment,
      MpiOnlyExperiment,
      OpenMPExperiment,
      Caliper,
    ):

      variant(
        "workload",
        default="standard",
        description="Which ramble workload to execute.",
      )

      variant(
        "version",
        default="2.3-caliper",
        values=("latest", "2.3-caliper", "2.3", "2.2"),
        description="Which benchmark version to use.",
      )

      maintainers("daboehme")

******************************************
 Step 3: Add a Ramble Application Section
******************************************

The ``experiment.py::compute_applications_section()`` function in Benchpark exists to
interface with the Ramble application for:

    1. Defining experiment variables.
    2. Defining a scaling configurations for ``strong``, ``weak``, and/or ``throughput``
       scaling.

Step 3a: Define Experiment Variables
====================================

We can specify experiment variables in Benchpark using the
``Experiment.add_experiment_variable()`` member function. *One* of ``n_ranks``,
``n_nodes``, ``n_gpus`` must be set, using ``add_experiment_variable()`` for Benchpark
to allocate the correct amount of resources for the experiment. You can also define
experiment variables here that will override the default values for the ``workload
variables`` in your ``application.py``. For HPL, we override the ``Ns``, ``N-Grids``,
``Ps``, ``Qs``, ``N-Ns``, ``N-NBs``, and ``NBs`` workload variables which are defined in
the base `application
<https://github.com/GoogleCloudPlatform/ramble/blob/develop/var/ramble/repos/builtin/base_applications/hpl/base_application.py>`__.

Additionally, all of ``n_resources``, ``process_problem_size``, and
``total_problem_size`` must be set, which can be accomplished using
``Experiment.set_required_variables()``. These variables will not exist in the
``application.py``, instead they are used by Benchpark to record important experiment
metadata. How you set ``process_problem_size`` or ``total_problem_size`` depends on how
your benchmark defines problem size (either per-process or a global/total problem size
that is divided among the processes in the application). For an example of a
"per-process problem size" benchmark see the ``amg2023/experiment.py``, and for "total
problem size" see the ``kripke/experiment.py``. For our use case, HPL requires a total
problem size.

Notice that we define separate sets of experiment variables for the ``exec_mode=test``
and ``exec_mode=perf`` cases. The difference between the variable definitions in these
cases depends on if you want to perform a test execution (small amount of resources and
problem difficulty) or a performance execution (relatively larger resource allocation
and problem difficulty). The only mode that is required to define is ``exec_mode=test``
by default.

::

    from benchpark.experiment import Experiment
    from benchpark.mpi import MpiOnlyExperiment
    from benchpark.openmp import OpenMPExperiment
    from benchpark.caliper import Caliper
    from benchpark.directives import variant, maintainers

    class Hpl(
      Experiment,
      MpiOnlyExperiment,
      OpenMPExperiment,
      Caliper,
    ):

      variant(
        "workload",
        default="standard",
        description="Which ramble workload to execute.",
      )

      variant(
        "version",
        default="2.3-caliper",
        values=("latest", "2.3-caliper", "2.3", "2.2"),
        description="Which benchmark version to use.",
      )

      maintainers("daboehme")

      def compute_applications_section(self):

        # exec_mode is a variant available for every experiment.
        # This can be used to define a "testing" and "performance" set of experiment variables.
        # The "performance" set of variables are usually a significantly larger workload.
        # The default setting is "exec_mode=test".
        if self.spec.satisfies("exec_mode=test"):
          self.add_experiment_variable("n_nodes", 1, True)

          # Overwrite values in application (https://github.com/GoogleCloudPlatform/ramble/blob/3c3e6b7c58270397ad10dfbe9c52bfad790c0631/var/ramble/repos/builtin/base_applications/hpl/base_application.py#L411-L419)
          self.add_experiment_variable("Ns", 10000, True)
          self.add_experiment_variable("N-Grids", 1, False)
          self.add_experiment_variable("Ps", "4 * {n_nodes}", True)
          self.add_experiment_variable("Qs", "8", False)
          self.add_experiment_variable("N-Ns", 1, False)
          self.add_experiment_variable("N-NBs", 1, False)
          self.add_experiment_variable("NBs", 128, False)
        # Must be exec_mode=perf if not test mode.
        # We can increase the magnitude of some/all the experiment variables for performance testing.
        else:
          self.add_experiment_variable("n_nodes", 16, True)

          self.add_experiment_variable("Ns", 100000, True)
          self.add_experiment_variable("N-Grids", 1, False)
          self.add_experiment_variable("Ps", "4 * {n_nodes}", True)
          self.add_experiment_variable("Qs", "8", False)
          self.add_experiment_variable("N-Ns", 1, False)
          self.add_experiment_variable("N-NBs", 1, False)
          self.add_experiment_variable("NBs", 128, False)

        # "sys_cores_per_node" will be defined by your system.py
        self.add_experiment_variable(
          "n_ranks", "{sys_cores_per_node} * {n_nodes}", False
        )
        self.add_experiment_variable(
          "n_threads_per_proc", ["2"], named=True, matrixed=True
        )

        # Set the variables required by the experiment
        self.set_required_variables(
          n_resources="{n_ranks}",
          process_problem_size="{Ns}/{n_ranks}",
          total_problem_size="{Ns}",
        )

For more details on the ``add_experiment_variable`` function, see :ref:`add-expr-var`.

Step 3b: Define Scaling Options
===============================

To complete our ``compute_applications_section()`` function, we import the scaling
module, inherit from the appropriate scaling options, and write the scaling
configuration in the ``compute_applications_section()``.

For HPL, we will be defining the ``strong`` and ``weak`` scaling configurations.

    - For ``strong`` scaling: we want to increase the resources experiment variable
      ``n_nodes``, and keep the problem size experiment variable ``Ns`` constant.
    - For ``weak`` scaling: we want to increase both ``n_nodes`` and ``Ns`` by the same
      factor, keeping the problem size per-process constant.

The scaling factor and amount of times the factor is applied can be configured using the
runtime parameters during experiment initialization, e.g., ``benchpark experiment init
... scaling-factor=2 scaling-iterations=4`` (i.e. 2x applied for 4 iterations).

::

    from benchpark.experiment import Experiment
    from benchpark.mpi import MpiOnlyExperiment
    from benchpark.openmp import OpenMPExperiment
    from benchpark.scaling import ScalingMode, Scaling
    from benchpark.caliper import Caliper
    from benchpark.directives import variant, maintainers

    class Hpl(
      Experiment,
      MpiOnlyExperiment,
      OpenMPExperiment,
      Scaling(ScalingMode.Strong, ScalingMode.Weak),
      Caliper,
    ):

      variant(
        "workload",
        default="standard",
        description="Which ramble workload to execute.",
      )

      variant(
        "version",
        default="2.3-caliper",
        values=("latest", "2.3-caliper", "2.3", "2.2"),
        description="Which benchmark version to use.",
      )

      maintainers("daboehme")

      def compute_applications_section(self):
        ...

        ### Add strong scaling definition
        # Register the scaling variables and their respective scaling functions
        # required to correctly scale the experiment for the given scaling policy
        # Strong scaling: scales up n_nodes by the specified scaling_factor, problem size is constant
        # Weak scaling: scales n_nodes and Ns problem size by scaling_factor
        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_nodes": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "Ns": lambda var, itr, dim, scaling_factor: var.val(dim),
                },
                ScalingMode.Weak: {
                    "n_nodes": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                    "Ns": lambda var, itr, dim, scaling_factor: var.val(dim)
                    * scaling_factor,
                },
            }
        )

See :ref:`this section <scaling-configs>` for more information on how to write Benchpark
scaling configurations.

***************************************
 Step 4: Add a Package Manager Section
***************************************

In ``experiment.py::compute_package_section()``, add the benchmark's package spec. We do
not list required packages for the benchmark here, since they are already defined in the
``package.py``.

::

    from benchpark.experiment import Experiment
    from benchpark.mpi import MpiOnlyExperiment
    from benchpark.openmp import OpenMPExperiment
    from benchpark.scaling import ScalingMode, Scaling
    from benchpark.caliper import Caliper
    from benchpark.directives import variant, maintainers

    class Hpl(
      Experiment,
      MpiOnlyExperiment,
      OpenMPExperiment,
      Scaling(ScalingMode.Strong, ScalingMode.Weak),
      Caliper,
    ):

      variant(
        "workload",
        default="standard",
        description="Which ramble workload to execute.",
      )

      variant(
        "version",
        default="2.3-caliper",
        values=("latest", "2.3-caliper", "2.3", "2.2"),
        description="Which benchmark version to use.",
      )

      maintainers("daboehme")

      def compute_applications_section(self):
        ...

      def compute_package_section(self):
        self.add_package_spec(self.name, [f"hpl{self.determine_version()}"])

*********************************************
 Step 5: Validating the Benchmark/Experiment
*********************************************

To manually validate that your new experiment works, you should start by initializing
your experiment:

::

    # first - initialize some system: benchpark system init --dest=my-system ...

    # second - initialize the experiment
    benchpark experiment init --dest=hpl my-system hpl

If this completes without errors, you can continue testing by setting up a benchpark
workspace as described in :doc:`testing-your-contribution`.

*********************
 Experiment Appendix
*********************

.. _experiment-variants:

More on Inherited Experiment Variants
=====================================

Variants of the experiment can be added to utilize different programming models used for
on-node parallelization, e.g., ``benchpark/experiments/amg2023/experiment.py`` can be
updated to inherit from different experiments, which can be set to ``cuda`` for an
experiment using CUDA (on an NVIDIA GPU), or ``openmp`` for an experiment using OpenMP
(on a CPU).:

::

    class Amg2023(
      Experiment,
      MpiOnlyExperiment
      OpenMPExperiment,
      CudaExperiment,
      ROCmExperiment,
      Scaling(ScalingMode.Strong, ScalingMode.Weak, ScalingMode.Throughput),
      Caliper,
    ):

Multiple types of experiments can be created using variants as well (e.g., strong
scaling, weak scaling). See AMG2023 or Kripke for examples. When implementing scaling,
the following variants are available to the experiment

- ``scaling`` defines the scaling mode e.g. ``strong``, ``weak`` and ``throughput``
- ``scaling-factor`` defines the factor by which a variable should be scaled
- ``scaling-iterations`` defines the number of scaling experiments to be generated

Once an experiment class has been written, an experiment is initialized with the
following command, with any boolean variants with +/~ or string variants defined in your
experiment.py passed in as key-value pairs: ``benchpark experiment init --dest
{path/to/dest} --system {path/to/system} {benchmark_name} +/~{boolean variant} {string
variant}={value}``

For example, to run the AMG2023 strong scaling experiment for problem 1, using CUDA the
command would be: ``benchpark experiment init --dest amg2023_experiment --system
{path/to/system} amg2023 +cuda+strong workload=problem1 scaling-factor=2
scaling-iterations=4``

Initializing an experiment generates the following yaml files:

- ``ramble.yaml`` defines the `Ramble specs
  <https://ramble.readthedocs.io/en/latest/workspace_config.html#>`__ for building,
  running, analyzing and archiving experiments.
- ``execution_template.tpl`` serves as a template for the final experiment script that
  will be concretized and executed.

A detailed description of Ramble configuration files is available at `Ramble
workspace_config <https://ramble.readthedocs.io/en/latest/workspace_config.html#>`__.

For more advanced usage, such as customizing hardware allocation or performance
profiling see :doc:`modifiers`.

.. _add-expr-var:

More on add_experiment_variable
===============================

The method ``add_experiment_variable`` is used to add a variable to the experiment's
``ramble.yaml``. It has the following signature:

::

    def add_experiment_variable(self, name, value, named, matrixed)

where,

- ``name`` is the name of the variable
- ``value`` is the value of the variable
- ``named`` indicates if the variable's name should appear in the experiment name
  (default ``False``)
- ``matrixed`` indicates if the variable must be matrixed in ``ramble.yaml`` (default
  ``False``)

``add_experiment_variable`` can be used to define multi-dimensional and scalar
variables. e.g.:

::

    self.add_experiment_variable("n_resources_dict", {"px": 2, "py": 2, "pz": 1}, named=True, matrix=True)
    self.add_experiment_variable("groups", 16, named=True, matrix=True)
    self.add_experiment_variable("n_gpus", 8, named=False, matrix=False)

In the above example, ``n_resources_dict`` is added as 3D variable with dimensions
``px``, ``py`` and ``pz`` and assigned the values ``2``, ``2``, and ``1`` respectively.
``groups`` and ``n_gpus`` are scalar variables with values ``16`` and ``8``
respectively. If ``named`` is set to ``True``, unexpanded variable name (individual
dimension names for multi-dimensional variables) is appended to the experiment name in
``ramble.yaml``

Every multi-dimensional experiment variable is defined as a zip in the ``ramble.yaml``.
If ``matrixed`` is set to ``True``, the variable (or the zip iin case of a
multi-dimensional variable) is declared as a matrix in ``ramble.yaml``. The generated
``ramble.yaml`` for the above example would be look like:

::

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

A variable also can be assigned a list of values, each individual value corresponding to
a single experiment. Refer to the Ramble documentation for a detailed explanation of zip
and matrix.

.. _scaling-configs:

More on Scaling Configurations
==============================

For each scaling mode supported by an application, the ``def register_scaling_config()``
method must define the scaled variables and their corresponding scaling function. The
input to ``def register_scaling_config()`` is a dictionary of the following form.:

::

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

Scaled variables can be multi-dimensional or one-dimensional. All multi-dimensional
variables in a scaling mode must have the same dimensionality. The scaling function for
each variable takes the following form.:

::

    def scaling_function(var, i, dim, sf):
      # scale var[dim] for the i-th experiment
      scaled_val = ...
      return scaled_val

where,

- ``var`` is the ``benchpark.Variable`` instance corresponding to the scaled variable
- ``i`` is the i-th experiment in the specified number of ``scaling-iterations``
- ``dim`` is the current dimension that is being scaled (in any given experiment
  iteration the same dimension of each variable is scaled)
- ``sf`` is the value by which the variable must be scaled, as specified by
  ``scaling-factor``

In the list of variables defined for each scaling mode, scaling starts from the
dimension that has the minimum value for the first variable and proceeds through the
dimensions in a round-robin manner till the specified number of experiments are
generated. That is, if the scaling config is defined as:

::

    register_scaling_config ({
      ScalingMode.Strong: {
        "n_resources_dict": lambda var, i, dim, sf: var.val(dim) * sf,
        "process_problem_size_dict": lambda var, i, dim, sf: var.val(dim) * sf,
      }
    })

and the initial values of the variables are:

::

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

then after 4 scaling iterations (i.e. 3 scalings), the final values of the scaled
variables will be:

::

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
(``n_resources_dict``) and proceeds in a round-robin manner through the other
dimensions. See AMG2023 or Kripke for examples of different scaling configurations.
