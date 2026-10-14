..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

######################
 Adding an Experiment
######################

**Glossary terms:** :ref:`Benchmark <beginner-tutorial-glossary-benchmark>`, :ref:`Package
<beginner-tutorial-glossary-package>`, :ref:`Application
<beginner-tutorial-glossary-application>`, :ref:`Spec
<beginner-tutorial-glossary-spec>`, :ref:`Variant
<beginner-tutorial-glossary-variant>`, :ref:`Experiment
<beginner-tutorial-glossary-experiment>`, :ref:`System
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
    from benchpark.programming_model import ProgrammingModel, ProgrammingModelType
    from benchpark.caliper import Caliper
    from benchpark.directives import variant, maintainers
    from benchpark.scaling import Scaling, ScalingMode


    class Hpl(
        Experiment,
        ProgrammingModel(ProgrammingModelType.Mpionly, ProgrammingModelType.Openmp),
        Caliper,
        Scaling(ScalingMode.Strong, ScalingMode.Weak),
    ):
        variant(
            "workload",
            default="standard",
            description="Which ramble workload to execute.",
        )

        variant(
            "version",
            default="2.3-caliper",
            values=(
                "latest",
                "2.3-caliper",
                # Step 1 adds more package versions here.
            ),
            description="Which benchmark version to use.",
        )

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

            # Step 2 adds the exec_mode=perf else block here.

            # Step 3 adds the required-variable definitions here.

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

1. Add More Benchmark Versions
==============================

Each explicit experiment version must be defined in the corresponding Spack package.
For HPL, ``2.3`` and ``2.2`` are defined in
``repos/spack_repo/benchpark/packages/hpl/package.py``. The ``latest`` value is a
Benchpark keyword that selects the newest version defined by the Spack package.

Replace the Step 1 placeholder in the ``values`` tuple with the additional versions:

.. code-block:: python

                "2.3",
                "2.2",

2. Add a Performance Experiment
===============================

The ``exec_mode=test`` experiment definition provides small values for the problem size and number of ranks. Replace the Step 2
placeholder with the following ``else`` branch to define a set of experiment variables that is more suited to collecting performance data:

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

3. Set Required Variables
=========================

Benchpark records the resources and problem sizes used by each experiment. Replace the
Step 3 placeholder with the following call, which defines the number of ranks, the HPL
problem size per rank, and the total HPL problem size:

.. code-block:: python

        # Set the variables required by the experiment
        self.set_required_variables(
            n_resources="{n_ranks}",
            process_problem_size="{Ns}/{n_ranks}",
            total_problem_size="{Ns}",
        )

.. _step-3b-define-scaling-options:

*******************************
Optional: Scaling Configuration
*******************************

``register_scaling_config()`` identifies the variables that change during a scaling
study. Strong scaling increases ``n_ranks`` while keeping ``Ns`` constant. Weak scaling
increases both values.

Initialize the experiment with the AWS tutorial system to validate the definition:

.. code-block:: console

    $ benchpark experiment init --dest=hpl aws-tutorial hpl +strong

For the complete experiment authoring reference, see :doc:`/add-an-experiment`.

***********
 Next Step
***********

.. container:: tutorial-next-steps

    .. container:: tutorial-next-step tutorial-goal-run

        :doc:`I want to build and run the new experiment on my existing system.
        <build-and-run-experiment>`
