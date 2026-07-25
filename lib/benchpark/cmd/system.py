# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# Copyright 2013-2023 Spack Project Developers.
#
# SPDX-License-Identifier: Apache-2.0

import difflib
import inspect
import os
import pickle
import re
import shutil
import subprocess
import sys
import textwrap
from pprint import pprint
from pathlib import Path

import llnl.util.tty.color as color
import yaml
from deepdiff import DeepDiff

import benchpark.spec
import benchpark.system
from benchpark.paths import paths


def system_init(args):
    system_spec = benchpark.spec.SystemSpec(" ".join(args.spec)).concretize()
    system_spec.destdir = args.dest
    system = system_spec.system

    if args.basedir:
        base = args.basedir
        sysdir = str(hash(system_spec))
        destdir = os.path.join(base, sysdir)
    elif args.dest:
        destdir = args.dest
    else:
        raise ValueError("Must specify one of: --dest, --basedir")

    try:
        os.makedirs(destdir)
        system.write_system_dict(destdir)
    except FileExistsError:
        print(f"Abort: system description dir already exists ({destdir})")
        sys.exit(1)
    except Exception:
        # If there was a failure, remove any partially-generated resources
        shutil.rmtree(destdir)
        raise

    system_pickle = os.path.join(destdir, "system.pkl")
    with open(system_pickle, "wb") as f:
        pickle.dump(system_spec, f)


def system_id(args):
    temp_sys = benchpark.system.System(args.system_dir)
    data = temp_sys.compute_system_id()
    name = data["system"]["name"]
    spec_hash = data["system"]["config-hash"]
    return f"{name}-{spec_hash[:7]}"

def _section(title):
    color.cprint(f"\n@*b== {title} ==@.")


def _spack_packages_yaml_path():
    # This matches where your current Spack run is actually writing.
    return Path(os.path.expanduser("~/.spack/packages.yaml"))


def _load_packages_yaml(path):
    if not path.exists():
        raise FileNotFoundError(f"Spack packages.yaml not found: {path}")

    with open(path, "r") as file:
        data = yaml.safe_load(file) or {}

    return data.get("packages", {})


def _external_specs(pkg_def):
    if not isinstance(pkg_def, dict):
        return []

    externals = pkg_def.get("externals", []) or []
    specs = []

    for external in externals:
        if isinstance(external, dict):
            specs.append(external.get("spec", "<missing spec>"))

    return specs


def _external_prefixes(pkg_def):
    if not isinstance(pkg_def, dict):
        return []

    externals = pkg_def.get("externals", []) or []
    prefixes = []

    for external in externals:
        if isinstance(external, dict):
            prefixes.append(external.get("prefix", "<missing prefix>"))

    return prefixes


def _print_system_context(system_spec, system):
    _section("System object")

    print(f"Spec string: {system_spec}")
    print(f"System class: {system.__class__.__module__}.{system.__class__.__name__}")

    if hasattr(system, "name"):
        print(f"System name: {system.name}")

    if hasattr(system, "spec"):
        print(f"System spec: {system.spec}")


def _print_package_table(title, packages):
    _section(f"{title} ({len(packages)} packages)")

    if not packages:
        print("No packages.")
        return

    rows = []

    for name in sorted(packages):
        pkg_def = packages[name] or {}
        buildable = pkg_def.get("buildable", "<unset>") if isinstance(pkg_def, dict) else "<unset>"
        specs = _external_specs(pkg_def)

        if specs:
            externals = "; ".join(specs)
        else:
            externals = "-"

        rows.append((name, str(buildable), externals))

    name_width = max(len("package"), max(len(row[0]) for row in rows))
    buildable_width = max(len("buildable"), max(len(row[1]) for row in rows))

    print(f"{'package':<{name_width}}  {'buildable':<{buildable_width}}  externals")
    print(f"{'-' * name_width}  {'-' * buildable_width}  {'-' * 60}")

    for name, buildable, externals in rows:
        print(f"{name:<{name_width}}  {buildable:<{buildable_width}}  {externals}")


def _print_package_yaml(title, packages):
    _section(title)
    print(
        yaml.safe_dump(
            {"packages": packages},
            sort_keys=True,
            default_flow_style=False,
        ).rstrip()
    )


def _print_name_list(title, names):
    _section(f"{title} ({len(names)})")

    if not names:
        print("None.")
        return

    for name in names:
        print(f"- {name}")


def _print_changed_packages(expected_packages, detected_packages):
    common = sorted(set(expected_packages) & set(detected_packages))

    changed = []

    for name in common:
        diff = DeepDiff(
            expected_packages[name],
            detected_packages[name],
            verbose_level=1,
            ignore_type_in_groups=[(int, str)],
            ignore_string_type_changes=True,
        )

        if diff:
            changed.append((name, diff))

    _section(f"Common packages with changed definitions ({len(changed)})")

    if not changed:
        print("None.")
        return

    for name, diff in changed:
        print(f"\n{name}")

        print("  Expected:")
        expected_yaml = yaml.safe_dump(
            expected_packages[name],
            sort_keys=True,
            default_flow_style=False,
        ).rstrip()
        print(textwrap.indent(expected_yaml, "    "))

        print("  Detected:")
        detected_yaml = yaml.safe_dump(
            detected_packages[name],
            sort_keys=True,
            default_flow_style=False,
        ).rstrip()
        print(textwrap.indent(detected_yaml, "    "))

        print("  Diff:")
        print(textwrap.indent(diff.pretty(), "    "))


_SPEC_VERSION_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9_.+-]+)@(?P<version>[^%+~\s^]+)"
)


def _spec_name_and_version(spec):
    """Return (package_name, version) for a concrete external spec."""
    if not isinstance(spec, str):
        return None, None

    match = _SPEC_VERSION_RE.match(spec.strip())
    if not match:
        return None, None

    return match.group("name"), match.group("version")


def _replace_spec_version(spec, new_version):
    """Replace only the version token, preserving variants and compiler constraints."""
    match = _SPEC_VERSION_RE.match(spec.strip())
    if not match:
        raise ValueError(f"Cannot identify a version in spec: {spec}")

    start, end = match.span("version")
    return spec[:start] + new_version + spec[end:]


def _normalize_prefix(prefix):
    if not prefix:
        return None
    return os.path.normpath(os.path.expanduser(str(prefix)))


def _normalize_modules(modules):
    if not modules:
        return set()
    if isinstance(modules, str):
        return {modules}
    return {str(module) for module in modules}


def _external_records(package_definition):
    """Convert a packages.yaml package entry into simple comparable records."""
    if not isinstance(package_definition, dict):
        return []

    records = []
    for external in package_definition.get("externals", []) or []:
        if not isinstance(external, dict):
            continue

        spec = external.get("spec")
        if not spec:
            continue

        name, version = _spec_name_and_version(spec)
        records.append(
            {
                "spec": spec,
                "name": name,
                "version": version,
                "prefix": _normalize_prefix(external.get("prefix")),
                "modules": _normalize_modules(external.get("modules")),
            }
        )

    return records


def _is_user_local_prefix(prefix):
    if not prefix:
        return False

    path = Path(prefix)
    home = Path.home()

    try:
        path.relative_to(home)
        return True
    except ValueError:
        pass

    return any(part in {".venv", ".venvs", "venv"} for part in path.parts)


def _select_detected_external(expected, detected_records, allow_fallback):
    """Select a detected external conservatively.

    Exact prefix and module matches are considered authoritative. A single
    fallback candidate is accepted only for packages with one expected
    external, and user-local/virtualenv candidates are rejected when the
    expected entry is system-wide.
    """
    if not detected_records:
        return None, "no detected external entries"

    same_name = [
        record
        for record in detected_records
        if record["name"] == expected["name"]
    ]
    if not same_name:
        return None, "no detected external with the same package name"

    if expected["prefix"]:
        prefix_matches = [
            record
            for record in same_name
            if record["prefix"] == expected["prefix"]
        ]
        if len(prefix_matches) == 1:
            return prefix_matches[0], "exact prefix match"
        if len(prefix_matches) > 1:
            same_version = [
                record
                for record in prefix_matches
                if record["version"] == expected["version"]
            ]
            if len(same_version) == 1:
                return same_version[0], "exact prefix and version match"
            return None, "multiple detected externals use the expected prefix"

    if expected["modules"]:
        module_matches = [
            record
            for record in same_name
            if expected["modules"] & record["modules"]
        ]
        if len(module_matches) == 1:
            return module_matches[0], "module match"
        if len(module_matches) > 1:
            return None, "multiple detected externals match the expected module"

    if not allow_fallback:
        return None, "multiple expected externals make fallback matching ambiguous"

    if len(same_name) == 1:
        candidate = same_name[0]
        if (
            _is_user_local_prefix(candidate["prefix"])
            and not _is_user_local_prefix(expected["prefix"])
        ):
            return None, "only detected candidate is user-local or from a virtualenv"
        return candidate, "single detected candidate"

    system_candidates = [
        record for record in same_name if not _is_user_local_prefix(record["prefix"])
    ]
    if len(system_candidates) == 1:
        return system_candidates[0], "single non-user-local detected candidate"

    return None, "detected external selection is ambiguous"


def _collect_version_update_proposals(expected_packages, detected_packages):
    """Return confident version changes and entries that need manual review."""
    proposals = []
    review = []

    for package in sorted(set(expected_packages) & set(detected_packages)):
        expected_records = _external_records(expected_packages[package])
        detected_records = _external_records(detected_packages[package])

        if not expected_records or not detected_records:
            continue

        # Fallback matching is safe only when the system spec declares one
        # external for this package.
        allow_fallback = len(expected_records) == 1

        for expected in expected_records:
            detected, reason = _select_detected_external(
                expected,
                detected_records,
                allow_fallback=allow_fallback,
            )

            if detected is None:
                review.append(
                    {
                        "package": package,
                        "expected_spec": expected["spec"],
                        "reason": reason,
                    }
                )
                continue

            if expected["version"] is None or detected["version"] is None:
                review.append(
                    {
                        "package": package,
                        "expected_spec": expected["spec"],
                        "detected_spec": detected["spec"],
                        "reason": "could not parse one of the versions",
                    }
                )
                continue

            if expected["version"] == detected["version"]:
                continue

            proposals.append(
                {
                    "package": package,
                    "expected_spec": expected["spec"],
                    "detected_spec": detected["spec"],
                    "expected_version": expected["version"],
                    "detected_version": detected["version"],
                    "expected_prefix": expected["prefix"],
                    "detected_prefix": detected["prefix"],
                    "match_reason": reason,
                }
            )

    # Remove duplicate proposals that can arise from repeated equivalent entries.
    unique = {}
    for proposal in proposals:
        key = (
            proposal["package"],
            proposal["expected_spec"],
            proposal["detected_spec"],
        )
        unique[key] = proposal

    return list(unique.values()), review


def _print_version_update_proposals(proposals, review):
    _section(f"Proposed package version updates ({len(proposals)})")

    if not proposals:
        print("None.")
    else:
        for proposal in proposals:
            print(f"\n{proposal['package']}")
            print(f"  current:  {proposal['expected_spec']}")
            print(f"  detected: {proposal['detected_spec']}")
            print(f"  match:    {proposal['match_reason']}")
            if proposal["expected_prefix"] or proposal["detected_prefix"]:
                print(f"  prefix:   {proposal['expected_prefix']} -> "
                      f"{proposal['detected_prefix']}")

    _section(f"Version comparisons requiring manual review ({len(review)})")
    if not review:
        print("None.")
    else:
        for item in review:
            print(f"- {item['package']}: {item['expected_spec']}")
            if item.get("detected_spec"):
                print(f"    detected: {item['detected_spec']}")
            print(f"    reason: {item['reason']}")


# def _system_source_path(system):
#     source = inspect.getsourcefile(system.__class__) or inspect.getfile(system.__class__)
#     if not source:
#         raise RuntimeError(
#             f"Unable to locate source for {system.__class__.__module__}."
#             f"{system.__class__.__name__}"
#         )
#     return Path(source).resolve()
def _system_source_path(system, system_name=None):
    """Locate the repository system.py for a concretized system object.

    Benchpark/Ramble may dynamically load system classes into synthetic modules
    such as ``benchpark.sys.sysbuiltin.olcf-frontier``. In that case,
    inspect.getsourcefile() cannot recover the original source path, so fall
    back to the Benchpark repository layout.
    """

    try:
        source = inspect.getsourcefile(system.__class__)

        if source:
            source_path = Path(source).resolve()

            if source_path.is_file():
                return source_path

    except (TypeError, OSError):
        # Dynamically loaded repository classes may look like built-in classes
        # to inspect.getsourcefile().
        pass

    possible_names = []

    if system_name:
        possible_names.append(system_name)

    # Example:
    # benchpark.sys.sysbuiltin.olcf-frontier -> olcf-frontier
    module_leaf = system.__class__.__module__.rsplit(".", 1)[-1]
    possible_names.append(module_leaf)

    # system.py is:
    # <repo>/lib/benchpark/cmd/system.py
    #
    # parents[3] is the Benchpark repository root.
    benchpark_repo = Path(__file__).resolve().parents[3]

    for name in dict.fromkeys(possible_names):
        candidate = benchpark_repo / "systems" / name / "system.py"

        if candidate.is_file():
            return candidate.resolve()

    searched = [
        str(benchpark_repo / "systems" / name / "system.py")
        for name in dict.fromkeys(possible_names)
    ]

    raise RuntimeError(
        "Unable to locate the target system.py.\n"
        f"Class: {system.__class__.__module__}."
        f"{system.__class__.__name__}\n"
        f"Searched: {searched}"
    )


def _build_system_source_proposal(source_path, proposals):
    """Build a non-destructive system.py proposal and unified diff.

    Only unique literal spec strings are changed. Resolved f-string values such
    as ``hip@{self.rocm_version}`` are intentionally not rewritten.
    """
    original = source_path.read_text()
    proposed = original
    applied = []
    skipped = []

    for proposal in proposals:
        old_spec = proposal["expected_spec"]
        new_spec = _replace_spec_version(
            old_spec,
            proposal["detected_version"],
        )

        occurrences = proposed.count(old_spec)
        if occurrences == 0:
            skipped.append(
                {
                    **proposal,
                    "reason": (
                        "resolved spec is not a literal in system.py; it is likely "
                        "generated from a variant or version attribute"
                    ),
                }
            )
            continue

        if occurrences > 1:
            skipped.append(
                {
                    **proposal,
                    "reason": (
                        f"the literal appears {occurrences} times in system.py, "
                        "so an automatic replacement would be ambiguous"
                    ),
                }
            )
            continue

        proposed = proposed.replace(old_spec, new_spec, 1)
        applied.append({**proposal, "replacement_spec": new_spec})

    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            proposed.splitlines(keepends=True),
            fromfile=str(source_path),
            tofile=f"{source_path}.proposed",
        )
    )

    return proposed, diff, applied, skipped


def _emit_system_source_proposal(
    system,
    proposals,
    system_name=None,
    proposal_file=None,
    proposed_system_file=None,
):
    source_path = _system_source_path(system)
    proposed_source, diff, applied, skipped = _build_system_source_proposal(
        source_path,
        proposals,
    )

    _section("Target system.py source")
    print(source_path)

    _section(f"Literal system.py updates included in proposal ({len(applied)})")
    if not applied:
        print("None.")
    else:
        for item in applied:
            print(
                f"- {item['package']}: "
                f"{item['expected_spec']} -> {item['replacement_spec']}"
            )

    _section(f"Version updates not automatically patchable ({len(skipped)})")
    if not skipped:
        print("None.")
    else:
        for item in skipped:
            print(
                f"- {item['package']}: "
                f"{item['expected_spec']} -> {item['detected_spec']}"
            )
            print(f"    reason: {item['reason']}")

    _section("Proposed system.py patch")
    if diff:
        print(diff.rstrip())
    else:
        print("No safe literal source changes could be generated.")

    if proposal_file:
        proposal_path = Path(proposal_file).expanduser().resolve()
        proposal_path.parent.mkdir(parents=True, exist_ok=True)
        proposal_path.write_text(diff)
        print(f"\nWrote patch proposal to: {proposal_path}")

    if proposed_system_file:
        proposed_path = Path(proposed_system_file).expanduser().resolve()
        proposed_path.parent.mkdir(parents=True, exist_ok=True)
        proposed_path.write_text(proposed_source)
        print(f"Wrote proposed system.py copy to: {proposed_path}")


# def system_external(args):
#     if args.new_system:
#         subprocess.run(
#             [
#                 paths.benchpark_home / "spack/bin/spack",
#                 "external",
#                 "find",
#                 "--not-buildable",
#             ]
#         )

#         #with open(paths.benchpark_home / "spack/etc/spack/packages.yaml", "r") as file:
#         with open(os.path.expanduser("~/.spack/packages.yaml"), "r") as file:
#             new_packages = yaml.safe_load(file)["packages"]

#         color.cprint("@*rHere are all of the new packages:@.")
#         pprint(new_packages)
#         return

#     system_spec = benchpark.spec.SystemSpec(" ".join(args.spec)).concretize()
#     system = system_spec.system

#     packages = system.compute_packages_section()["packages"]
#     pkg_list = list(packages.keys())
#     subprocess.run(
#         [
#             paths.benchpark_home / "spack/bin/spack",
#             "external",
#             "find",
#             "--not-buildable",
#         ]
#         + [pkg for pkg in pkg_list]
#     )

#     # with open(paths.benchpark_home / "spack/etc/spack/packages.yaml", "r") as file:
#     with open(os.path.expanduser("~/.spack/packages.yaml"), "r") as file:
#         new_packages = yaml.safe_load(file)["packages"]

#     # Use DeepDiff to find differences
#     diff = DeepDiff(
#         packages,
#         new_packages,
#         verbose_level=1,
#         ignore_type_in_groups=[(int, str)],
#         ignore_string_type_changes=True,
#     )

#     if not diff:
#         color.cprint("@*gNo new packages.@.")
#     else:
#         color.cprint("@*rThe Packages are different. Here are the differences:@.")
#         pprint(diff)
#         color.cprint("@*rHere are all of the new packages:@.")
#         pprint(new_packages)

def system_external(args):
    spack_cmd = [
        paths.benchpark_home / "spack/bin/spack",
        "external",
        "find",
        "--not-buildable",
    ]

    if args.new_system:
        if args.propose or args.patch_file or args.write_proposed_system:
            raise ValueError(
                "Source update proposals require an existing Benchpark system spec; "
                "do not combine them with --new-system."
            )

        subprocess.run(spack_cmd, check=True)

        packages_yaml = _spack_packages_yaml_path()
        new_packages = _load_packages_yaml(packages_yaml)

        print(f"\nDetected packages file: {packages_yaml}")
        _print_package_table("Detected packages from spack external find", new_packages)
        _print_package_yaml("Detected packages.yaml contents", new_packages)
        return

    system_spec = benchpark.spec.SystemSpec(" ".join(args.spec)).concretize()
    system = system_spec.system

    expected_packages = system.compute_packages_section()["packages"]
    expected_pkg_names = sorted(expected_packages.keys())

    _print_system_context(system_spec, system)

    _print_package_table(
        "Expected packages from system.compute_packages_section()",
        expected_packages,
    )

    # This is the object of comparison from the Benchpark system.py.
    _print_package_yaml(
        "Expected packages YAML object from system.py",
        expected_packages,
    )

    subprocess.run(spack_cmd + expected_pkg_names, check=True)

    packages_yaml = _spack_packages_yaml_path()
    detected_packages = _load_packages_yaml(packages_yaml)

    print(f"\nDetected packages file: {packages_yaml}")

    _print_package_table(
        "Detected packages from spack external find",
        detected_packages,
    )

    expected_names = set(expected_packages)
    detected_names = set(detected_packages)

    missing_from_detection = sorted(expected_names - detected_names)
    extra_detected = sorted(detected_names - expected_names)

    _print_name_list(
        "Expected packages not detected by spack external find",
        missing_from_detection,
    )

    _print_name_list(
        "Detected packages not present in system.compute_packages_section()",
        extra_detected,
    )

    _print_changed_packages(expected_packages, detected_packages)

    proposal_requested = (
        args.propose
        or args.patch_file
        or args.write_proposed_system
    )
    if proposal_requested:
        proposals, review = _collect_version_update_proposals(
            expected_packages,
            detected_packages,
        )
        _print_version_update_proposals(proposals, review)
        _emit_system_source_proposal(
            system,
            proposals,
            system_name=system_spec.name,
            proposal_file=args.patch_file,
            proposed_system_file=args.write_proposed_system,
        )

    full_diff = DeepDiff(
        expected_packages,
        detected_packages,
        verbose_level=1,
        ignore_type_in_groups=[(int, str)],
        ignore_string_type_changes=True,
    )

    if not full_diff:
        color.cprint("\n@*gNo package differences detected.@.")
    else:
        color.cprint("\n@*rPackage sections differ.@.")

def setup_parser(root_parser):
    system_subparser = root_parser.add_subparsers(
        dest="system_subcommand", required=True
    )

    init_parser = system_subparser.add_parser("init")
    init_parser.add_argument("--dest", help="Place all system files here directly")
    init_parser.add_argument(
        "--basedir", help="Generate a system dir under this, and place all files there"
    )

    init_parser.add_argument("spec", nargs="+", help="System spec")

    id_parser = system_subparser.add_parser("id")
    id_parser.add_argument("system_dir")

    external_parser = system_subparser.add_parser(
        "external",
        help='Check packages using "spack external find" for current system against the definitions in benchpark.',
    )
    external_parser.add_argument("spec", nargs="+", help="System spec")
    external_parser.add_argument(
        "--new-system",
        help="Flag if system does not exist in benchpark",
        action="store_true",
    )
    external_parser.add_argument(
        "--propose",
        help=(
            "Propose safe version-only updates to literal external specs in the "
            "target system.py. The source file is not modified."
        ),
        action="store_true",
    )
    external_parser.add_argument(
        "--patch-file",
        help=(
            "Write the proposed system.py changes as a unified diff. "
            "This implies --propose."
        ),
    )
    external_parser.add_argument(
        "--write-proposed-system",
        help=(
            "Write a complete proposed system.py copy to this path. "
            "This implies --propose."
        ),
    )


def command(args):
    actions = {
        "init": system_init,
        "id": system_id,
        "external": system_external,
    }
    if args.system_subcommand in actions:
        actions[args.system_subcommand](args)
