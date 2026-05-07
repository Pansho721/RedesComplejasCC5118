import networkx as nx
import matplotlib.pyplot as plt
import csv
import sys


def CreateGraph_from_file(path, sep='\t', head=10, cols=None, count=False, kind='DiGraph'):
    match kind:
        case 'DiGraph':
            G = nx.DiGraph()
        case 'MultiDiGraph':
            G = nx.MultiDiGraph()
        case _:
            print(f"Unsupported graph type: {kind}", file=sys.stderr)
            return None


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


def create_reddit_edgelist_from_file(input_path, output_path="graph.edgelist", sep='\t'):
    G = CreateGraph_from_file(
        input_path,
        sep=sep,
        head=0,
        cols=["SOURCE_SUBREDDIT", "TARGET_SUBREDDIT"],
        count=True,
    )
    if G is None:
        print("No graph generated from input file.", file=sys.stderr)
        return None

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter='\t')
        for src, dst in G.edges():
            writer.writerow([src, dst])

    print(
        f"Saved edgelist to: {output_path} "
        f"({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)"
    )
    return G


def iter_reddit_publishes(path, sep='\t', cols=("SOURCE_SUBREDDIT", "TARGET_SUBREDDIT", "LINK_SENTIMENT"), skip_header=True):
    """Yield (src, dst, link_sentiment) for every publish in the source file.

    This function does NOT aggregate or simplify duplicate edges: if the
    same (src,dst) appears multiple times with different LINK_SENTIMENT
    values, each appearance is yielded separately.

    Args:
        path: input file path (CSV/TSV)
        sep: delimiter or 'auto' to sniff
        cols: tuple/list of column names (src, dst, sentiment)
        skip_header: if True, treat the first row as header and use it to
                     locate columns; if False, use positional columns

    Yields:
        (src:str, dst:str, link_sentiment: str|float|None)
    """
    with open(path, newline='', encoding='utf-8') as f:
        # delimiter sniffing consistent with CreateGraph_from_file
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
        # locate columns
        header = None
        idxs = None
        if skip_header:
            try:
                header = next(reader)
            except StopIteration:
                return
            if cols:
                idxs = []
                for c in cols:
                    try:
                        idxs.append(header.index(c))
                    except ValueError:
                        # column not found: fall back to positional interpretation
                        idxs = None
                        break
        # iterate rows and yield triples
        for row in reader:
            if not row:
                continue
            if idxs:
                # ensure row has enough columns
                row_sel = [row[i] if i < len(row) else '' for i in idxs]
            else:
                # use positional: first two (and third if present)
                row_sel = row[:3]

            if len(row_sel) < 2:
                continue
            src = row_sel[0].strip()
            dst = row_sel[1].strip()
            if not src or not dst:
                continue

            link_sent = None
            if len(row_sel) >= 3:
                raw = row_sel[2].strip()
                if raw != '':
                    # try to parse numeric sentiment/weight
                    try:
                        if '.' in raw:
                            link_sent = float(raw)
                        else:
                            link_sent = int(raw)
                    except Exception:
                        link_sent = raw

            yield (src, dst, link_sent)


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
        G = load_graph_from_edgelist(out_path, sep='\t')
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

def plot_graph():
    G = load_graph_from_edgelist("graph.edgelist", sep='\t')
    print(f"Graph loaded with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    title = f"Full graph ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)"
    draw_and_save_graph(G, "graph.png", title, node_size=4, fig_size=(80, 80), dpi=30)


def plot_all():
    plot_graph()
    plot_partitions()
