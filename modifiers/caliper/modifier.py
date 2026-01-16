# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import json

from ramble.modkit import *


def add_mode(mode_name, mode_option, description):
    mode(
        name=mode_name,
        description=description,
    )

    env_var_modification(
        "CALI_CONFIG_MODE",
        mode_option,
        method="append",
        separator=",",
        modes=[mode_name],
    )


class Caliper(BasicModifier):
    """Define a modifier for Caliper"""

    name = "caliper"

    tags("profiler", "performance-analysis")

    maintainers("pearce8")

    # The filename for metadata forwarded from Benchpark to Caliper
    _caliper_metadata_file = "{experiment_run_dir}/{experiment_name}_metadata.json"

    modifier_conflict("name_mode")

    _default_mode = "time"

    add_mode(
        mode_name=_default_mode,
        mode_option="time.exclusive,time.variance",
        description="Platform-independent collection of time (default mode)",
    )

    def modify_experiment(self, app):
        """If app has built-in Caliper configuration, do not set CALI_CONFIG.
        Config parameters are parsed out into SPOT_CONFIG and OTHER_CALI_CONFIG if the application still requires them.
        """
        SPOT_CONFIG = r"spot(${CALI_CONFIG_MODE})"
        OTHER_CALI_CONFIG = f'metadata(file={self._caliper_metadata_file}),metadata(file=/etc/node_info.json,keys="host.name,host.cluster,host.os")'

        if "builtin-caliper" not in app.tags:
            # Normal mode
            self.env_var_modification(
                "CALI_CONFIG",
                f"{SPOT_CONFIG},{OTHER_CALI_CONFIG}",
                method="set",
                modes=[self._default_mode],
            )
        else:
            # Set env vars in case application can use them
            self.env_var_modification(
                "SPOT_CONFIG",
                SPOT_CONFIG,
                method="set",
                modes=[self._default_mode],
            )
            self.env_var_modification(
                "OTHER_CALI_CONFIG",
                OTHER_CALI_CONFIG,
                method="set",
                modes=[self._default_mode],
            )

    add_mode(
        mode_name="mpi",
        mode_option="profile.mpi",
        description="Profile MPI functions",
    )

    add_mode(
        mode_name="cuda",
        mode_option="profile.cuda,cuda.gputime",
        description="Profile CUDA API functions, time spent on GPU",
    )

    add_mode(
        mode_name="rocm",
        mode_option="profile.hip,rocm.gputime",
        description="Profile HIP API functions, time spent on GPU",
    )

    add_mode(
        mode_name="topdown-counters-all",
        mode_option="topdown-counters.all",
        description="Raw counter values for Intel top-down analysis (all levels)",
    )

    add_mode(
        mode_name="topdown-counters-toplevel",
        mode_option="topdown-counters.toplevel",
        description="Raw counter values for Intel top-down analysis (top level)",
    )

    add_mode(
        mode_name="topdown-all",
        mode_option="topdown.all",
        description="Top-down analysis for Intel CPUs (all levels)",
    )

    add_mode(
        mode_name="topdown-toplevel",
        mode_option="topdown.toplevel",
        description="Top-down analysis for Intel CPUs (top level)",
    )

    # Write out the metadata file once all variables are resolved
    register_phase("build_metadata", pipeline="setup", run_after=["make_experiments"])

    def _build_metadata(self, workspace, app_inst):
        """Write the caliper metadata to json"""

        cali_metadata = {}

        # system metadata
        system_metadata = [
            "sys_cores_per_node",  # required
            "scheduler",  # required
            "rocm_arch",
            "cuda_arch",
            "sys_cores_os_reserved_per_node",
            "sys_cores_os_reserved_per_node_list",
            "sys_gpus_per_node",
            "sys_mem_per_node_GB",
            "system_site",
        ]
        for key in system_metadata:
            # Certain keys not required or may not be present
            if key in app_inst.variables.keys():
                cali_metadata[key] = app_inst.variables[key]

        # Load the Caliper metadata variable from ramble.yaml
        experiment_metadata = app_inst.expander.expand_var_name(
            "caliper_metadata", typed=True, merge_used_stage=False
        )
        app_inst.expander.flush_used_variable_stage()
        # rebuild dictionary with expanded variables
        for key, val in experiment_metadata.items():
            cali_metadata[key] = app_inst.expander.expand_var(val)

        # Write to the Caliper metadata file
        cali_metadata_file = self.expander.expand_var(self._caliper_metadata_file)
        with open(cali_metadata_file, "w") as f:
            f.write(json.dumps(cali_metadata))

    software_spec("caliper", pkg_spec="caliper")

    required_package("caliper")
