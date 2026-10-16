import os
import shlex
import subprocess

import spack.util.spack_yaml as syaml
from ramble.modkit import *
from ramble.util.logger import logger


class CompilerAttribution(BasicModifier):
    """Define a modifier for compiler attribution plugin runtime setup."""

    name = "compiler_attribution"

    tags("profiler", "performance-analysis", "compiler-analysis")

    maintainers("yejashi")

    mode(
        name="on",
        description="Collect compiler attribution plugin trace data",
    )

    default_mode("on")

    with when("package_manager_family=spack"):
        software_spec(
            "compiler_attribution_plugin",
            pkg_spec="compiler-attribution-plugin",
            inject_if_missing=True,
        )

    register_phase(
        "instrument_benchmark",
        pipeline="setup",
        run_before=["make_experiments"],
    )

    def _instrument_benchmark(self, workspace, app_inst=None):
        if workspace.dry_run:
            logger.msg("Skipping compiler attribution instrumentation in dry-run mode")
            return

        if app_inst is None:
            logger.die(
                "compiler_attribution requires an application instance during setup"
            )

        package_manager = app_inst.package_manager
        if package_manager is None or "spack" not in package_manager.name:
            logger.die(
                "compiler_attribution requires the spack package manager, "
                f"got '{getattr(package_manager, 'name', None)}'"
            )

        env_path = app_inst.expander.env_path

        cache_tupl = ("compiler-attribution", env_path)
        if workspace.check_cache(cache_tupl):
            return
        workspace.add_to_cache(cache_tupl)

        package_manager._software_create_env(workspace, app_inst)

        benchmark_spec = self._benchmark_spec(workspace, app_inst)

        self._run_spack(["-e", env_path, "install", "compiler-attribution-plugin"])
        plugin_prefix = self._run_spack(
            ["-e", env_path, "location", "-i", "compiler-attribution-plugin"],
            capture_output=True,
        ).stdout.strip()
        if not plugin_prefix:
            logger.die(
                "compiler_attribution could not locate compiler-attribution-plugin"
            )

        self._run_spack(
            ["-e", env_path, "install", "--only", "dependencies", benchmark_spec]
        )

        build_stage = self._first_absolute_build_stage(env_path)
        source_root = os.path.commonpath([build_stage, env_path])
        extraction_root = os.path.join(env_path, "compiler-attribution")
        os.makedirs(extraction_root, exist_ok=True)

        plugin_spec = self._plugin_spec(workspace, app_inst)
        inst_env = self._instrumented_env(
            plugin_prefix, extraction_root, source_root, plugin_spec
        )
        self._run_spack(
            [
                "-e",
                env_path,
                "install",
                "--yes-to-all",
                "--only",
                "package",
                "--overwrite",
                "--no-cache",
                "--dirty",
                benchmark_spec,
            ],
            env=inst_env,
        )

    def _benchmark_spec(self, workspace, app_inst):
        package = self._application_package(workspace, app_inst)
        software_envs = workspace.software_environments
        return package.spec_str(
            all_packages=software_envs._rendered_packages,
            compiler=False,
        )

    def _plugin_spec(self, workspace, app_inst):
        package = self._package_by_name(
            workspace, app_inst, "compiler_attribution_plugin"
        )
        if package is None:
            return ""

        software_envs = workspace.software_environments
        return package.spec_str(
            all_packages=software_envs._rendered_packages,
            compiler=False,
        )

    def _application_package(self, workspace, app_inst):
        app_names = {self._normalize_name(app_inst.expander.application_spec)}
        if getattr(app_inst, "name", None):
            app_names.add(self._normalize_name(app_inst.name))

        software_env = self._software_environment(workspace, app_inst)
        for package in software_env._packages:
            if self._normalize_name(package.name) in app_names:
                return package

        package_names = ", ".join(package.name for package in software_env._packages)
        logger.die(
            "compiler_attribution could not identify the benchmark root package "
            f"for application '{app_inst.expander.application_spec}' in software "
            f"environment '{software_env.name}'. Packages found: {package_names}"
        )

    def _package_by_name(self, workspace, app_inst, package_name):
        normalized_name = self._normalize_name(package_name)
        software_env = self._software_environment(workspace, app_inst)
        for package in software_env._packages:
            if self._normalize_name(package.name) == normalized_name:
                return package
        return None

    def _software_environment(self, workspace, app_inst):
        env_name = self._active_environment_name(app_inst)
        return workspace.software_environments.render_environment(
            env_name,
            app_inst.expander,
            app_inst.package_manager,
            require=True,
        )

    def _active_environment_name(self, app_inst):
        try:
            return app_inst.expander.expand_var_name("env_name")
        except Exception:
            return app_inst.expander.application_spec

    def _first_absolute_build_stage(self, env_path):
        output = self._run_spack(
            ["-e", env_path, "config", "get", "config"],
            capture_output=True,
        ).stdout
        config = syaml.load_config(output) or {}
        if "config" in config:
            config = config["config"] or {}

        build_stages = config.get("build_stage", [])
        if isinstance(build_stages, str):
            build_stages = [build_stages]

        for path in build_stages:
            expanded = os.path.expanduser(str(path))
            if os.path.isabs(expanded):
                return expanded

        logger.die(
            "compiler_attribution requires at least one absolute "
            "Spack config:build_stage path. Add an absolute build_stage "
            f"to the Spack config used by environment {env_path}."
        )

    def _instrumented_env(
        self, plugin_prefix, extraction_root, source_root, plugin_spec
    ):
        env = os.environ.copy()
        lib_dir = os.path.join(plugin_prefix, "lib")
        compile_flags = (
            f"-fpass-plugin={os.path.join(lib_dir, 'CompilerAttributionPlugin.so')} "
            "-mllvm -pass-remarks=.*"
        )
        if "+kru" in plugin_spec:
            compile_flags += " -mllvm -pass-remarks-analysis=kernel-resource-usage"

        link_flags = ""
        if "+association" in plugin_spec:
            runtime_path = os.path.join(lib_dir, "CaliperAssociationLib.so")
            link_flags = f"{runtime_path} -Wl,-rpath,{lib_dir} -Wl,--export-dynamic"

        for name in ("SPACK_CXXFLAGS", "CXXFLAGS", "HIPFLAGS"):
            self._append_flag(env, name, compile_flags)
        for name in ("SPACK_LDFLAGS", "LDFLAGS"):
            self._append_flag(env, name, link_flags)

        env["EXTRACTION_SRC_PATH"] = source_root
        env["EXTRACTION_OUT_PATH"] = extraction_root
        env["ASSOCIATION_SRC_PATH"] = source_root
        env["EXTRACTION_REMARK_COUNTS"] = self._variant_enabled(
            plugin_spec, "+remark_counts"
        )
        env["EXTRACTION_REMARK_DETAILS"] = self._variant_enabled(
            plugin_spec, "+remark_details"
        )
        env["EXTRACTION_KRU"] = self._variant_enabled(plugin_spec, "+kru")
        env["EXTRACTION_IR_METRICS"] = self._variant_enabled(plugin_spec, "+ir_metrics")
        env["EXTRACTION_PER_PASS_IR_METRICS"] = self._variant_enabled(
            plugin_spec, "+per_pass_ir_metrics"
        )
        return env

    def _run_spack(self, args, env=None, capture_output=False):
        cmd = ["spack"] + args
        logger.msg(f"compiler_attribution: running {shlex.join(cmd)}")
        try:
            return subprocess.run(
                cmd,
                check=True,
                text=True,
                env=env,
                capture_output=capture_output,
            )
        except subprocess.CalledProcessError as exc:
            logger.die(
                "compiler_attribution setup command failed: "
                f"{shlex.join(cmd)}\n{exc}"
            )

    @staticmethod
    def _append_flag(env, name, flag):
        if not flag:
            return
        current = env.get(name, "")
        env[name] = f"{current} {flag}".strip()

    @staticmethod
    def _variant_enabled(spec, variant):
        return "ON" if variant in spec else "OFF"

    @staticmethod
    def _normalize_name(name):
        return str(name).replace("_", "-").lower()

    executable_modifier("compiler_attribution")

    def compiler_attribution(self, executable_name, executable, app_inst=None):
        from ramble.util.executable import CommandExecutable

        trace_file = (
            "{experiment_run_dir}/{experiment_name}."
            f"{executable_name}.compiler_attribution.trace.jsonl"
        )
        extraction_dir = "{env_path}/compiler-attribution/extraction_plugin_output"
        pre_exec = [
            CommandExecutable(
                f"set-compiler-attribution-trace-{executable_name}",
                template=[
                    f"export TRACE_LOG_OUTPUT_PATH={trace_file}",
                    "export " f"COMPILER_ATTRIBUTION_EXTRACTION_DIR={extraction_dir}",
                ],
            )
        ]

        return pre_exec, []
