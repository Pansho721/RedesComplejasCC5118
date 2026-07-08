import networkx as nx
from concurrent.futures import ProcessPoolExecutor
from plot import load_graph_from_edgelist

def small_world_analysis(graph, name):

    print(f"[{name}] (0/3) Starting analysis")
    if graph.is_directed():
        # Use largest strongly connected component for directed graphs
        comp_nodes = max(nx.strongly_connected_components(graph), key=len)
        H = graph.subgraph(comp_nodes).copy()
    else:
        # Use largest connected component for undirected graphs
        comp_nodes = max(nx.connected_components(graph), key=len)
        H = graph.subgraph(comp_nodes).copy()

    
    print(f"[{name}] (1/3) Calculating Nodes and edges")
    N = H.number_of_nodes()
    E = H.number_of_edges()
    k = (2 * E) / N
    print(f"[{name}] (2/3) Calculating L and C")
    L = nx.average_shortest_path_length(H)
    C = nx.average_clustering(H)
    print(f"[{name}] (3/3) Done")

    return f"[{name}], [{N}], [{E}], [{k:.6f}], [{L:.6f}], [{C:.6f}]"


def properties_analysis(graph, name):
    print(f"[{name}] (1/3) Connectivity")
    if graph.is_directed():
        conx = nx.is_strongly_connected(graph)
    else:
        conx = nx.is_connected(graph)
    print(f"[{name}] (2/3) Assortativity")
    assortativity = nx.degree_assortativity_coefficient(graph)
    print(f"[{name}] (3/3) Done")

    return f"[{name}], [{conx}], [{assortativity:.6f}]"

def analyze_model(func, model_kind, N, per, pdba, m, m1, m2):
    if model_kind == "AGG":
        graph = load_graph_from_edgelist("graphs/reddit_weighted_aggregated.edgelist", kind='DiGraph')
        name = "AGG_REDDIT"
    elif model_kind == "ER":
        graph = nx.erdos_renyi_graph(N, per, directed=True)
        name = "Erdos-Renyi"
    elif model_kind == "BA":
        graph = nx.barabasi_albert_graph(N, m)
        name = "Barabasi-Albert"
    elif model_kind == "DBA":
        graph = nx.dual_barabasi_albert_graph(N, m1, m2, pdba)
        name = "Dual Barabasi-Albert"
    else:
        raise ValueError(f"Unsupported model: {model_kind}")

    return func(graph, name)


def modelAnalisys(N, per, pdba, m, m1, m2):
    kinds = ["AGG", "ER", "BA", "DBA"]
    with ProcessPoolExecutor(max_workers=4) as executor:
        rows1 = executor.map(
            analyze_model,
            [small_world_analysis] * 4,
            kinds,
            [N] * 4,
            [per] * 4,
            [pdba] * 4,
            [m] * 4,
            [m1] * 4,
            [m2] * 4,
        )
        rows1 = list(rows1)

    with ProcessPoolExecutor(max_workers=4) as executor:
        rows2 = executor.map(
            analyze_model,
            [properties_analysis] * 4,
            kinds,
            [N] * 4,
            [per] * 4,
            [pdba] * 4,
            [m] * 4,
            [m1] * 4,
            [m2] * 4,
        )
        rows2 = list(rows2)
    print(f"[*Graph*], [*N*], [*E*], [*k*], [*L*], [*C*]")
    for row in rows1:
        print(row)
    print(f"\n\n[*Graph*], [*Connected*], [*Assortativity*]")
    for row in rows2:
        print(row)
    


if __name__ == "__main__":
    POS_REDDIT = load_graph_from_edgelist("graphs/reddit_positive.edgelist", kind='DiGraph')
    NEG_REDDIT = load_graph_from_edgelist("graphs/reddit_negative.edgelist", kind='DiGraph')
    AGG_REDDIT = load_graph_from_edgelist("graphs/reddit_weighted_aggregated.edgelist", kind='DiGraph')
      
    N = AGG_REDDIT.number_of_nodes()
    E = AGG_REDDIT.number_of_edges()
    per = E / (N * (N - 1))
    m = int(E / N)
    m1 = int(NEG_REDDIT.number_of_edges() / NEG_REDDIT.number_of_nodes())
    m2 = int(POS_REDDIT.number_of_edges() / POS_REDDIT.number_of_nodes())
    pdba = m1 / (m1 + m2)

    print(f"N: {N}, E: {E}, per: {per}, pdba: {pdba}, m: {m}, m1: {m1}, m2: {m2}")
    modelAnalisys(N, per, pdba, m, m1, m2)