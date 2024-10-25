from benchpark.directives import variant
from benchpark.experiment import Experiment
from benchpark.openmp import OpenMPExperiment
from benchpark.cuda import CudaExperiment
from benchpark.rocm import ROCmExperiment
from benchpark.expr.builtin.caliper import Caliper


class Amg2023(OpenMPExperiment, CudaExperiment, ROCmExperiment, Caliper, Experiment):
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

    variant(
        "version",
        default="develop",
        description="app version",
    )

    # requires("system+papi", when(caliper=topdown*))

    # TODO: Support list of 3-tuples
    # variant(
    #     "p",
    #     description="value of p",
    # )

    # TODO: Support list of 3-tuples
    # variant(
    #     "n",
    #     description="value of n",
    # )

    def make_experiment_example(self):
        self.add_experiment_name_prefix("example")

        if self.spec.satisfies("openmp=oui"):
            # TODO: Support variants
            n = ["55", "110"]
            self.add_experiment_variable("n_nodes", ["1", "2"], True)
            self.add_experiment_variable("n_ranks", "8", True)
            self.add_experiment_variable("n_threads_per_proc", ["4", "6", "12"], True)
        elif self.spec.satisfies("cuda=oui"):
            # TODO: Support variants
            n = ["10", "20"]
            self.add_experiment_variable("n_gpus", "8", True)
        elif self.spec.satisfies("rocm=oui"):
            # TODO: Support variants
            n = ["110", "220"]
            self.add_experiment_variable("n_gpus", "8", True)
        else:
            raise NotImplementedError(
                "Unsupported programming_model. Only openmp, cuda and rocm are supported"
            )

        # TODO: Support variant
        p = "2"
        self.add_experiment_variable("px", p, True)
        self.add_experiment_variable("py", p, True)
        self.add_experiment_variable("pz", p, True)

        self.add_experiment_variable("nx", n, True)
        self.add_experiment_variable("ny", n, True)
        self.add_experiment_variable("nz", n, True)

        self.zip_experiment_variables("size", ["nx", "ny", "nz"])

        if self.spec.satisfies("openmp=oui"):
            self.matrix_experiment_variables(["size", "n_nodes", "n_threads_per_proc"])
        if self.spec.satisfies("cuda=oui") or self.spec.satisfies("rocm=oui"):
            self.matrix_experiment_variables("size")

        if self.spec.satisfies("openmp=oui"):
            self.add_experiment_exclude(
                "{n_threads_per_proc} * {n_ranks} > {n_nodes} * {sys_cores_per_node}"
            )

    def compute_applications_section(self):
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

    def compute_spack_section(self):
        # get package version
        app_version = self.spec.variants["version"][0]

        # get system config options
        # TODO: Get compiler/mpi/package handles directly from system.py
        system_specs = {}
        system_specs["compiler"] = "default-compiler"
        system_specs["mpi"] = "default-mpi"
        system_specs["lapack"] = "lapack"
        if self.spec.satisfies("cuda=oui"):
            system_specs["cuda_version"] = "{default_cuda_version}"
            system_specs["cuda_arch"] = "{cuda_arch}"
            system_specs["blas"] = "cublas-cuda"
        if self.spec.satisfies("rocm=oui"):
            system_specs["rocm_arch"] = "{rocm_arch}"
            system_specs["blas"] = "blas-rocm"

        # set package spack specs
        if self.spec.satisfies("cuda=oui") or self.spec.satisfies("rocm=oui"):
            # empty package_specs value implies external package
            self.add_spack_spec(system_specs["blas"])
        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["mpi"])
        # empty package_specs value implies external package
        self.add_spack_spec(system_specs["lapack"])

        self.add_spack_spec(
            self.name, [f"amg2023@{app_version} +mpi", system_specs["compiler"]]
        )
