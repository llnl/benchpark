# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from ramble.modkit import *

_default_mode = "time"


class Caliper(BasicModifier):
    """Define a modifier for Caliper"""

    name = "caliper"

    tags("profiler", "performance-analysis")

    maintainers("pearce8")

    _cali_datafile = "{experiment_run_dir}/{experiment_name}.cali"

    def determine_cali_config(self):
        if self.app.name != "raja-perf":
            self.env_var_modification(
                "CALI_CONFIG",
                "spot(output={}{})".format(_cali_datafile, "${CALI_CONFIG_MODE}"),
                method="set",
                modes=[_default_mode],
            )
        else:
            pass

    def inherit_from_application(self, app):
        super().inherit_from_application(app)
        self.app = app

        self.determine_cali_config()

        self.add_modes()

    def add_mode(self, mode_name, mode_option, description, app):
        self.mode(
            name=mode_name,
            description=description,
        )

        self.env_var_modification(
            "CALI_CONFIG_MODE",
            mode_option,
            method="append",
            separator="," if app.name != "raja-perf" else "",
            modes=[mode_name],
        )

    def add_modes(self):
        self.add_mode(
            mode_name=_default_mode,
            mode_option="time.exclusive",
            description="Platform-independent collection of time (default mode)",
            app=self.app,
        )

        self.add_mode(
            mode_name="mpi",
            mode_option="profile.mpi",
            description="Profile MPI functions",
            app=self.app,
        )

        self.add_mode(
            mode_name="cuda",
            mode_option="profile.cuda",
            description="Profile CUDA API functions",
            app=self.app,
        )

        self.add_mode(
            mode_name="topdown-counters-all",
            mode_option="topdown-counters.all",
            description="Raw counter values for Intel top-down analysis (all levels)",
            app=self.app,
        )

        self.add_mode(
            mode_name="topdown-counters-toplevel",
            mode_option="topdown-counters.toplevel",
            description="Raw counter values for Intel top-down analysis (top level)",
            app=self.app,
        )

        self.add_mode(
            mode_name="topdown-all",
            mode_option="topdown.all",
            description="Top-down analysis for Intel CPUs (all levels)",
            app=self.app,
        )

        self.add_mode(
            mode_name="topdown-toplevel",
            mode_option="topdown.toplevel",
            description="Top-down analysis for Intel CPUs (top level)",
            app=self.app,
        )

    archive_pattern(_cali_datafile)

    software_spec("caliper", pkg_spec="caliper")

    required_package("caliper")
