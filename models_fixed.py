"""
models_fixed.py 

Compara los modelos generativos (ER, BA, Dual BA) contra AGG_REDDIT,
pero generando los modelos con el MISMO N que la componente conexa
real del AGG, para que la comparacion sea justa.

"""

import networkx as nx
from models import small_world_analysis, properties_analysis
from plot import load_graph_from_edgelist


if __name__ == "__main__":
    # ── Cargar los grafos reales ──────────────────────────────────────────
    POS_REDDIT = load_graph_from_edgelist("graphs/reddit_positive.edgelist", kind='DiGraph')
    NEG_REDDIT = load_graph_from_edgelist("graphs/reddit_negative.edgelist", kind='DiGraph')
    AGG_REDDIT = load_graph_from_edgelist("graphs/reddit_weighted_aggregated.edgelist", kind='DiGraph')

    # ── Tamaño de la COMPONENTE FUERTEMENTE CONEXA del AGG ────────────────
    # Este es el cambio clave: N ya no es el total de nodos del AGG,
    # sino el de su componente conexa (la que realmente se compara).
    scc_nodes = max(nx.strongly_connected_components(AGG_REDDIT), key=len)
    N = len(scc_nodes)                       # antes: AGG_REDDIT.number_of_nodes()
    E = AGG_REDDIT.subgraph(scc_nodes).number_of_edges()

    per = E / (N * (N - 1))
    m = max(1, int(E / N))
    m1 = max(1, int(NEG_REDDIT.number_of_edges() / NEG_REDDIT.number_of_nodes()))
    m2 = max(1, int(POS_REDDIT.number_of_edges() / POS_REDDIT.number_of_nodes()))
    pdba = m1 / (m1 + m2)

    print(f"N (componente conexa AGG): {N}, E: {E}")
    print(f"per: {per:.8f}, pdba: {pdba:.4f}, m: {m}, m1: {m1}, m2: {m2}\n")

    # ── Generar los modelos con el N corregido ────────────────────────────
    agg_scc = AGG_REDDIT.subgraph(scc_nodes).copy()
    er  = nx.erdos_renyi_graph(N, per, directed=True)
    ba  = nx.barabasi_albert_graph(N, m)
    dba = nx.dual_barabasi_albert_graph(N, m1, m2, pdba)

    modelos = [
        (agg_scc, "AGG_REDDIT (real)"),
        (er,  "Erdos-Renyi"),
        (ba,  "Barabasi-Albert"),
        (dba, "Dual Barabasi-Albert"),
    ]

    # ── Tabla 1: mundo pequeño ────────────────────────────────────────────
    print("[*Graph*], [*N*], [*E*], [*k*], [*L*], [*C*]")
    for g, name in modelos:
        print(small_world_analysis(g, name))

    # ── Tabla 2: propiedades (conexo + assortativity) ─────────────────────
    print("\n\n[*Graph*], [*Connected*], [*Assortativity*]")
    for g, name in modelos:
        print(properties_analysis(g, name))
