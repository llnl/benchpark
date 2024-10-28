from benchpark.directives import variant
from benchpark.experiment import Experiment


class Kripke(Experiment):
    variant(
        "programming_model",
        default="openmp",
        values=("openmp", "cuda", "rocm"),
        description="node-level parallelism model",
    )

    variant(
        "scaling",
        default="single-node",
        values=("single-node", "weak", "strong"),
        description="Single node, weak scaling, or strong scaling study",
    )

    def compute_applications_section(self):
        self.workload = "kripke"

        npx = "npx"
        npy = "npy"
        npz = "npz"
        nzx = "nzx"
        nzy = "nzy"
        nzz = "nzz"
        num_procs = "{npx} * {npy} * {npz}"

        variables = {}

        if self.spec.satisfies("programming_model=openmp"):
            variables["arch"] = "OpenMP"
            variables["n_ranks"] = num_procs
            variables["n_threads_per_proc"] = 1
            n_resources = "{n_ranks}_{n_threads_per_proc}"
        elif self.spec.satisfies("programming_model=cuda"):
            variables["arch"] = "CUDA"
            variables["n_gpus"] = num_procs
            n_resources = "{n_gpus}"
        elif self.spec.satisfies("programming_model=rocm"):
            variables["arch"] = "HIP"
            variables["n_gpus"] = num_procs
            n_resources = "{n_gpus}"

        variables |= {
            "ngroups": 64,
            "gs": 1,
            "nquad": 128,
            "ds": 128,
            "lorder": 4,
        }

        # Number of processes in each dimension
        initial_np = [2, 2, 1]

        # Number of zones in each dimension, per process
        initial_nz = [64, 64, 32]

        if self.spec.satisfies("scaling=single-node"):
            variables[npx] = initial_np[0]
            variables[npy] = initial_np[1]
            variables[npz] = initial_np[2]
            variables[nzx] = initial_nz[0]
            variables[nzy] = initial_nz[1]
            variables[nzz] = initial_nz[2]
        else:
            input_params = {}
            if self.spec.satisfies("scaling=strong"):
                scaling_variable = (npx, npy, npz)
                input_params[scaling_variable] = initial_np
                variables[nzx] = initial_nz[0]
                variables[nzy] = initial_nz[1]
                variables[nzz] = initial_nz[2]
            if self.spec.satisfies("scaling=weak"):
                scaling_variable = (npx, npy, npz)
                input_params[scaling_variable] = initial_np
                input_params[(nzx, nzy, nzz)] = initial_nz
            variables |= self.scale_experiment_variables(
                input_params,
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
                scaling_variable,
            )

        experiment_name_template = f"kripke_{self.spec.variants['programming_model'][0]}_{self.spec.variants['scaling'][0]}_{{n_nodes}}_{n_resources}_{{ngroups}}_{{gs}}_{{nquad}}_{{ds}}_{{lorder}}_{{{nzx}}}_{{{nzy}}}_{{{nzz}}}_{{{npx}}}_{{{npy}}}_{{{npz}}}"

        return {
            self.spec.name: {
                "workloads": {
                    self.workload: {
                        "experiments": {
                            experiment_name_template: {
                                "variants": {
                                    "package_manager": "spack",
                                },
                                "variables": variables,
                            }
                        }
                    }
                }
            }
        }

    def compute_spack_section(self):
        app_name = self.spec.name

        # set package versions
        app_version = "develop"
        chai_version = "2024.02"
        # caliper_version = "master"

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"
        if self.spec.satisfies("programming_model=cuda"):
            system_specs["cuda_version"] = "{default_cuda_version}"
            system_specs["cuda_arch"] = "{cuda_arch}"
        if self.spec.satisfies("programming_model=rocm"):
            system_specs["rocm_arch"] = "{rocm_arch}"

        # set package spack specs
        package_specs = {}
        if self.spec.satisfies("programming_model=cuda"):
            package_specs["cuda"] = {
                "pkg_spec": "cuda@{}+allow-unsupported-compilers".format(
                    system_specs["cuda_version"]
                ),
                "compiler": system_specs["compiler"],
            }
        package_specs[system_specs["mpi"]] = (
            {}
        )  # empty package_specs value implies external package
        package_specs["chai"] = {
            "pkg_spec": f"chai@{chai_version} +mpi",
            "compiler": system_specs["compiler"],
        }
        package_specs[app_name] = {
            "pkg_spec": f"kripke@{app_version} +mpi",
            "compiler": system_specs["compiler"],
        }

        if self.spec.satisfies("programming_model=openmp"):
            package_specs["chai"]["pkg_spec"] += "+openmp"
            package_specs[app_name]["pkg_spec"] += "+openmp"
        elif self.spec.satisfies("programming_model=cuda"):
            package_specs["chai"]["pkg_spec"] += "+cuda cuda_arch={}".format(
                system_specs["cuda_arch"]
            )
            package_specs[app_name]["pkg_spec"] += "+cuda cuda_arch={}".format(
                system_specs["cuda_arch"]
            )
        elif self.spec.satisfies("programming_model=rocm"):
            package_specs["chai"]["pkg_spec"] += "+rocm amdgpu_target={}".format(
                system_specs["rocm_arch"]
            )
            package_specs[app_name]["pkg_spec"] += "+rocm amdgpu_target={}".format(
                system_specs["rocm_arch"]
            )

        return {
            "packages": {k: v for k, v in package_specs.items() if v},
            "environments": {app_name: {"packages": list(package_specs.keys())}},
        }
