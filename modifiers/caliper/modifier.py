# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.modkit import *
import json

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

    # The filename for Caliper output data
    _cali_datafile = "{experiment_run_dir}/{experiment_name}.cali"

    # The filename for metadata forwarded from Benchpark to Caliper
    _caliper_metadata_file = "{experiment_run_dir}/{experiment_name}_metadata.json"

    _default_mode = "time"

    # Write out the metadata file once all variables are resolved
    register_phase('build_metadata', pipeline='setup', run_after=['make_experiments']) 

    add_mode(
        mode_name=_default_mode,
        mode_option="time.exclusive",
        description="Platform-independent collection of time (default mode)",
    )

    env_var_modification(
        "CALI_CONFIG",
        "spot(output={}{}),metadata(file={})".format(_cali_datafile, "${CALI_CONFIG_MODE}", _caliper_metadata_file),
        method="set",
        modes=[_default_mode],
    )

    add_mode(
        mode_name="mpi",
        mode_option="profile.mpi",
        description="Profile MPI functions",
    )

    add_mode(
        mode_name="cuda",
        mode_option="profile.cuda",
        description="Profile CUDA API functions",
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

    def _build_metadata(self, workspace, app_inst):
        ''' Write the caliper metadata to json '''
        # Load the Caliper metadata variable from ramble.yaml
        # experiment_metadata = self.expander.expand_var('caliper_metadata', typed=True, merge_used_stage=False)
        # Error: expand_var() got an unexpected keyword argument 'merge_used_stage'
        # TODO: How to get this from the ramble.yaml?
        experiment_metadata = self.expander.expand_var('caliper_metadata', typed=True)	
        #self.expander.flush_used_variables() 
        # Error: 'Expander' object has no attribute 'flush_used_variables'

        # Write to the Caliper metadata file    
        cali_metadata_file = self.expander.expand_var(self._caliper_metadata_file) 
        print(f"writing to %s", cali_metadata_file)
        with open(cali_metadata_file, "w") as f: 
            f.write(json.dumps(experiment_metadata)) 


    archive_pattern(_cali_datafile)

    software_spec("caliper", pkg_spec="caliper")

    required_package("caliper")
    