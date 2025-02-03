import textwrap

import yaml

import benchpark.paths


def gen_header(name):
    print("=" * 20 + f"\n=== {name}\n" + "=" * 20)


def info_system(args):
    def _info_system_system_site(system_spec):
        gen_header("System Site")
        print(system_spec.system_class.system_site)

    def _info_system_maintainer(system_spec):
        gen_header("Maintainer")
        print(system_spec.system_class.maintainer)

    def _info_system_variants(system_spec):
        gen_header("Variants")
        all_variants = list(system_spec.system_class.variants.values())[0]
        for var in all_variants.values():
            for attr, value in var.__dict__.items():
                print(f"{attr}: {value}")
            print()

    def _info_system_hardware(system_spec):
        gen_header("Hardware")
        for cluster, resource_dict in system_spec.system_class.id_to_resources.items():
            print(f"For cluster {cluster}:")
            for resource_key, resource_value in resource_dict.items():
                if isinstance(resource_value, str) and ".yaml" in resource_value:
                    print(f"\t{resource_key}:")
                    with open(resource_value, "r") as f:
                        data = yaml.safe_load(f)
                        print(textwrap.indent(yaml.dump(data), "\t"))
                else:
                    print(f"\t{resource_key}: {resource_value}")

    system_spec = benchpark.spec.SystemSpec(" ".join(args.spec))

    # Map argument flags to functions
    actions = {
        "system_site": _info_system_system_site,
        "maintainer": _info_system_maintainer,
        "variants": _info_system_variants,
        "hardware": _info_system_hardware,
    }

    # Call functions for enabled options, or all if no flag is set
    any_flag_set = False
    for flag, action in actions.items():
        if getattr(args, flag, False):
            action(system_spec)
            any_flag_set = True

    if not any_flag_set:
        for action in actions.values():
            action(system_spec)


def setup_parser(root_parser):
    info_subparser = root_parser.add_subparsers(dest="info_subcommand")

    system_parser = info_subparser.add_parser("system")
    system_parser.add_argument(
        "--variants", action="store_true", help="Available system variants"
    )
    system_parser.add_argument(
        "--hardware", action="store_true", help="Hardware descriptions per cluster"
    )
    system_parser.add_argument("--system-site", action="store_true", help="System site")
    system_parser.add_argument("--maintainer", action="store_true", help="Maintainer")

    system_parser.add_argument("spec", nargs="+", help="System spec")


def command(args):
    actions = {
        "system": info_system,
    }
    if args.info_subcommand in actions:
        actions[args.info_subcommand](args)
    else:
        raise ValueError(f"Unknown subcommand for 'info': {args.info_subcommand}")
