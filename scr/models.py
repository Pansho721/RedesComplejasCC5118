"""Stage: compare the real network against synthetic graph models.

Answers "how does the real network compare to ER / Barabási-Albert /
Dual-BA / Holme-Kim?" The models themselves are a lazy (name, build_fn)
dispatch table (MODEL_BUILDERS), matching the pattern used for centrality
measures in centrality.py - add or swap a model there without touching the
analysis functions below it.
"""
import csv
import os
from concurrent.futures import ProcessPoolExecutor

import matplotlib.pyplot as plt
import networkx as nx

import palette
from graph_io import load_graph_from_edgelist

VERBOSE = False


def vprint(message):
    if VERBOSE:
        print(message)


# Lazy dispatch: each entry is (kind, build_fn(params) -> Graph). params is
# the dict returned by estimate_params() (N, E, per, m, m1, m2, pdba, plus
# agg_path for the "AGG" entry, which loads the real graph from disk).
#
# NOTE: "AGG" always loads the full aggregated graph, even when the rest of
# the comparison uses CONX_REDDIT-derived parameters (see run()) - this
# matches the original script's behavior, where the "real network" row is
# always the whole aggregated graph for reference.
MODEL_BUILDERS = [
    ("AGG", lambda p: load_graph_from_edgelist(p["agg_path"], kind="DiGraph")),
    ("ER", lambda p: nx.erdos_renyi_graph(p["N"], p["per"], directed=True)),
    ("BA", lambda p: nx.barabasi_albert_graph(p["N"], p["m"])),
    ("DBA", lambda p: nx.dual_barabasi_albert_graph(p["N"], p["m1"], p["m2"], p["pdba"])),
    ("HK", lambda p: nx.powerlaw_cluster_graph(p["N"], p["m"], p["per"])),
]
MODEL_LABELS = {
    "AGG": "AGG_REDDIT",
    "ER": "Erdos-Renyi",
    "BA": "Barabasi-Albert",
    "DBA": "Dual Barabasi-Albert",
    "HK": "Holme-Kim",
}
MODEL_BUILD_DISPATCH = dict(MODEL_BUILDERS)
KINDS = [k for k, _ in MODEL_BUILDERS]


def small_world_analysis(model_kind, params):
    graph = MODEL_BUILD_DISPATCH[model_kind](params)

    if graph.is_directed():
        comp_nodes = max(nx.strongly_connected_components(graph), key=len)
    else:
        comp_nodes = max(nx.connected_components(graph), key=len)
    H = graph.subgraph(comp_nodes).copy()

    N = H.number_of_nodes()
    E = H.number_of_edges()
    k = (2 * E) / N
    L = nx.average_shortest_path_length(H)
    C = nx.average_clustering(H)

    return {"model": model_kind, "name": MODEL_LABELS[model_kind], "N": N, "E": E, "k": k, "L": L, "C": C}


def properties_analysis(model_kind, params):
    graph = MODEL_BUILD_DISPATCH[model_kind](params)

    conx = nx.is_strongly_connected(graph) if graph.is_directed() else nx.is_connected(graph)
    assortativity = nx.degree_assortativity_coefficient(graph)

    return {"model": model_kind, "name": MODEL_LABELS[model_kind], "connected": conx, "assortativity": assortativity}


def plot_model_comparison(rows, out_path):
    """L and C per model - each model is a distinct entity (identity job),
    so bars take the fixed categorical order rather than a single hue."""
    names = [r["name"] for r in rows]
    colors = palette.CATEGORICAL[: len(rows)]
    x = range(len(names))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    axes[0].bar(x, [r["L"] for r in rows], color=colors)
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels(names, rotation=20)
    axes[0].set_title("Largo característico (L)")

    axes[1].bar(x, [r["C"] for r in rows], color=colors)
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(names, rotation=20)
    axes[1].set_title("Coeficiente de clustering (C)")

    fig.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def compare_models(params, chart_path, csv_path, kinds=KINDS):
    with ProcessPoolExecutor(max_workers=4) as executor:
        rows1 = list(executor.map(small_world_analysis, kinds, [params] * len(kinds)))
    with ProcessPoolExecutor(max_workers=4) as executor:
        rows2 = list(executor.map(properties_analysis, kinds, [params] * len(kinds)))

    by_model = {r["model"]: r for r in rows1}
    for r in rows2:
        by_model[r["model"]].update(connected=r["connected"], assortativity=r["assortativity"])
    rows = [by_model[k] for k in kinds]

    plot_model_comparison(rows, chart_path)

    # Persisted to OUTPUT/raw so report.py can build the models page from
    # disk alone, without re-running the (expensive) comparison.
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["model", "name", "N", "E", "k", "L", "C", "connected", "assortativity"])
        writer.writeheader()
        writer.writerows(rows)

    print("[*Graph*], [*N*], [*E*], [*k*], [*L*], [*C*]")
    for r in rows:
        print(f"[{r['name']}], [{r['N']}], [{r['E']}], [{r['k']:.6f}], [{r['L']:.6f}], [{r['C']:.6f}]")
    print("\n[*Graph*], [*Connected*], [*Assortativity*]")
    for r in rows:
        print(f"[{r['name']}], [{r['connected']}], [{r['assortativity']:.6f}]")

    return rows


def estimate_params(agg_path, graph, pos, neg):
    N = graph.number_of_nodes()
    E = graph.number_of_edges()
    per = E / (N * (N - 1))
    m = int(E / N)
    m1 = int(neg.number_of_edges() / neg.number_of_nodes())
    m2 = int(pos.number_of_edges() / pos.number_of_nodes())
    pdba = m1 / (m1 + m2)

    return {
        "agg_path": agg_path,
        "N": N, "E": E, "per": per,
        "m": max(m, 1), "m1": max(m1, 1), "m2": max(m2, 1),
        "pdba": pdba,
    }


def run(config):
    """Entry point called by scr/main.py. Runs the model comparison twice -
    once against the full AGG_REDDIT graph, once against CONX_REDDIT (its
    largest SCC) - and returns {"AGG_REDDIT": rows, "CONX_REDDIT": rows}
    for report.py."""
    global VERBOSE
    VERBOSE = config.get("verbose", False)

    paths = config["paths"]
    edgelist_dir = paths["edgelist_dir"]
    graphics_dir = os.path.join(paths["output_raw"], "graphics")
    os.makedirs(graphics_dir, exist_ok=True)

    agg_path = os.path.join(edgelist_dir, "reddit_weighted_aggregated.edgelist")
    pos_path = os.path.join(edgelist_dir, "reddit_positive.edgelist")
    neg_path = os.path.join(edgelist_dir, "reddit_negative.edgelist")

    POS_REDDIT = load_graph_from_edgelist(pos_path, kind="DiGraph")
    NEG_REDDIT = load_graph_from_edgelist(neg_path, kind="DiGraph")
    AGG_REDDIT = load_graph_from_edgelist(agg_path, kind="DiGraph")

    overrides = config.get("model_params_override", {})
    results = {}

    print("=== Model analysis using AGG_REDDIT ===")
    params_full = estimate_params(agg_path, AGG_REDDIT, POS_REDDIT, NEG_REDDIT)
    params_full.update(overrides)
    results["AGG_REDDIT"] = compare_models(
        params_full,
        os.path.join(graphics_dir, "models_comparison_agg.png"),
        os.path.join(graphics_dir, "models_comparison_agg.csv"),
    )

    print("=== Model analysis using CONX_REDDIT ===")
    CONX_REDDIT = nx.DiGraph(AGG_REDDIT.subgraph(max(nx.strongly_connected_components(AGG_REDDIT), key=len)))
    CONX_POS = nx.DiGraph(POS_REDDIT.subgraph(max(nx.strongly_connected_components(POS_REDDIT), key=len)))
    CONX_NEG = nx.DiGraph(NEG_REDDIT.subgraph(max(nx.strongly_connected_components(NEG_REDDIT), key=len)))
    params_conx = estimate_params(agg_path, CONX_REDDIT, CONX_POS, CONX_NEG)
    params_conx.update(overrides)
    results["CONX_REDDIT"] = compare_models(
        params_conx,
        os.path.join(graphics_dir, "models_comparison_conx.png"),
        os.path.join(graphics_dir, "models_comparison_conx.csv"),
    )

    return results
