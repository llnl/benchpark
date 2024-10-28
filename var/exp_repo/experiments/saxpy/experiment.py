from benchpark.directives import variant
from benchpark.experiment import Experiment


class Saxpy(Experiment):
    variant(
        "programming_model",
        default="openmp",
        values=("openmp", "cuda", "rocm"),
        description="on-node parallelism model",
    )

    def compute_applications_section(self):
        variables = {}

        # GPU tests include some smaller sizes
        n = ["512", "1024"]
        if self.spec.satisfies("programming_model=openmp"):
            variables["n_nodes"] = ["1", "2"]
            variables["n_ranks"] = "8"
            variables["omp_num_threads"] = ["2", "4"]
            matrix_cfg = {
                "matrices": [
                    {
                        "size_threads": ["n", "omp_num_threads"],
                    }
                ]
            }
        else:
            n = ["128", "256"] + n
            variables["n_gpus"] = "1"
            matrix_cfg = {"matrix": ["n"]}

        variables["n"] = n

        the_experiment = {
            "variants": {
                "package_manager": "spack",
            },
            "variables": variables,
        }
        the_experiment.update(matrix_cfg)

        if self.spec.satisfies("programming_model=openmp"):
            experiment_id = "saxpy_{n}_{n_nodes}_{omp_num_threads}"
        elif self.spec.satisfies("programming_model=cuda") or self.spec.satisfies(
            "programming_model=rocm"
        ):
            experiment_id = "saxpy_{n}"

        return {
            "saxpy": {  # ramble Application name
                "workloads": {
                    # TODO replace with a hash once we have one?
                    "problem": {
                        "experiments": {
                            experiment_id: the_experiment,
                        }
                    }
                }
            }
        }

    def compute_include_section(self):
        return [
            "./configs/software.yaml",
            "./configs/variables.yaml",
            "./configs/modifier.yaml",
        ]

    def compute_spack_section(self):
        # TODO: express that we need certain variables from system
        # Does not need to happen before merge, separate task
        saxpy_spack_spec = "saxpy@1.0.0{modifier_spack_variant}"
        if self.spec.satisfies("programming_model=openmp"):
            saxpy_spack_spec += "+openmp"
        elif self.spec.satisfies("programming_model=cuda"):
            saxpy_spack_spec += "+cuda cuda_arch={cuda_arch}"
        elif self.spec.satisfies("programming_model=rocm"):
            saxpy_spack_spec += "+rocm amdgpu_target={rocm_arch}"

        packages = ["default-mpi", self.spec.name, "{modifier_package_name}"]

        return {
            "packages": {
                "saxpy": {
                    "pkg_spec": saxpy_spack_spec,
                    "compiler": "default-compiler",  # TODO: this should probably move?
                }
            },
            "environments": {"saxpy": {"packages": packages}},
        }
