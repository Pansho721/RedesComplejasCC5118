import os

from plot import load_graph_from_edgelist
import networkx as nx
import pandas as pd
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

def join(prefix, sufix="_full_centrality.csv"):
    df1 = pd.read_csv(f"{prefix}_degree.centrality", sep='\t', names=['node', 'degree'])
    df2 = pd.read_csv(f"{prefix}_betweenness.centrality", sep='\t', names=['node', 'betweenness'])
    df3 = pd.read_csv(f"{prefix}_closeness.centrality", sep='\t', names=['node', 'closeness'])
    result = df1.merge(df2, on='node').merge(df3, on='node')
    result['average'] = (result['degree'] + result['betweenness'] + result['closeness']) / 3
    result = result.sort_values('average', ascending=False)
    result.to_csv(f"{prefix}{sufix}", sep=',', index=False)

def print_typst_table(path):
    df = pd.read_csv(path, sep=',')
    df = df.head(10)  # Print only top 10 for brevity
    print("[*node*], [*degree*], [*betweenness*], [*closeness*], [*average*]")
    for _, row in df.iterrows():
        print(f"[{row['node']}], [{row['degree']:.6f}], [{row['betweenness']:.6f}], [{row['closeness']:.6f}], [{row['average']:.6f}],")
                

if __name__ == "__main__":
    print("Loading negative graph...")
    neg_graph = load_graph_from_edgelist("graphs/reddit_negative.edgelist", kind='DiGraph')
    print("Loading aggregated graph...")
    agg_graph = load_graph_from_edgelist("graphs/reddit_weighted_aggregated.edgelist", kind='MultiDiGraph')

    print("Negative graph centrality...")
    neg_centrality = get_full_centrality(neg_graph)
    print("Aggregated graph centrality...")
    agg_centrality = get_full_centrality(agg_graph)

    print("Saving negative graph centrality...")
    save_centrality(neg_centrality, "centrality/reddit_negative_centrality")
    print("Saving aggregated graph centrality...")
    save_centrality(agg_centrality, "centrality/reddit_aggregated_centrality")

    print("Joining negative graph centrality...")
    join("centrality/reddit_negative_centrality","_full_centrality.csv")
    print_typst_table("centrality/reddit_negative_centrality_full_centrality.csv")

    print("Joining aggregated graph centrality...")
    join("centrality/reddit_aggregated_centrality","_full_centrality.csv")
    print_typst_table("centrality/reddit_aggregated_centrality_full_centrality.csv")