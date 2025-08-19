.. Copyright 2023 Lawrence Livermore National Security, LLC and other
   Benchpark Project Developers. See the top-level COPYRIGHT file for details.

   SPDX-License-Identifier: Apache-2.0

====================
Adding an Experiment
====================

.. note: 
  TODO: If contributing an experiment, extend existing experiment.py. Otherwise create a new experiment.py in the benchmark folder for the experiments

This guide is intended for those wanting to define a new set of experiment parameters for a given benchmark. 

Similar to systems, Benchpark also provides an API where you can represent experiments 
as objects and customize their description with command line arguments.

Experiment specifications are created with ``experiment.py`` files each located in the experiment repo: ``benchpark/experiments/${Benchmark1}``.

* If you are adding experiments to an existing benchmark, it is best to extend the current experiment.py for that benchmark in the experiment repo.

* If you are adding experiments to a benchmark you created, create a new folder for your benchmark in the experiment repo, and put your new experiment.py inside of it.

These ``experiment.py`` files inherit from the Experiment base class in ``/lib/benchpark/experiment.py`` shown below, and when used in conjunction with the system configuration files 
and package/application repositories, are used to generate a set of concrete Ramble experiments for the target system and programming model.

.. literalinclude:: ../lib/benchpark/experiment.py
   :language: python


Some or all of the functions in the Experiment base class can be overridden to define custom behavior, such as adding experiment variants. 


compute_applications_section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In ``compute_applications_section``, we define the experiment variables necessary to perform scaling runs (``strong``, ``weak``, or ``throughput``)
using ramble. We also define programming model (``CUDA``, ``ROCm``, or ``OpenMP``) specific variables, such as ``arch``, which may be used by the benchmark.

We can specify experiment variables to benchpark using the ``Experiment.add_experiment_variable()`` member function.
*One* of ``n_ranks``, ``n_nodes``, ``n_gpus`` must be set, using ``add_experiment_variable`` for benchpark to allocate the correct amount of resources for the experiment.
Additionally, all of ``n_resources``, ``process_problem_size``, and ``total_problem_size`` must be set, which can be accomplished using ``Experiment.set_required_variables()``.

add_experiment_variable
-----------------------
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


compute_package_section
~~~~~~~~~~~~~~~~~~~~~~~
In ``compute_package_section`` add the benchmark's package spec. Required packages for the benchmark should be defined in the ``package.py``. 
``ADDITIONAL_SPECS`` should be specifications that the exeperiment always uses, such as ``+mpi``, e.g. ``amg2023@{app_version} +mpi``. 

::
  
  def compute_package_section(self):
      app_version = self.spec.variants["version"][0]
      self.add_package_spec(self.name, [f"BENCHMARK@{app_version} [ADDITIONAL_SPECS]"])

.. note: 
  This will change and need updates

Variants
~~~~~~~~

Variants of the experiment can be added to utilize different *ProgrammingModels* used for on-node parallelization,
e.g., ``benchpark/experiments/amg2023/experiment.py`` can be updated to inherit from different experiments to , which can be
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
``benchpark experiment init --dest {path/to/dest} --system {path/to/system} {benchmark_name} +/~{boolean variant} {string variant}={value} ``

For example, to run the AMG2023 strong scaling experiment for problem 1, using CUDA the command would be:
``benchpark experiment init --dest amg2023_experiment --system {path/to/system} amg2023 +cuda workload=problem1 scaling=strong scaling-factor=2 scaling-iterations=4``

Initializing an experiment generates the following yaml files:

- ``ramble.yaml`` defines the `Ramble specs <https://ramble.readthedocs.io/en/latest/workspace_config.html#>`_ for building, running, analyzing and archiving experiments.
- ``execution_template.tpl`` serves as a template for the final experiment script that will be concretized and executed.

A detailed description of Ramble configuration files is available at `Ramble workspace_config <https://ramble.readthedocs.io/en/latest/workspace_config.html#>`_.

For more advanced usage, such as customizing hardware allocation or performance profiling see :doc:`modifiers`.

register_scaling_config
~~~~~~~~~~~~~~~~~~~~~~~

For each scaling mode supported by an application, the ``register_scaling_config`` method must define the scaled variables and their
corresponding scaling function.
The input to ``register_scaling_config`` is a dictionary of the form::

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

Scaled variables can be multi-dimensional or one-dimensional. All multi-dimensional variables in a scaling mode must have the same dimensionality.
The scaling function for each variable takes the form::

    def scaling_function(var, i, dim, sf):
       # scale var[dim] for the i-th experiment
       scaled_val = ...
       return scaled_val

where,

- ``var`` is the ``benchpark.Variable`` instance corresponding to the scaled variable
- ``i`` is the i-th experiment in the specified number of ``scaling-iterations``
- ``dim`` is the current dimension that is being scaled (in any given experiment iteration the same dimension of each variable is scaled)
- ``sf`` is the value by which the variable must be scaled, as specified by ``scaling-factor``

In the list of variables defined for each scaling mode, scaling starts from the dimension that has the minimum value 
for the first variable and proceeds through the dimensions in a round-robin manner till the specified number of experiments are generated
e.g. if the scaling config is defined as::

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

Note that scaling starts from the minimum value dimension (``pz``) of the first variable (``n_resources_dict``)
and proceeds in a round-robin manner through the other dimensions.
See AMG2023 or Kripke for examples of different scaling configurations.


Validating the Benchmark/Experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To manually validate your new experiments work, you should initialize an existing system, and run your experiments. 
For example if you just created a benchmark *baz* with OpenMP and strong scaling variants it may look like this:::

  benchpark system init --dest=genericx86-system genericx86 
  benchpark experiment init --dest=baz-benchmark --system=genericx86-system baz +openmp +strong
  benchpark setup ./baz-benchmark workspace/


When this is complete you have successfully completed the :doc:`benchpark-setup` step and can run and analyze following the Benchpark output or following steps in :doc:`build-experiment`.

