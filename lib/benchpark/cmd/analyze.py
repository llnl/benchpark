# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import re
import logging
from glob import glob

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
    scaling_list = spec.unique()
    if len(scaling_list) != 1:
        raise ValueError(f"Multiple scaling types found, expected 1. {scaling_list}")
    scaling = scaling_list[0]
    if scaling in SCALING_TYPES:
        return scaling
    raise ValueError(
        f"Unknown scaling type '{scaling}'. Must be one of {SCALING_TYPES}"
    )


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
    workspace_dir = kwargs["workspace_dir"]
    files = glob(
        os.path.join(workspace_dir, f"**/*{kwargs['file_name_match']}.cali"),
        recursive=True,
    )
    logger.info(f"Found {len(files)} .cali files for analysis.")

    if kwargs["calltree_unification"] == "intersection":
        intersection = True
    else:
        intersection = False
    tk = th.Thicket.from_caliperreader(
        files, intersection=intersection, disable_tqdm=True
    )
    tk.update_inclusive_columns()

    # Save tree before modification
    # Cleans ANSI escape sequences and legend from a raw calltree string.
    tk.dataframe["nothing"] = 0
    raw_tree = tk.tree("nothing", render_header=False, precision=0)
    ansi_escape = re.compile(r"\x1b\[([0-9;]*m)")
    text = ansi_escape.sub("", raw_tree)
    legend_index = text.find("Legend")
    if legend_index != -1:
        text = text[:legend_index]
    clean_tree = text.replace("0", "")
    kwargs["tree_str"] = clean_tree

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
    # col varies based on new_scaling/old_scaling
    if "scaling" not in tk.metadata:
        # This can be deprecated once all benchmarks are transitioned to new_scaling
        if "benchpark_spec" in tk.metadata:
            spec_series = tk.metadata["benchpark_spec"]
            if not spec_series.apply(lambda x: x == spec_series.iloc[0]).all():
                raise ValueError("Not all lists in the Series are equal.")
            spec = spec_series.iloc[0][0]
            for keyword in SCALING_TYPES:
                if "+" + keyword in spec:
                    tk.metadata["scaling"] = keyword
        else:
            raise ValueError(
                "Expected either 'scaling' or 'benchpark_spec' in metadata"
            )
    spec = tk.metadata["scaling"]
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

    # Group by varied parameters
    grouped = tk.groupby(x_axis_metadata)
    ctk = th.Thicket.concat_thickets(
        list(grouped.values()), headers=list(grouped.keys()), axis="columns"
    )

    # Check these values are constant
    app = validate_single_metadata_value("application_name", tk)
    cluster = validate_single_metadata_value("host.cluster", tk)
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

    prefix = kwargs.get("filter_regions_name_prefix", "")
    if prefix:
        ctk.dataframe = ctk.dataframe.filter(like=prefix, axis=0)

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
    Adds command-line arguments to the root parser.

    Args:
        root_parser (argparse.ArgumentParser): The root argument parser.
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
        "--filter-regions-name-prefix",
        default="",
        type=str,
        help="Filter for region names starting with PREFIX to be included in the chart.",
        metavar="PREFIX",
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


def command(args):
    """
    Validates the workspace directory and initiates data processing.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    if ".ramble-workspace" not in os.listdir(args.workspace_dir):
        raise ValueError(
            f"Directory '{args.workspace_dir}' must be a valid ramble workspace"
        )

    wkp_dir = args.workspace_dir
    if wkp_dir[-1] != "/":
        wkp_dir += "/"
    args.out_dir = wkp_dir + "analyze/"

    if not os.path.isdir(args.out_dir):
        os.mkdir(args.out_dir)

    prepare_data(**vars(args))
