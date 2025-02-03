import textwrap

import yaml

import benchpark.paths


def gen_header(name):
    print("=" * 20 + f"\n=== {name}\n" + "=" * 20)


def info_system_system_site(system_spec):
    gen_header("System Site")
    print(system_spec.system_class.system_site)


def info_system_maintainer(system_spec):
    gen_header("Maintainer")
    print(system_spec.system_class.maintainer)


def info_system_variants(system_spec):
    gen_header("Variants")
    # Dict with one value
    all_variants = list(system_spec.system_class.variants.values())[0]
    for var in all_variants.values():
        for attr in var.__dict__.keys():
            print(attr + ":", var.__dict__[attr])
        print()
        # print(var.name+":", var.values)


def info_system_hardware(system_spec):
    gen_header("Hardware")
    for cluster, resource_dict in system_spec.system_class.id_to_resources.items():
        print("For cluster", cluster + ":")
        for resource_key, resource_value in resource_dict.items():
            if isinstance(resource_value, str) and ".yaml" in resource_value:
                print("\t" + resource_key + ":")
                data = yaml.safe_load(open(resource_value, "r"))
                print(textwrap.indent(yaml.dump(data), "\t"))
            else:
                print("\t" + resource_key + ":", resource_value)


def info_system(args):
    system_spec = benchpark.spec.SystemSpec(" ".join(args.spec))

    if args.system_site:
        info_system_system_site(system_spec)
    if args.maintainer:
        info_system_maintainer(system_spec)
    if args.variants:
        info_system_variants(system_spec)
    if args.hardware:
        info_system_hardware(system_spec)
    if not args.system_site and not args.variants and not args.hardware:
        info_system_system_site(system_spec)
        info_system_maintainer(system_spec)
        info_system_variants(system_spec)
        info_system_hardware(system_spec)


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
