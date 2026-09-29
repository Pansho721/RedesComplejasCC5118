"""Stage: structural analyses beyond centrality - small-world, assortativity,
and the bow-tie macrostructure decomposition.

Each analysis answers one report question ("is the network small-world?",
"is it assortative or disassortative?", "what does its macrostructure look
like?"), and the three are wired up as a lazy (name, fn) list (ANALYSES) so
one can be skipped or reordered from run() without touching the analysis
code itself - same pattern as CENTRALITY_FUNCS in centrality.py and
MODEL_BUILDERS in models.py.
"""
import csv
import math
import os

import matplotlib.pyplot as plt
import networkx as nx

import palette
from graph_io import load_graph_from_edgelist


def small_world_stats(graphs, names):
    rows = []
    for graph, name in zip(graphs, names):
        k_avg = sum(dict(graph.degree()).values()) / graph.number_of_nodes()
        k = (2 * graph.number_of_edges()) / graph.number_of_nodes()

        L_ER = math.log(graph.number_of_nodes()) / math.log(k_avg)
        C_ER = k_avg / graph.number_of_nodes()

        L = nx.average_shortest_path_length(graph)
        C = nx.average_clustering(graph)

        rows.append({"name": name, "k": k, "k_avg": k_avg, "L": L, "L_ER": L_ER, "C": C, "C_ER": C_ER})
    return rows


def plot_small_world(rows, out_path):
    """Grouped bars comparing each real graph against its Erdős–Rényi
    reference - a polarity/comparison job, so it takes the diverging pair
    (blue = real, red = ER reference) rather than the categorical order."""
    names = [r["name"] for r in rows]
    x = range(len(names))
    width = 0.35

    _fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))

    axes[0].bar([i - width / 2 for i in x], [r["L"] for r in rows], width, label="Red real", color=palette.DIVERGING_POS)
    axes[0].bar([i + width / 2 for i in x], [r["L_ER"] for r in rows], width, label="Erdős–Rényi equivalente", color=palette.DIVERGING_NEG)
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels(names, rotation=15)
    axes[0].set_title("Largo característico (L)")
    axes[0].legend()

    axes[1].bar([i - width / 2 for i in x], [r["C"] for r in rows], width, label="Red real", color=palette.DIVERGING_POS)
    axes[1].bar([i + width / 2 for i in x], [r["C_ER"] for r in rows], width, label="Erdős–Rényi equivalente", color=palette.DIVERGING_NEG)
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(names, rotation=15)
    axes[1].set_title("Coeficiente de clustering (C)")
    axes[1].legend()

    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()


def assortativity_stats(graphs):
    return {name: nx.degree_assortativity_coefficient(g, weight="weight") for name, g in graphs.items()}


def plot_assortativity(values, out_path):
    """Each bar's sign is the message, so color follows sign with the
    diverging pair rather than a fixed per-graph hue."""
    names = list(values.keys())
    scores = list(values.values())
    colors = [palette.DIVERGING_POS if v >= 0 else palette.DIVERGING_NEG for v in scores]

    plt.figure(figsize=(6, 4.2))
    plt.bar(names, scores, color=colors)
    plt.axhline(0, color=palette.AXIS, linewidth=0.8)
    plt.ylabel("Coeficiente de asortatividad")
    plt.title("Asortatividad por grado")
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()


def bowtie(AGG_REDDIT, CONX_REDDIT, out_path):
    scc_nodes = set(CONX_REDDIT.nodes())
    nodo_referencia = next(iter(scc_nodes))

    # IN-Component: nodes that can reach the SCC (ancestors), but aren't in it
    in_component = nx.ancestors(AGG_REDDIT, nodo_referencia) - scc_nodes
    # OUT-Component: nodes reachable from the SCC (descendants), but not in it
    out_component = nx.descendants(AGG_REDDIT, nodo_referencia) - scc_nodes
    # Tendrils: everything else
    tendrils = set(AGG_REDDIT.nodes()) - scc_nodes - in_component - out_component

    counts = {
        "total": AGG_REDDIT.number_of_nodes(),
        "scc": len(scc_nodes),
        "in_component": len(in_component),
        "out_component": len(out_component),
        "tendrils": len(tendrils),
    }

    print(f"Total nodos en la red: {counts['total']}")
    print(f"Núcleo (SCC): {counts['scc']} nodos")
    print(f"Componente IN (inician hilos hacia el núcleo): {counts['in_component']} nodos")
    print(f"Componente OUT (mencionados por el núcleo): {counts['out_component']} nodos")
    print(f"Tendrils/Tubos (periferia aislada): {counts['tendrils']} nodos")

    # Four distinct categories (parts of the whole) -> fixed-order categorical hues.
    etiquetas = ["Núcleo (SCC)", "Componente IN", "Componente OUT", "Tendrils"]
    valores = [counts["scc"], counts["in_component"], counts["out_component"], counts["tendrils"]]
    colores = palette.CATEGORICAL[:4]

    plt.figure(figsize=(8, 5))
    barras = plt.bar(etiquetas, valores, color=colores)
    for barra in barras:
        yval = barra.get_height()
        plt.text(barra.get_x() + barra.get_width() / 2, yval + 200, f"{yval}", ha="center", va="bottom", fontsize=11, fontweight="bold")

    plt.title("Estructura macroscópica bow-tie de Reddit", fontsize=14)
    plt.ylabel("Cantidad de subreddits", fontsize=12)
    plt.ylim(0, max(valores) + 2000)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved figure to: {out_path}")

    counts["chart"] = out_path
    return counts


# ---------------------------------------------------------------------------
# Lazy dispatch: each analysis is (name, fn(ctx) -> result dict). Comment a
# line out of ANALYSES to skip that analysis; nothing else needs to change.
# ---------------------------------------------------------------------------

def _run_assortativity(ctx):
    values = assortativity_stats({
        "AGG_REDDIT": ctx["AGG_REDDIT"],
        "NEG_REDDIT": ctx["NEG_REDDIT"],
        "POS_REDDIT": ctx["POS_REDDIT"],
    })
    chart = os.path.join(ctx["graphics_dir"], "assortativity.png")
    plot_assortativity(values, chart)
    for name, v in values.items():
        print(f"Assortativity en {name}: {v}")

    # Persisted to OUTPUT/raw so report.py can build the page from disk
    # alone, without re-running this analysis.
    csv_path = os.path.join(ctx["graphics_dir"], "assortativity.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["graph", "assortativity"])
        for name, v in values.items():
            writer.writerow([name, v])

    return {"values": values, "chart": chart, "csv": csv_path}


def _run_small_world(ctx):
    rows = small_world_stats(
        [ctx["CONX_REDDIT"], ctx["CONX_NEG"], ctx["CONX_POS"]],
        ["CONX_REDDIT", "CONX_NEG", "CONX_POS"],
    )
    chart = os.path.join(ctx["graphics_dir"], "small_world.png")
    plot_small_world(rows, chart)
    for r in rows:
        print(f"[{r['name']}] L={r['L']:.4f} (ER={r['L_ER']:.4f})  C={r['C']:.4f} (ER={r['C_ER']:.4f})")

    csv_path = os.path.join(ctx["graphics_dir"], "small_world.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "k", "k_avg", "L", "L_ER", "C", "C_ER"])
        writer.writeheader()
        writer.writerows(rows)

    return {"rows": rows, "chart": chart, "csv": csv_path}


def _run_bowtie(ctx):
    chart = os.path.join(ctx["images_dir"], "bowtie_reddit.png")
    counts = bowtie(ctx["AGG_REDDIT"], ctx["CONX_REDDIT"], chart)

    csv_path = os.path.join(ctx["images_dir"], "bowtie_summary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["component", "count"])
        for key in ("total", "scc", "in_component", "out_component", "tendrils"):
            writer.writerow([key, counts[key]])

    counts["csv"] = csv_path
    return counts


ANALYSES = [
    ("assortativity", _run_assortativity),
    ("small_world", _run_small_world),
    ("bowtie", _run_bowtie),
]


def run(config):
    """Entry point called by scr/main.py. Loads AGG/NEG/POS and their
    largest strongly connected components once, then runs every analysis
    in ANALYSES against that shared context. Returns {name: result}."""
    paths = config["paths"]
    edgelist_dir = paths["edgelist_dir"]
    images_dir = os.path.join(paths["output_raw"], "images")
    graphics_dir = os.path.join(paths["output_raw"], "graphics")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(graphics_dir, exist_ok=True)

    AGG_REDDIT = load_graph_from_edgelist(os.path.join(edgelist_dir, "reddit_weighted_aggregated.edgelist"), kind="DiGraph")
    NEG_REDDIT = load_graph_from_edgelist(os.path.join(edgelist_dir, "reddit_negative.edgelist"), kind="DiGraph")
    POS_REDDIT = load_graph_from_edgelist(os.path.join(edgelist_dir, "reddit_positive.edgelist"), kind="DiGraph")
    CONX_REDDIT = nx.DiGraph(AGG_REDDIT.subgraph(max(nx.strongly_connected_components(AGG_REDDIT), key=len)))
    CONX_NEG = nx.DiGraph(NEG_REDDIT.subgraph(max(nx.strongly_connected_components(NEG_REDDIT), key=len)))
    CONX_POS = nx.DiGraph(POS_REDDIT.subgraph(max(nx.strongly_connected_components(POS_REDDIT), key=len)))

    ctx = {
        "AGG_REDDIT": AGG_REDDIT, "NEG_REDDIT": NEG_REDDIT, "POS_REDDIT": POS_REDDIT,
        "CONX_REDDIT": CONX_REDDIT, "CONX_NEG": CONX_NEG, "CONX_POS": CONX_POS,
        "images_dir": images_dir, "graphics_dir": graphics_dir,
    }

    results = {}
    for name, fn in ANALYSES:
        print(f"\n=== Analysis: {name} ===")
        results[name] = fn(ctx)
    return results
