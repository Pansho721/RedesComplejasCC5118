import networkx as nx
import matplotlib.pyplot as plt

import argparse
import csv
import sys


def CreateGraph_from_file(path, sep='\t', head=10, cols=None, count=False):
    G = nx.DiGraph()
    with open(path, newline='', encoding='utf-8') as f:
        # try to sniff delimiter if sep is 'auto'
        if sep == 'auto':
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters='\t,; ')
                sep_used = dialect.delimiter
            except Exception:
                sep_used = '\t'
        else:
            sep_used = sep

        reader = csv.reader(f, delimiter=sep_used)
        try:
            header = next(reader)
        except StopIteration:
            print("empty file", file=sys.stderr)
            return

        if cols:
            idxs = []
            for c in cols:
                try:
                    idxs.append(header.index(c))
                except ValueError:
                    print(f"column not found: {c}", file=sys.stderr)
                    return
        else:
            idxs = None

        print("Delimiter:", repr(sep_used))
        print("Header:", header if not idxs else [header[i] for i in idxs])

        total = 0
        if head:
            # show header row count included in head? show rows after header
            for row in reader:
                total += 1
                if idxs:
                    row = [row[i] if i < len(row) else '' for i in idxs]
                if len(row) >= 2:
                    src = row[0].strip()
                    dst = row[1].strip()
                    if src and dst:
                        G.add_edge(src, dst)
        else:
            # if head==0, process all data rows and count
            for row in reader:
                total += 1
                if idxs:
                    row = [row[i] if i < len(row) else '' for i in idxs]
                if len(row) >= 2:
                    src = row[0].strip()
                    dst = row[1].strip()
                    if src and dst:
                        G.add_edge(src, dst)

        if count:
            print("Total rows (excluding header):", total)

    return G


def load_graph_from_edgelist(path, sep='\t'):
    G = nx.DiGraph()
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


def write_partition_graphs(num_partitions=8, file_prefix="partition"):
    partitions = []
    for i in range(num_partitions):
        out_path = f"{file_prefix}{i}.graph"
        partitions.append(load_graph_from_edgelist(out_path, sep='\t'))
        print(f"Saved partition graph to: {out_path} ({partitions[i].number_of_edges()} edges)")
    return partitions



def draw_and_save_graph(G, out_path, title):
    if G.number_of_nodes() == 0:
        print(f"Graph is empty; skipping plot for {out_path}.")
        return

    plt.figure(figsize=(80, 80))
    try:
        # spring layout can be slow for large graphs
        if G.number_of_nodes() <= 2500:
            pos = nx.spring_layout(G, seed=42)
        else:
            pos = nx.random_layout(G, seed=42)
    except Exception as e:
        print("layout failed; falling back to random_layout:", e)
        pos = nx.random_layout(G, seed=42)

    nx.draw_networkx_nodes(G, pos, node_size=8, node_color="#2f6db3", alpha=0.85)
    nx.draw_networkx_edges(G, pos, arrows=False, alpha=0.15, width=0.4)

    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    try:
        plt.savefig(out_path, dpi=10, bbox_inches="tight")
        print(f"Saved figure to: {out_path}")
    except Exception as e:
        print("Failed to save figure:", e)
    plt.close()


def plot_partitions():
    partition = write_partition_graphs(num_partitions=8, file_prefix="partition")
    for i, p in enumerate(partition):
        out_path = f"graph_{i}.png"
        title = f"Partition {i} ({p.number_of_nodes()} nodes, {p.number_of_edges()} edges)"
        draw_and_save_graph(p, out_path, title)

def plot_graph():
    G = load_graph_from_edgelist("graph.edgelist", sep='\t')
    print(f"Graph loaded with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    title = f"Full graph ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)"
    draw_and_save_graph(G, "graph.png", title)


def plot_all():
    plot_graph()
    plot_partitions()

def main():
    plot_graph()

if __name__ == "__main__":
    main()