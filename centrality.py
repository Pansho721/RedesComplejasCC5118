import plot
import networkx as nx

from joblib import Parallel, delayed
from multiprocessing import Pool
import time
import itertools

import csv
import json



def chunks(l, n):
    """Divide a list of nodes `l` in `n` chunks"""
    l_c = iter(l)
    while 1:
        x = tuple(itertools.islice(l_c, n))
        if not x:
            return
        yield x


def betweenness_centrality_parallel(G, processes=None):
    """Parallel betweenness centrality  function"""
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

    # Reduce the partial solutions
    bt_c = bt_sc[0]
    for bt in bt_sc[1:]:
        for n in bt:
            bt_c[n] += bt[n]
    return bt_c


def compute_centrality(graph, kind='degree'):
    match kind:
        case 'degree':
            return nx.degree_centrality(graph)
        case 'betweenness':
            return betweenness_centrality_parallel(graph)
        case 'closeness':
            return nx.closeness_centrality(graph)
        case _:
            print(f"Unsupported centrality type: {kind}")
            return None


def get_full_centrality(graph):
    """Compute all centrality measures and return as dict of dicts."""
    centrality = {}
    kinds = ['degree', 'betweenness', 'closeness']
    
    results = Parallel(n_jobs=-1)(  # -1 = use all cores
        delayed(compute_centrality)(graph, kind) 
        for kind in kinds
    )

    centrality = dict(zip(kinds, results))
    return centrality


def save_full_centrality(graph, out_path):
    """Compute all centrality measures and save to JSON."""
    centrality = get_full_centrality(graph)

    #full_centrality = centrality['degree'].join(centrality['betweenness'], centrality['closeness'], centrality['eigenvector'])

    #with open(out_path, 'w', encoding='utf-8') as f:
    #    json.dump(full_centrality, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # Example usage
    graph = plot.CreateGraph_from_file('soc-redditHyperlinks-body.tsv', head=1, cols=["SOURCE_SUBREDDIT", "TARGET_SUBREDDIT"], count=False, kind='MultiDiGraph')
    #save_full_centrality(graph, 'centrality_full.json')
    get_full_centrality(graph)