from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.expr.builtin.caliper import Caliper


class Amg2023(Caliper, Experiment):
    variant(
        "programming_model",
        default="openmp",
        values=("openmp", "cuda", "rocm"),
        description="on-node parallelism model",
    )

    variant(
        "workload",
        default="problem1",
        values=("problem1", "problem2"),
        description="problem1 or problem2",
    )

    variant(
        "experiment",
        default="single-node",
        values=("strong", "weak", "example", "single-node", "throughput"),
        description="strong scaling, weak scaling, single-node, throughput study or an example",
    )

    def make_experiment_example(self):
        app_name = self.spec.name

        variables = {}
        matrices = []
        zips = {}

        if self.spec.satisfies("programming_model=openmp"):
            # TODO: Support variants
            n = ["55", "110"]
            variables["n_nodes"] = ["1", "2"]
            variables["n_ranks"] = "8"
            variables["n_threads_per_proc"] = ["4", "6", "12"]
            exp_name = f"{app_name}_example_omp_{{n_nodes}}_{{n_ranks}}_{{n_threads_per_proc}}_{{px}}_{{py}}_{{pz}}_{{nx}}_{{ny}}_{{nz}}"
        elif self.spec.satisfies("programming_model=cuda"):
            # TODO: Support variants
            n = ["10", "20"]
            variables["n_gpus"] = "8"
            exp_name = f"{app_name}_example_cuda_{{n_gpus}}_{{px}}_{{py}}_{{pz}}_{{nx}}_{{ny}}_{{nz}}"
        elif self.spec.satisfies("programming_model=rocm"):
            # TODO: Support variants
            n = ["110", "220"]
            variables["n_gpus"] = "8"
            exp_name = f"{app_name}_example_rocm_{{n_gpus}}_{{px}}_{{py}}_{{pz}}_{{nx}}_{{ny}}_{{nz}}"
        else:
            raise NotImplementedError(
                "Unsupported programming_model. Only openmp, cuda and rocm are supported"
            )

        # TODO: Support variant
        p = "2"
        variables["px"] = p
        variables["py"] = p
        variables["pz"] = p

        variables["nx"] = n
        variables["ny"] = n
        variables["nz"] = n
        zips["size"] = ["nx", "ny", "nz"]

        if self.spec.satisfies("programming_model=openmp"):
            matrices.extend(["size", "n_nodes", "n_threads_per_proc"])
        elif self.spec.satisfies("programming_model=cuda") or self.spec.satisfies(
            "programming_model=rocm"
        ):
            matrices.append("size")
        else:
            pass

        excludes = {}
        if self.spec.satisfies("programming_model=openmp"):
            excludes["where"] = [
                "{n_threads_per_proc} * {n_ranks} > {n_nodes} * {sys_cores_per_node}"
            ]

        return {
            app_name: {
                "workloads": {
                    f"{self.workload}": {
                        "experiments": {
                            exp_name: {
                                "variants": {"package_manager": "spack"},
                                "variables": variables,
                                "zips": zips,
                                "exclude": excludes,
                                "matrix": matrices,
                            }
                        }
                    }
                }
            }
        }

    def compute_modifiers_section(self):
        return Experiment.compute_modifiers_section(
            self
        ) + Caliper.compute_modifiers_section(self)

    def compute_applications_section(self):
        if self.spec.satisfies("workload=problem1"):
            self.workload = "problem1"
        else:
            self.workload = "problem2"

        if self.spec.satisfies("experiment=example"):
            return self.make_experiment_example()

        px = "px"
        py = "py"
        pz = "pz"
        nx = "nx"
        ny = "ny"
        nz = "nz"
        num_procs = "{px} * {py} * {pz}"

        variables = {}
        variables["n_ranks"] = num_procs

        if self.spec.satisfies("programming_model=openmp"):
            variables["n_ranks"] = num_procs
            variables["n_threads_per_proc"] = 1
            n_resources = "{n_ranks}_{n_threads_per_proc}"
        elif self.spec.satisfies("programming_model=cuda"):
            variables["n_gpus"] = num_procs
            n_resources = "{n_gpus}"
        elif self.spec.satisfies("programming_model=rocm"):
            variables["n_gpus"] = num_procs
            n_resources = "{n_gpus}"

        experiment_name = f"amg2023_{self.spec.variants['programming_model'][0]}_{self.spec.variants['experiment'][0]}_{self.workload}_{{n_nodes}}_{n_resources}_{{{px}}}_{{{py}}}_{{{pz}}}_{{{nx}}}_{{{ny}}}_{{{nz}}}"

        experiment_setup = {}
        experiment_setup["variants"] = {"package_manager": "spack"}

        # Number of processes in each dimension
        initial_p = [2, 2, 2]

        # Per-process size (in zones) in each dimension
        initial_n = [80, 80, 80]

        if self.spec.satisfies("experiment=single-node"):
            variables[px] = initial_p[0]
            variables[py] = initial_p[1]
            variables[pz] = initial_p[2]
            variables[nx] = initial_n[0]
            variables[ny] = initial_n[1]
            variables[nz] = initial_n[2]
        else:  # A scaling study
            input_params = {}
            if self.spec.satisfies("experiment=throughput"):
                variables[px] = initial_p[0]
                variables[py] = initial_p[1]
                variables[pz] = initial_p[2]
                scaling_variable = (nx, ny, nz)
                input_params[scaling_variable] = initial_n
            elif self.spec.satisfies("experiment=strong"):
                scaling_variable = (px, py, pz)
                input_params[scaling_variable] = initial_p
                variables[nx] = initial_n[0]
                variables[ny] = initial_n[1]
                variables[nz] = initial_n[2]
            elif self.spec.satisfies("experiment=weak"):
                scaling_variable = (px, py, pz)
                input_params[scaling_variable] = initial_p
                input_params[(nx, ny, nz)] = initial_n
            variables |= self.scale_experiment_variables(
                input_params,
                int(self.spec.variants["scaling-factor"][0]),
                int(self.spec.variants["scaling-iterations"][0]),
                scaling_variable,
            )

        # TODO: Add explanation
        experiment_setup["variables"] = variables

        return {
            self.spec.name: {
                "workloads": {
                    self.workload: {
                        "experiments": {
                            experiment_name: experiment_setup,
                        }
                    }
                }
            }
        }

    def compute_spack_section(self):
        app_name = self.spec.name

        # set package versions
        app_version = "develop"
        hypre_version = "2.31.0"

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"
        system_specs["lapack"] = "lapack"
        if self.spec.satisfies("programming_model=cuda"):
            system_specs["cuda_version"] = "{default_cuda_version}"
            system_specs["cuda_arch"] = "{cuda_arch}"
            system_specs["blas"] = "cublas-cuda"
        if self.spec.satisfies("programming_model=rocm"):
            system_specs["rocm_arch"] = "{rocm_arch}"
            system_specs["blas"] = "blas-rocm"

        # set package spack specs
        package_specs = {}
        if self.spec.satisfies("programming_model=cuda"):
            package_specs["cuda"] = {
                "pkg_spec": "cuda@{}+allow-unsupported-compilers".format(
                    system_specs["cuda_version"]
                ),
                "compiler": system_specs["compiler"],
            }
            package_specs[system_specs["blas"]] = (
                {}
            )  # empty package_specs value implies external package
        if self.spec.satisfies("programming_model=rocm"):
            package_specs[system_specs["blas"]] = (
                {}
            )  # empty package_specs value implies external package
        package_specs[system_specs["mpi"]] = (
            {}
        )  # empty package_specs value implies external package
        package_specs[system_specs["lapack"]] = (
            {}
        )  # empty package_specs value implies external package
        package_specs["hypre"] = {
            "pkg_spec": f"hypre@{hypre_version} +mpi+mixedint~fortran",
            "compiler": system_specs["compiler"],
        }
        package_specs[app_name] = {
            "pkg_spec": f"amg2023@{app_version} +mpi",
            "compiler": system_specs["compiler"],
        }

        caliper_package_specs = Caliper.compute_spack_section(self)
        if Caliper.is_enabled(self):
            package_specs["hypre"]["pkg_spec"] += "+caliper"
            package_specs[app_name]["pkg_spec"] += "+caliper"
        else:
            package_specs["hypre"]["pkg_spec"] += "~caliper"
            package_specs[app_name]["pkg_spec"] += "~caliper"

        if self.spec.satisfies("programming_model=openmp"):
            package_specs["hypre"]["pkg_spec"] += "+openmp"
            package_specs[app_name]["pkg_spec"] += "+openmp"
        elif self.spec.satisfies("programming_model=cuda"):
            package_specs["hypre"]["pkg_spec"] += "+cuda cuda_arch={}".format(
                system_specs["cuda_arch"]
            )
            package_specs[app_name]["pkg_spec"] += "+cuda cuda_arch={}".format(
                system_specs["cuda_arch"]
            )
        elif self.spec.satisfies("programming_model=rocm"):
            package_specs["hypre"]["pkg_spec"] += "+rocm amdgpu_target={}".format(
                system_specs["rocm_arch"]
            )
            package_specs[app_name]["pkg_spec"] += "+rocm amdgpu_target={}".format(
                system_specs["rocm_arch"]
            )

        return {
            "packages": {k: v for k, v in package_specs.items() if v}
            | caliper_package_specs["packages"],
            "environments": {
                app_name: {
                    "packages": list(package_specs.keys())
                    + list(caliper_package_specs["packages"].keys())
                }
            },
        }
