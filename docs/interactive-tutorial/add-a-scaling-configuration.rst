..
    Copyright 2023 Lawrence Livermore National Security, LLC and other
    Benchpark Project Developers. See the top-level COPYRIGHT file for details.

    SPDX-License-Identifier: Apache-2.0

################################
 Adding a Scaling Configuration
################################

**Glossary terms:** :ref:`Benchmark <beginner-tutorial-glossary-benchmark>`,
:ref:`Experiment <beginner-tutorial-glossary-experiment>`, :ref:`Scaling Study
<beginner-tutorial-glossary-scaling-study>`

Start with the HPL experiment definition below in ``experiments/hpl/experiment.py``.
This definition includes the completed experiment from the previous tutorial page, but
does not yet register its scaling configuration.

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
            values=("latest", "2.3-caliper", "2.3", "2.2"),
            description="Which benchmark version to use.",
        )

        maintainers("daboehme")

        def compute_applications_section(self):

            if self.spec.satisfies("exec_mode=test"):
                self.add_experiment_variable("n_ranks", 1, True)
                self.add_experiment_variable("Ns", 1000, True)
                self.add_experiment_variable("N-Grids", 1, False)
                self.add_experiment_variable("Ps", "{n_ranks}", True)
                self.add_experiment_variable("Qs", "1", False)
                self.add_experiment_variable("N-Ns", 1, False)
                self.add_experiment_variable("N-NBs", 1, False)
                self.add_experiment_variable("NBs", 128, False)
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

            # Set the variables required by the experiment
            self.set_required_variables(
                n_resources="{n_ranks}",
                process_problem_size="{Ns}/{n_ranks}",
                total_problem_size="{Ns}",
            )

            # Step 1 adds the scaling configuration here.

        def compute_package_section(self):
            self.add_package_spec(self.name, [f"hpl{self.determine_version()}"])

***************************************
 1. Register the Scaling Configuration
***************************************

Replace the Step 1 placeholder in ``compute_applications_section()`` with the following
call. Strong scaling increases ``n_ranks`` while keeping ``Ns`` constant. Weak scaling
increases both values.

.. code-block:: python

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

Initialize the strong-scaling experiment with the Fluxtainer system to validate the
definition:

.. code-block:: console

    $ benchpark experiment init --dest=hpl fluxtainer hpl+strong

For the complete experiment authoring reference, see :doc:`/add-an-experiment`.

Next Step
=========

.. tutorialcontainer:: tutorial-next-steps

    .. tutorialcontainer:: tutorial-next-step tutorial-goal-run

        :doc:`I want to build and run the experiment with its scaling configuration.
        <build-and-run-experiment>`
