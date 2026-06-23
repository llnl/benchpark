# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import shlex
from ramble.pkg_man.builtin.spack import Spack
from ramble.pkgmankit import *
from ramble.util.command_runner import RunnerError
from ramble.util.logger import logger


class SpackReuse(Spack):
    """Spack package manager that preferentially reuses pre-installed packages.

    This package manager extends the standard 'spack' package manager by:
    1. Searching for already-installed packages using 'spack find'
    2. Adding concrete specs (with hashes) to the environment for found packages
    3. Falling back to abstract specs for packages that need installation

    This enables reusing pre-existing spack installations while still allowing
    new packages to be installed as needed.
    """

    name = "spack-reuse"

    def _software_create_env(self, workspace, app_inst=None):
        """Create the spack environment, preferring already-installed specs.

        Overrides the parent's _software_create_env to query for existing
        installations before generating the environment file.
        """

        logger.msg("Creating Spack environment (with reuse)")

        # Ignore externally active spack environment
        import os
        if "SPACK_ENV" in os.environ and not os.path.isdir(
            os.environ["SPACK_ENV"]
        ):
            _spack_vars = ["SPACK_ENV", "SPACK_ENV_VIEW"]
            for var in _spack_vars:
                os.environ.pop(var, None)

        # See if we cached this already, and if so return
        env_path = app_inst.expander.env_path
        if not env_path:
            raise PackageManagerError("Ramble env_path is set to None.")

        cache_tupl = ("spack-env", env_path)
        if workspace.check_cache(cache_tupl):
            logger.debug(f"{cache_tupl} already in cache.")
            return
        else:
            workspace.add_to_cache(cache_tupl)

        package_manager_config_dicts = [app_inst.package_manager_configs]
        for mod_inst in app_inst._modifier_instances:
            package_manager_config_dicts.append(
                mod_inst.package_manager_configs
            )

        for config_dict in package_manager_config_dicts:
            for _, config in config_dict.items():
                keep_config = app_inst.expander.satisfies(
                    config["when"], variant_set=self.experiment_variants()
                )
                if keep_config:
                    self.runner.add_config(config["config"])

        try:
            self.runner.set_dry_run(workspace.dry_run)
            self.runner.create_env(
                app_inst.expander.expand_var_name(self.keywords.env_path)
            )
            self.runner.activate()

            # Write auxiliary software files into created spack env.
            for name, contents in workspace.all_auxiliary_software_files():
                aux_file_path = app_inst.expander.expand_var(
                    os.path.join(
                        app_inst.expander.expansion_str(
                            self.keywords.env_path
                        ),
                        f"{name}",
                    )
                )
                self.runner.add_include_file(aux_file_path)
                with open(aux_file_path, "w+") as f:
                    f.write(app_inst.expander.expand_var(contents))

            env_context = app_inst.expander.expand_var_name(
                self.keywords.env_name
            )
            require_env = self.environment_required
            software_envs = workspace.software_environments
            software_env = software_envs.render_environment(
                env_context, app_inst.expander, self, require=require_env
            )

            if software_env is not None:
                if isinstance(software_env, ExternalEnvironment):
                    self.runner.copy_from_external_env(
                        software_env.external_env
                    )
                else:
                    # This is the key difference: check for installed packages first
                    for pkg_spec in software_envs.package_specs_for_environment(
                        software_env
                    ):
                        concrete_spec = self._find_installed_spec(pkg_spec)
                        if concrete_spec:
                            logger.msg(f"Reusing installed package: {concrete_spec}")
                            self.runner.add_spec(concrete_spec)
                        else:
                            logger.msg(f"Will install: {pkg_spec}")
                            self.runner.add_spec(pkg_spec)

                    self.runner.generate_env_file()

                added_packages = set(self.runner.added_packages())
                for pkg, conf in app_inst.required_packages.items():
                    if (
                        app_inst.expander.satisfies(
                            conf["when"],
                            variant_set=self.experiment_variants(),
                        )
                        and pkg not in added_packages
                    ):
                        logger.die(
                            f"Software spec {pkg} is not defined "
                            f"in environment {env_context}, but is "
                            f"required by the {self.name} application "
                            "definition"
                        )

                for mod_inst in app_inst._modifier_instances:
                    for pkg, conf in mod_inst.required_packages.items():
                        if (
                            app_inst.expander.satisfies(
                                conf["when"],
                                variant_set=self.experiment_variants(
                                    include_modifier=mod_inst
                                ),
                            )
                            and pkg not in added_packages
                        ):
                            logger.die(
                                f"Software spec {pkg} is not defined "
                                f"in environment {env_context}, but is "
                                f"required by the {mod_inst.name} modifier "
                                "definition"
                            )

                self.runner.deactivate()

        except RunnerError as e:
            logger.die(e)

    def _find_installed_spec(self, pkg_spec):
        """Check if a spec is already installed and return concrete spec if found.

        Uses a "softened" search that looks for any installed package matching
        the package name, rather than requiring exact variant/version matches.

        Args:
            pkg_spec (str): The abstract package spec to search for

        Returns:
            str: Concrete spec with hash if found, None otherwise
        """
        if self.runner.dry_run:
            return None

        # Use spack's library API to query installed packages
        import spack.spec
        import spack.store

        # Parse the requested spec
        requested_spec = spack.spec.Spec(pkg_spec)
        pkg_name = requested_spec.name

        logger.debug(f"Searching for installed package: {pkg_name}")

        # Query the spack database for installed specs matching this package name
        installed_specs = spack.store.STORE.db.query(pkg_name)

        if not installed_specs:
            logger.debug(f"No installed package found for: {pkg_name}")
            return None

        # TODO: When multiple installs exist, pick the one that best matches
        # the requested_spec's variants/version using spec.satisfies() or
        # a custom scoring function. For now, take first.
        chosen_spec = installed_specs[0]

        # Format as concrete spec with hash for spack environment
        concrete_spec_str = f"{chosen_spec.name}@{chosen_spec.version}/{chosen_spec.dag_hash(7)}"
        logger.debug(f"Found installed spec: {concrete_spec_str}")

        return concrete_spec_str
