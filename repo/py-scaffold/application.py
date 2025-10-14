# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import yaml

from ramble.appkit import *


class PyScaffold(ExecutableApplication):
    """Scaffold benchmark"""

    name = "scaffold"

    tags = ["python"]

    # Add system logic to determine spec whether rocm or cuda system here in app.py
    #pip_spec = "{package_path}[rocmwci]"

    register_phase("prepend_library_path", pipeline="setup", run_before=["make_experiments"])

    def _prepend_library_path(self, workspace, app_inst=None):
        """Function to prepend to LD_LIBRARY_PATH, can't do in spack because python_platlib points to wrong site-packages dir"""
        # paths = []
        # dic = yaml.safe_load(workspace._auxiliary_software_files['compilers.yaml'])
        # compilers = list(dic.values())[0]
        # for compiler in compilers:
        #     env = compiler["compiler"]["environment"]
        #     if env != {}:
        #         paths.append(env["prepend_path"]["LD_LIBRARY_PATH"])
        # app_inst.variables["ld_paths"] = ":".join(paths)
        # print(self.__dict__)
        # print(workspace.__dict__)
        # print(app_inst.__dict__)
        paths = []
        # if cuda
        if "cuda_arch" in app_inst.variables.keys():
            # Avoid libcudnn_graph.so error (unecessary if cuX_full, necessary if cuX wheel)
            paths.append("{env_path}/.venv/lib64/python3.11/site-packages/nvidia/cudnn/lib")

        app_inst.variables["rocm_mods"] = ""
        if "rocm_arch" in app_inst.variables.keys():
            app_inst.variables["rocm_mods"] = "module load rccl/fast-env-slows-mpi\nexport MPICH_GPU_SUPPORT_ENABLED=0\n"

        # if caliper
        # Avoid libcaffe2_nvrtc.so
        paths.append("{env_path}/.venv/lib64/python3.11/site-packages/torch/lib")

        app_inst.variables["ld_paths"] = ":".join(paths)

    # register_phase("install_python_packages", pipeline="setup", run_before=["make_experiments"])

    # def _install_python_packages(self, workspace, app_inst=None):
    #     # activate ramble env python

    #     # model = self.system["provides"] # "cuda" or "rocm", depends on package defining these in pyproject.toml

    #     #             vvvvvvvvvvvvvv depends on local install
    #     # pip install {package_path}[model]

    software_spec("scaffold", None)

    # TODO: Figure out MPICH_GPU_SUPPORT_ENABLED=0, disabling GTL otherwise linker error.
    executable(
        "modules",
        "{rocm_mods}export LD_LIBRARY_PATH={ld_paths}:$LD_LIBRARY_PATH",
    )
    # executable(
    #     "pip",
    #     "pip install -r {package_path}requirements.txt\npip install torch==2.8.0+rocm642",
    #     use_mpi=False,
    # )

    # # matrix
    # executable(
    #     "modules",
    #     "export LD_LIBRARY_PATH=/usr/WS1/mckinsey/bp_scaffold_spack/wkp3/py-scaffold-sp-mat/matrix/workspace/software/spack-pip/py-scaffold/.venv/lib/python3.11/site-packages/nvidia/cudnn/lib/:$LD_LIBRARY_PATH # libcudnn_graph.so\nexport LD_LIBRARY_PATH=/usr/WS1/mckinsey/bp_scaffold_spack/wkp3/py-scaffold-sp-mat/matrix/workspace/software/spack-pip/py-scaffold/.venv/lib/python3.11/site-packages/torch/lib:$LD_LIBRARY_PATH",
    # )
    # # tuo
    # executable(
    #     "modules",
    #     "export LD_LIBRARY_PATH=/usr/WS1/mckinsey/bp_scaffold_spack/wkp2/py-scaffold-sp/tuolumne/workspace/software/spack-pip/py-scaffold/ramble/lib/python3.11/site-packages/torch/lib:$LD_LIBRARY_PATH  # libcaffe2_nvrtc.so\nexport SPINDLE_FLUXOPT=off  # specific issue with WCI wheel\nexport LD_LIBRARY_PATH=/opt/cray/pe/cce/20.0.0/cce-clang/x86_64/lib/:$LD_LIBRARY_PATH  # torch libmagma error\nexport LD_LIBRARY_PATH=/opt/cray/pe/cce/20.0.0/cce/x86_64/lib/:$LD_LIBRARY_PATH  # libmodules.so.1",
    # )
    executable(
        "generate",
        "scaffold generate_fractals -c {package_path}ScaFFold/configs/benchmark_default.yml --problem-scale {problem_scale}",
        use_mpi=True,
    )
    executable(
        "run",
        "scaffold benchmark -c {package_path}ScaFFold/configs/benchmark_default.yml --problem-scale {problem_scale}",
        use_mpi=True,
    )

    workload("sweep", executables=["modules",
                                   # "pip",
                                    "generate",
                                    "run"])
