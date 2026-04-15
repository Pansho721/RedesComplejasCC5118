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
    G = CreateGraph_from_tsv("soc-redditHyperlinks-body.tsv", "\t", 10, ["SOURCE_SUBREDDIT","TARGET_SUBREDDIT"], None)
    nx.draw(G, with_labels=True)
    plt.show()

if __name__ == "__main__":
    main()