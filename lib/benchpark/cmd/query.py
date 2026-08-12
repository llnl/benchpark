# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import shlex
import sys
from datetime import datetime
from glob import glob

import pandas as pd
import thicket as th


def setup_parser(root_parser):
    root_parser.add_argument(
        "directories",
        nargs="+",
        type=str,
        help="One or more directories to recursively search for Caliper files.",
        metavar="DIRECTORY",
    )
    root_parser.add_argument(
        "--query-regions-byname",
        default=[],
        nargs="+",
        type=str,
        help="Region name substring(s) to query.",
        metavar="REGION",
    )
    root_parser.add_argument(
        "--filter-regions-byname",
        default=[],
        nargs="+",
        type=str,
        help="Filter for region names starting with one or more PREFIX values.",
        metavar="PREFIX",
    )
    root_parser.add_argument(
        "--metric",
        required=True,
        type=str,
        help="Metric to query.",
        metavar="METRIC",
    )
    root_parser.add_argument(
        "--metadata-columns",
        nargs="+",
        default=[],
        type=str,
        help="Metadata columns to include in the CSV.",
        metavar="COLUMN",
    )
    root_parser.add_argument(
        "--exclude-regions",
        nargs="+",
        type=str,
        help="One or more patterns to exclude based on region name.",
        metavar="PATTERN",
    )


def _command_line(args):
    if hasattr(args, "command_line"):
        return args.command_line
    return "benchpark " + shlex.join(sys.argv[1:])


def _write_csv(df, filename, args):
    with open(filename, "w", newline="") as csv_file:
        csv_file.write(f"# {_command_line(args)}\n")
        df.to_csv(csv_file, index=False)


def command(args):
    cali_files = []
    for directory in args.directories:
        cali_files.extend(glob(os.path.join(directory, "**/*.cali"), recursive=True))
    if not cali_files:
        raise ValueError(f"No Caliper files found under {args.directories}")

    tk = th.Thicket.from_caliperreader(cali_files, disable_tqdm=True)
    columns = ["cluster", "application_name"] + args.metadata_columns

    if args.metric in tk.metadata.columns:
        df = tk.metadata[columns + [args.metric]]
        filename = f"query-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
        _write_csv(df, filename, args)
        print(filename)
        return 0

    if not args.query_regions_byname and not args.filter_regions_byname:
        raise ValueError(
            "Must provide --query-regions-byname or --filter-regions-byname "
            "when --metric is not a metadata column."
        )

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

    if args.query_regions_byname:
        query = (
            th.query.Query()
            .match(
                ".",
                lambda row: row["name"]
                .apply(
                    lambda n: n is not None
                    and any(r in n for r in args.query_regions_byname)
                )
                .all(),
            )
            .rel("*")
        )
        if args.filter_regions_byname:
            query = query.rel("*")
        tk = tk.query(query)

    prefix = args.filter_regions_byname
    if prefix:
        tk.dataframe = pd.concat([tk.dataframe.filter(like=p, axis=0) for p in prefix])
        tk = tk.squash()

    tk.metadata_columns_to_perfdata(columns)

    df = tk.dataframe[columns + [args.metric]]
    if df.empty:
        raise ValueError(
            f"No regions matched query={args.query_regions_byname} "
            f"filter={args.filter_regions_byname} under {args.directories}"
        )
    df = (
        df.reset_index()
        .groupby("profile", as_index=False)
        .agg({**{col: "first" for col in columns}, args.metric: "sum"})
    )
    df = df[columns + [args.metric]]

    filename = f"query-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"

    _write_csv(df, filename, args)
    print(filename)

    return 0
