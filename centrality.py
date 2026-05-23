import os

from plot import load_graph_from_edgelist
import networkx as nx

from multiprocessing import Pool
import itertools


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
    kinds = ['degree', 'betweenness', 'closeness']
    results = [compute_centrality(graph, kind) for kind in kinds]
    return dict(zip(kinds, results))

def save_centrality(dict, output_name):
    for kind in dict:
        out_path = f"{output_name}_{kind}.centrality"
        out_dir = os.path.dirname(out_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        with open(out_path, 'w', encoding='utf-8') as f:
            print(kind, "centrality saved to:", out_path)
            for node, centrality in sorted(dict[kind].items(), key=lambda item: item[1], reverse=True):
                f.write(f"{node}\t{centrality}\n")
                
if __name__ == "__main__":
    # Example usage
    graph = load_graph_from_edgelist("graphs/reddit_negative.edgelist", kind='DiGraph')
    centrality = get_full_centrality(graph)
    save_centrality(centrality, "centrality/reddit_negative_centrality")