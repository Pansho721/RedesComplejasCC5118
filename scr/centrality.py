"""Stage: centrality measures per graph.

Answers "which subreddits are most central/influential?" The centrality
measures themselves are a lazy (name, fn) dispatch table (CENTRALITY_FUNCS)
so a new measure can be added, or an existing one swapped out, in one place
without touching the callers - the pattern the rest of the pipeline follows
too (see MODEL_BUILDERS in models.py, ANALYSES in analysis.py, STAGES in
main.py).
"""
import itertools
import os
from multiprocessing import Pool

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

import palette
from graph_io import load_graph_from_edgelist

VERBOSE = False


def vprint(message):
    if VERBOSE:
        print(message)

#   ==========================================================================================
#           BEGIN NETWORKX COPY PASTE DOCUMENTATION
#           parallel betweenness centrality function
#   ==========================================================================================


def chunks(l, n):
    """Divide a list of nodes `l` in `n` chunks"""
    l_c = iter(l)
    while 1:
        x = tuple(itertools.islice(l_c, n))
        if not x:
            return
        yield x


def betweenness_centrality_parallel(G, processes=None):
    """Parallel betweenness centrality function"""
    p = Pool(processes=processes)
    node_divisor = len(p._pool) * 4
    node_chunks = list(chunks(G.nodes(), G.order() // node_divisor))
    num_chunks = len(node_chunks)
    bt_sc = p.starmap(
        nx.betweenness_centrality_subset,
        zip(
            [G] * num_chunks,
            node_chunks,
            [list(G)] * num_chunks,
            [True] * num_chunks,
            [None] * num_chunks,
        ),
    )

    bt_c = bt_sc[0]
    for bt in bt_sc[1:]:
        for n in bt:
            bt_c[n] += bt[n]
    return bt_c

#   ==========================================================================================
#           END NETWORKX COPY PASTE DOCUMENTATION
#   ==========================================================================================


def _alpha_centrality(graph):
    eigenvalues = nx.adjacency_spectrum(graph)
    spectral_radius = max(abs(e) for e in eigenvalues)
    alpha = 0.85 / spectral_radius
    return nx.katz_centrality(graph, alpha=alpha, weight="weight")


# Lazy dispatch table: (kind, fn(graph) -> {node: score}). Add, remove, or
# replace a centrality measure here - compute_centrality() and every caller
# stay unchanged.
CENTRALITY_FUNCS = [
    ("degree", lambda G: nx.degree_centrality(G)),
    ("in-degree", lambda G: nx.in_degree_centrality(G)),
    ("out-degree", lambda G: nx.out_degree_centrality(G)),
    ("betweenness", lambda G: betweenness_centrality_parallel(G)),
    ("closeness", lambda G: nx.closeness_centrality(G)),
    ("alpha-centrality", lambda G: _alpha_centrality(G)),
    ("pagerank", lambda G: nx.pagerank(G, alpha=0.85, weight="weight")),
]
CENTRALITY_DISPATCH = dict(CENTRALITY_FUNCS)


def compute_centrality(graph, kind="degree"):
    fn = CENTRALITY_DISPATCH.get(kind)
    if fn is None:
        print(f"\t\tUnsupported centrality type: {kind}")
        return None
    try:
        return fn(graph)
    except Exception as e:
        print(f"\t\tError computing {kind} centrality: {e}")
        return None


def get_some_centrality(graph, kinds=("degree", "alpha-centrality")):
    """Compute all requested centrality measures and return as dict of dicts."""
    results = []
    for kind in kinds:
        vprint(f"\t\tComputing {kind} centrality...")
        results.append(compute_centrality(graph, kind))
    return dict(zip(kinds, results))


def save_centrality(centralities, output_name):
    """Save each measure to its own CSV, sorted highest to lowest."""
    try:
        for kind in centralities:
            out_path = f"{output_name}_{kind}.csv"
            out_dir = os.path.dirname(out_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                vprint(f"\t\t{kind} centrality saved to: {out_path}")
                for node, value in sorted(centralities[kind].items(), key=lambda item: item[1], reverse=True):
                    f.write(f"{node}\t{value}\n")
    except Exception as e:
        print(f"\t\tError saving centrality: {e}")


def join(centrality_dir, summary_dir, prefix, suffix, kinds):
    """Merge each per-metric CSV into one summary CSV with an added
    'average' column. Returns (DataFrame, output_path)."""
    dfs = [
        pd.read_csv(os.path.join(centrality_dir, f"{prefix}_{k}.csv"), sep="\t", names=["node", k])
        for k in kinds
    ]
    result = dfs[0]
    for df in dfs[1:]:
        result = result.merge(df, on="node")
    result["average"] = sum(result[k] for k in kinds) / len(kinds)
    result = result.sort_values("average", ascending=False)

    os.makedirs(summary_dir, exist_ok=True)
    out_path = os.path.join(summary_dir, f"{prefix}_{suffix}")
    result.to_csv(out_path, sep=",", index=False)
    return result, out_path


def plot_top_centrality(df, graph_name, out_dir, top_n=10):
    """Bar chart of the top-N nodes by average centrality - a magnitude
    ranking, so a single sequential hue (blue) is the right encoding."""
    top = df.head(top_n).iloc[::-1]  # reverse so the largest bar renders on top
    os.makedirs(out_dir, exist_ok=True)

    plt.figure(figsize=(7, 4.2))
    plt.barh(top["node"], top["average"], color=palette.BLUE)
    plt.xlabel("Centralidad promedio")
    plt.title(f"{graph_name}: top {top_n} nodos por centralidad promedio")
    plt.tight_layout()

    out_path = os.path.join(out_dir, f"{graph_name}_top_centrality.png")
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def stats(df, kinds):
    result = {}
    for kind in kinds:
        max_value = df[kind].max()
        min_value = df[kind].min()
        avg_value = df[kind].mean()
        max_node = df.loc[df[kind] == max_value, "node"].values[0]
        min_node = df.loc[df[kind] == min_value, "node"].values[0]
        result[kind] = dict(max=max_value, max_node=max_node, min=min_value, min_node=min_node, avg=avg_value)
    return result


def print_typst_table(df, kinds, top_n=10):
    top = df.head(top_n)
    print("[*node*], " + " ".join(f"[*{k}*]," for k in kinds))
    for _, row in top.iterrows():
        cells = " ".join(f"[{row[k]:.6f}]," for k in kinds)
        print(f"[{row['node']}], {cells}")


def run(config):
    """Entry point called by scr/main.py. Loads AGG_REDDIT, NEG_REDDIT, and
    CONX_REDDIT (the largest SCC of AGG_REDDIT, derived here rather than
    read from a file), computes each graph's configured centrality kinds,
    and returns a dict main.py/report.py can hand to the HTML builder."""
    global VERBOSE
    VERBOSE = config.get("verbose", False)

    paths = config["paths"]
    edgelist_dir = paths["edgelist_dir"]
    centrality_dir = os.path.join(paths["output_raw"], "centralities")
    summary_dir = os.path.join(centrality_dir, "summary")
    images_dir = os.path.join(paths["output_raw"], "images")

    kinds_by_graph = config["centrality_kinds"]

    neg_graph = load_graph_from_edgelist(os.path.join(edgelist_dir, "reddit_negative.edgelist"), kind="DiGraph")
    agg_graph = load_graph_from_edgelist(os.path.join(edgelist_dir, "reddit_weighted_aggregated.edgelist"), kind="DiGraph")
    largest = nx.DiGraph(agg_graph.subgraph(max(nx.strongly_connected_components(agg_graph), key=len)))

    graphs = {"NEG_REDDIT": neg_graph, "AGG_REDDIT": agg_graph, "CONX_REDDIT": largest}

    results = {}
    for name, graph in graphs.items():
        kinds = kinds_by_graph[name]
        print(f"\tCalculating {name} centrality...")
        centralities = get_some_centrality(graph, kinds)
        save_centrality(centralities, os.path.join(centrality_dir, f"reddit_{name}_centrality"))

        df, summary_path = join(centrality_dir, summary_dir, f"reddit_{name}_centrality", "full_centrality.csv", kinds)
        top_chart = plot_top_centrality(df, name, images_dir)
        graph_stats = stats(df, kinds)
        print_typst_table(df, kinds)

        results[name] = {
            "kinds": list(kinds),
            "summary_csv": summary_path,
            "top_chart": top_chart,
            "stats": graph_stats,
            "top10": df.head(10).to_dict("records"),
            "n_nodes": graph.number_of_nodes(),
            "n_edges": graph.number_of_edges(),
        }
    return results
