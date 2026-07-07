import networkx as nx
from plot import load_graph_from_edgelist
from analysis import smallWorld

def modelAnalisys(N, per, pdba, m, m1, m2):
          
    ER = nx.erdos_renyi_graph(N, per, directed=True)
    BA = nx.barabasi_albert_graph(N, m)
    DBA = nx.dual_barabasi_albert_graph(N, m1, m2, pdba)

    smallWorld(ER, "Erdos-Renyi")
    smallWorld(BA, "Barabasi-Albert")
    smallWorld(DBA, "Dual Barabasi-Albert")


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

    ER = nx.erdos_renyi_graph(N, per, directed=True)
    
    print(N, per, pdba, m, m1, m2)
    modelAnalisys(N, per, pdba, m, m1, m2)