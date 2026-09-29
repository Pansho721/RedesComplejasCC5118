"""Shared edgelist loading used by every downstream stage.

Previously part of plot.py, which also drew and saved node-link visualizations
of graph partitions. That drawing code (and the C++ partitioner that fed it)
was dropped in the refactor to scr/ - this module keeps only the loader that
every other stage actually depends on.
"""
import csv

import networkx as nx

_BUILDERS = {
    "DiGraph": nx.DiGraph,
    "Graph": nx.Graph,
    "MultiDiGraph": nx.MultiDiGraph,
    "MultiGraph": nx.MultiGraph,
}


def load_graph_from_edgelist(path, kind="DiGraph", sep="\t"):
    """Load a plain-text edgelist into a NetworkX graph.

    Infers the edge schema from the column count:
      - 2 columns: (src, dst)                   -> unweighted edge
      - 3 columns: (src, dst, sentiment)         -> weight = sentiment
      - 4 columns: (src, dst, sentiment, count)  -> weight = count * sentiment
    """
    if kind not in _BUILDERS:
        raise ValueError(f"Unsupported graph type: {kind}")
    G = _BUILDERS[kind]()

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=sep)
        for row in reader:
            if len(row) < 2:
                continue
            if len(row) >= 4:
                src, dst, sent, value = row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip()
                try:
                    value = int(value)
                except ValueError:
                    value = 1
                try:
                    sent = int(sent)
                except ValueError:
                    sent = 1
                G.add_edge(src, dst, weight=value * sent)
            elif len(row) == 3:
                src, dst, sent = row[0].strip(), row[1].strip(), row[2].strip()
                try:
                    sent = int(sent)
                except ValueError:
                    sent = 1
                G.add_edge(src, dst, weight=sent)
            else:
                src, dst = row[0].strip(), row[1].strip()
                if not src or not dst:
                    continue
                G.add_edge(src, dst)
    return G
