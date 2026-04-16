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
            # map column names to indices (if possible)
            idxs = []
            for c in cols:
                if c.isdigit():
                    idxs.append(int(c))
                else:
                    try:
                        idxs.append(header.index(c))
                    except ValueError:
                        print(f"column not found: {c}", file=sys.stderr)
                        return
        else:
            idxs = None

        print("Delimiter:", repr(sep_used))
        print("Header:", header if not idxs else [header[i] for i in idxs])

        shown = 0
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

def main():
    # Use fixed inputs (do not generalize via command-line)
    file = "soc-redditHyperlinks-body.tsv"
    sep = "\t"
    head = 10
    cols = ["SOURCE_SUBREDDIT", "TARGET_SUBREDDIT"]
    max_nodes = 40000

    # Build graph
    G = CreateGraph_from_tsv(file, sep, head, cols, False)

    if G is None:
        print("No graph was created (file empty or error).")
        return

    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    print(f"Graph loaded: {n_nodes} nodes, {n_edges} edges")

    if n_nodes == 0:
        print("Graph is empty — nothing to plot.")
        return

    # If graph is too big to plot, reduce to largest weakly connected component
    H = G
    if n_nodes > max_nodes:
        comps = list(nx.weakly_connected_components(G))
        if comps:
            comps.sort(key=len, reverse=True)
            largest = comps[0]
            H = G.subgraph(largest).copy()
            # If the largest component is still too big, downsample to max_nodes for plotting
            if H.number_of_nodes() > max_nodes:
                nodes_to_plot = list(largest)[:max_nodes]
                H = G.subgraph(nodes_to_plot).copy()
                print(f"Graph larger than {max_nodes} nodes — plotting a {H.number_of_nodes()}-node sample from the largest component")
            else:
                print(f"Graph larger than {max_nodes} nodes — plotting largest component with {H.number_of_nodes()} nodes")

    # Draw
    # larger canvas for better readability
    plt.figure(figsize=(18, 12))
    try:
        pos = nx.spring_layout(H, seed=42)
    except Exception as e:
        # spring_layout can require scipy for large/sparse graphs; fallback to a random layout
        print("spring_layout failed (maybe missing scipy) — falling back to random_layout:", e)
        pos = nx.random_layout(H, seed=42)

    nx.draw_networkx_nodes(H, pos, node_size=10, node_color="lightblue")
    nx.draw_networkx_edges(H, pos, arrows=True, arrowstyle='->')
    nx.draw_networkx_labels(H, pos, font_size=2)

    plt.title(f"Subreddit hyperlink graph ({H.number_of_nodes()} nodes, {H.number_of_edges()} edges)")
    plt.tight_layout()
    out_path = "graph.png"
    try:
        plt.savefig(out_path, dpi=200)
        print(f"Saved figure to: {out_path}")
    except Exception as e:
        print("Failed to save figure:", e)

    # Show is optional in headless environments; keep it but don't fail if it warns
    try:
        plt.show()
    except Exception:
        pass
    

if __name__ == "__main__":
    main()