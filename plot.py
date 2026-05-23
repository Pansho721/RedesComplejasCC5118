import networkx as nx
import matplotlib.pyplot as plt
import csv
import os
import sys

def load_graph_from_edgelist(path, kind='DiGraph', sep='\t'):
    if kind == 'DiGraph':
        G = nx.DiGraph()
    elif kind == 'Graph':
        G = nx.Graph()
    elif kind == 'MultiDiGraph':
        G = nx.MultiDiGraph()
    elif kind == 'MultiGraph':
        G = nx.MultiGraph()
    else:
        raise ValueError(f"Unsupported graph type: {kind}")

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=sep)
        for row in reader:
            if len(row) < 2:
                continue
            src = row[0].strip()
            dst = row[1].strip()
            if not src or not dst:
                continue
            G.add_edge(src, dst)
    return G


def load_node_set(path):
    nodes = set()
    try:
        with open(path, encoding='utf-8') as f:
            for line in f:
                v = line.strip()
                if v:
                    nodes.add(v)
    except FileNotFoundError:
        pass
    return nodes


def write_partition_graphs(num_partitions=8, file_prefix="partition/"):
    partitions = []
    for i in range(num_partitions):
        out_path = f"{file_prefix}{i}.graph"
        master_nodes = load_node_set(f"partitionMaster/{i}_master.graph")
        mirror_nodes = load_node_set(f"partitionMirror/{i}_mirror.graph")
        G = load_graph_from_edgelist(out_path, kind='DiGraph', sep='\t')
        G.graph['master_nodes'] = master_nodes
        G.graph['mirror_nodes'] = mirror_nodes
        partitions.append(G)
        print(f"Loaded partition from: {out_path} ({G.number_of_edges()} edges, {len(master_nodes)} masters, {len(mirror_nodes)} mirrors)")
    return partitions



def draw_and_save_graph(G, out_path, title, node_size=8, fig_size=(20, 20), dpi=50):
    if G.number_of_nodes() == 0:
        print(f"Graph is empty; skipping plot for {out_path}.")
        return

    master_nodes = G.graph.get('master_nodes', set())
    mirror_nodes = G.graph.get('mirror_nodes', set())

    node_colors = []
    for n in G.nodes():
        if n in master_nodes:
            node_colors.append("#d9534f")  # red
        elif n in mirror_nodes:
            node_colors.append("#2f6db3")  # blue
        else:
            node_colors.append("#aaaaaa")  # grey fallback

    plt.figure(figsize=fig_size)
    try:
        # spring layout can be slow for large graphs
        if G.number_of_nodes() <= 2500:
            pos = nx.spring_layout(G, seed=42)
        else:
            pos = nx.random_layout(G, seed=42)
    except Exception as e:
        print("layout failed; falling back to random_layout:", e)
        pos = nx.random_layout(G, seed=42)

    nx.draw_networkx_nodes(G, pos, node_size=node_size, node_color=node_colors, alpha=0.85)
    nx.draw_networkx_edges(G, pos, arrows=False, alpha=0.15, width=0.4)

    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    try:
        out_dir = os.path.dirname(out_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        plt.savefig(out_path, dpi=dpi, bbox_inches="tight")
        print(f"Saved figure to: {out_path}")
    except Exception as e:
        print("Failed to save figure:", e)
    plt.close()


def plot_partitions():
    partition = write_partition_graphs(num_partitions=9, file_prefix="partition/")
    for i, p in enumerate(partition):
        out_path = f"graph_{i}.png"
        draw_and_save_graph(p, out_path,"", node_size=10, fig_size=(20, 20), dpi=100)

def plot_graph(path="graphs/reddit.edgelist", title="Full graph", size=(80, 80), dpi=30, sep='\t'):
    G = load_graph_from_edgelist(path, sep=sep)
    print(f"Graph loaded with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    title = f"{title}: ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)"
    draw_and_save_graph(G, "img/graph.png", title, node_size=1, fig_size=size, dpi=dpi)

if __name__ == "__main__":
    plot_graph("graphs/reddit_negative.edgelist","Grafo Negativo", size=(10, 10), dpi=100)