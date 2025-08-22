# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import re
import logging
import sys
import shlex
from glob import glob
import tarfile
import shutil
from datetime import datetime

import warnings
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt
import matplotlib as mpl
import thicket as th

# -----------------------------
# Constants
# -----------------------------
COLOR_PALETTE = [
    "#1f77b4",  # Blue
    "#ff7f0e",  # Orange
    "#2ca02c",  # Green
    "#d62728",  # Red
    "#9467bd",  # Purple
    "#8c564b",  # Brown
    "#e377c2",  # Pink
    "#7f7f7f",  # Gray
    "#bcbd22",  # Olive
    "#17becf",  # Cyan
    "#aec7e8",  # Light Blue
    "#ffbb78",  # Light Orange
    "#98df8a",  # Light Green
    "#ff9896",  # Light Red
    "#c5b0d5",  # Light Purple
    "#c49c94",  # Light Brown
    "#f7b6d2",  # Light Pink
    "#c7c7c7",  # Light Gray
    "#dbdb8d",  # Light Olive
    "#9edae5",  # Light Cyan
]
SCALING_TYPES = ["strong", "throughput", "weak"]
NAME_REMAP = {
    "total_problem_size": "Total Problem Size",
    "process_problem_size": "Process Problem Size",
    "n_resources": "MPI Ranks",
    "n_nodes": "Node(s)",
}

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s: %(message)s")


# -----------------------------
# Helper Functions
# -----------------------------
def get_scaling_type(spec):
    """
    Determines the scaling type based on a specification string.

    Args:
        spec (str): Specification string containing scaling information.

    Returns:
        str: The identified scaling type ("strong", "throughput", or "weak").

    Raises:
        ValueError: If no valid scaling type is found in the specification.
    """

    for keyword in SCALING_TYPES:
        if "+" + keyword in spec:
            return keyword

    raise ValueError(f"Unknown scaling type. Must be one of {SCALING_TYPES}")


def validate_single_metadata_value(column, tk):
    """
    Validates that a Thicket metadata column has a single unique value.

    Args:
        column (str): Column name to check.
        tk (th.Thicket): Thicket object.

    Returns:
        Any: The single unique value in the column.

    Raises:
        ValueError: If the column contains more than one unique value.
    """
    unique_vals = tk.metadata[column].unique()
    if len(unique_vals) != 1:
        raise ValueError(f"Expected one {column}, got: {list(unique_vals)}")
    return unique_vals[0]


# -----------------------------
# Workspace utils
# -----------------------------
def _validate_workspace_dir(workspace_dir):
    if not os.path.isdir(workspace_dir):
        raise ValueError(
            f"Workspace dir '{workspace_dir}' does not exist or is not a directory"
        )
    if ".ramble-workspace" not in os.listdir(workspace_dir):
        raise ValueError(
            f"Directory '{workspace_dir}' must be a valid ramble workspace (missing .ramble-workspace)"
        )
    return os.path.abspath(workspace_dir)


def _write_last_cmd(analyze_dir):
    last_cmd_file = os.path.join(analyze_dir, ".last-command.sh")
    with open(last_cmd_file, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("benchpark " + " ".join([shlex.quote(arg) for arg in sys.argv[1:]]))


def workspace_clean(workspace_dir, dry_run=False):
    entries = [
        os.path.join(workspace_dir, e)
        for e in os.listdir(workspace_dir)
        if e not in {".", ".."}
    ]
    logger.info("Cleaning workspace contents: %s", workspace_dir)
    for path in entries:
        if os.path.basename(path) == ".ramble-workspace":
            continue
        if dry_run:
            logger.info("[dry-run] Would remove %s", path)
            continue
        try:
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path)
                logger.info("Removed directory %s", path)
            else:
                os.remove(path)
                logger.info("Removed file %s", path)
        except FileNotFoundError:
            logger.debug("Already gone: %s", path)


def analyze_archive(analyze_dir, cali_files, output=None):
    if output is None:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        base = os.path.basename(os.path.normpath(analyze_dir))
        output = os.path.join(analyze_dir, f"{base}-{ts}.tar.gz")
    logger.info("Creating archive %s from %s", output, analyze_dir)
    with tarfile.open(output, "w:gz") as tar:
        tar.add(
            analyze_dir,
            arcname=os.path.basename(analyze_dir),
            filter=lambda ti: None if ti.name.endswith(".tar.gz") else ti,
        )
        for f in cali_files:
            tar.add(f, arcname=os.path.basename(f))
    logger.info("Archive written: %s", output)
    return output


# -----------------------------
# Chart Generation
# -----------------------------
def make_stacked_line_chart(**kwargs):
    """
    Generates a stacked area line chart based on Thicket DataFrame.

    Args:
        df (pd.DataFrame): DataFrame to plot.
        chart_type (str): Type of chart ("raw" or "percentage").
        x_axis (list): Metadata keys to use for the X-axis.
        yaxis_metric (str): Metric to plot on the Y-axis.
        chart_ylabel (str, optional): Y-axis label.
        chart_title (str, optional): Chart title.
        chart_xlabel (str, optional): X-axis label.
        chart_fontsize (int, optional): Font size.
        chart_figsize (tuple, optional): Figure size.
        chart_file_name (str): Name for the saved files.
        out_dir (str): Directory to save output images and CSV.
    """
    df = kwargs.get("df")
    chart_type = kwargs.get("chart_type")
    x_axis = kwargs.get("x_axis")
    yaxis_metric = kwargs.get("yaxis_metric")

    value = "perc" if chart_type == "percentage" else yaxis_metric
    y_label = kwargs.get("chart_ylabel") or (
        f"Percentage of {yaxis_metric}" if chart_type == "percentage" else yaxis_metric
    )

    os.makedirs(kwargs["out_dir"], exist_ok=True)

    tdf_calls = df[[(i, "Calls/rank (max)") for i in x_axis]].T.reset_index(
        level=1, drop=True
    )
    calls_list = []
    for column in tdf_calls.columns:
        mx = max(tdf_calls[column])
        val = int(mx) if mx > 0 else 0
        calls_list.append((column, val))

    tdf = df[[(i, value) for i in x_axis]].T.reset_index(level=1, drop=True)
    mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=COLOR_PALETTE)
    if kwargs.get("chart_fontsize"):
        mpl.rcParams.update({"font.size": kwargs.get("chart_fontsize")})

    xlabel = kwargs.get("chart_xlabel")
    if isinstance(xlabel, list):
        xlabel = ", ".join(NAME_REMAP[x] for x in xlabel)
    else:
        if xlabel in NAME_REMAP:
            xlabel = NAME_REMAP[xlabel]
    fig, ax = plt.subplots()
    tdf.plot(
        kind="area",
        title=kwargs.get("chart_title", ""),
        xlabel=xlabel,
        ylabel=y_label,
        figsize=kwargs["chart_figsize"] if kwargs["chart_figsize"] else (12, 7),
        ax=ax,
    )
    y_axis_limits = kwargs.get("chart_yaxis_limits")
    if y_axis_limits is not None:
        ax.set_ylim(y_axis_limits[0], y_axis_limits[1])

    handles, labels = ax.get_legend_handles_labels()
    handles = list(reversed(handles))
    labels = list(reversed(labels))
    calls_list = list(reversed(calls_list))
    for i, label in enumerate(labels):
        obj = calls_list[i][0]
        name = obj if isinstance(obj, str) else obj[0].frame["name"]
        if name not in label:
            raise ValueError(f"Name '{name}' is not in label '{label}'")
        labels[i] = str(name) + " (" + str(calls_list[i][1]) + ")"
    ax.legend(
        handles,
        labels,
        bbox_to_anchor=(1, 0.5),
        loc="center left",
        title="Region (Calls/rank (max))",
    )

    fig.autofmt_xdate()
    plt.tight_layout()

    filename = os.path.join(kwargs["out_dir"], kwargs["chart_file_name"])
    logger.info(f"Saving figure data points to {filename}.csv")
    tdf.to_csv(filename + ".csv")
    logger.info(f"Saving figure to {filename}.png")
    plt.savefig(filename + ".png")
    logger.info(
        "Note: ordering of regions in the figure are in reverse order of the tree."
    )


# ----------------
# Data Preparation
# ----------------
def prepare_data(**kwargs):
    """
    Processes .cali files from a Ramble workspace to generate performance charts.
    """
    files = kwargs["cali_files"]
    logger.info(f"Found {len(files)} .cali files for analysis.")

    if kwargs["calltree_unification"] == "intersection":
        intersection = True
    else:
        intersection = False
    tk = th.Thicket.from_caliperreader(
        files, intersection=intersection, disable_tqdm=True
    )
    tk.update_inclusive_columns()

    clean_tree = tk.tree(kwargs["tree_metric"], render_header=True)
    clean_tree = re.compile(r"\x1b\[([0-9;]*m)").sub("", clean_tree)

    # Remove MPI regions, if necesasry
    if kwargs.get("no_mpi"):
        query = th.query.Query().match(
            ".",
            lambda row: row["name"]
            .apply(
                # 'n is None' avoid comparison for MPI in n (will cause error)
                lambda n: n is None
                or "MPI_" not in n
            )
            .all(),
        )
        tk = tk.query(query)

    # Remove singular roots if inclusive metric
    metric = kwargs["yaxis_metric"]
    if metric in tk.inc_metrics and len(tk.graph.roots) == 1:
        root_name = tk.graph.roots[0].frame["name"]
        logger.info(
            f"Removing root '{root_name}' to improve chart readability for inclusive metric."
        )
        query = (
            th.query.Query()
            .match(".", lambda row: row["name"].apply(lambda n: n != root_name).all())
            .rel("*")
        )
        tk = tk.query(query)

    # Spec should not vary across runs
    spec = tk.metadata["benchpark_spec"].iloc[0][0]
    scaling = get_scaling_type(spec)

    # What we are varying for each scaling type
    x_axis_metadata = (
        kwargs.get("xaxis_parameter")
        or {
            "strong": ["n_nodes", "n_resources"],
            "weak": ["n_nodes", "n_resources", "total_problem_size"],
            "throughput": "total_problem_size",
        }[scaling]
    )
    kwargs["xaxis_parameter"] = x_axis_metadata

    if kwargs.get("group_regions_name"):
        logger.info(
            "Computing sum of metrics for regions with the same name. Warning: this operation also sums Calls/rank value in figure legend, for affected regions."
        )
        grouped = (
            tk.dataframe.reset_index()
            .groupby(["name", "profile"])
            .agg(
                {
                    **{
                        col: "sum"
                        for col in tk.dataframe.select_dtypes(include="number").columns
                    },
                    "node": "first",
                }
            )
            .reset_index()
            .set_index(["node", "profile"])
        )
        tk.dataframe = grouped
        tk = tk.squash()

    region_name = kwargs.get("query_region_byname", "")
    if region_name:
        children = False
        if region_name.endswith(":nochildren"):
            region_name = region_name.rstrip(":nochildren")
        else:
            children = True

        query = th.query.Query().match(
            ".", lambda row: row["name"].apply(lambda n: n == region_name).all()
        )

        if children:
            query = query.rel("*")

        tk = tk.query(query)

    prefix = kwargs.get("filter_regions_byname", "")
    if prefix:
        tk.dataframe = tk.dataframe.filter(like=prefix, axis=0)

    # Group by varied parameters
    grouped = tk.groupby(x_axis_metadata)
    ctk = th.Thicket.concat_thickets(
        list(grouped.values()), headers=list(grouped.keys()), axis="columns"
    )

    cluster_col = "cluster" if "cluster" in tk.metadata.columns else "host.cluster"
    # Check these values are constant
    app = validate_single_metadata_value("application_name", tk)
    cluster = validate_single_metadata_value(cluster_col, tk)
    version = validate_single_metadata_value("version", tk)

    # Find programming model from spec
    programming_model = "mpi"
    for keyword in ["+cuda", "+rocm", "+openmp"]:
        if keyword in spec:
            programming_model = keyword.lstrip("+")

    # Constant information that will be added to the title
    constant_keys = {
        "strong": ["total_problem_size"],
        "weak": ["process_problem_size"],
        "throughput": ["n_resources", "n_nodes"],
    }[scaling]
    constant_str = ", ".join(
        f"{int(tk.metadata[key].iloc[0]):,} {NAME_REMAP[key]}" for key in constant_keys
    )
    # Check constant
    for key in constant_keys:
        validate_single_metadata_value(key, tk)

    if not kwargs.get("chart_title"):
        kwargs["chart_title"] = (
            f"{app}+{programming_model}@{version} on {cluster} ({scaling} scaling)\n{constant_str}"
        )

    if kwargs["output_filename"]:
        kwargs["chart_file_name"] = kwargs["output_filename"]
    else:
        kwargs["chart_file_name"] = (
            f"{app}_{programming_model}_{scaling}_{kwargs['chart_type']}_{'inc' if metric in tk.inc_metrics else 'exc'}"
        )

    # Save tree to file
    tree_file = os.path.join(kwargs["out_dir"], kwargs["chart_file_name"] + "-tree.txt")
    with open(tree_file, "w") as f:
        f.write(clean_tree)
    logger.info(f"Saving Input Calltree to {tree_file}")

    for key in grouped.keys():
        ctk.dataframe[(key, "perc")] = (
            ctk.dataframe[(key, metric)] / ctk.dataframe[(key, metric)].sum()
        ) * 100

    top_n = kwargs.get("top_n_regions", -1)
    if top_n != -1:
        temp_df_idx = ctk.dataframe.nlargest(
            top_n, [(list(grouped.keys())[0], metric)]
        ).index
        temp_df = ctk.dataframe[ctk.dataframe.index.isin(temp_df_idx)]
        temp_df.loc["Sum(removed_regions)"] = 0
        for p in ctk.profile:
            temp_df.loc["Sum(removed_regions)", (p[1], metric)] = (
                ctk.dataframe.loc[:, (p[1], metric)].sum()
                - temp_df.loc[:, (p[1], metric)].sum()
            ).iloc[0]
        ctk.dataframe = temp_df
        logger.info(
            f"Filtered top {top_n} regions for chart display. Added the sum of the regions that were removed as single region."
        )

    if not kwargs.get("chart_xlabel"):
        kwargs["chart_xlabel"] = x_axis_metadata

    if "scaling-factor" in tk.metadata.columns:
        scaling_factors = tk.metadata["scaling-factor"].unique()
        if len(scaling_factors) == 1:
            kwargs["scaling-factor"] = scaling_factors[0]
        else:
            raise ValueError(
                f"Expected one scaling factor, found: {list(scaling_factors)}"
            )

    make_stacked_line_chart(df=ctk.dataframe, x_axis=list(grouped.keys()), **kwargs)


def setup_parser(root_parser):
    """
    Adds command-line arguments to the analyze parser, and supports trailing
    positional actions: `clean` and `archive`.
    """
    root_parser.add_argument(
        "--workspace-dir",
        required=True,
        type=str,
        help="Directory of ramble workspace.",
        metavar="RAMBLE_WORKSPACE_DIR",
    )
    root_parser.add_argument(
        "--calltree-unification",
        default="union",
        choices=["intersection", "union"],
        type=str,
        help="Type of unification operation to perform the Caliper calltrees.",
    )
    root_parser.add_argument(
        "--chart-type",
        default="raw",
        choices=["raw", "percentage"],
        type=str,
        help="Specify processing on the metric. 'raw' does nothing, 'percentage' shows the metric values as a percentage relative to the total summation of all regions.",
    )
    root_parser.add_argument(
        "--xaxis-parameter",
        default=None,
        type=str,
        nargs="+",
        help="One or more parameters from the metadata that are varied during the experiment (values will become the x-axis).",
        metavar="PARAM",
    )
    root_parser.add_argument(
        "--yaxis-metric",
        default="Avg time/rank (exc)",
        type=str,
        help="Performance metric to be visualized on the y-axis.",
    )
    root_parser.add_argument(
        "--filter-regions-byname",
        default="",
        type=str,
        help="Filter for region names starting with PREFIX.",
        metavar="PREFIX",
    )
    root_parser.add_argument(
        "--query-region-byname",
        default="",
        type=str,
        help="Query for specific region REGION. Includes children of region by default, for no children specify 'REGION:nochildren'.",
        metavar="REGION",
    )
    root_parser.add_argument(
        "--top-n-regions",
        default=-1,
        type=int,
        help="Filters only top N largest metric entries to be included in chart (based on the first profile).",
        metavar="N",
    )
    root_parser.add_argument(
        "--group-regions-name",
        action="store_true",
        help="Whether to combine regions (sum of metric) with the same name.",
    )
    root_parser.add_argument(
        "--no-mpi", action="store_true", help="Hide MPI regions in the tree."
    )
    root_parser.add_argument(
        "--chart-title",
        default=None,
        type=str,
        help="Title of the output chart.",
    )
    root_parser.add_argument("--chart-xlabel", type=str, help="X Label of chart.")
    root_parser.add_argument("--chart-ylabel", type=str, help="Y Label of chart.")
    root_parser.add_argument(
        "--chart-figsize",
        nargs="+",
        type=int,
        help="Size of the output chart (xdim, ydim). Ex: --chart-figsize 12 6",
    )
    root_parser.add_argument(
        "--chart-fontsize", type=int, help="Font size of the output chart."
    )
    root_parser.add_argument(
        "--chart-yaxis-limits",
        type=float,
        nargs=2,
        metavar=("YMIN", "YMAX"),
        default=None,
        help="Set both y-axis limits: --chart-yaxis-limits YMIN YMAX",
    )
    root_parser.add_argument(
        "--file-name-match",
        type=str,
        default="",
        help="Set optional cali file name to match. Useful if multiple caliper files are generated per experiment (e.g. RAJAPerf)",
    )
    root_parser.add_argument(
        "--output-filename",
        type=str,
        default=None,
        help="Configure the output file names (the default value is already unique to the workspace).",
    )
    root_parser.add_argument(
        "--tree-metric",
        type=str,
        default="Calls/rank (max)",
        help="Metric to show on the tree output",
    )

    # Workspace commands
    root_parser.add_argument(
        "action",
        nargs="?",
        choices=["clean", "archive"],
        help=(
            "Optional trailing action to manage the workspace: 'clean' to remove contents, "
            "'archive' to create a tar.gz of the workspace. If omitted, performs analysis."
        ),
    )
    root_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With 'clean', show items that would be removed without deleting.",
    )
    root_parser.add_argument(
        "--archive-output",
        type=str,
        default=None,
        help="With 'archive', path for the .tar.gz (defaults to CWD/<workspace>-<timestamp>.tar.gz)",
    )


def command(args):
    """
    Implements either analysis (default) or the trailing `clean`/`archive` actions
    requested as positional arguments after `analyze`.
    """

    def _setup_dir(args):
        wkp_dir = args.workspace_dir
        if wkp_dir[-1] != "/":
            wkp_dir += "/"
        args.out_dir = wkp_dir + "analyze/"
        if not os.path.isdir(args.out_dir):
            os.mkdir(args.out_dir)
        _validate_workspace_dir(wkp_dir)
        args.cali_files = glob(
            os.path.join(wkp_dir, f"**/*{args.file_name_match}.cali"),
            recursive=True,
        )
        return args

    args = _setup_dir(args)

    # Handle workspace management actions first
    if getattr(args, "action", None) == "clean":
        workspace_clean(args.out_dir, dry_run=getattr(args, "dry_run", False))
        return
    if getattr(args, "action", None) == "archive":
        out = analyze_archive(
            args.out_dir, args.cali_files, output=getattr(args, "archive_output", None)
        )
        print(out)
        return

    _write_last_cmd(args.out_dir)

    prepare_data(**vars(args))

    return 0
