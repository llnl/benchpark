import subprocess
import textwrap

import yaml
import spack.cmd.info as spackinfo

import benchpark.paths


def gen_header(name):
    print("=" * 20 + f"\n=== {name}\n" + "=" * 20)


def info_variants(spec_class):
    """SystemSpec.system_class or ExperimentSpec.experiment_class"""
    gen_header("Variants")
    all_variants = list(spec_class.variants.values())[0]
    for var in all_variants.values():
        for attr, value in var.__dict__.items():
            print(f"{attr}: {value}")
        print()


def info_maintainer(spec_class):
    """SystemSpec.system_class or ExperimentSpec.experiment_class"""
    gen_header("Maintainer")
    print(spec_class.maintainer)


def info_system(args):
    def _info_system_system_site(system_class):
        gen_header("System Site")
        print(system_class.system_site)

    def _info_system_hardware(system_class):
        gen_header("Hardware")
        for cluster, resource_dict in system_class.id_to_resources.items():
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
    system_class = system_spec.system_class

    # Map argument flags to functions
    actions = {
        "system_site": (_info_system_system_site, [system_class]),
        "maintainer": (info_maintainer, [system_class]),
        "variants": (info_variants, [system_class]),
        "hardware": (_info_system_hardware, [system_class]),
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
    def _info_url(experiment_class):
        gen_header("URL")
        print(experiment_class.url)

    experiment_spec = benchpark.spec.ExperimentSpec(" ".join(args.spec))
    experiment_class = experiment_spec.experiment_class

    #spackinfo.print_variants(experiment_class)

    if args.spack:
        subprocess.run(["spack", "info", experiment_class.spack_name])
        return
    elif args.ramble:
        subprocess.run(["ramble", "info", experiment_class.ramble_name])
        return
    else:
        actions = {
            "variants": (info_variants, [experiment_class]),
            "maintainer": (info_maintainer, [experiment_class]),
            "url": (_info_url, [experiment_class]),
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

    experiment_parser = info_subparser.add_parser("experiment")
    experiment_parser.add_argument(
        "--spack", action="store_true", help="Information from Spack package"
    )
    experiment_parser.add_argument(
        "--ramble", action="store_true", help="Information from Ramble package"
    )
    experiment_parser.add_argument(
        "--url", action="store_true", help="URL for experiment"
    )
    experiment_parser.add_argument("spec", nargs="+", help="Experiment spec")


def command(args):
    actions = {
        "system": info_system,
        "experiment": info_experiment,
    }
    if args.info_subcommand in actions:
        actions[args.info_subcommand](args)
    else:
        raise ValueError(f"Unknown subcommand for 'info': {args.info_subcommand}")
