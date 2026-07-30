# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import thicket as th


def setup_parser(root_parser):
    root_parser.add_argument(
        "base_file",
        type=str,
        help="Baseline Caliper file.",
        metavar="BASE_FILE",
    )
    root_parser.add_argument(
        "compare_file",
        type=str,
        help="Caliper file to compare against the baseline.",
        metavar="COMPARE_FILE",
    )
    root_parser.add_argument(
        "--region",
        required=True,
        type=str,
        help="Region name to compare.",
        metavar="REGION",
    )
    root_parser.add_argument(
        "--metric",
        required=True,
        type=str,
        help="Metric to compare.",
        metavar="METRIC",
    )
    root_parser.add_argument(
        "--metadata-profile-identifier",
        type=str,
        default=None,
        help="Metadata column to use as the profile identifier.",
        metavar="COLUMN",
    )
    root_parser.add_argument(
        "--exclude-regions",
        nargs="+",
        type=str,
        help="One or more patterns to exclude based on region name.",
        metavar="PATTERN",
    )


def command(args):
    tk = th.Thicket.from_caliperreader(
        [args.base_file, args.compare_file], disable_tqdm=True
    )
    profiles = list(tk.profile)

    if args.metadata_profile_identifier:
        profiles = [
            tk.metadata.loc[p, args.metadata_profile_identifier] for p in profiles
        ]
        tk.replace_profile_index(args.metadata_profile_identifier)

    if args.exclude_regions:
        query = th.query.Query().match(
            ".",
            lambda row: row["name"]
            .apply(
                lambda n: n is None
                or all(excl not in n for excl in args.exclude_regions)
            )
            .all(),
        )
        tk = tk.query(query)

    if args.metric not in tk.dataframe.columns and args.metric in tk.metadata.columns:
        tk.metadata_columns_to_perfdata(args.metric)

    values = tk.dataframe.loc[tk.get_node(args.region), args.metric]
    base_profile = profiles[0]
    compare_profile = profiles[1]
    base_value = values.loc[base_profile]
    compare_value = values.loc[compare_profile]
    delta = compare_value - base_value
    pct_change = (compare_value / base_value - 1) * 100

    print(f"{args.region}, {args.metric}")
    print(f"{base_profile}: {base_value:.6g}")
    print(f"{compare_profile}: {compare_value:.6g}")
    print(f"{delta:.6g}")

    return 0
