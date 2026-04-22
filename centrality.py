import read
import networkx as nx
import csv
import json

def compute_centrality(graph, kind='degree'):
    match kind:
        case 'degree':
            return nx.degree_centrality(graph)
        case 'betweenness':
            return nx.betweenness_centrality(graph)
        case 'closeness':
            return nx.closeness_centrality(graph)
        case 'eigenvector':
            return nx.eigenvector_centrality(graph)
        case _:
            print(f"Unsupported centrality type: {kind}")
            return None

if __name__ == "__main__":
    # Example usage
    graph = read.CreateGraph_from_file('soc-redditHyperlinks-body.tsv', head=1, cols=["SOURCE_SUBREDDIT", "TARGET_SUBREDDIT"], count=False, kind='MultiDiGraph')
    centrality = compute_centrality(graph, kind='degree')
    # print to console (optional)
    print(f"Computed {len(centrality)} centrality values (showing 10):")
    for i, (n, v) in enumerate(sorted(centrality.items(), key=lambda x: x[1], reverse=True)):
        if i >= 10:
            break
        print(n, v)

    def save_centrality(centrality_dict, filename, fmt='csv'):
        """Save centrality dict to file.

        Args:
            centrality_dict: mapping node -> centrality value
            filename: output filename
            fmt: 'csv' or 'json'
        """
        if fmt == 'csv':
            # write header and rows sorted by centrality desc
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['node', 'centrality'])
                for node, val in sorted(centrality_dict.items(), key=lambda x: x[1], reverse=True):
                    writer.writerow([node, val])
        elif fmt == 'json':
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(centrality_dict, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    # Save results to CSV
    out_csv = 'centrality_degree.csv'
    save_centrality(centrality, out_csv, fmt='csv')
    print(f"Saved centrality to {out_csv}")
    