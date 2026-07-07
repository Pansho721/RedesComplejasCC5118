import os
import math
import pandas as pd
import networkx as nx
from plot import load_graph_from_edgelist
import matplotlib.pyplot as plt


def smallWorld(graphs, names):
    print(f"[*Graph*], [*Metric*], [*graph value*], [*ER*],")
    for i in range(len(graphs)):
        graph = graphs[i]
        name = names[i]

        k_avg = sum(dict(graph.degree()).values()) / graph.number_of_nodes()
        k = (2 * graph.number_of_edges()) / graph.number_of_nodes()

        L_ER = math.log(graph.number_of_nodes()) / math.log(k_avg)
        C_ER = k_avg / graph.number_of_nodes()

        L = nx.average_shortest_path_length(graph)
        C = nx.average_clustering(graph)

        print(f"[{name}], [Grado promedio], [{k}], [{k_avg}],")
        print(f"[{name}], [Largo caracteristico], [{L}], [{L_ER}],")
        print(f"[{name}], [Coeficiente de clustering], [{C}], [{C_ER}],")

    return


def bowtie(AGG_REDDIT, CONX_REDDIT):
    scc_nodes = set(CONX_REDDIT.nodes())
    nodo_referencia = next(iter(scc_nodes))

    # IN-Component: Nodos que pueden llegar al SCC (Ancestros), pero no están en el SCC
    in_component = nx.ancestors(AGG_REDDIT, nodo_referencia) - scc_nodes
    # OUT-Component: Nodos alcanzables desde el SCC (Descendientes), pero no están en el SCC
    out_component = nx.descendants(AGG_REDDIT, nodo_referencia) - scc_nodes
    # Tendrils: El resto de los nodos que no pertenecen a ninguna de las 3 anteriores
    tendrils = set(AGG_REDDIT.nodes()) - scc_nodes - in_component - out_component

    print(f"Total nodos en la red: {len(AGG_REDDIT.nodes())}")
    print(f"\nNúcleo (SCC): {len(scc_nodes)} nodos")
    print(f"\nComponente IN (Inician hilos hacia el núcleo): {len(in_component)} nodos")
    print(f"\nComponente OUT (Son mencionados por el núcleo): {len(out_component)} nodos")
    print(f"\nTendrils/Tubos (Periferia aislada): {len(tendrils)} nodos\n")


    # GRÁFICO 2: Proporciones de la Estructura Bow-tie
    etiquetas = ['Núcleo (SCC)', 'Componente IN', 'Componente OUT', 'Tendrils']
    valores = [len(scc_nodes), len(in_component), len(out_component), len(tendrils)]
    colores = ['#9b59b6', '#3498db', '#e74c3c', '#95a5a6']

    plt.figure(figsize=(8, 5))
    barras = plt.bar(etiquetas, valores, color=colores)

    for barra in barras:
        yval = barra.get_height()
        plt.text(barra.get_x() + barra.get_width()/2, yval + 200,
                f'{yval}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.title("Estructura Macroscópica Bow-tie de Reddit", fontsize=14)
    plt.ylabel("Cantidad de Subreddits", fontsize=12)
    plt.ylim(0, max(valores) + 2000)

    try:
        out_path="img/bowtie_reddit.png"
        out_dir = os.path.dirname(out_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        print(f"Saved figure to: {out_path}")
    except Exception as e:
        print("Failed to save figure:", e)

if __name__ == "__main__":
    AGG_REDDIT = load_graph_from_edgelist("graphs/reddit_weighted_aggregated.edgelist", kind='DiGraph')
    NEG_REDDIT = load_graph_from_edgelist("graphs/reddit_negative.edgelist", kind='DiGraph')
    POS_REDDIT = load_graph_from_edgelist("graphs/reddit_positive.edgelist", kind='DiGraph')
    CONX_REDDIT = nx.DiGraph(AGG_REDDIT.subgraph(max(nx.strongly_connected_components(AGG_REDDIT), key=len)))
    CONX_NEG = nx.DiGraph(NEG_REDDIT.subgraph(max(nx.strongly_connected_components(NEG_REDDIT), key=len)))
    CONX_POS = nx.DiGraph(POS_REDDIT.subgraph(max(nx.strongly_connected_components(POS_REDDIT), key=len)))

    print("\n==========================================================")
    print("\tAssortativity SECTION")
    print("==========================================================\n")

    assortativity_neg = nx.degree_assortativity_coefficient(NEG_REDDIT, weight='weight')
    assortativity_agg = nx.degree_assortativity_coefficient(AGG_REDDIT, weight='weight')
    assortativity_pos = nx.degree_assortativity_coefficient(POS_REDDIT, weight='weight')
    print(f"Assortativity en AGG_REDDIT: {assortativity_agg}")
    print(f"Assortativity en NEG_REDDIT: {assortativity_neg}")
    print(f"Assortativity en POS_REDDIT: {assortativity_pos}")

    print("\n==========================================")
    print("\tSmall world analysis SECTION")
    print("==========================================\n")

    smallWorld([CONX_REDDIT, CONX_NEG, CONX_POS], ["CONX_REDDIT", "CONX_NEG", "CONX_POS"])

    print("\n==========================================================")
    print("\tBowtie analysis SECTION")
    print("==========================================================\n")

    bowtie(AGG_REDDIT, CONX_REDDIT)