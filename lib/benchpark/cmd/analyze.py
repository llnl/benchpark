# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import re
import shlex
import shutil
import sys
import tarfile
import warnings
from datetime import datetime
from glob import glob
from importlib.metadata import version

import hatchet as ht
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn
import thicket as th
from packaging.version import Version
from tqdm import tqdm

min_hatchet = "2025.2.0"
min_thicket = "2026.1.0"

hatchet_v = version("llnl-hatchet")
thicket_v = version("llnl-thicket")

assert Version(hatchet_v) >= Version(min_hatchet), (
    f"llnl-hatchet {hatchet_v} installed; " f"require >= {min_hatchet}"
)

assert Version(thicket_v) >= Version(min_thicket), (
    f"llnl-thicket {thicket_v} installed; " f"require >= {min_thicket}"
)

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

warnings.filterwarnings("ignore")
# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s: %(message)s")


class RAJAPerf:
    def __init__(self, tk):
        self.tk = tk
        # Matches application_name column in metadata
        self.name = "raja-perf"

    def set_metrics(self):
        self.tk.dataframe["Memory Bandwidth (GB/s)"] = (
            self.tk.dataframe["Bytes/Rep"]
            / self.tk.dataframe["Avg time/rank (exc)"]
            / 10**9
            * self.tk.dataframe["Reps"]
            * self.tk.metadata["mpi.world.size"]
        )

        self.tk.dataframe["FLOP Rate (GFLOPS)"] = (
            self.tk.dataframe["Flops/Rep"]
            / self.tk.dataframe["Avg time/rank (exc)"]
            / 10**9
            * self.tk.dataframe["Reps"]
            * self.tk.metadata["mpi.world.size"]
        )

        return ["Memory Bandwidth (GB/s)", "FLOP Rate (GFLOPS)"]


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
def make_chart(**kwargs):
    """
    Generates a chart based on Thicket DataFrame.

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

    y_label = kwargs.get("chart_ylabel") or (
        f"Percentage of {yaxis_metric}" if chart_type == "percentage" else yaxis_metric
    )
    yaxis_metric = (
        yaxis_metric + "-perc" if chart_type == "percentage" else yaxis_metric
    )

    os.makedirs(kwargs["out_dir"], exist_ok=True)

    # Calls/rank in legend
    calls_dict = {}
    for node in set(df.index.get_level_values("node")):
        v = df.loc[node, "Calls/rank (max)"].max()
        name = node.frame["name"] if isinstance(node, ht.node.Node) else node
        calls_dict[name] = int(v) if pd.notna(v) else v

    mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=COLOR_PALETTE)
    if kwargs.get("chart_fontsize"):
        mpl.rcParams.update({"font.size": kwargs.get("chart_fontsize")})

    xlabel = kwargs.get("chart_xlabel")
    if isinstance(xlabel, list):
        xlabel = ", ".join(NAME_REMAP[x] for x in xlabel)
    else:
        if xlabel in NAME_REMAP:
            xlabel = NAME_REMAP[xlabel]
    fig, ax = plt.subplots(figsize=kwargs.get("chart_figsize", (12, 7)))
    kind = kwargs.get("chart_kind", "line")
    ax.set_title(kwargs.get("chart_title", ""))
    ax.set_xlabel(xlabel)
    ax.set_ylabel(y_label)
    if kwargs["yaxis_log"]:
        ax.set_yscale("log", base=2)
    plt.grid(True)
    df = df.sort_values(by=x_axis)
    plot_args = dict(
        ax=ax,
    )
    if kind == "area":
        plot_args["kind"] = "area"
        df["xaxis"] = df.apply(lambda row: tuple(row[col] for col in x_axis), axis=1)
    else:
        plot_args["data"] = df
        plot_args["x"] = "xaxis"
        plot_args["y"] = yaxis_metric
        df["xaxis"] = df.apply(
            lambda row: ", ".join([str(row[col]) for col in x_axis]), axis=1
        )
    if yaxis_metric not in df.columns:
        raise KeyError(f"'{yaxis_metric}' not in the data. Choose from: {df.columns}")
    if kwargs["cluster"] == "multiple":
        plot_args["hue"] = "cluster"
    # Add marker only if line plot
    if kind == "line":
        plot_args["marker"] = "o"
        seaborn.lineplot(**plot_args)
    elif kind == "area":
        tdf = df[[yaxis_metric, "name", "xaxis"]].reset_index().sort_values("xaxis")
        tdf["node"] = tdf["node"].apply(
            lambda i: (
                ht.node.Node(ht.frame.Frame({"name": i})) if isinstance(i, str) else i
            )
        )
        tdf = tdf.pivot(index="xaxis", columns="node", values=yaxis_metric)
        tdf = tdf.rename(columns={col: col.frame["name"] for col in tdf.columns})
        tdf.plot(**plot_args)
    elif kind == "scatter":
        seaborn.scatterplot(**plot_args)
    elif kind == "bar":
        seaborn.barplot(**plot_args)
    else:
        raise NotImplementedError(f"Unknown plot kind {kind}")

    y_axis_limits = kwargs.get("chart_yaxis_limits")
    if y_axis_limits is not None:
        ax.set_ylim(y_axis_limits[0], y_axis_limits[1])

    handles, labels = ax.get_legend_handles_labels()
    handles = list(reversed(handles))
    labels = list(reversed(labels))
    if kwargs["cluster"] != "multiple":
        for i, label in enumerate(labels):
            labels[i] = str(label) + " (" + str(calls_dict[label]) + ")"
    title = (
        "Region (Calls/rank (max))" if kwargs["cluster"] != "multiple" else "Cluster"
    )
    if not kwargs["disable_legend"]:
        ax.legend(
            handles,
            labels,
            bbox_to_anchor=(1, 0.5),
            loc="center left",
            title=title,
        )
    ax.set_xlabel(xlabel)

    fig.autofmt_xdate()
    plt.tight_layout()

    filename = os.path.join(kwargs["out_dir"], kwargs["chart_file_name"])
    logger.info(f"Saving figure data points to {filename}.csv")
    df.to_csv(filename + ".csv")
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
    if kwargs["yaxis_metric"] in tk.inc_metrics and not kwargs["no_update_inc_cols"]:
        pbar = tqdm(total=1, desc="Updating inclusive columns")
        tk.update_inclusive_columns()
        pbar.update(1)
        pbar.close()

    clean_tree = tk.tree(kwargs["tree_metric"], render_header=True)
    clean_tree = re.compile(r"\x1b\[([0-9;]*m)").sub("", clean_tree)

    exclude_regions = []
    # Remove MPI regions, if necessary
    if kwargs.get("no_mpi"):
        exclude_regions.append("MPI_")
    if kwargs.get("exclude_regions"):
        exclude_regions.extend(kwargs.get("exclude_regions"))
    if len(exclude_regions) > 0:
        logger.info(
            f"Removing regions that match the following pattern: {exclude_regions}"
        )
        query = th.query.Query().match(
            ".",
            lambda row: row["name"]
            .apply(
                # 'n is None' avoid comparison for MPI in n (will cause error)
                lambda n: n is None
                or all(excl not in n for excl in exclude_regions)
            )
            .all(),
        )
        tk = tk.query(query)

    metric = kwargs["yaxis_metric"]

    known_applications = {"raja-perf": RAJAPerf}
    for ta in tk.metadata["application_name"].unique():
        if ta in known_applications.keys():
            added_mets = known_applications[ta](tk).set_metrics()
            logger.info(
                f"Added the following derived metrics for app '{ta}':\n\t{added_mets}\n\tUse them via the '--yaxis-metric' parameter."
            )

    # Remove singular roots if inclusive metric
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
            "throughput": ["total_problem_size"],
        }[scaling]
    )
    kwargs["xaxis_parameter"] = (
        [x_axis_metadata] if not isinstance(x_axis_metadata, list) else x_axis_metadata
    )

    region_names = kwargs.get("query_regions_byname", "")
    if region_names:
        query = (
            th.query.Query()
            .match(
                ".", lambda row: row["name"].apply(lambda n: n in region_names).all()
            )
            .rel("*")
        )

        tk = tk.query(query)

    prefix = kwargs.get("filter_regions_byname", "")
    if prefix:
        tk.dataframe = pd.concat([tk.dataframe.filter(like=p, axis=0) for p in prefix])

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

    cluster_col = "cluster" if "cluster" in tk.metadata.columns else "host.cluster"
    tk.metadata_columns_to_perfdata([cluster_col] + list(NAME_REMAP.keys()))

    # Check these values are constant
    app = validate_single_metadata_value("application_name", tk)
    try:
        cluster = validate_single_metadata_value(cluster_col, tk)
    except ValueError:
        print("Multiple clusters detected. Using multi-cluster mode.")
        cluster = "multiple"
        if kwargs.get("chart_kind") == "area":
            raise ValueError(
                "Data from multiple workspaces (clusters) not allowed for 'area' chart type."
            )
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
    constant_str = (
        ", ".join(
            f"{int(tk.metadata[key].iloc[0]):,} {NAME_REMAP[key]}"
            for key in constant_keys
        )
        if cluster != "multiple"
        else ""
    )
    # Check constant
    if cluster != "multiple":
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

    # Compute percentage
    if kwargs.get("chart_type") == "percentage":
        tk.dataframe[metric + "-perc"] = 0
        for profile in tk.profile:
            tk.dataframe.loc[(slice(None), profile), metric + "-perc"] = (
                tk.dataframe.loc[(slice(None), profile), metric]
                * 100
                / tk.dataframe.loc[(slice(None), profile), metric].sum()
            )

    top_n = kwargs.get("top_n_regions", -1)
    if top_n != -1:
        chosen_profile = tk.profile[0]
        temp_df_idx = (
            tk.dataframe.loc[(slice(None), chosen_profile), :]
            .nlargest(top_n, metric)
            .index.get_level_values("node")
        )
        temp_df = tk.dataframe[
            tk.dataframe.index.get_level_values("node").isin(temp_df_idx)
        ]
        for p in tk.profile:
            temp_df.loc[("Sum(removed_regions)", p), metric] = (
                tk.dataframe.loc[(slice(None), p), metric].sum()
                - temp_df.loc[(slice(None), p), metric].sum()
            )
            for xp in kwargs["xaxis_parameter"]:
                temp_df.loc[("Sum(removed_regions)", p), xp] = tk.dataframe.loc[
                    (slice(None), p), xp
                ].iloc[0]
        temp_df.loc[("Sum(removed_regions)",), "name"] = "Sum(removed_regions)"
        tk.dataframe = temp_df
        logger.info(
            f"Filtered top {top_n} regions for chart display (based on first profile in Thicket.profile). Added the sum of the regions that were removed as single region."
        )

    # Convert int-like columns to int
    for col in kwargs["xaxis_parameter"]:
        tk.dataframe[col] = tk.dataframe[col].astype(int)

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
    kwargs["cluster"] = cluster

    if metric in tk.metadata.columns:
        tk.metadata_columns_to_perfdata(metric)
        logger.info(
            f"Adding metadata column '{metric}' to the performance data from the metadata."
        )

    norm_col = kwargs.get("normalize_by", "")
    if norm_col != "":
        logger.info(f"Normalizing '{kwargs['yaxis_metric']}' by '{norm_col}'")
        tk.dataframe[kwargs["yaxis_metric"]] /= tk.dataframe[norm_col]

    make_chart(df=tk.dataframe, x_axis=x_axis_metadata, **kwargs)


def setup_parser(root_parser):
    """
    Adds command-line arguments to the analyze parser, and supports trailing
    positional actions: `clean` and `archive`.
    """
    root_parser.add_argument(
        "--workspace-dir",
        required=True,
        type=str,
        help="Directory Caliper files. Files will be found recursively.",
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
        default=[],
        nargs="+",
        type=str,
        help="Filter for region names starting with one or more PREFIX values.",
        metavar="PREFIX",
    )
    root_parser.add_argument(
        "--query-regions-byname",
        default=[],
        nargs="+",
        type=str,
        help="Query for one or more regions REGION. Includes children of region.",
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
        "--normalize-by",
        default="",
        type=str,
        required=False,
        help="Optionally normalize the y-axis column by this column.",
        metavar="COLUMN",
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
    root_parser.add_argument(
        "--chart-kind",
        type=str,
        default="area",
        choices=["area", "line", "bar", "scatter"],
        help="Type of chart to generate",
    )
    root_parser.add_argument(
        "--no-update-inc-cols",
        action="store_true",
        help="Don't call Thicket.update_inclusive_columns() which can take a while.",
    )
    root_parser.add_argument(
        "--yaxis-log", action="store_true", help="Change yaxis to log base 2."
    )
    root_parser.add_argument(
        "--disable-legend",
        action="store_true",
        help="Turn off the legend on the figure",
    )
    root_parser.add_argument(
        "--exclude-regions",
        nargs="+",
        type=str,
        help="One or more patterns to exclude based on region name",
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
