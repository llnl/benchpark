from glob import glob
import os
import re

import matplotlib.pyplot as plt
import matplotlib as mpl
import thicket as th


def make_stacked_line_chart(**kwargs):
    # Extract required parameters from kwargs
    df = kwargs.get("df")
    chart_type = kwargs.get("chart_type")
    x_axis = kwargs.get("x_axis")
    y_axis_metric = kwargs.get("y_axis_metric")

    # Validate required parameters
    if df is None or chart_type is None or x_axis is None or y_axis_metric is None:
        raise ValueError(
            "Missing required parameters. Ensure 'df', 'chart_type', 'x_axis', and 'y_axis_metric' are provided in kwargs."
        )

    # Determine value and y_label based on chart_type
    if chart_type == "percentage_time":
        value = "perc"
        y_label = (
            kwargs["chart_ylabel"]
            if "chart_ylabel" in kwargs and kwargs["chart_ylabel"]
            else "Percentage of " + y_axis_metric
        )
    elif chart_type == "time":
        value = y_axis_metric
        y_label = (
            kwargs["chart_ylabel"]
            if "chart_ylabel" in kwargs and kwargs["chart_ylabel"]
            else y_axis_metric
        )
    else:
        raise ValueError(
            "Invalid chart_type value. Please choose from 'percentage_time' or 'time'."
        )

    # Save DataFrame to CSV
    csvfile = kwargs["out_dir"] + kwargs["chart_file_name"] + ".csv"
    print(csvfile)
    df.to_csv(csvfile)

    # Transform DataFrame for plotting
    tdf = df[[(i, value) for i in x_axis]].T
    tdf = tdf.reset_index(level=1, drop=True)  # Drop metric name from index

    # Hard coded color map
    color = [
        "#00FFFF",
        "#ff7f00",
        "#4daf4a",
        "#f781bf",
        "#a65628",
        "#984ea3",
        "#999999",
        "#e41a1c",
        "#dede00",
        "#377eb8",
    ]
    mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=color)

    # Set font size of text
    if "chart_fontsize" in kwargs and kwargs["chart_fontsize"]:
        mpl.rcParams.update({"font.size": kwargs["chart_fontsize"]})

    # Plotting
    fig, ax = plt.subplots()
    tdf.plot(
        kind="area",
        title=kwargs.get("chart_title", ""),
        xlabel=kwargs.get("chart_xlabel", ""),
        ylabel=y_label,
        figsize=(
            tuple(kwargs["chart_figsize"])
            if "chart_figsize" in kwargs and kwargs["chart_figsize"]
            else (10, 6)
        ),
        ax=ax,
    )

    # Reverse legend order
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        list(reversed(handles)),
        list(reversed(labels)),
        bbox_to_anchor=(1, 0.5),
        loc="center left",
    )

    # Try to fix xlabel spacing automatically
    fig.autofmt_xdate()

    plt.tight_layout()
    filename = kwargs["out_dir"] + kwargs["chart_file_name"] + ".png"
    print(filename)
    plt.savefig(filename)


def prepare_data(
    **additional_args,
):

    files = glob(additional_args["workspace_dir"] + "/**/*.cali", recursive=True)
    print(f"Analyzing {len(files)} files:")
    for i, f in enumerate(files):
        print(i + 1, f)

    tk = th.Thicket.from_caliperreader(files, disable_tqdm=True)
    tk.update_inclusive_columns()

    # This is to get tree with no metric
    tk.dataframe["nothing"] = 0
    additional_args["tree_str"] = tk.tree("nothing", render_header=False, precision=0)
    # Regular expression to match ANSI escape codes
    ansi_escape_pattern = re.compile(r"\x1b\[([0-9;]*m)")
    # Remove ANSI escape codes
    text_without_ansi = ansi_escape_pattern.sub("", additional_args["tree_str"])
    # Find and remove everything starting from "Legend"
    legend_index = text_without_ansi.find("Legend")
    if legend_index != -1:
        text_without_ansi = text_without_ansi[:legend_index]
    text_without_ansi = text_without_ansi.replace("0", "")
    additional_args["tree_str"] = text_without_ansi

    filename = additional_args["out_dir"] + additional_args["chart_file_name"] + ".txt"
    print(filename)
    f = open(filename, "w")
    f.write(additional_args["tree_str"])
    f.close()
    print("Full tree:\n" + additional_args["tree_str"])

    # Apply query to remove MPI regions from the tree, if any
    if additional_args["no_mpi"]:
        query = th.query.Query().match(
            ".", lambda row: row["name"].apply(lambda n: "MPI_" not in n).all()
        )
        tk = tk.query(query)
    if additional_args["y_axis_metric"] in tk.inc_metrics:
        if len(tk.graph.roots) == 1:
            root = tk.graph.roots[0].frame["name"]
            y_axis_met = additional_args["y_axis_metric"]
            print(
                f"Automatically removing singular root '{root}' to visualize inclusive metric '{y_axis_met}' with greater fidelity"
            )
            query = (
                th.query.Query()
                .match(".", lambda row: row["name"].apply(lambda n: n != root).all())
                .rel("*")
            )
            tk = tk.query(query)

    spec = tk.metadata["benchpark_spec"].iloc[0][0]
    known_scaling_types = ["+strong", "+throughput", "+weak"]
    scaling = None
    for keyword in known_scaling_types:
        if keyword in spec:
            scaling = keyword.lstrip("+")
    if not scaling:
        raise ValueError(f"Unknown scaling type. Must be one of {known_scaling_types}")

    x_axis_dict = {
        "strong": ["n_resources", "n_nodes"],
        "weak": ["n_resources", "n_nodes", "total_problem_size"],
        "throughput": "total_problem_size",
    }
    if not additional_args["x_axis_unique_metadata"]:
        # Infer from scaling type
        additional_args["x_axis_unique_metadata"] = x_axis_dict[scaling]

    gb = tk.groupby(additional_args["x_axis_unique_metadata"])

    thickets = list(gb.values())
    x_axis = list(gb.keys())
    ctk = th.Thicket.concat_thickets(
        thickets=thickets,
        headers=x_axis,
        axis="columns",
    )

    if len(tk.metadata["application_name"].unique()) == 1:
        app_name = tk.metadata["application_name"].unique()[0]
    else:
        raise ValueError(
            f"Expected data for one application, instead got: {list(tk.metadata['application_name'].unique())}"
        )

    if len(tk.metadata["cluster"].unique()) == 1:
        cluster = tk.metadata["cluster"].unique()[0]
    else:
        raise ValueError(
            f"Expected data for one cluster, instead got: {list(tk.metadata['cluster'].unique())}"
        )

    if len(tk.metadata["version"].unique()) == 1:
        version = tk.metadata["version"].unique()[0]
    else:
        raise ValueError(
            f"Expected data for one version, instead got: {list(tk.metadata['version'].unique())}"
        )

    programming_model = "mpi"
    for keyword in ["+cuda", "+rocm", "+openmp"]:
        if keyword in spec:
            programming_model = keyword.lstrip("+")

    constant_dict = {
        "strong": ["total_problem_size"],
        "weak": ["process_problem_size"],
        "throughput": ["n_resources", "n_nodes"],
    }
    # assert len(tk.metadata[constant_dict[scaling]].unique()) == 1
    if not additional_args["chart_title"]:
        additional_args["chart_title"] = (
            f"{cluster}/{app_name}@{version} ({scaling} scaling, constant {' '.join([str(tk.metadata[x].iloc[0]) + ' ' + x for x in constant_dict[scaling]])})"
        )

    additional_args["chart_file_name"] = (
        f"{app_name}_{programming_model}_{scaling}_{additional_args['chart_type']}"
    )

    if additional_args["group_nodes_name"]:
        ctk.dataframe = ctk.dataframe.groupby("name").sum()

    for i in x_axis:
        ctk.dataframe[i, "perc"] = (
            ctk.dataframe[i, additional_args["y_axis_metric"]]
            / ctk.dataframe[i, additional_args["y_axis_metric"]].sum()
        ) * 100

    if additional_args["filter_nodes_name_prefix"] != "":
        ctk.dataframe = ctk.dataframe.filter(
            like=additional_args["filter_nodes_name_prefix"], axis=0
        )

    if additional_args["top_n_nodes"] != -1:
        ctk.dataframe = ctk.dataframe.nlargest(
            additional_args["top_n_nodes"],
            [(x_axis[0], additional_args["y_axis_metric"])],
        )
        print("Showing only top 10 nodes")

    # Set default label to x_axis_unique_metadata if not provided
    if not additional_args["chart_xlabel"]:
        additional_args["chart_xlabel"] = additional_args["x_axis_unique_metadata"]

    if (
        "scaling-factor" in tk.metadata.columns
        and len(tk.metadata["scaling-factor"].unique()) == 1
    ):
        additional_args["scaling-factor"] = tk.metadata["scaling-factor"].unique()[0]
    elif len(tk.metadata["scaling-factor"].unique()) > 1:
        raise ValueError(
            f"Multiple scaling factors in metadata, expected singular value: {list(tk.metadata['scaling-factor'].unique())}"
        )

    make_stacked_line_chart(
        df=ctk.dataframe,
        x_axis=x_axis,
        **additional_args,
    )


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
    os.mkdir(args.out_dir)

    prepare_data(**vars(args))
