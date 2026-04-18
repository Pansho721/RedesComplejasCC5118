import networkx as nx
import matplotlib.pyplot as plt

import argparse
import csv
import sys

def CreateGraph_from_tsv(path, sep='\t', head=10, cols=None, count=False):
    
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
                    G.add_edge(row[0], row[1])
        else:
            # if head==0, just count or nothing
            for row in reader:
                total += 1

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

def main():
    partition = write_partition_graphs(num_partitions=8, file_prefix="partition")
    for i, p in enumerate(partition):
        if p.number_of_nodes() == 0:
            print(f"Partition {i} is empty; skipping plot.")
            continue

        # Draw
        plt.figure(figsize=(100, 100))
        try:
            pos = nx.spring_layout(p, seed=42)
        except Exception as e:
            # spring_layout can require scipy for large/sparse graphs; fallback to a random layout
            print("spring_layout failed (maybe missing scipy) — falling back to random_layout:", e)
            pos = nx.random_layout(p, seed=42)

        nx.draw_networkx_nodes(p, pos, node_size=5, node_color="lightblue")
        nx.draw_networkx_edges(p, pos, arrows=True, arrowstyle='->', alpha=0.5)

        plt.title(f"Subreddit hyperlink graph ({p.number_of_nodes()} nodes, {p.number_of_edges()} edges)")
        plt.tight_layout()
        out_path = f"graph_{i}.png"
        try:
            plt.savefig(out_path, dpi=200)
            print(f"Saved figure to: {out_path}")
        except Exception as e:
            print("Failed to save figure:", e)
        plt.close()
    

if __name__ == "__main__":
    main()