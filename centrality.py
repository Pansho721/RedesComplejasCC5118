from multiprocessing import Pool
from plot import load_graph_from_edgelist
import networkx as nx
import pandas as pd
import itertools
import math
import os

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

#   ==========================================================================================
#           END NETWORKX COPY PASTE DOCUMENTATION
#   ==========================================================================================


# Lazy compute centraliy
def compute_centrality(graph, kind='degree'):
    try:
        match kind:
            case 'degree':
                return nx.degree_centrality(graph)
            case 'in-degree':
                return nx.in_degree_centrality(graph)
            case 'out-degree':
                return nx.out_degree_centrality(graph)
            case 'betweenness':
                return betweenness_centrality_parallel(graph)
            case 'closeness':
                return nx.closeness_centrality(graph)
            case 'alpha-centrality':
                eigenvalues = nx.adjacency_spectrum(graph)
                spectral_radius = max(abs(e) for e in eigenvalues)
                alpha = 0.85 / spectral_radius
                return nx.katz_centrality(graph, alpha=alpha, weight='weight')
            case 'pagerank':
                return nx.pagerank(graph, alpha=0.85, weight='weight')
            case _:
                print(f"\t\tUnsupported centrality type: {kind}")
                return None
    except Exception as e:
        print(f"\t\tError computing {kind} centrality: {e}")
        return None

# Compute the selected centrality measure
def get_some_centrality(graph,kinds=['degree', 'alpha-centrality']):
    """Compute all centrality measures and return as dict of dicts."""
    results = []
    for kind in kinds:
        print(f"\t\tComputing {kind} centrality...")
        results.append(compute_centrality(graph, kind))
    return dict(zip(kinds, results))

# Save centrality measures to CSV files
def save_centrality(dict, output_name):
        try:
            for kind in dict:
                out_path = f"{output_name}_{kind}.csv"
                out_dir = os.path.dirname(out_path)
                if out_dir:
                    os.makedirs(out_dir, exist_ok=True)

                with open(out_path, 'w', encoding='utf-8') as f:
                    print(f"\t\t{kind} centrality saved to: {out_path}")
                    for node, centrality in sorted(dict[kind].items(), key=lambda item: item[1], reverse=True):
                        f.write(f"{node}\t{centrality}\n")
        except Exception as e:
            print(f"\t\tError saving centrality: {kind}\n\t\t{e}")

# Join all centralities into a single CSV file with an average column
def join(output, prefix, sufix, kinds):
    df = []
    for kind in kinds:
        df.append(pd.read_csv(f"centrality/{prefix}_{kind}.csv", sep='\t', names=['node', kind]))
    result = df[0]
    for i in range(1, len(df)):
        result = result.merge(df[i], on='node')
    result['average'] = sum(result[k] for k in kinds) / len(kinds)
    result = result.sort_values('average', ascending=False)
    out_dir = os.path.dirname(f"{output}{prefix}_{sufix}")
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    result.to_csv(f"{output}{prefix}_{sufix}", sep=',', index=False)

def print_typst_table(path, kinds):
    print(kinds)
    df = pd.read_csv(path, sep=',')
    df = df.head(10)  # Print only top 10 for brevity
    print("[*node*],", end=' ')
    for k in kinds:
        print(f"[*{k}*],", end=' ')
    print("\n")
    for _, row in df.iterrows():
        print(f"[{row['node']}],", end=' ')
        for k in kinds:
            print(f"[{row[k]:.6f}],", end=' ')
        print("\n")
        
def stats(input, graph, kinds):
    df = pd.read_csv(f"{input}/{graph}_full_centrality.csv", sep=',')
    print(f"\t\tStatistics for {graph} centrality:")
    for kind in kinds:
        max_value = df[kind].max()
        min_value = df[kind].min()
        avg_value = df[kind].mean()
        max_node = df.loc[df[kind] == max_value, 'node'].values[0]
        min_node = df.loc[df[kind] == min_value, 'node'].values[0]
        print(f"\t\t\t{kind}: max={max_value:.6f} ({max_node}), min={min_value:.6f} ({min_node}), avg={avg_value:.6f}")

if __name__ == "__main__":
    kinds = {
        'AGG_REDDIT': ['degree', 'pagerank'],
        'CONX_REDDIT': ['degree', 'betweenness', 'closeness', 'alpha-centrality', 'pagerank'],
        'NEG_REDDIT': ['degree', 'in-degree', 'out-degree', 'alpha-centrality', 'pagerank'],
    }

    print("==========================================")
    print("Loading graph SECTION")
    print("==========================================")

    print("\tLoading negative graph...")
    neg_graph = load_graph_from_edgelist("graphs/reddit_negative.edgelist", kind='DiGraph')
    print("\tLoading aggregated graph...")
    agg_graph = load_graph_from_edgelist("graphs/reddit_weighted_aggregated.edgelist", kind='DiGraph')
    print("\tLoading largest strongly connected component...")
    largest = nx.DiGraph(agg_graph.subgraph(max(nx.strongly_connected_components(agg_graph), key=len)))

    graphs = {  'NEG_REDDIT': neg_graph,
                'AGG_REDDIT': agg_graph,
                'CONX_REDDIT': largest}


    print("==========================================")
    print("Centrality Calculating SECTION")
    print("==========================================")
    centralities = {}
    for g,_ in graphs.items():
        print(f"\tCalculating {g} graph centrality...")
        kind = kinds[g]
        centralities[g] = get_some_centrality(graphs[g], kind)
    
    print("==========================================")
    print("Centrality Saving SECTION")
    print("==========================================")
    for g, centrality in centralities.items():
        print(f"\tSaving {g} graph centrality...")
        save_centrality(centrality, f"centrality/reddit_{g}_centrality")

    print("==========================================")
    print("Joining SECTION")
    print("==========================================")
    for g, centrality in centralities.items():
        print(f"\tJoining {g} graph centrality...")
        kind = kinds[g]
        join("centrality_summary/", f"reddit_{g}_centrality", "full_centrality.csv", kind)
    
    print("==========================================")
    print("Stadistic SECTION")
    print("==========================================")
    for g, centrality in centralities.items():
        print(f"\tPrinting {g} graph centrality statistics...")
        kind = kinds[g]
        stats("centrality_summary", f"reddit_{g}_centrality", kind)

    print("==========================================")
    print("Printing SECTION")
    print("==========================================")
    for g, centrality in centralities.items():
        print(f"\tPrinting centrality for {g} table")
        kind = kinds[g]
        kind.append('average')
        print_typst_table(f"centrality_summary/reddit_{g}_centrality_full_centrality.csv", kind)


    