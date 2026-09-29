"""Stage: degree-distribution histograms with a power-law fit.

Answers "does the degree distribution follow a power law?" Reads the
per-metric centrality CSVs (not the *_full_centrality.csv summaries, which
live in a separate summary/ subdirectory) and produces one log-log
frequency-distribution scatter plot per (graph, metric) pair.
"""
import csv
import glob
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import powerlaw

GRAPH_LABELS = {
    "NEG_REDDIT": "NEG_REDDIT",
    "AGG_REDDIT": "AGG_REDDIT",
    "CONX_REDDIT": "CONX_REDDIT",
}

METRIC_LABELS = {
    "alpha-centrality": "Alpha",
    "betweenness": "Betweenness",
    "closeness": "Closeness",
    "degree": "Degree",
    "in-degree": "In-Degree",
    "out-degree": "Out-Degree",
    "pagerank": "Pagerank",
}


def build_histogram(filepath, out_root):
    filename = os.path.basename(filepath)                        # reddit_NEG_REDDIT_centrality_degree.csv
    stem = filename.replace("reddit_", "").replace(".csv", "")    # NEG_REDDIT_centrality_degree
    parts = stem.split("_centrality_")                            # ['NEG_REDDIT', 'degree']
    graph_key = parts[0]
    metric_key = parts[1] if len(parts) > 1 else stem
    metric = METRIC_LABELS.get(metric_key, metric_key.title())

    graph_label = GRAPH_LABELS.get(graph_key, graph_key.upper())
    title = f"{graph_label} | Distribución de frecuencia: {metric}"
    outdir = os.path.join(out_root, graph_label)
    os.makedirs(outdir, exist_ok=True)

    df = pd.read_csv(filepath, sep="\t", names=["node", "value"])
    values = df["value"]
    counts = values.value_counts().sort_index()
    total = counts.sum()

    plt.figure()
    plt.scatter(counts.index, counts.values / total, s=3, color="black")
    plt.xscale("log")
    plt.yscale("log")
    plt.title(title)
    plt.xlabel(metric)
    plt.ylabel("Frecuencia")

    gamma = xmin = None
    if metric_key == "degree":
        values_array = np.array(values)
        fit = powerlaw.Fit(values_array, verbose=False)
        gamma = fit.alpha
        xmin = fit.xmin

        if np.isfinite(gamma) and np.isfinite(xmin):
            x_fit = counts.index[counts.index >= xmin].to_numpy(dtype=float)
            if x_fit.size:
                observed_tail = (counts.loc[x_fit] / total).to_numpy(dtype=float)
                y_fit = observed_tail[0] * np.power(x_fit / x_fit[0], -gamma)
                valid = y_fit >= observed_tail.min()

                if np.count_nonzero(valid) >= 2:
                    plt.plot(x_fit[valid], y_fit[valid], "r--", linewidth=2, label=f"Power law (γ={gamma:.2f})")
                    plt.legend()

    out_path = os.path.join(outdir, f"{graph_label}-{metric}.png")
    plt.savefig(out_path)
    plt.close()

    return {
        "graph": graph_label,
        "metric": metric,
        "metric_key": metric_key,
        "path": out_path,
        "gamma": gamma,
        "xmin": xmin,
    }


def run(config):
    """Entry point called by scr/main.py. Globs every per-metric centrality
    CSV produced by the centrality stage and builds one plot per file.

    Besides the plots themselves, this also writes
    OUTPUT/raw/histograms/powerlaw_fit_summary.csv (graph, gamma, xmin) so
    report.py can build the degree-distribution page purely from
    OUTPUT/raw, without depending on this function's return value."""
    paths = config["paths"]
    centrality_dir = os.path.join(paths["output_raw"], "centralities")
    histogram_dir = os.path.join(paths["output_raw"], "histograms")

    results = []
    for filepath in sorted(glob.glob(os.path.join(centrality_dir, "*.csv"))):
        print(f"Constructing dot diagram for {os.path.basename(filepath)}...")
        results.append(build_histogram(filepath, histogram_dir))

    fits = [r for r in results if r["gamma"] is not None]
    for r in fits:
        print(f"[{r['graph']}] gamma: {r['gamma']:.6f}, xmin: {r['xmin']:.6f}")

    os.makedirs(histogram_dir, exist_ok=True)
    fit_summary_path = os.path.join(histogram_dir, "powerlaw_fit_summary.csv")
    with open(fit_summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["graph", "gamma", "xmin"])
        for r in fits:
            writer.writerow([r["graph"], r["gamma"], r["xmin"]])

    return results
