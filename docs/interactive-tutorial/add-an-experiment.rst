..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

######################
 Adding an Experiment
######################

**Glossary terms:** :ref:`Benchmark <beginner-tutorial-glossary-benchmark>`,
:ref:`Package <beginner-tutorial-glossary-package>`, :ref:`Application
<beginner-tutorial-glossary-application>`, :ref:`Spec
<beginner-tutorial-glossary-spec>`, :ref:`Variant <beginner-tutorial-glossary-variant>`,
:ref:`Experiment <beginner-tutorial-glossary-experiment>`, :ref:`System
<beginner-tutorial-glossary-system>`, :ref:`Modifier
<beginner-tutorial-glossary-modifier>`, :ref:`Scaling Study
<beginner-tutorial-glossary-scaling-study>`

**********************************
 Create the Experiment Definition
**********************************

This example defines the HPL experiment used throughout the Beginner Tutorial. Start
``experiments/hpl/experiment.py`` with the definition below. The steps that follow add
the components omitted from this initial version.

.. code-block:: python
    :linenos:

    # Copyright 2023 Lawrence Livermore National Security, LLC and other
    # Benchpark Project Developers. See the top-level COPYRIGHT file for details.
    #
    # SPDX-License-Identifier: Apache-2.0

    from benchpark.experiment import Experiment
    # Step 1 adds the programming-model import here.
    from benchpark.caliper import Caliper
    from benchpark.directives import variant, maintainers
    from benchpark.scaling import Scaling, ScalingMode


    class Hpl(
        Experiment,
        # Step 1 adds the supported programming models here.
        Caliper,
        Scaling(ScalingMode.Strong, ScalingMode.Weak),
    ):
        variant(
            "workload",
            default="standard",
            description="Which ramble workload to execute.",
        )

        # Step 2 adds the version variant here.

        maintainers("daboehme")

        def compute_applications_section(self):

            if self.spec.satisfies("exec_mode=test"):
                self.add_experiment_variable("n_ranks", 2, True)
                self.add_experiment_variable("Ns", 10000, True)
                self.add_experiment_variable("N-Grids", 1, False)
                self.add_experiment_variable("Ps", "{n_ranks}", True)
                self.add_experiment_variable("Qs", "1", False)
                self.add_experiment_variable("N-Ns", 1, False)
                self.add_experiment_variable("N-NBs", 1, False)
                self.add_experiment_variable("NBs", 128, False)

            # Step 3 adds the exec_mode=perf else block here.

            # Step 4 adds the required-variable definitions here.

            self.register_scaling_config(
                {
                    ScalingMode.Strong: {
                        "n_ranks": lambda var, itr, dim, scaling_factor: (
                            var.val(dim) * scaling_factor
                        ),
                        "Ns": lambda var, itr, dim, scaling_factor: var.val(dim),
                    },
                    ScalingMode.Weak: {
                        "n_ranks": lambda var, itr, dim, scaling_factor: (
                            var.val(dim) * scaling_factor
                        ),
                        "Ns": lambda var, itr, dim, scaling_factor: (
                            var.val(dim) * scaling_factor
                        ),
                    },
                }
            )

        def compute_package_section(self):
            self.add_package_spec(self.name, [f"hpl{self.determine_version()}"])

1. Add Programming Models
=========================

Programming models define the parallel execution modes supported by an experiment.
Replace the first Step 1 placeholder with the programming-model import:

.. code-block:: python

    from benchpark.programming_model import ProgrammingModel, ProgrammingModelType

Replace the second Step 1 placeholder in the ``Hpl`` class bases with the supported MPI
and OpenMP programming models:

.. code-block:: python

    ProgrammingModel(ProgrammingModelType.Mpionly, ProgrammingModelType.Openmp),

2. Add the Version Variant
==========================

Each explicit experiment version must be defined in the corresponding Spack package. For
HPL, ``2.3`` and ``2.2`` are defined in
``repos/spack_repo/benchpark/packages/hpl/package.py``. The ``latest`` value is a
Benchpark keyword that selects the newest version defined by the Spack package.

Replace the Step 2 placeholder with the complete version variant:

.. code-block:: python

    variant(
        "version",
        default="2.3-caliper",
        values=("latest", "2.3-caliper", "2.3", "2.2"),
        description="Which benchmark version to use.",
    )

3. Add a Performance Mode
=========================

The ``exec_mode=test`` experiment definition provides small values for the problem size
and number of ranks. Replace the Step 3 placeholder with the following ``else`` branch
to define a set of experiment variables that is more suited to collecting performance
data:

.. code-block:: python

    # Must be exec_mode=perf if not test mode.
    else:
        self.add_experiment_variable("n_ranks", 32, True)
        self.add_experiment_variable("Ns", 100000, True)
        self.add_experiment_variable("N-Grids", 1, False)
        self.add_experiment_variable("Ps", "({n_ranks} // 8)", True)
        self.add_experiment_variable("Qs", "8", False)
        self.add_experiment_variable("N-Ns", 1, False)
        self.add_experiment_variable("N-NBs", 1, False)
        self.add_experiment_variable("NBs", 128, False)

4. Set Required Variables
=========================

Benchpark records the resources and problem sizes used by each experiment. Replace the
Step 4 placeholder with the following call, which defines the number of ranks, the HPL
problem size per rank, and the total HPL problem size:

.. code-block:: python

    # Set the variables required by the experiment
    self.set_required_variables(
        n_resources="{n_ranks}",
        process_problem_size="{Ns}/{n_ranks}",
        total_problem_size="{Ns}",
    )

For the complete experiment authoring reference, see :doc:`/add-an-experiment`.

***********
 Next Step
***********

.. tutorialcontainer:: tutorial-next-steps

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-scaling

        :doc:`I want to add a scaling configuration to this experiment.
        <add-a-scaling-configuration>`

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-run

        :doc:`I want to build and run the new experiment on my existing system.
        <build-and-run-experiment>`
