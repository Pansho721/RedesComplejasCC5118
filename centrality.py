from multiprocessing import Pool
from plot import load_graph_from_edgelist
import networkx as nx
import pandas as pd
import itertools
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
            case 'betweenness':
                return betweenness_centrality_parallel(graph)
            case 'closeness':
                return nx.closeness_centrality(graph)
            case 'alpha-centrality':
                max_degree = max(d for _, d in graph.degree())
                alpha = 1.0 / (max_degree + 1.0)
                return nx.katz_centrality(graph, alpha=alpha, weight='weight')
            case _:
                print(f"\t\tUnsupported centrality type: {kind}")
                return None
    except Exception as e:
        print(f"\t\tError computing {kind} centrality: {e}")
        return None

# Compute the selected centrality measure
def get_some_centrality(graph,kinds=['degree', 'betweenness', 'alpha-centrality']):
    """Compute all centrality measures and return as dict of dicts."""
    results = [compute_centrality(graph, kind) for kind in kinds]
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
def join(prefix, sufix="_full_centrality.csv", kinds=['degree', 'betweenness', 'alpha-centrality']):
    df = []
    for kind in kinds:
        df.append(pd.read_csv(f"{prefix}_{kind}.csv", sep='\t', names=['node', kind]))
    result = df[0]
    for i in range(1, len(df)):
        result = result.merge(df[i], on='node')
    result['average'] = sum(result[k] for k in kinds) / len(kinds)
    result = result.sort_values('average', ascending=False)
    result.to_csv(f"{prefix}{sufix}", sep=',', index=False)

def print_typst_table(path,kind=['degree', 'betweenness', 'alpha-centrality', 'average']):
    df = pd.read_csv(path, sep=',')
    df = df.head(10)  # Print only top 10 for brevity
    print("[*node*],", end=' ')
    for k in kind:
        print(f"[*{k}*],", end=' ')
    print("\n")
    for _, row in df.iterrows():
        print(f"[{row['node']}],", end=' ')
        for k in kind:
            print(f"[{row[k]:.6f}],", end=' ')
        print("\n")
        


if __name__ == "__main__":

    print("==========================================")
    print("Loading graph SECTION")
    print("==========================================")

    print("\tLoading negative graph...")
    neg_graph = load_graph_from_edgelist("graphs/reddit_negative.edgelist", kind='DiGraph')
    print("\tLoading aggregated graph...")
    agg_graph = load_graph_from_edgelist("graphs/reddit_weighted_aggregated.edgelist", kind='DiGraph')
    print("\tLoading largest strongly connected component...")
    largest = nx.DiGraph(agg_graph.subgraph(max(nx.strongly_connected_components(agg_graph), key=len)))

    print("==========================================")
    print("Centrality Calculating SECTION")
    print("==========================================")

    print("\tNegative graph centrality...")
    neg_centrality = get_some_centrality(neg_graph)
    print("\tAggregated graph centrality...")
    agg_centrality = get_some_centrality(agg_graph)
    print("\tLargest strongly connected component graph centrality...")
    lar_centrality = get_some_centrality(largest, ['degree', 'betweenness', 'closeness', 'alpha-centrality'])

    print("==========================================")
    print("Centrality Saving SECTION")
    print("==========================================")

    print("\tSaving negative graph centrality...")
    save_centrality(neg_centrality, "centrality/reddit_negative_centrality")
    print("\tSaving aggregated graph centrality...")
    save_centrality(agg_centrality, "centrality/reddit_aggregated_centrality")
    print("\tSaving largest strongly connected component graph centrality...")
    save_centrality(lar_centrality, "centrality/reddit_largest_component_centrality")

    print("==========================================")
    print("Printing SECTION")
    print("==========================================")

    print("\tJoining negative graph centrality...")
    join("centrality/reddit_negative_centrality","_full_centrality.csv")
    print_typst_table("centrality/reddit_negative_centrality_full_centrality.csv")

    print("\tJoining aggregated graph centrality...")
    join("centrality/reddit_aggregated_centrality","_full_centrality.csv")
    print_typst_table("centrality/reddit_aggregated_centrality_full_centrality.csv")

    print("\tJoining largest strongly connected component graph centrality...")
    join("centrality/reddit_largest_component_centrality","_full_centrality.csv", kinds=['degree', 'betweenness', 'closeness', 'alpha-centrality'])
    print_typst_table("centrality/reddit_largest_component_centrality_full_centrality.csv",['degree', 'betweenness', 'closeness', 'alpha-centrality', 'average'])


# ==========================================================================================
#               Histogram construction
# ==========================================================================================

    print("Constructing histograms for negative graph...")
    for kind in ['degree', 'alpha-centrality']:
        data = list(neg_centrality[kind].values())
        plt.figure()
        plt.hist(data, bins=50, density=True)
        plt.title(f"{kind.capitalize()} Centrality Distribution (Negative Graph)")
        plt.xlabel(f"{kind.capitalize()} Centrality")
        plt.ylabel("Density")
        plt.savefig(f"histograms/reddit_negative_{kind}_histogram.png")