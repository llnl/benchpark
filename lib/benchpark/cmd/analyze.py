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
    "#00FFFF", "#ff7f00", "#4daf4a", "#f781bf", "#a65628",
    "#984ea3", "#999999", "#e41a1c", "#dede00", "#377eb8"
]
SCALING_TYPES = ["+strong", "+throughput", "+weak"]

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s: %(message)s"
)

# -----------------------------
# Helper Functions
# -----------------------------
def configure_matplotlib(colors=None, fontsize=None):
    mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=colors or COLOR_PALETTE)
    if fontsize:
        mpl.rcParams.update({"font.size": fontsize})

def get_scaling_type(spec):
    for keyword in SCALING_TYPES:
        if keyword in spec:
            return keyword.lstrip("+")
    raise ValueError(f"Unknown scaling type. Must be one of {SCALING_TYPES}")

def validate_single_metadata_value(column, tk, label):
    unique_vals = tk.metadata[column].unique()
    if len(unique_vals) != 1:
        raise ValueError(f"Expected one {label}, got: {list(unique_vals)}")
    return unique_vals[0]

def clean_tree_string(raw_tree_str):
    ansi_escape = re.compile(r"\x1b\[([0-9;]*m)")
    text = ansi_escape.sub("", raw_tree_str)
    legend_index = text.find("Legend")
    if legend_index != -1:
        text = text[:legend_index]
    return text.replace("0", "")

# -----------------------------
# Chart Generation
# -----------------------------
def make_stacked_line_chart(**kwargs):
    df = kwargs.get("df")
    chart_type = kwargs.get("chart_type")
    x_axis = kwargs.get("x_axis")
    y_axis_metric = kwargs.get("y_axis_metric")

    if df is None or chart_type is None or x_axis is None or y_axis_metric is None:
        raise ValueError("Missing required parameters. 'df', 'chart_type', 'x_axis', and 'y_axis_metric' are required.")

    value = "perc" if chart_type == "percentage_time" else y_axis_metric
    y_label = kwargs.get("chart_ylabel") or (f"Percentage of {y_axis_metric}" if chart_type == "percentage_time" else y_axis_metric)

    os.makedirs(kwargs["out_dir"], exist_ok=True)
    csvfile = os.path.join(kwargs["out_dir"], kwargs["chart_file_name"] + ".csv")
    logger.info(f"Saving DataFrame to {csvfile}")
    df.to_csv(csvfile)

    tdf = df[[(i, value) for i in x_axis]].T.reset_index(level=1, drop=True)
    configure_matplotlib(fontsize=kwargs.get("chart_fontsize"))

    fig, ax = plt.subplots()
    tdf.plot(
        kind="area",
        title=kwargs.get("chart_title", ""),
        xlabel=kwargs.get("chart_xlabel", ""),
        ylabel=y_label,
        figsize=(10,6),#tuple(kwargs.get("chart_figsize", (10, 6))),
        ax=ax,
    )

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(list(reversed(handles)), list(reversed(labels)), bbox_to_anchor=(1, 0.5), loc="center left")

    fig.autofmt_xdate()
    plt.tight_layout()

    imgfile = os.path.join(kwargs["out_dir"], kwargs["chart_file_name"] + ".png")
    logger.info(f"Saving figure to {imgfile}")
    plt.savefig(imgfile)

# -----------------------------
# Data Preparation Pipeline
# -----------------------------
def prepare_data(**kwargs):
    workspace_dir = kwargs["workspace_dir"]
    files = glob(os.path.join(workspace_dir, "**/*.cali"), recursive=True)
    logger.info(f"Found {len(files)} .cali files for analysis.")

    tk = th.Thicket.from_caliperreader(files, disable_tqdm=True)
    tk.update_inclusive_columns()

    # Prepare tree string
    tk.dataframe["nothing"] = 0
    raw_tree = tk.tree("nothing", render_header=False, precision=0)
    clean_tree = clean_tree_string(raw_tree)
    kwargs["tree_str"] = clean_tree

    tree_file = os.path.join(kwargs["out_dir"], kwargs["chart_file_name"] + ".txt")
    with open(tree_file, "w") as f:
        f.write(clean_tree)
    logger.info(f"Saving Unmodified Calltree structure to {tree_file}")

    # Optional: Filter out MPI regions
    if kwargs.get("no_mpi"):
        query = th.query.Query().match(".", lambda row: row["name"].apply(lambda n: "MPI_" not in n).all())
        tk = tk.query(query)

    metric = kwargs["y_axis_metric"]
    if metric in tk.inc_metrics and len(tk.graph.roots) == 1:
        root_name = tk.graph.roots[0].frame["name"]
        logger.info(f"Removing root '{root_name}' to improve chart readability.")
        query = th.query.Query().match(".", lambda row: row["name"].apply(lambda n: n != root_name).all()).rel("*")
        tk = tk.query(query)

    spec = tk.metadata["benchpark_spec"].iloc[0][0]
    scaling = get_scaling_type(spec)

    x_axis_metadata = kwargs.get("x_axis_unique_metadata") or {
        "strong": ["n_resources", "n_nodes"],
        "weak": ["n_resources", "n_nodes", "total_problem_size"],
        "throughput": "total_problem_size"
    }[scaling]
    kwargs["x_axis_unique_metadata"] = x_axis_metadata

    grouped = tk.groupby(x_axis_metadata)
    ctk = th.Thicket.concat_thickets(list(grouped.values()), headers=list(grouped.keys()), axis="columns")

    app = validate_single_metadata_value("application_name", tk, "application")
    cluster = validate_single_metadata_value("cluster", tk, "cluster")
    version = validate_single_metadata_value("version", tk, "version")

    programming_model = "mpi"
    for keyword in ["+cuda", "+rocm", "+openmp"]:
        if keyword in spec:
            programming_model = keyword.lstrip("+")

    constant_keys = {
        "strong": ["total_problem_size"],
        "weak": ["process_problem_size"],
        "throughput": ["n_resources", "n_nodes"],
    }[scaling]
    constant_str = ", ".join(f"{tk.metadata[key].iloc[0]} {key}" for key in constant_keys)

    if not kwargs.get("chart_title"):
        kwargs["chart_title"] = f"{cluster}/{app}+{programming_model}@{version} ({scaling} scaling, constant {constant_str})"

    kwargs["chart_file_name"] = f"{app}_{programming_model}_{scaling}_{kwargs['chart_type']}_{'inc' if metric in tk.inc_metrics else 'exc'}"

    if kwargs.get("group_nodes_name"):
        ctk.dataframe = ctk.dataframe.groupby("name").sum()

    for key in grouped.keys():
        ctk.dataframe[(key, "perc")] = (
            ctk.dataframe[(key, metric)] / ctk.dataframe[(key, metric)].sum()
        ) * 100

    prefix = kwargs.get("filter_nodes_name_prefix", "")
    if prefix:
        ctk.dataframe = ctk.dataframe.filter(like=prefix, axis=0)

    top_n = kwargs.get("top_n_nodes", -1)
    if top_n != -1:
        ctk.dataframe = ctk.dataframe.nlargest(top_n, [(list(grouped.keys())[0], metric)])
        logger.info(f"Filtered top {top_n} nodes for chart display.")

    if not kwargs.get("chart_xlabel"):
        kwargs["chart_xlabel"] = x_axis_metadata

    if "scaling-factor" in tk.metadata.columns:
        scaling_factors = tk.metadata["scaling-factor"].unique()
        if len(scaling_factors) == 1:
            kwargs["scaling-factor"] = scaling_factors[0]
        else:
            raise ValueError(f"Expected one scaling factor, found: {list(scaling_factors)}")

    make_stacked_line_chart(df=ctk.dataframe, x_axis=list(grouped.keys()), **kwargs)


def setup_parser(root_parser):
    root_parser.add_argument(
        "--workspace-dir",
        required=True,
        type=str,
        help="Directory of ramble workspace.",
    )
    root_parser.add_argument(
        "--chart-type",
        default="time",
        choices=["percentage_time", "time"],
        type=str,
        help="Specify type of output chart.",
    )
    root_parser.add_argument(
        "--x_axis-unique-metadata",
        default=None,
        type=str,
        help="Parameter that is varied during the experiment.",
    )
    root_parser.add_argument(
        "--y-axis-metric",
        default="Avg time/rank (exc)",
        type=str,
        help="Metric to be visualized.",
    )
    root_parser.add_argument(
        "--filter-nodes-name-prefix",
        default="",
        type=str,
        help="Optional: Filters only entries with prefix to be included in chart.",
    )
    root_parser.add_argument(
        "--group-nodes-name",
        default=True,
        type=bool,
        help="Optional: Specify if nodes with the same name are combined or not.",
    )
    root_parser.add_argument(
        "--top-n-nodes",
        default=-1,
        type=int,
        help="Optional: Filters only top n longest time entries to be included in chart.",
    )
    root_parser.add_argument(
        "--chart-title",
        default=None,
        type=str,
        help="Optional: Title of the output chart.",
    )
    root_parser.add_argument(
        "--chart-xlabel",
        type=str,
        help="Optional: X Label of chart.",
    )
    root_parser.add_argument(
        "--chart-ylabel",
        type=str,
        help="Optional: Y Label of chart.",
    )
    root_parser.add_argument(
        "--chart-file-name",
        default="stacked_line_chart",
        type=str,
        help="Optional: Set output chart file name.",
    )
    root_parser.add_argument(
        "--chart-figsize",
        nargs="+",
        type=int,
        help="Optional: Size of the output chart (xdim, ydim). Ex: --chart-figsize 10 6",
    )
    root_parser.add_argument(
        "--chart-fontsize",
        type=int,
        help="Optional: Font size of the output chart.",
    )
    root_parser.add_argument(
        "--no-mpi", action="store_true", help="Hide MPI regions in the tree."
    )


def command(args):
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
