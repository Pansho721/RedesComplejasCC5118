import networkx as nx
from plot import load_graph_from_edgelist
from analysis import smallWorld

def center_analysis(graph, name):
    if graph.is_directed():
        # Use largest strongly connected component for directed graphs
        comp_nodes = max(nx.strongly_connected_components(graph), key=len)
        H = graph.subgraph(comp_nodes).copy()
    else:
        # Use largest connected component for undirected graphs
        comp_nodes = max(nx.connected_components(graph), key=len)
        H = graph.subgraph(comp_nodes).copy()

    N = H.number_of_nodes()
    E = H.number_of_edges()
    k = (2 * E) / N

    L = nx.average_shortest_path_length(H)
    C = nx.average_clustering(H)

    print(f"[{name}], [{N}], [{E}], [{L}], [{C}]")


def modelAnalisys(N, per, pdba, m, m1, m2):
          
    ER = nx.erdos_renyi_graph(N, per, directed=True)
    BA = nx.barabasi_albert_graph(N, m)
    DBA = nx.dual_barabasi_albert_graph(N, m1, m2, pdba)

    center_analysis(ER, "Erdos-Renyi")
    center_analysis(BA, "Barabasi-Albert")
    center_analysis(DBA, "Dual Barabasi-Albert")


if __name__ == "__main__":
    POS_REDDIT = load_graph_from_edgelist("graphs/reddit_positive.edgelist", kind='DiGraph')
    NEG_REDDIT = load_graph_from_edgelist("graphs/reddit_negative.edgelist", kind='DiGraph')
    AGG_REDDIT = load_graph_from_edgelist("graphs/reddit_weighted_aggregated.edgelist", kind='DiGraph')
      
    N = AGG_REDDIT.number_of_nodes()
    E = AGG_REDDIT.number_of_edges()
    per = E / (N * (N - 1))
    m = int(E / N)
    m1 = NEG_REDDIT.number_of_nodes()
    m2 = POS_REDDIT.number_of_nodes()
    pdba = m1 / (m1 + m2)

    print("ER")
    ER = nx.erdos_renyi_graph(N, per, directed=True)
    print("analysis")
    center_analysis(ER, "Erdos-Renyi")

    print(N, per, pdba, m, m1, m2)

    print(f"[Graph], [N], [E], [L], [C]")
    modelAnalisys(N, per, pdba, m, m1, m2)