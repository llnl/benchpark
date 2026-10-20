---
name: benchpark-add-experiment
description: "Add a new benchmark experiment to Benchpark (experiments/<benchmark>/experiment.py) or extend an existing one with programming models (+openmp/+cuda/+rocm), scaling studies (strong/weak/throughput), workloads, or Caliper support. Use this whenever someone wants to add, port, or onboard a benchmark to Benchpark, write or fix an experiment.py, wire it to its Spack package.py and Ramble application.py, or debug a failing `benchpark experiment init`, `benchpark audit`, or CI dryrun for an experiment, even if they never say the word 'experiment'."
---

# Benchpark: Add an Experiment

An `experiment.py` describes how to map one benchmark onto any Benchpark system: which programming models and scaling studies it supports, what problem it runs, and how it is built. At `benchpark experiment init` time it generates the `applications:` and `software:` sections of a Ramble `ramble.yaml`. It sits on top of two other layers. Most failures come from a missing required piece or a mismatch between layers, so check each layer directly rather than copying the nearest experiment.

| Layer | Benchpark copy (wins if present) | Fallback |
|---|---|---|
| Build: Spack `package.py` | `repos/spack_repo/benchpark/packages/<name_with_underscores>/package.py` | upstream spack-packages |
| Run: Ramble `application.py` | `repos/ramble_applications/<name_with_underscores>/application.py` | upstream Ramble builtin (check its base application for inherited variables) |
| Map: `experiment.py` | `experiments/<name>/experiment.py` | none |

Naming ties the layers together. For `experiments/my-bench/`:
- the spec name users type is `my-bench`;
- the class must be `MyBench`, the CamelCase of the directory (`osu-micro-benchmarks` → `OsuMicroBenchmarks`, `amg2023` → `Amg2023`);
- `self.name` becomes `my_bench`, which must equal the Ramble application name (hence `repos/ramble_applications/osu_micro_benchmarks/`);
- the Spack package named inside the spec string may differ (`md-test` builds `mdtest`).

## Required components

Each item is enforced somewhere. Several of the resulting errors don't point at their cause; the error lookup at the end maps each one back.

1. **License header**, copied verbatim from an existing experiment, year included: the checker accepts only 2023 or 2024 and reports "Copyright date mismatch" for any other year. CI runs `python .github/workflows/bin/license verify` over `experiments/`.
2. **Bases: `Experiment` plus `ProgrammingModel(...)` with at least one `ProgrammingModelType`.** Without it, init fails with `AttributeError: '<Class>' object has no attribute '_available_programming_models'`. Without `ProgrammingModelType.Mpionly`, the experiment can only be initialized with `+cuda`, `+rocm`, or `+openmp`.
3. **A `workload` variant** whose values are workload names in the Ramble application. Fails with "Package <name> must define a workload variant". List `values=` so a typo fails at init instead of inside Ramble.
4. **A `version` variant** listing versions from `package.py`, plus `latest` (no `@` constraint) and branch names such as `develop` if the package has them. `determine_version()` reads it; without it init fails with `KeyError: 'version'`.
5. **`maintainers("<github-username>")`.** Every experiment has one; ask the user whose handle to use.
6. **`compute_applications_section()` defined on this class itself.** `benchpark audit` checks the class `__dict__`, so inheriting the method from another experiment class fails the audit. The method must:
   - Define a resource variable the allocation modifier reads: `n_ranks` or `n_gpus`, optionally with `n_nodes` and `n_threads_per_proc`.
     - With none of these, init succeeds but Ramble setup fails with "Must specify one of: n_nodes, n_ranks, n_gpus".
     - `n_nodes` alone also fails in Ramble, with `unsupported operand type(s) for //: 'NoneType' and 'int'`. Pair it with `n_ranks`, `n_gpus`, or `n_ranks_per_node`.
     - Convention: `n_gpus` under `+cuda`/`+rocm`, `n_ranks` otherwise, and `n_threads_per_proc` under `+openmp`. Keep `n_threads_per_proc` at 1 in `exec_mode=test` (as kripke, amg2023, and raja-perf do), because CI's `generic-x86` system has one core per node.
   - Set all of `n_resources`, `process_problem_size`, and `total_problem_size`, usually via `self.set_required_variables(...)`. Fails with "The following experiment variables must be set".
     - Use `""` for a quantity that has no meaning for the benchmark, or that lives in a fixed input file (as ad, gpcnet, and osu-micro-benchmarks do).
     - Express problem size the way the application consumes it: per process like amg2023, or global like kripke.
   - Handle `exec_mode=test`, the default: a small problem that CI dry-runs on every system. Preferably also handle `exec_mode=perf`. Make each branch complete on its own rather than defining a variable in only one branch.
   - If the class inherits `Scaling(...)`, call `self.register_scaling_config({...})` with an entry for every declared mode. Fails with "Experiment supports scaling modes ..., but does not define a config for them", on every init, with or without a scaling flag.
7. **`compute_package_section()` defined on this class itself**, calling `self.add_package_spec(self.name, ["<spack-pkg><version> <variants>"])`.
   - The first argument must be `self.name`, or init fails with "Package section must be defined for application package".
   - Extra dependencies get their own calls (`hypre` in amg2023).

## Contracts between the layers

Declare only what the layers support. A programming model needs the matching package variant, `Caliper` needs an instrumented build, and scaling needs workload variables that control resources and problem size. An application that reads its whole problem from a fixed input file, like HPCC, has nothing to scale.

- **Programming models append Spack variants.** For each declared model, the mixin appends one of these pairs: `+openmp`/`~openmp`, `+cuda cuda_arch={cuda_arch}`/`~cuda`, `+rocm amdgpu_target={rocm_arch}`/`~rocm`.
  - `Mpionly` appends nothing, so add `+mpi` yourself if the package has an `mpi` variant.
  - If the package names these variants differently, override the helper as `experiments/babelstream/experiment.py` does (`+omp`, `+hip`). If it has no such variant at all, as with a package that only ever builds for one GPU vendor, make the override return `""`.
- **`Caliper` appends `+caliper`/`~caliper`.** Inherit it only if the package has a `caliper` variant and the source is instrumented.
- **Dry-runs never concretize, so CI can't catch a variant mismatch.** A dry-run passes even when a mixin appends `+openmp` to a package with no `openmp` variant. After `. workspace/setup.sh`, run `spack info <package>` and confirm every variant in the generated `spack_pkg_spec` exists. Short of a build, `spack -e <workspace>/software/spack/<name> concretize -f --fresh` solves against the system's real externals and shows which dependencies would be built from source; it needs the site's module system if the system loads compilers through modules. Only a real build proves the layers agree.
- **Appended variants get no leading space** (the generated spec reads `saxpy@1.0.0~openmp ~cuda`). If your spec string ends in a `key=value` token, end the string with a space, as the hecbench experiments do.
- **Experiment variables feed `application.py`.** Use the exact names of its `workload_variable(...)`s, including ones inherited from a base application, and of anything its executables reference. Otherwise `ramble workspace setup` fails.
- **Experiment names come from `named=True` variables.** Together, the named variables must distinguish every generated experiment (anything given a list, matrixed, or scaled), or Ramble fails with "Experiment ... is not unique".
- **Scaled variables must start as single numbers**, or as dicts of numbers.
  - Use ints, not strings: `"1"` scaled by 2 becomes `"11"`, then `"1111"`, and `experiment init` accepts this silently.
  - Don't scale a list or matrixed variable. Scaling appends to it, which duplicates experiments. If the experiment sweeps a list when not scaling (as saxpy does with `n`), switch to one base value when a scaling flag is set:
    ```python
    if self.spec.satisfies("+strong") or self.spec.satisfies("+weak"):
        self.add_experiment_variable("n", 512, True)
    else:
        self.add_experiment_variable("n", [128, 256, 512], True, True)
    ```
- **The signature is `add_experiment_variable(name, value, named=False, matrixed=False)`.**
  - A dict value creates a zipped multi-dimensional variable (`{"px": 2, "py": 2, "pz": 1}`), which you reference by its dimension names (`{px}`).
  - The keyword is `matrixed`, not `matrix`.
- **System facts:** in variable strings use `{sys_cores_per_node}` and `{sys_gpus_per_node}`; in Python use `self.system_spec.system` (see osu-micro-benchmarks and raja-perf).
- **Variants you already inherit** (don't reuse these names for something else):
  - from the base class: `exec_mode`, `package_manager`, `n_repeats`, `append_path`, `prepend_path`, `allocation`, `affinity`, `hwloc`, `githash`;
  - from the mixins: the model flags, `strong`/`weak`/`throughput`, `scaling-factor`, `scaling-iterations`, and Caliper's `caliper`, `caliper_services`, `cali_version`.
  - Redefining one to extend its values is fine; raja-perf adds an `exec_mode` value this way.
- **Every variant needs a real default.** A missing default (or `""`) fails with the misleading `AttributeError: type object '<Class>' has no attribute '_name'`.

## How CI exercises the experiment

Design for this up front; it's where new experiments most often fail review.

- **Detection is by text search.** `benchpark list experiments`, which drives CI, finds models and scaling modes by searching the file for literal strings such as `ProgrammingModelType.Openmp` or `ScalingMode.Weak`.
  - Don't alias the enums.
  - Don't name an unsupported model or mode, even in a comment. A comment mentioning `ProgrammingModelType.Cuda` is enough for CI to dry-run `+cuda`.
  - Modifier support (e.g. `caliper`) is detected the same way.
- **What gets run.** The `dryrunexperiments` job runs `experiment init` plus `ramble workspace setup --dry-run` with default variants for:
  - each declared model, on every system that supports it;
  - `<name>+strong`, `+weak`, and `+throughput` (no model flag), on every system;
  - modifiers (`affinity=on`, `hwloc=on`, and `caliper=time` if declared), on `llnl-cluster cluster=dane`.
- **How many cases that is.** An MPI-only experiment such as HPCC gets 43 cases, and saxpy (four models) gets 93. Each scaling mode adds one case per system configuration, about 41. Each case takes roughly 10 to 20 seconds.
- **Consequences:**
  - `exec_mode=test` must fit the smallest systems (`generic-x86` has one core per node). "Experiment requests more cores per rank than are available on a node" means `n_threads_per_proc` is too large.
  - A GPU-only experiment (no `Mpionly`) that declares scaling fails the scaling dryruns. Add commented `SKIP_EXPR` entries in `.github/utils/dryruns.py`, as py-scaffold does.
  - An experiment that needs a system variant (ior needs `mount_point`) requires a matching special case in `dryruns.py`.

## Workflow

### 1. Gather facts before writing code

Ask the user in one round for anything you can't find (use your agent's question tool if it has one):
- source location and versions;
- supported programming models;
- how the problem is sized;
- what a strong-scaling and a weak-scaling step should change;
- a CI-sized test problem;
- whether the source is Caliper-instrumented;
- the maintainer's GitHub username.

Then check the repo:
1. `ls experiments/`. If the benchmark already has an experiment, extend it instead of adding another.
2. The Spack package (Benchpark copy first, then upstream): note its versions and its variants (`mpi`, `openmp`, `cuda`, `rocm`, `caliper`).
3. The Ramble application (Benchpark copy first, then upstream and its base application): note workload names, `workload_variable`s and their defaults, input files, executables, and figures of merit.

If the package or application is missing, write it first (see `docs/interactive-tutorial/add-a-spack-package.rst` and `add-a-ramble-application.rst`). Give a new application `tags` from `taxonomy.yaml`; they feed the docs catalogue.

### 2. Start from the closest existing experiment

| Situation | Model on |
|---|---|
| Scalar problem size, MPI (+OpenMP) | `hpl`, `hpcg`, `stream` |
| 3-D decomposition, per-process size | `amg2023` |
| 3-D decomposition, global size | `kripke` |
| All four models with an `n_gpus`/`n_ranks` switch | `raja-perf`, `test/saxpy` |
| GPU only | `commbench`, `py-scaffold` |
| Many workloads selectable at once (`multi=True`) | `osu-micro-benchmarks` |
| No meaningful problem size | `ad`, `gpcnet` |
| Package names model variants differently | `babelstream` |
| Several experiments sharing one package in a sub-namespace | `hecbench/*`: needs its own `repo.yaml`, entries under both `experiments:` and `applications:` in `config/repos.yaml`, and `self.name` set in `__init__`. `benchpark list` shows these as `<namespace>.<name>` |

### 3. Write `experiments/<name>/experiment.py`

```python
# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from benchpark.caliper import Caliper
from benchpark.directives import maintainers, variant
from benchpark.experiment import Experiment
from benchpark.programming_model import ProgrammingModel, ProgrammingModelType
from benchpark.scaling import Scaling, ScalingMode


class MyBench(
    Experiment,
    # Declare only models that package.py has variants for (MPI-only needs none)
    ProgrammingModel(
        ProgrammingModelType.Mpionly,
        ProgrammingModelType.Openmp,
        ProgrammingModelType.Cuda,
        ProgrammingModelType.Rocm,
    ),
    Scaling(ScalingMode.Strong, ScalingMode.Weak),
    Caliper,  # only if package.py has a `caliper` variant
):
    variant(
        "workload",
        default="problem1",
        values=("problem1",),  # workload names from application.py
        description="Ramble workload to run",
    )

    variant(
        "version",
        default="1.0.0",
        values=("latest", "develop", "1.0.0"),  # versions from package.py
        description="app version",
    )

    maintainers("github-username")

    def compute_applications_section(self):
        # Application-specific names ("size") must match workload_variable()s.
        # Values that get scaled must be numbers, not strings.
        if self.spec.satisfies("exec_mode=test"):
            self.add_experiment_variable("n_resources", 2)
            self.add_experiment_variable("size", 1024, True)
        else:  # exec_mode=perf
            self.add_experiment_variable("n_resources", 64)
            self.add_experiment_variable("size", 1048576, True)

        if self.spec.satisfies("+cuda") or self.spec.satisfies("+rocm"):
            self.add_experiment_variable("n_gpus", "{n_resources}", True)
        else:
            self.add_experiment_variable("n_ranks", "{n_resources}", True)
        if self.spec.satisfies("+openmp"):
            # 1 in test mode: CI's generic-x86 system has one core per node
            self.add_experiment_variable("n_threads_per_proc", 1, True)

        # n_resources is set above; this completes the required trio
        self.set_required_variables(
            process_problem_size="{size}/{n_resources}",
            total_problem_size="{size}",
        )

        # One entry per declared mode; each key must already be a variable
        self.register_scaling_config(
            {
                ScalingMode.Strong: {
                    "n_resources": lambda var, itr, dim, sf: var.val(dim) * sf,
                    "size": lambda var, itr, dim, sf: var.val(dim),
                },
                ScalingMode.Weak: {
                    "n_resources": lambda var, itr, dim, sf: var.val(dim) * sf,
                    "size": lambda var, itr, dim, sf: var.val(dim) * sf,
                },
            }
        )

    def compute_package_section(self):
        # Key is self.name; the string starts with the Spack package name.
        # Model and Caliper variants are appended automatically.
        self.add_package_spec(self.name, [f"my-bench{self.determine_version()} +mpi"])
```

### 4. Validate, in this order

Run everything from the repo root. The first `./bin/benchpark` call bootstraps Spack and Ramble into `~/.benchpark/` and needs network access. Install the pinned linters with `pip install -r .github/workflows/requirements/style.txt`.

```bash
# Static checks
./bin/benchpark list experiments | grep my-bench   # e.g. my-bench+[openmp|cuda|rocm|mpi]+[strong|weak]
./bin/benchpark audit
ruff format experiments/my-bench && ruff check --fix experiments/my-bench
codespell --ignore-words=.codespellignore experiments/my-bench
# Importing experiments leaves __pycache__/*.pyc, which can crash the license check
find experiments -name __pycache__ -prune -exec rm -rf {} +
python .github/workflows/bin/license verify

# One full dry run by hand
./bin/benchpark system init --dest=dane llnl-cluster cluster=dane
./bin/benchpark experiment init --dest=my-bench dane my-bench   # writes dane/my-bench/ramble.yaml
./bin/benchpark setup ./dane/my-bench workspace/
. workspace/setup.sh
ramble --workspace-dir workspace/dane/my-bench/workspace --disable-logger workspace setup --dry-run
spack info my-bench   # every variant in the generated spack_pkg_spec must be listed

# Every case CI will run for this experiment, using CI's own enumeration
S=.agents/skills/benchpark-add-experiment/scripts/ci_dryruns.py
python3 $S my-bench --list
python3 $S my-bench --match 'generic-x86|cluster=dane$'   # a fast subset first
python3 $S my-bench                                        # then everything
```

After the dry runs:
- Read `dane/my-bench/ramble.yaml` and confirm the experiment names, variables, and Spack spec are what you intended.
- The manual steps leave `dane/` and `workspace/` in the repo root, and neither is gitignored, so delete them. The script cleans up after itself and keeps only logs.
- Don't run `.github/utils/dryrun.sh` in parallel: it names directories by the second and shares `workspace/`.
- Tell the user exactly which cases you ran. A clean `experiment init` alone doesn't show that the experiment works, and a clean dry-run doesn't show that it builds.
- On a real machine, drop `--dry-run` to build, then run with `ramble --workspace-dir <ws> on`.

### 5. Before opening the PR

- Include `experiment.py` plus any new or overridden `package.py`/`application.py`. If an upstream copy is insufficient, the PR template asks for a follow-up issue to upstream the change.
- Give every new `SKIP_EXPR` entry a comment explaining why it's skipped.
- Ask the user whether the benchmark should run in LC GitLab CI. If so:
  - add it to the `BENCHMARK` lists in `.gitlab/tests/*.yml`;
  - for shared hosts, also update the matching `resource_rules_*` entry in `.gitlab/utils/rules.yml`.
- The docs catalogue is generated by `docs/generate-benchmark-list.py`, so no table edits are needed.

## Error lookup

| Message | Cause and fix |
|---|---|
| `Package X must define a workload variant` | Add the `workload` variant |
| `'X' object has no attribute '_available_programming_models'` | No `ProgrammingModel(...)` in the bases |
| `module 'benchpark.expr.<namespace>.<dir>' has no attribute 'X'` | The class name isn't the CamelCase of the directory name |
| `type object 'X' has no attribute '_name'` | A variant has no default, or `default=""` |
| `"x" cannot run with MPI only without inheriting from ProgrammingModelType.Mpionly` | Pass `+cuda`/`+rocm`/`+openmp`, or declare `Mpionly` |
| `The following experiment variables must be set ...` | Set all three required variables |
| `Package section must be defined for application package x` | The first `add_package_spec` argument must be `self.name` |
| `Experiment supports scaling modes ..., but does not define a config for them` | Add the missing mode to `register_scaling_config` |
| `All scaling variables must either have the same number of dimensions, or only one dimension` | Make the scaled multi-dimensional variables match |
| `spec cannot specify multiple scaling options` / `... mutually-exclusive programming models` | Only one scaling mode and one of cuda/rocm/openmp per spec |
| `X does not implement compute_...` (audit) / `Each experiment must implement compute_...` (init) | Define the method on this class |
| `KeyError: 'version'` | Add the `version` variant |
| `got an unexpected keyword argument 'matrix'` | The keyword is `matrixed` |
| `Copyright date mismatch` (license verify) | Use the header year from an existing experiment (2023 or 2024) |
| Ramble setup: `Must specify one of: n_nodes, n_ranks, n_gpus` | Add a resource variable |
| Ramble setup: `unsupported operand type(s) for //: 'NoneType' and 'int'` | `n_nodes` set without `n_ranks`, `n_gpus`, or `n_ranks_per_node` |
| Ramble setup: `Experiment requests more cores per rank than are available on a node` | `n_threads_per_proc` exceeds the system's cores per node; use 1 in test mode |
| Ramble setup: `Experiment ... is not unique` | The named variables don't distinguish every experiment, or a list variable was scaled |
| Only during a real build: Spack rejects an unknown variant | A mixin appends a variant the package lacks; check `spack info` |

## References

- `scripts/ci_dryruns.py` (in this skill): lists and runs the CI dry-run cases for one experiment.
- Docs:
  - `docs/add-an-experiment.rst` (full guide, plus an appendix on variables and scaling)
  - `docs/interactive-tutorial/add-an-experiment.rst` and `add-a-scaling-configuration.rst`
  - `docs/testing-your-contribution.rst`
  - `docs/ci-developer-guide.rst`
- Library code:
  - `lib/benchpark/experiment.py`, `programming_model.py`, `scaling.py`, `caliper.py`, `directives.py`
  - `modifiers/allocation/modifier.py`, which defines the resource variables
- CI: `.github/utils/dryruns.py`, `.github/utils/dryrun.sh`, `.github/workflows/run.yml`
- `.github/ISSUE_TEMPLATE/benchmark-status.md`: the project's checklist for a fully integrated benchmark
- Ramble application guide: https://ramble.readthedocs.io/en/latest/dev_guides/application_dev_guide.html
