import os
import subprocess
import textwrap

import llnl.util.tty.color as color
import yaml

import benchpark.paths


def indent():
    return " " * 4


def gen_header(name):
    attr_name = "@*b" + name + "@."
    color.cprint(f"{attr_name}:")


def info_variants(spec_class):
    """SystemSpec.system_class or ExperimentSpec.experiment_class"""
    gen_header("Variants")
    all_variants = list(spec_class.variants.values())[0]
    for var in all_variants.values():
        for attr, value in var.__dict__.items():
            color.cprint(indent() + "@*g" + attr + "@.: " + str(value))
        print()


def info_maintainers(spec_class):
    """SystemSpec.system_class or ExperimentSpec.experiment_class"""
    gen_header("Maintainers")
    print(indent() + ",".join(spec_class.maintainers))


def info_system(args):
    def _info_system_hardware(system_class):
        def _replace_keys_with_colors(data, colors, level=0):
            if not isinstance(data, dict):
                return data

            new_data = {}
            for key, value in data.items():
                color_prefix = (
                    colors[level % len(colors)] if level < len(colors) else ""
                )
                new_key = color_prefix + key + "@."
                new_data[new_key] = _replace_keys_with_colors(value, colors, level + 1)

            return new_data

        gen_header("Hardware")
        for cluster, resource_dict in system_class.id_to_resources.items():
            color.cprint(f"{indent()}@*g{cluster}@.:")
            for resource_key, resource_value in resource_dict.items():
                if resource_key == "hardware_key":
                    with open(resource_value, "r") as f:
                        data = yaml.safe_load(f)
                        colors = ["@*r", "@*c", "@*m", "@*y"]
                        data = _replace_keys_with_colors(data, colors)
                        color.cprint(
                            textwrap.indent(
                                yaml.dump(data).replace("'", ""), indent() * 2
                            )
                        )
                else:
                    resource_key = "@*r" + resource_key + "@."
                    color.cprint(f"{indent()*2}{resource_key}: {resource_value}")

    def _handle_query(query):
        key, value = query.split("=", 1)
        exclude = {"all_hardware_descriptions", "repo.yaml", "generic-x86"}
        all_system_specs = []
        for d in set(os.listdir(benchpark.paths.benchpark_root / "systems")) - exclude:
            all_system_specs.append(benchpark.spec.SystemSpec(d))

        matching_systems = []
        for spec in all_system_specs:
            resources = spec.system_class.id_to_resources
            for cluster, resource_dict in resources.items():
                if str(resource_dict.get(key)) == value:
                    matching_systems.append((spec.name, cluster))

        if matching_systems:
            gen_header(query)
            for system_name, cluster in matching_systems:
                color.cprint(f"{indent()}@*g{system_name}@.: {cluster}")
        else:
            print("No matching systems found.")

    if args.query:
        _handle_query(args.query)
        return

    system_spec = benchpark.spec.SystemSpec(args.name)
    system_class = system_spec.system_class

    # Map argument flags to functions
    actions = {
        "hardware": (_info_system_hardware, [system_class]),
        "maintainers": (info_maintainers, [system_class]),
        "variants": (info_variants, [system_class]),
    }

    # Call functions for enabled options, or all if no flag is set
    any_flag_set = False
    for flag, (action, aargs) in actions.items():
        if getattr(args, flag, False):
            action(*aargs)
            any_flag_set = True

    if not any_flag_set:
        for action, aargs in actions.values():
            action(*aargs)


def info_experiment(args):
    def _info_spack_name(experiment_class):
        gen_header("Spack Name")
        print(
            indent()
            + (
                experiment_class.spack_name
                if experiment_class.spack_name
                else experiment_class.name
            )
        )

    def _info_ramble_name(experiment_class):
        gen_header("Ramble Name")
        print(
            indent()
            + (
                experiment_class.ramble_name
                if experiment_class.ramble_name
                else experiment_class.name
            )
        )

    experiment_spec = benchpark.spec.ExperimentSpec(args.name)
    conc = experiment_spec.concretize()
    experiment_class = conc.experiment

    if args.spack:
        subprocess.run(
            [
                "spack",
                "info",
                (
                    experiment_class.spack_name
                    if experiment_class.spack_name
                    else experiment_class.name
                ),
            ]
        )
        return
    elif args.ramble:
        subprocess.run(
            [
                "ramble",
                "info",
                (
                    experiment_class.ramble_name
                    if experiment_class.ramble_name
                    else experiment_class.name
                ),
            ]
        )
        return
    else:
        actions = {
            "maintainers": (info_maintainers, [experiment_class]),
            "ramble_name": (_info_ramble_name, [experiment_class]),
            "spack_name": (_info_spack_name, [experiment_class]),
            "variants": (info_variants, [experiment_class]),
        }

        # Call functions for enabled options, or all if no flag is set
        any_flag_set = False
        for flag, (action, aargs) in actions.items():
            if getattr(args, flag, False):
                action(*aargs)
                any_flag_set = True

        if not any_flag_set:
            for action, aargs in actions.values():
                action(*aargs)


def setup_parser(root_parser):
    info_subparser = root_parser.add_subparsers(dest="info_subcommand", required=True)

    system_parser = info_subparser.add_parser("system")
    system_parser.add_argument(
        "--variants", action="store_true", help="Available system variants"
    )
    system_parser.add_argument(
        "--hardware", action="store_true", help="Hardware descriptions per cluster"
    )
    system_parser.add_argument("--system-site", action="store_true", help="System site")
    system_parser.add_argument("--maintainers", action="store_true", help="Maintainers")
    system_parser.add_argument(
        "--query", type=str, help="Query systems with key-value pairs (e.g., key=value)"
    )
    system_parser.add_argument("name", help="System name", nargs="?")

    experiment_parser = info_subparser.add_parser("experiment")
    experiment_parser.add_argument(
        "--spack", action="store_true", help="Information from Spack package"
    )
    experiment_parser.add_argument(
        "--ramble", action="store_true", help="Information from Ramble package"
    )
    experiment_parser.add_argument(
        "--variants", action="store_true", help="Available experiment variants"
    )
    experiment_parser.add_argument(
        "--maintainers", action="store_true", help="Maintainers"
    )
    experiment_parser.add_argument("name", help="Experiment name")


def command(args):
    actions = {
        "system": info_system,
        "experiment": info_experiment,
    }
    if args.info_subcommand in actions:
        actions[args.info_subcommand](args)
