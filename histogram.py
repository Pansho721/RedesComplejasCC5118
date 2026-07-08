import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import powerlaw
import glob
import os

# ==========================================================================================
#               Histogram construction
# ==========================================================================================

LOG = []

GRAPH_LABELS = {
    'negative': 'NEG_REDDIT',
    'aggregated': 'AGG_REDDIT',
    'largest_component': 'CONX_REDDIT',
}

METRIC_LABELS = {
    'alpha-centrality': 'Alpha',
    'betweenness': 'Betweenness',
    'closeness': 'Closeness',
    'degree': 'Degree',
    'full_centrality': 'Promedio',
}

for filepath in sorted(glob.glob("centrality/*.csv")):
    filename = os.path.basename(filepath)                        # reddit_negative_centrality_degree.csv
    stem = filename.replace("reddit_", "").replace(".csv", "")   # negative_centrality_degree
    parts = stem.split("_centrality_")                           # ['negative', 'degree']
    graph_key = parts[0]                                         # 'GRAPH name'
    metric_key = parts[1] if len(parts) > 1 else stem
    metric = METRIC_LABELS.get(metric_key, metric_key.title())   # 'kind -> Kind label'

    graph_label = GRAPH_LABELS.get(graph_key, graph_key.upper()) # 'NEG_REDDIT'
    title = f"{graph_label} | Distribución de frecuencia: {metric}"
    outdir = f"Graficos/{graph_label}"
    os.makedirs(outdir, exist_ok=True)

    print(f"Constructing dot diagram for {filename}...")
    df = pd.read_csv(filepath, sep='\t', names=['node', 'value'])
    values = df['value']
    counts = values.value_counts().sort_index()
    total = counts.sum()

    plt.figure()
    plt.scatter(counts.index, counts.values / total, s=3, color='black')
    plt.xscale('log')
    plt.yscale('log')
    plt.title(title)
    plt.xlabel(metric)
    plt.ylabel("Frecuencia")

    if metric_key == 'degree':
        values_array = np.array(values)
        fit = powerlaw.Fit(values_array, verbose=False)
        gamma = fit.alpha
        xmin = fit.xmin
        
        LOG.append({"graph": graph_label, "gamma": gamma, "xmin": xmin})

        if np.isfinite(gamma) and np.isfinite(xmin):
            x_fit = counts.index[counts.index >= xmin].to_numpy(dtype=float)
            if x_fit.size:
                observed_tail = (counts.loc[x_fit] / total).to_numpy(dtype=float)
                y_fit = observed_tail[0] * np.power(x_fit / x_fit[0], -gamma)
                valid = y_fit >= observed_tail.min()

                if np.count_nonzero(valid) >= 2:
                    plt.plot(x_fit[valid], y_fit[valid], 'r--', linewidth=2, label=f'Power law (γ={gamma:.2f})')
                    plt.legend()

    plt.savefig(f"{outdir}/{graph_label}-{metric}.png")
    plt.close()

for l in LOG:
    print(f"[{l['graph']}] gamma: {l['gamma']:.6f}, xmin: {l['xmin']:.6f}")