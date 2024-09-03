from benchpark.directives import variant
from benchpark.experiment import Experiment


class Qws(Experiment):
    variant(
        "programming_model",
        default="mpi",
        values=("mpi", "openmp"),
        description="on-node parallelism model",
    )

    def compute_applications_section(self):
        env_vars = {}
        variables = {}

        variables["experiment_setup"] = ""
        variables["lx"] = "32"
        variables["ly"] = "6"
        variables["lz"] = "4"
        variables["lt"] = "3"
        variables["px"] = "1"
        variables["py"] = "1"
        variables["pz"] = "1"
        variables["pt"] = "1"
        variables["tol_outer"] = "-1"
        variables["tol_inner"] = "-1"
        variables["maxiter_plus1_outer"] = "6"
        variables["maxiter_inner"] = "50"

        if self.spec.satisfies("programming_model=openmp"):
            env_vars["OMP_NUM_THREADS"] = "{omp_num_threads}"

            variables["n_nodes"] = ["1"]
            variables["n_ranks"] = "{processes_per_node} * {n_nodes}"
            variables["omp_num_threads"] = ["48"]
            variables["arch"] = "OpenMP"

        return {
            "qws": {
                "workloads": {
                    f"problem-{str(self.spec)}": {
                        "env_vars": env_vars,
                        "experiments": {
                            "qws_mpi_{n_nodes}_{omp_num_threads}_{lx}_{ly}_{lz}_{lt}_{px}_{py}_{pz}_{pt}_{tol_outer}_{tol_inner}_{maxiter_plus1_outer}_{maxiter_inner}": {
                                "variants": {
                                    "package_manager": "spack",
                                },
                                "variables": variables,
                            },
                        },
                    },
                },
            },
        }

    def compute_spack_section(self):
        # TODO: express that we need certain variables from system
        # Does not need to happen before merge, separate task
        spack_spec = "qws@master +mpi{modifier_spack_variant}"
        packages = [self.spec.name, "{modifier_package_name}"]

        if self.spec.satisfies("programming_model=openmp"):
            spack_spec += "+openmp"
            packages.append("openmp")

        return {
            "software": {
                "packages": {
                    self.spec.name: {
                        "spack_spec": spack_spec,
                        "compiler": "default_compiler",  # TODO: this should probably move?
                    }
                },
                "environments": {"qws": {"packages": packages}},
            }
        }
