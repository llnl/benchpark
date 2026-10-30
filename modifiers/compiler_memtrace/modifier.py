# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import copy as python_copy
import fnmatch
import hashlib
import json
import os
import re
import shlex
import subprocess
from pathlib import Path

import spack.util.spack_yaml as syaml
from ramble.modkit import *
from ramble.util.logger import logger


class CompilerMemtrace(BasicModifier):
    """Build and run separate HIP memory-operation count and trace executables."""

    name = "compiler_memtrace"
    tags("profiler", "performance-analysis", "compiler-analysis")
    modifier_conflict("name_only")

    mode(
        name="baseline", description="Catalog memory operations without instrumentation"
    )
    mode(name="count", description="Build and run memory-operation counts")
    mode(
        name="trace",
        description="Build count and trace executables and run them in order",
    )
    default_mode("trace")

    for option, default, description in (
        (
            "executables",
            "run",
            "Space-separated executable name patterns to instrument",
        ),
        ("addrspaces", "1:0", "Colon-separated AMDGPU address spaces to catalog"),
        (
            "prevectorize",
            "0",
            "Merge adjacent memory operations before instrumentation (0 or 1)",
        ),
        (
            "waves_per_eu",
            "",
            "Optional occupancy file, one mangled kernel and waves/EU per line",
        ),
        (
            "timing",
            "0",
            "Record timing and placement in trace mode on gfx940 or newer (0 or 1)",
        ),
    ):
        modifier_variable(
            f"compiler_memtrace_{option}",
            default=default,
            description=description,
            modes=["baseline", "count", "trace"],
        )

    with when("package_manager_family=spack"):
        software_spec(
            "memtrace_llvm",
            pkg_spec="memtrace-llvm +runtime +python",
            inject_if_missing=True,
        )

    def _make_experiments(self, workspace):
        # Ramble calls this hook immediately before writing the application
        # script, after its package manager has installed the ordinary roots.
        # Keep that concretization stable before adding instrumented installs
        # to Spack's reuse candidates. Modifier phase edges cannot reference
        # package-manager phases in the pinned Ramble version.
        self._build_memtrace(workspace, self.app_inst)

    def _value(self, name):
        return self.expander.expand_var_name(f"compiler_memtrace_{name}")

    def _options(self):
        options = {
            name: str(self._value(name))
            for name in ("addrspaces", "prevectorize", "waves_per_eu", "timing")
        }
        for name in ("prevectorize", "timing"):
            if options[name] not in ("0", "1"):
                logger.die(f"compiler_memtrace_{name} must be 0 or 1")
        if not re.fullmatch(r"\d+(?::\d+)*", options["addrspaces"]):
            logger.die(
                "compiler_memtrace_addrspaces must contain colon-separated integers"
            )
        if options["timing"] == "1" and self._usage_mode != "trace":
            logger.die("compiler_memtrace_timing=1 requires trace mode")
        if options["waves_per_eu"]:
            path = Path(options["waves_per_eu"]).expanduser().resolve()
            if not path.is_file():
                logger.die(f"compiler_memtrace occupancy file does not exist: {path}")
            options["waves_per_eu"] = str(path)
            options["occupancy_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        return options

    def _build_root(self, app_inst, options):
        # Separate options and modes must never overwrite another experiment's build.
        key = hashlib.sha256(
            json.dumps([self._usage_mode, options], sort_keys=True).encode()
        ).hexdigest()[:16]
        return Path(app_inst.expander.env_path) / "compiler-memtrace" / key

    def _benchmark_package(self, workspace, app_inst):
        environments = workspace.software_environments
        env_name = app_inst.expander.expand_var_name("env_name")
        environment = environments.render_environment(
            env_name, app_inst.expander, app_inst.package_manager, require=True
        )
        names = {
            str(name).replace("_", "-").lower()
            for name in (app_inst.name, app_inst.expander.application_spec)
        }
        for package in environment._packages:
            if package.name.replace("_", "-").lower() in names:
                return package
        logger.die(
            "compiler_memtrace cannot identify the application's Spack root package"
        )

    def _run_spack(self, args, env=None):
        command = ["spack"] + [str(arg) for arg in args]
        env = dict(os.environ if env is None else env)
        # Interactive startup hooks can corrupt machine-readable stdout.
        env.pop("PYTHONSTARTUP", None)
        logger.msg(f"compiler_memtrace: running {shlex.join(command)}")
        try:
            return subprocess.run(
                command, check=True, text=True, env=env, stdout=subprocess.PIPE
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.die(
                f"compiler_memtrace command failed: {shlex.join(command)}\n{exc}\n"
                f"{getattr(exc, 'stdout', '') or ''}"
            )

    def _check_reader(self, plugin):
        command = [
            plugin["python"],
            str(Path(self._file_path).resolve().with_name("check_reader.py")),
            *plugin["reader_paths"],
        ]
        env = os.environ.copy()
        preload = plugin.get("reader_preload", [])
        if preload:
            env["LD_PRELOAD"] = " ".join(preload + env.get("LD_PRELOAD", "").split())
        result = subprocess.run(command, capture_output=True, text=True, env=env)
        if result.returncode:
            logger.die(
                "compiler_memtrace reader check failed before benchmark builds. "
                "Check the memtrace-llvm Python/NumPy dependencies.\n"
                + result.stdout
                + result.stderr
            )

    def _use_builtin_numpy(self, env_path):
        helper = Path(self._file_path).resolve().with_name("spack_env.py")
        output = self._run_spack(["-e", env_path, "python", helper, "use-builtin-numpy"])
        if output:
            logger.msg(output)

    def _root_info(self, env_path, name):
        # Query the active environment with its own Spack, not Ramble's older
        # bundled Spec implementation (which cannot parse modern compiler edges).
        helper = Path(self._file_path).resolve().with_name("spack_env.py")
        output = self._run_spack(["-e", env_path, "python", helper, "root-info", name])
        try:
            return json.loads(output)
        except json.JSONDecodeError as exc:
            logger.die(
                f"compiler_memtrace: invalid JSON metadata for {name} "
                f"in Spack environment {env_path}: {exc}\n"
                f"Spack stdout: {output!r}"
            )

    def _install_root(self, env_path, spec, env):
        output = self._run_spack(
            [
                "-e",
                env_path,
                "install",
                "--only",
                "package",
                "--no-cache",
                "--keep-stage",
                "--dont-restage",
                "--dirty",
                spec,
            ],
            env=env,
        )
        if output:
            logger.msg(output)

    @staticmethod
    def _validate_catalogs(catalogs, source, mode, target):
        source = Path(source).resolve()
        for path in Path(catalogs).rglob("*.device.json"):
            try:
                data = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError) as exc:
                logger.die(f"compiler_memtrace cannot read catalog {path}: {exc}")
            metadata = data.get("Metadata", {})
            module = Path(metadata.get("ModuleName", ""))
            if (
                metadata.get("Mode") == mode
                and metadata.get("TargetCPU") == target
                and metadata.get("OpCount", 0) > 0
                and module.is_absolute()
                and source in module.resolve().parents
            ):
                return
        logger.die(
            f"compiler_memtrace build produced no benchmark memory-operation catalogs "
            f"for mode={mode}, target={target}, source={source}: {catalogs}"
        )

    @staticmethod
    def _split_root_spec(spec):
        """Keep new root flags ahead of dependency and compiler constraints."""
        quote = None
        escaped = False
        for index, char in enumerate(spec):
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif quote:
                if char == quote:
                    quote = None
            elif char in ("'", '"'):
                quote = char
            elif char in ("^", "%"):
                return spec[:index].rstrip(), spec[index:]
        return spec, ""

    @staticmethod
    def _instrumentation_flags(plugin_prefix, mode, options):
        library = Path(plugin_prefix) / "lib"
        compile_flags = [
            "-g",
            f"-fpass-plugin={shlex.quote(str(library / 'MemTracePlugin.so'))}",
        ]
        if mode != "baseline":
            compile_flags += [
                f"-DMEMTRACE_{mode.upper()}",
                "-include",
                shlex.quote(str(Path(plugin_prefix) / "include/memtrace_device.h")),
            ]
        if mode == "trace" and options["timing"] == "1":
            compile_flags.append("-DMEMTRACE_TIMING")
        link_flags = [
            "-Wl,--push-state,--no-as-needed",
            shlex.quote(str(library / "libmemtrace_runtime.so")),
            "-Wl,--pop-state",
            f"-Wl,-rpath,{shlex.quote(str(library))}",
        ]
        return compile_flags, link_flags

    @staticmethod
    def _instrumented_spec(
        benchmark, plugin_prefix, mode, options, original_flags, context="", cmake=False
    ):
        # Only these two flag fields are replaced; retain the original values.
        benchmark, dependencies = CompilerMemtrace._split_root_spec(benchmark)
        benchmark = re.sub(
            r"""(?<!\S)(?:cxxflags|ldflags)=(?:'[^']*'|"[^"]*"|\S+)""", "", benchmark
        ).strip()
        compile_flags, link_flags = CompilerMemtrace._instrumentation_flags(
            plugin_prefix, mode, options
        )
        if cmake:
            # CMake's HIP compiler probes use --cuda-host-only. The device
            # header adds a device variable and therefore an undefined fatbin
            # to those probes. Apply instrumentation to directory targets below.
            compile_flags, link_flags = [], []
        compile_flags = list(original_flags.get("cxxflags", [])) + compile_flags
        link_flags += list(original_flags.get("ldflags", []))
        # Compile-time options participate in the Spack hash, even though the
        # pass reads them from the build environment rather than these defines.
        signature = hashlib.sha256(
            json.dumps(
                [options, context, mode, plugin_prefix, cmake], sort_keys=True
            ).encode()
        ).hexdigest()[:16]
        compile_flags.append(f"-DBENCHPARK_MEMTRACE_CONFIG={signature}")
        return (
            f"{benchmark} cxxflags={json.dumps(' '.join(compile_flags))} "
            f"ldflags={json.dumps(' '.join(link_flags))} {dependencies}"
        ).strip()

    @staticmethod
    def _configure_cmake(source, cmake_root, build_env, plugin_prefix, mode, options):
        """Instrument targets in the benchmark's staged CMake source tree."""
        source = Path(source).resolve()
        root = (source / cmake_root).resolve()
        if root != source and source not in root.parents:
            logger.die(f"compiler_memtrace CMake root is outside its stage: {root}")
        cmakelists = root / "CMakeLists.txt"
        if not cmakelists.is_file():
            logger.die(f"compiler_memtrace cannot find {cmakelists}")
        compile_flags, link_flags = CompilerMemtrace._instrumentation_flags(
            plugin_prefix, mode, options
        )

        def quote(value):
            delimiter = "="
            while f"]{delimiter}]" in value:
                delimiter += "="
            return f"[{delimiter}[{value}]{delimiter}]"

        config = Path(build_env) / "memtrace.cmake"
        config.write_text(
            "# Generated by Benchpark compiler_memtrace.\n"
            "# Directory options reach build targets, but not try_compile probes.\n"
            "add_compile_options(\n  "
            + quote(
                "$<$<COMPILE_LANGUAGE:CXX,HIP>:SHELL:" + " ".join(compile_flags) + ">"
            )
            + "\n)\nadd_link_options(\n  "
            + quote("SHELL:" + " ".join(link_flags))
            + "\n)\n"
        )
        begin = "# BEGIN Benchpark compiler_memtrace\n"
        end = "# END Benchpark compiler_memtrace\n"
        text = cmakelists.read_text()
        if text.startswith(begin):
            text = text.split(end, 1)[1]
        cmakelists.write_text(
            begin + f"include({quote(str(config.resolve()))})\n" + end + text
        )

    def _write_build_environment(self, parent, destination, spec):
        with (parent / "spack.yaml").open() as stream:
            manifest = syaml.load_config(stream)
        manifest = python_copy.deepcopy(manifest)
        config = manifest["spack"]
        config["specs"] = [spec]
        config["view"] = False
        config.pop("definitions", None)
        # Resolve included configuration before moving the manifest to a child.
        # Spack handles URLs and absolute includes directly.
        includes = []
        for entry in config.get("include", []):
            if not isinstance(entry, str):
                logger.die(
                    "compiler_memtrace currently requires string Spack include paths"
                )
            if (
                not os.path.isabs(entry)
                and "://" not in entry
                and not entry.startswith("$")
            ):
                entry = str((parent / entry).resolve())
            includes.append(entry)
        if includes:
            config["include"] = includes
        destination.mkdir(parents=True, exist_ok=True)
        with (destination / "spack.yaml").open("w") as stream:
            syaml.dump_config(manifest, stream)

    def _build_memtrace(self, workspace, app_inst=None):
        if (
            app_inst is None
            or app_inst.package_manager is None
            or app_inst.package_manager.name != "spack"
        ):
            logger.die("compiler_memtrace requires the spack package manager")
        options = self._options()
        workload = app_inst.get_workload(app_inst.expander.workload_name)
        patterns = str(self._value("executables")).split()
        if not any(
            fnmatch.fnmatchcase(name, pattern)
            for name in workload.executables
            for pattern in patterns
        ):
            logger.die(
                "No workload executable matches compiler_memtrace_executables="
                + " ".join(patterns)
            )
        if any(
            mod["name"].replace("-", "_") == "compiler_attribution"
            for mod in app_inst.modifiers
        ):
            logger.die(
                "compiler_memtrace and compiler_attribution require separate experiments"
            )
        build_root = self._build_root(app_inst, options)
        self._builds_file = str(build_root / "builds.json")
        self._python = "python3"
        if workspace.dry_run:
            logger.msg("Skipping compiler_memtrace builds in dry-run mode")
            return

        cache_key = ("compiler-memtrace", str(build_root))
        if workspace.check_cache(cache_key):
            with open(self._builds_file) as stream:
                self._python = json.load(stream)["python"]
            return

        parent = Path(app_inst.expander.env_path)
        app_inst.package_manager._software_create_env(workspace, app_inst)
        self._run_spack(["-e", parent, "concretize"])
        self._use_builtin_numpy(parent)
        package = self._benchmark_package(workspace, app_inst)
        benchmark = package.spec_str(
            all_packages=workspace.software_environments._rendered_packages,
            compiler=False,
        )
        # The rendered package key may differ from the actual Spack package name.
        name = re.match(r"[\w-]+", benchmark).group()
        original = self._root_info(parent, name)
        targets = original.get("targets", [])
        if not original["rocm"] or len(targets) != 1 or targets[0] == "none":
            logger.die(
                "compiler_memtrace requires a +rocm benchmark with one amdgpu_target"
            )
        if options["timing"] == "1" and not re.fullmatch(
            r"gfx(?:94[0-9]|95[0-9])", targets[0]
        ):
            logger.die(
                "compiler_memtrace timing requires a supported gfx94x or gfx95x target"
            )

        self._run_spack(["-e", parent, "install", "memtrace-llvm"])
        plugin = self._root_info(parent, "memtrace-llvm")
        self._check_toolchain(original, plugin)
        self._check_reader(plugin)
        builds = {
            "original": original["prefix"],
            "python": plugin["python"],
            "reader_paths": plugin["reader_paths"],
            "reader_preload": plugin["reader_preload"],
            "prefixes": {},
            "options": options,
        }
        self._python = plugin["python"]
        modes = (
            ("count", "trace") if self._usage_mode == "trace" else (self._usage_mode,)
        )
        occupancy = None
        if options["waves_per_eu"]:
            build_root.mkdir(parents=True, exist_ok=True)
            occupancy = build_root / "waves-per-eu.txt"
            occupancy.write_bytes(Path(options["waves_per_eu"]).read_bytes())
        for mode in modes:
            build_env = build_root / mode
            spec = self._instrumented_spec(
                benchmark,
                plugin["prefix"],
                mode,
                options,
                original["flags"],
                context=str(build_root),
                cmake="cmake_root" in original,
            )
            self._write_build_environment(parent, build_env, spec)
            self._run_spack(["-e", build_env, "concretize", "--force"])
            built = self._root_info(build_env, name)
            self._check_toolchain(built, plugin)
            if built.get("targets") != targets:
                logger.die("compiler_memtrace build changed the benchmark's GPU target")
            self._run_spack(
                ["-e", build_env, "install", "--only", "dependencies", spec]
            )
            self._run_spack(["-e", build_env, "stage", spec])
            source = self._run_spack(
                ["-e", build_env, "location", "--source-dir", spec]
            )
            if "cmake_root" in built:
                self._configure_cmake(
                    source,
                    built["cmake_root"],
                    build_env,
                    plugin["prefix"],
                    mode,
                    options,
                )
            catalogs = build_env / "catalogs"
            catalogs.mkdir(exist_ok=True)
            env = os.environ.copy()
            env.update(
                MEMTRACE_SRC_PATH=source,
                MEMTRACE_OUT_PATH=str(catalogs),
                MEMTRACE_ADDRSPACES=options["addrspaces"],
                MEMTRACE_PREVECTORIZE=options["prevectorize"],
            )
            # CMake's native HIP language initializes CMAKE_HIP_FLAGS from HIPFLAGS.
            # Spack stores flags with arguments (e.g. '-include header') as
            # single strings. Preserve those groups as shell words, not one argv.
            env["HIPFLAGS"] = " ".join(built["flags"].get("cxxflags", []))
            env.pop("MEMTRACE_WAVES_PER_EU", None)
            if occupancy:
                env["MEMTRACE_WAVES_PER_EU"] = str(occupancy)
            # Spack otherwise destroys the prepared stage before configuring,
            # removing the CMake include added above. --keep-stage alone only
            # preserves the stage after a successful installation.
            self._install_root(build_env, spec, env)
            self._validate_catalogs(catalogs, source, mode, targets[0])
            builds["prefixes"][mode] = built["prefix"]
        temporary = build_root / "builds.json.tmp"
        temporary.write_text(json.dumps(builds, indent=2) + "\n")
        temporary.replace(self._builds_file)
        workspace.add_to_cache(cache_key)

    @staticmethod
    def _check_toolchain(benchmark, plugin):
        if benchmark["compiler"] != plugin["compiler"]:
            logger.die(
                "compiler_memtrace: benchmark and memtrace-llvm must use the same C++ compiler"
            )
        if benchmark.get("hip") != plugin.get("hip"):
            logger.die(
                "compiler_memtrace: benchmark and runtime must use the same HIP installation"
            )

    executable_modifier("compiler_memtrace")

    def compiler_memtrace(self, executable_name, executable, app_inst=None):
        from ramble.util.executable import CommandExecutable

        if not any(
            fnmatch.fnmatchcase(executable_name, pattern)
            for pattern in str(self._value("executables")).split()
        ):
            return [], []
        options = self._options()
        builds_file = getattr(
            self,
            "_builds_file",
            str(self._build_root(app_inst, options) / "builds.json"),
        )
        python = getattr(self, "_python", "python3")
        runner = str(Path(self._file_path).resolve().parent / "run.py")
        templates = executable.template
        if isinstance(templates, str):
            templates = [templates]
        if len(templates) != 1:
            logger.die(
                "compiler_memtrace requires one benchmark command per executable"
            )
        if executable.run_in_background:
            logger.die("compiler_memtrace requires foreground benchmark commands")
        # Prefixing a compound shell command would leave some processes untraced.
        lexer = shlex.shlex(templates[0], posix=True, punctuation_chars=";&|<>")
        lexer.whitespace_split = True
        if any(token in (";", "&&", "||", "|", "&", ">", ">>", "<") for token in lexer):
            logger.die(
                "compiler_memtrace requires a direct benchmark command, without shell operators"
            )

        output = f"{{experiment_run_dir}}/compiler_memtrace.{executable_name}.XXXXXX"
        pre = [
            CommandExecutable(
                f"prepare-memtrace-{executable_name}",
                template=[
                    f"export BENCHPARK_MEMTRACE_RUN=$(mktemp -d {shlex.quote(output)})",
                    'test -n "$BENCHPARK_MEMTRACE_RUN" || exit 1',
                ],
            )
        ]

        def wrapped(mode):
            flags = " --timing" if mode == "trace" and options["timing"] == "1" else ""
            ranks = "{n_ranks}" if executable.mpi else "1"
            return (
                f"{shlex.quote(python)} {shlex.quote(runner)} --builds {shlex.quote(builds_file)} "
                f'--mode {mode} --output "$BENCHPARK_MEMTRACE_RUN" --ranks {ranks}{flags} -- {templates[0]}'
            )

        if self._usage_mode == "trace":
            count = python_copy.deepcopy(executable)
            count.name = f"count-memtrace-{executable_name}"
            count.template = [wrapped("count")]
            count.redirect = (
                f"{{experiment_run_dir}}/compiler_memtrace.{executable_name}.count.out"
            )
            pre.extend(
                [
                    count,
                    CommandExecutable(
                        f"check-memtrace-count-{executable_name}",
                        template=["test $? -eq 0 || exit 1"],
                    ),
                ]
            )
        executable.template = [wrapped(self._usage_mode)]
        return pre, []
